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

class RstQinghaiGovCnSpider(BasePortiaSpider):
    name = "rst_qinghai_gov_cn"
    allowed_domains = ["rst.qinghai.gov.cn"]
    start_urls = [
        "https://rst.qinghai.gov.cn/zxzx/rdzx/list/1.html",  # 资讯中心热点资讯
        "https://rst.qinghai.gov.cn/zxzx/tzgg/list/1.html",  # 资讯中心通知公告
        "https://rst.qinghai.gov.cn/zxzx/rsyw/list/1.html",  # 资讯中心青海人社
        "https://rst.qinghai.gov.cn/zxzx/swdt/list/1.html",  # 资讯中心省际动态
        "https://rst.qinghai.gov.cn/zxzx/gnyw/list/1.html",  # 资讯中心国内要闻
        "https://rst.qinghai.gov.cn/ztzl/gxzcxc/list/1.html",  # 校毕业生就业政策宣传-政策宣传
        "https://rst.qinghai.gov.cn/ztzl/gzqxzcfg/list/1.html",  # 专题专栏-根治欠薪-政策法规
        "https://rst.qinghai.gov.cn/ztzl/gzqxbgt/list/1.html",  # 专题专栏-根治欠薪-曝光台
        "https://rst.qinghai.gov.cn/ztzl/gzqxqxrz/list/1.html",  # 专题专栏-根治欠薪-工作动态
        "https://rst.qinghai.gov.cn/ztzl/gzqxwqqd/list/1.html",  # 专题专栏-根治欠薪-维权渠道
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r"/(\d+)\.html$", f"/{page + 2}.html", base_url)

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
                Field('detail_urls','//div[@class="new_jobs_con"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="new_jobs_con"]//ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="page"]//a[last()]/@href', [Regex(r"/(\d+)\.html$")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//div[@class="content_tt"]/text()',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//div[@class="content_ttx"]/span[1]/text()',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('menu',
                       '//div[@class="cur_pos"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//div[@class="content_ttx"]/span[1]/text()',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="content_con"]//p',
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
                       '//div[@class="content_con"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="content_con"]//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
