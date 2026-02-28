from __future__ import absolute_import

import scrapy
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, AgriItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex

class HrssSanyaGovCnSpider(BasePortiaSpider):
    name = "hrss_sanya_gov_cn"
    allowed_domains = ["hrss.sanya.gov.cn"]
    start_urls = [
        "https://hrss.sanya.gov.cn/rsjsite/gzdt/list2.shtml",  # 首页>要闻动态>工作动态
        "https://hrss.sanya.gov.cn/rsjsite/tzgg/list2.shtml",  # 首页>要闻动态>通知公告
        "https://hrss.sanya.gov.cn/rsjsite/zcjd/list2.shtml",  # 首页>解读回应>政策解读
        "https://hrss.sanya.gov.cn/rsjsite/hygq/list2.shtml",  # 首页>解读回应>回应关切
        "https://hrss.sanya.gov.cn/rsjsite/dsxxjy/list2.shtml",  # 首页>党史学习教育
        "https://hrss.sanya.gov.cn/rsjsite/sjd/list2.shtml",  # 首页>学习宣传贯彻党的十九大精神
        "https://hrss.sanya.gov.cn/rsjsite/djgz/list2.shtml",  # 首页>党建工作
        "https://hrss.sanya.gov.cn/rsjsite/sjkf/list2.shtml",  # 首页>数据开放
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.split('.shtml')[0]}_{page + 2}.shtml"

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
                Field('detail_urls','//div[@class="list_1 box3"]/ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list_1 box3"]/ul//em/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"createPageHTML\('page_div',(\d+)")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//meta[@name="description"]/@content',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//meta[@name="others"]/@content',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('menu',
                       '//div[@class="crumbs"]//text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="SiteName"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="pages_content"]//span',
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

                 # Field('attachment',
                 #       '//div[@class="other-word"]//a/@href',
                 #       [], type='xpath', file_category='attachment'),
                 #
                 # Field('attachment_name',
                 #       '//div[@class="other-word"]//a//text()',
                 #       [], type='xpath', file_category='attachment'),
                 #
                 # Field('status',
                 #       '//div[@class="maincon-info"]/div[5]/div[1]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       '//div[@class="maincon-info"]/div[1]/div[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       '//div[@class="maincon-info"]/div[3]/div[1]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       '//div[@class="maincon-info"]/div[1]/div[1]/text()',
                 #       [], required=False, type='xpath'),

             ])]]
