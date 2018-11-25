# Scrapy settings for nola_com project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'nola_com'

SPIDER_MODULES = ['nola_com.spiders']
NEWSPIDER_MODULE = 'nola_com.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'nola_com (+http://www.yourdomain.com)'
USER_AGENT = 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0'
HTTPERROR_ALLOW_ALL = True
