import json, codecs, MySQLdb, locale, datetime, os, urllib2, time

dirName = 'nola_com'

locale.setlocale(locale.LC_ALL, 'en_US.UTF8')
connection = MySQLdb.connect(host="127.0.0.1",user="testdb", passwd="testdb", db="testdb",charset='utf8', use_unicode=True)
connection.autocommit(True)
cursor = connection.cursor()
cursor.execute('SET NAMES UTF8MB4')


stdheaders = {
    'Accept-Encoding':'gzip',
    'Accept-Language':'en-US',
    'Cache-Control':'no-cache',
    'Connection':'keep-alive',
    'Pragma':'no-cache',
    'User-Agent':'Mozilla/5.0 (Windows;U;Windows NT 6.1; en-US) Gecko/20100101 Firefox/35.0'
}
idx = 0
cacheDir = 'cache'
usecache = True
maxRetryCount = 10
retryDelay = 10

#function to open url and retry if needed
def urlopen(url,max_retry_count=maxRetryCount):
    global idx
    retrycount = 0
    while retrycount<max_retry_count:
        idx += 1
        try:
            print '[%d] %s' % (idx,url)
            request = urllib2.Request(url,headers=stdheaders)
            response = urllib2.urlopen(request)
            return response.read()
        except:
            print 'Error opening page!'
            raise
            retrycount += 1
            time.sleep(retryDelay)
    return

def getCacheFileName(url):
    cacheFileName = url.replace('/','_').replace(':','').replace('?','_')
    cacheFileName = os.path.join(cacheDir,os.path.basename(url)[:2],cacheFileName)
    return cacheFileName

def urlopenCache(url):
    cacheFileName = getCacheFileName(url)
    if usecache and os.path.exists(cacheFileName):
        f = open(cacheFileName,'rb')
        result = f.read()
        f.close()
    else:
        if not os.path.exists(os.path.dirname(cacheFileName)):
            os.makedirs(os.path.dirname(cacheFileName))
        result  = urlopen(url)
        if usecache and result != None:
            f = open(cacheFileName,'wb')
            f.write(result)
            f.close()
    return result




def IsNULL(a,b):
    return a if a != None else b

ImageId = None
n = 1
for fileName in os.listdir(dirName):
    if not fileName.lower().endswith('.json'): continue
    print fileName
    f = open(os.path.join(dirName,fileName),'rb')
    for line in f.readlines():
        r = json.loads(unicode(line,'UTF-8').lstrip(unicode(codecs.BOM_UTF8,"utf8")))
        try:
            date = datetime.datetime.strptime(','.join(r[u'date'].split(',')[:2]),'%B %d, %Y at %I:%M %p')
        except:
            continue
        sql = "select `ID` from `NewsItem` where `Title`=%s and `Date`=%s and `IdAuthor`=%s" 
        args = (r[u'title'],date,r[u'author'][u'id'])
        cursor.execute(sql, args)
        rows = cursor.fetchall()
        if len(rows)==0:
            sql = "select max(`ID`)+1 from `NewsItem`"
            cursor.execute(sql)
            NewsItemId = cursor.fetchone()[0]
            if NewsItemId==None: NewsItemId = 1
            sql = "insert into `NewsItem` (`Id`,`Title`,`Lead`,`Date`,`Views`,`Content`,`Url`,`IdAuthor`,`score`,`cat1`,`cat2`,`cat3`,`cat4`,`cat5`,`Twitter`,`Facebook`,`GooglePlus`,`PinIt`) values (%s,%s,%s,%s,NULL,%s,%s,%s,NULL,NULL,NULL,NULL,NULL,NULL,%s,%s,%s,%s);" 
            args = (NewsItemId,r[u'title'],r[u'lead'],date,r[u'text'].encode('UTF-8'),r[u'url'],r[u'author'][u'id'],IsNULL(r['twitter'],0),IsNULL(r['facebook'],0),IsNULL(r['googleplus'],0),IsNULL(r['pinit'],0))
            print NewsItemId, r['url']
            cursor.execute(sql, args)
        else:
            NewsItemId = rows[0][0]
        for comment in r[u'comments']:
            sql = 'select * from `Comment` where `Id`=%s'
            args = (comment['id'],)
            cursor.execute(sql,args)
            rows = cursor.fetchall()
            if len(rows)==0:
                sql = u"insert into `Comment` (`Id`,`AuthorID`,`Content`,`ParentID`,`Score`,`Date`,`AuthorShortname`,`NewsItemId`) values (%s,%s,%s,%s,%s,%s,%s,%s);"
                args = (comment[u'id'],comment[u'author'][u'id'],comment[u'content'],None if comment[u'parent_id']=='' else int(comment[u'parent_id']),comment[u'score'],comment['date'],comment[u'author'][u'name'],NewsItemId)
                cursor.execute(sql,args)
        for image in r[u'images']:
            try:
                ImageData = urlopenCache(image[u'imageurl'])
            except:
                continue
            if len(ImageData)==0: 
                print image[u'imageurl']
                continue
            fileName = os.path.basename(image[u'imageurl'])
            ImageName = '.'.join(fileName.split('.')[:-1])
            ImageType = fileName.split('.')[-1]
            ImageSize = '%1.1fkb' % (len(ImageData)/1024.0)
            sql = "select * from `Images` where `NewsItemId`=%s and `ImageName`=%s" 
            args = (NewsItemId,ImageName)
            cursor.execute(sql,args)
            rows = cursor.fetchall()
            if len(rows)==0:
                if ImageId == None:
                    sql = "select max(`Id`)+1 from `Images`"
                    cursor.execute(sql)
                    ImageId = cursor.fetchone()[0]
                    if ImageId==None: ImageId = 1
                else:
                    ImageId += 1
                sql = u"insert into `Images` (`Id`,`NewsItemId`,`ImageType`,`Image`,`ImageSize`,`ImageCategory`,`ImageName`) values (%s,%s,%s,%s,%s,'',%s)"
                args = (ImageId,NewsItemId,ImageType,ImageData,ImageSize,ImageName)
                try:
                    cursor.execute(sql, args)
                except:
                    print r['url'], image[u'imageurl']
                    print (ImageId,NewsItemId,ImageType,ImageSize,ImageName)
                    continue
        n += 1
    f.close()

