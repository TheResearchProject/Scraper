# This Python file uses the following encoding: UTF-8

import re
from scrapy.spider import BaseSpider
from scrapy.http import Request
from scrapy.shell import inspect_response
from scrapy.selector import Selector


from nola_com.items import Article, Comment, Image
import urlparse, json, datetime, urllib, os, shutil, html2text
from scrapy.utils.request import request_fingerprint
import nola_com.settings as settings



class ArticleSpider(BaseSpider):
    name = 'articles'
    allowed_domains = ['www.nola.com','bootstrap.advancedigital.fyre.co','free.sharedcount.com']
    start_urls = ['http://www.nola.com/crime/']
    
    def __init__(self, full = False):
        self.full = full

    def parse(self, response):
    #inspect_response(response)
        if response.status != 200:
            return
        sel = Selector(response)	
        for link in sel.xpath('//div[starts-with(@class,"h2")]/a/@href').extract():
            if link == 'http://www.nola.com/crime/index.ssf/': continue
            yield Request(url=link,callback=self.scrape_article)
        a = sel.xpath('//div[@id="river-load"]/a[@class="button"]/@href').extract()
        if len(a)>0:
            yield Request(urlparse.urljoin(response.url,a[0]))
            yield Request(urlparse.urljoin(response.url,a[0].replace('2','3')))
        if self.full:
            nexta = sel.xpath('//a[@title="Next page"]/@href').extract()
            if len(nexta)>0:
                yield Request(urlparse.urljoin(response.url,nexta[0]))
            for link in sel.xpath('//select[@id="date_select"]/option[@name]/@value').extract():
                yield Request(urlparse.urljoin(response.url,link))

    def scrape_article(self, response):
        if response.status != 200:
            inspect_response(response)
        sel = Selector(text=response.body.replace('/>','>'))
        meta = {}
        for v in sel.xpath('//script').re('".+":\s*".+"'):
            m = re.search('"(.+)":\s*"(.+)"',v)
            meta[m.group(1)] = m.group(2)
        article = Article()
        author_name = ''.join(sel.xpath('//div[@id="Byline"]/span[@class="author vcard"]/a/text()').re('\s*(.+),'))
        author_id = ''.join(sel.xpath('//div[@id="Byline"]/span[@class="author vcard"]/a/@href').re('/user/(.+)/posts.html'))
        article['author'] = {'name': author_name,'id': author_id, 'type': 'author'}
        st = ''.join(sel.xpath('//div[@id="Byline"]//text()').extract()).strip()
        m = re.search('on (.+)$',st)
        article['date'] = re.search('on (.+)$',st).group(1) if m != None else None
        article['views'] = None
        article['lead'] = ''.join(sel.xpath('//script').re('var desc\s*=\s\'(.+)\';'))
        
        #article['text'] = ''.join(sel.xpath('//div[@class="entry-content"]//text()').extract()).strip()
        h = html2text.HTML2Text(bodywidth=0)
        h.ignore_links = True
        h.ignore_iamges = True
        article['text'] = h.handle(''.join(sel.xpath('//div[@class="entry-content"]').extract())).strip()
        del h
        article['title'] = ''.join(sel.xpath('//div[@id="article"]//h1/text()').extract())
        article['url'] = response.url
        article['comments'] = []
        article['images'] = []
        for img in sel.xpath('//div[@id="article_container"]//span[@data-image]'):
            if img.xpath('./@data-position').extract() == [u'byline-avatar']: continue
            image = Image()
            image['imageurl'] = ''.join(img.xpath('./@data-image').extract())
            image['imagename'] = ''.join(img.xpath('./text()').extract()).strip()
            image['position'] = ''.join(img.xpath('./@data-position').extract())
            article['images'].append(image)

        url = 'https://free.sharedcount.com/url?url=%s&apikey=479dfb502221d2b4c4a0433c600e16ba5dc0df4e' % response.url
        request = Request(url,self.scrape_shares)
        request.meta['article'] = article
        try:
            request.meta['commentsurl'] = 'http://bootstrap.advancedigital.fyre.co/bs3/v3.1/%s/%s/%s=/init' % (meta['networkId'],meta['siteId'],meta['collectionMeta'][101:101+43])
        except:
            inspect_response(response)
        yield request

    def scrape_shares(self, response):
        article = response.meta['article']
        if response.status==401 and 'quota_exceeded' in response.body:
            request = Request(response.url,callback=self.scrape_shares,dont_filter=True)
            request.meta['article'] = article
            request.meta['commentsurl'] = response.meta['commentsurl']
            yield request
            return

        r = json.loads(response.body)
        article['twitter'] = r[u'Twitter']
        article['facebook'] = r[u'Facebook'][u'total_count']
        article['googleplus'] = r[u'GooglePlusOne']
        article['pinit'] = r[u'Pinterest']
        url = response.meta['commentsurl']
        request = Request(url,self.scrape_comments)
        request.meta['article'] = article
        yield request

    def scrape_comments(self, response):
        article = response.meta['article']
        if response.status == 404:
            yield article
            return
        if response.status in [400,503,504]:
            request = Request(response.url,callback=self.scrape_comments,dont_filter=True)
            request.meta['article'] = article
            yield request
            return
        r = json.loads(response.body)
        for content in r['headDocument']['content']:
            if 'authorId' not in content['content'].keys() or 'bodyHtml' not in content['content'].keys(): continue
            comment = Comment()
            comment['id'] = content['content']['id']
            comment['parent_id'] = content['content']['parentId']
            comment['author'] = {
                'name': r['headDocument']['authors'][content['content']['authorId']]['displayName'],
                'id': content['content']['authorId'],
                'type': 'commentator'
            }
            comment['date'] = datetime.datetime.utcfromtimestamp(content['content']['createdAt']).isoformat()
            comment['score'] = len(content['content']['annotations']['likedBy']) if 'annotations' in content['content'].keys() and 'likedBy' in content['content']['annotations'].keys() else 0 
            comment['content'] = ''.join(Selector(text=content['content']['bodyHtml']).xpath('//text()').extract()).strip()
            article['comments'].append(comment)
        yield article
