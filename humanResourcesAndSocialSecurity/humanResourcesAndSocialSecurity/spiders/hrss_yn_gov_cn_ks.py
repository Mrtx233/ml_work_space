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

class HrssYnGovCnKsSpider(BasePortiaSpider):
    name = "hrss_yn_gov_cn_ks"
    allowed_domains = ["hrss.yn.gov.cn"]
    start_urls = [
        "https://hrss.yn.gov.cn/ynrsksw/News2.html",  # 工作动态
        "https://hrss.yn.gov.cn/ynrsksw/News3.html",  # 重要通知
        "https://hrss.yn.gov.cn/ynrsksw/News4.html",  # 政策法规
        "https://hrss.yn.gov.cn/ynrsksw/News5.html",  # 常见问题
        "https://hrss.yn.gov.cn/ynrsksw/News6.html",  # 工具下载
        "https://hrss.yn.gov.cn/ynrsksw/Special7.html",  # 公务员考试
        "https://hrss.yn.gov.cn/ynrsksw/Special8.html",  # 事业单位考试
        "https://hrss.yn.gov.cn/ynrsksw/Special9.html",  # 执业（职业）资格考试
        "https://hrss.yn.gov.cn/ynrsksw/Special10.html",  # 其他考试
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r"(\.\w+)$", f"_{page + 1}\\1", base_url)

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
                Field('detail_urls','//div[@class="pagelist"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="pagelist"]//ul//em/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="anpager"]/a[last()]/@href', [Regex(r"_(\d+)\.\w+$"),lambda vals: ['1'] if not vals or (vals and vals[0] == '') else vals],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//div[@class="panel-body"]/h1/text()',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//div[@class="text-center small  page_newsinfo"]//text()',
                       [Regex(r"日期：(\d{4}-\d{2}-\d{2})")],type='xpath'),

                 Field('menu',
                       '//ol[@class="breadcrumb"]/li/a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//div[@class="text-center small  page_newsinfo"]//text()',
                       [Regex(r"来源：\s*([^\s]+)")], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="newscont"]//p',
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
                       '//div[@class="newscont"]//p//a/@href | //div[@class="newscont"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="newscont"]//p//a/text() | //div[@class="newscont"]//a/text()',
                       [], type='xpath', file_category='attachment'),

                 # Field('indexnumber',
                 #       '//div[@class="scroll_main"]/table[1]//tr[1]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       '//div[@class="scroll_main"]/table[1]//tr[2]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       '//div[@class="scroll_main"]/table[1]//tr[2]/td[4]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       '//div[@class="scroll_main"]/table[1]//tr[3]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       '//div[@class="scroll_main"]/table[1]//tr[3]/td[4]/text()',
                 #       [], required=False, type='xpath'),

             ])]]
