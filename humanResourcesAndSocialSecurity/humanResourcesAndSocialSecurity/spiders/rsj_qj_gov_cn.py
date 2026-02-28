from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, AgriItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex

class RsjQjGovCnSpider(BasePortiaSpider):
    name = "rsj_qj_gov_cn"
    allowed_domains = ["rsj.qj.gov.cn"]
    start_urls = [
        "https://rsj.qj.gov.cn/list/gsgg/auto/108.html",  # 首页>要闻动态>公示公告
        "https://rsj.qj.gov.cn/list/gzdt/auto/48.html",  # 首页>要闻动态>工作动态
        "https://rsj.qj.gov.cn/list/djgz/auto/44.html",  # 首页>要闻动态>党建工作
        "https://rsj.qj.gov.cn/list/jyfw/auto/107.html",  # 首页>业务专栏>就业岗位推送
        "https://rsj.qj.gov.cn/list/sbfw/auto/109.html",  # 首页>业务专栏>社会保险
        "https://rsj.qj.gov.cn/list/sydw/auto/214.html",  # 首页>业务专栏>事业单位
        "https://rsj.qj.gov.cn/list/rsks/auto/127.html",  # 首页>业务专栏>人事考试
        "https://rsj.qj.gov.cn/list/qyzp/auto/213.html",  # 首页>业务专栏>就业业务指引
        "https://rsj.qj.gov.cn/list/ldbzjc/auto/111.html",  # 首页>业务专栏>劳动保障监察
        "https://rsj.qj.gov.cn/list/ldrszyzc/auto/116.html",  # 首页>业务专栏>劳动人事争议仲裁
        "https://rsj.qj.gov.cn/list/disclosure/auto/105.html",  # 首页>交流互动>留言公开
        "https://rsj.qj.gov.cn/list/cjwt/auto/98.html",  # 首页>交流互动>常见问题
        "https://rsj.qj.gov.cn/list/jyxxts/auto/208.html",  # 首页>专题专栏>百日千万招聘专项行动
        "https://rsj.qj.gov.cn/list/pfxc/auto/217.html",  # 首页>专题专栏>人社普法宣传专栏
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r"/auto/", f"/{page + 2}/", base_url)

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    list_items = [[
        Item(ListItems,
            None,
            'body',
            [
                Field('detail_urls','//ul[@class="textDl minH600"]//a/@href',[], type="xpath"),
                Field('publish_times','//ul[@class="textDl minH600"]//div[1]/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"\.value\s*=\s*(\d+)")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//meta[@name="ArticleTitle"]/@content',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//meta[@name="PubDate"]/@content',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('menu',
                       '//div[@class="location"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="text"]//p',
                       [
                       lambda vals:[
                            html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                            for html_str in vals
                                if isinstance(html_str,str) and html_str.strip()
                       ],
                       lambda html_list: [
                            scrapy.Selector(text=html).xpath('string(.)').get().strip()
                            for html in html_list
                            ], Join(separator='\n')], required=False, type='xpath'),

                 Field('attachment',
                       '//div[@class="text"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="text"]//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
