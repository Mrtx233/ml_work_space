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

class RsjYueyangGovCnSpider(BasePortiaSpider):
    name = "rsj_yueyang_gov_cn_index"
    allowed_domains = ["rsj.yueyang.gov.cn"]
    start_urls = [
        "https://rsj.yueyang.gov.cn/rsks/71684/index.htm",  # 公务员事业单位考试
        "https://rsj.yueyang.gov.cn/rsks/71685/index.htm",  # 专业技术职（执）业资格考试
        "https://rsj.yueyang.gov.cn/rsks/71686/index.htm",  # 其他考试信息
        "https://rsj.yueyang.gov.cn/rsks/71687/index.htm",  # 证书管理
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.split('.htm')[0]}_{page + 1}.htm"

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
                Field('detail_urls','//div[@class="list_li my-4 news_list"]/ul/li//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list_li my-4 news_list"]/ul/li/a/span[2]/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"else if\(num>(\d+)\)")],type="xpath"),
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
                       '//div[@class="col-12"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="show-content shadow  mb-5"]//p',
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
                       '//div[@class="show-content shadow  mb-5"]//p/a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="show-content shadow  mb-5"]//p/a/text()',
                       [], type='xpath', file_category='attachment'),



             ])]]
