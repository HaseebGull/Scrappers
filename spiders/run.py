import urllib.parse
import sys
import urllib.parse

from scrapy.crawler import CrawlerProcess

filename = sys.argv[1]
classname = sys.argv[2]
scraper_name = sys.argv[3]
store_url = sys.argv[4]
store_ids = sys.argv[5]
product_url = urllib.parse.unquote_plus(sys.argv[6])

if store_url != 'None':
    start_url = store_url
else:
    start_url = product_url

some_module = __import__(filename)
SpiderName = getattr(some_module, classname)
from FashionStores.Scrapers.Scrapers.settings import *

my_settings = {
    # 'COOKIES_DEBUG': True,
    'COOKIES_ENABLED': True,
    # 'COMPRESSION_ENABLED': True,
    'AJAXCRAWL_ENABLED': True,
    'dont_redirect': True,
    'REACTOR_THREADPOOL_MAXSIZE': 20,
    'HTTPERROR_ALLOWED_CODES': [404, 403],
    'handle_httpstatus_list': [403],
}
process = CrawlerProcess(settings=my_settings)


def run_spider():
    process.crawl(SpiderName, name=scraper_name, start_urls=[start_url], product_url=True)
    process.start(stop_after_crawl=True)


run_spider()

# import sys
#
# from scrapy.crawler import CrawlerRunner
# from twisted.internet import reactor
#
# print('sys.argv', sys.argv)
# filename = sys.argv[1]
# classname = sys.argv[2]
# scraper_name = sys.argv[3]
#
# store_url = sys.argv[4]
# store_ids = sys.argv[5]
# product_url = sys.argv[6]
# if store_url != 'None':
#     start_url = store_url
# else:
#     start_url = product_url
#
# some_module = __import__(filename)
# SpiderName = getattr(some_module, classname)
# my_settings = {
#     'COOKIES_DEBUG': True
# }
#
# def run_spider():
#     runner = CrawlerRunner()
#     d = runner.crawl(SpiderName, name=scraper_name, start_urls=[start_url], product_url=True)
#     d.addBoth(lambda _: reactor.stop())
#     reactor.run()  # the script will block here until the crawling is finished
#
# run_spider()
