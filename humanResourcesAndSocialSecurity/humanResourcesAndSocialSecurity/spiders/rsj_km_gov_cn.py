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

class RsjKmGovCnSpider(BasePortiaSpider):
    name = "rsj_km_gov_cn"
    allowed_domains = ["rsj.km.gov.cn"]
    start_urls = [
        # "https://rsj.km.gov.cn/gzdt/",  # 首页/工作动态
        # "https://rsj.km.gov.cn/tzgg/",  # 首页/通知公告
        "https://rsj.km.gov.cn/hdjl/cjwtwd/",  # 首页/互动交流/常见问题问答
        # "https://rsj.km.gov.cn/zxfw/fwzn/",  # 首页/在线服务/服务指南
        # "https://rsj.km.gov.cn/zxfw/zlxz/",  # 首页/在线服务/资料下载
        # "https://rsj.km.gov.cn/dqzh/zbhd/",  # 首页/党建窗口/支部活动
        # "https://rsj.km.gov.cn/dqzh/jgdj/",  # 首页/党建窗口/机关党建
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 移除base_url末尾的/，拼接index_{page}.shtml
        base_url_clean = base_url.rstrip('/')  # 清理末尾的/，避免出现//index_1.shtml
        return f"{base_url_clean}/index_{page + 2}.shtml"

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
                Field('detail_urls','//div[@class="list-text"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list-text"]//ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', "//script/text()", [Regex(r"ele\.value>(\d+)")], type="xpath")
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
                       '//div[@class="list-title"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="content"]//p',
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
                       '//div[@class="content"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="content"]//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
