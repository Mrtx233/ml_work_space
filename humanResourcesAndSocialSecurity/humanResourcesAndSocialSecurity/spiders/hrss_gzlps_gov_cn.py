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

class HrssGzlpsGovCnSpider(BasePortiaSpider):
    name = "hrss_gzlps_gov_cn"
    allowed_domains = ["hrss.gzlps.gov.cn"]
    start_urls = [
        # 工作动态分类
        "https://hrss.gzlps.gov.cn/gzdt_42000/gzdt/index.html",  # 人社要闻
        "https://hrss.gzlps.gov.cn/gzdt_42000/szyw/index.html",  # 时政要闻
        # 公众参与分类
        "https://hrss.gzlps.gov.cn/gzcy_42075/xwfb_42078/index.html",  # 新闻发布会
        "https://hrss.gzlps.gov.cn/gzcy_42075/zjdc_42081/index.html",  # 征集调查
        # 专题专栏分类
        "https://hrss.gzlps.gov.cn/ztzl_42084/djzc/index.html",  # 调解仲裁
        "https://hrss.gzlps.gov.cn/ztzl_42084/srxxjhjs/index.html",  # 学习贯彻总书记重要讲话精神
        "https://hrss.gzlps.gov.cn/ztzl_42084/xzzf/xzzfzdjz/index.html",  # 行政执法-制度机制
        "https://hrss.gzlps.gov.cn/ztzl_42084/gzqx/index.html",  # 劳动维权治理欠薪
        # 通知公告
        "https://hrss.gzlps.gov.cn/tzgg_42003/index.html",  # 通知公告
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.split('.html')[0]}_{page + 1}.html"

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
                Field('detail_urls','//div[@class="right"]//ul//a/@href | //div[@class="ctt"]//ul//a/@href ',[], type="xpath"),
                Field('publish_times','//div[@class="right"]//ul//span/text() | //div[@class="ctt"]//ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="page"]/script/text()', [Regex(r"createPageHTML\(\s*(\d+)")],type="xpath"),
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
                       '//div[@class="addr"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="content_1"]//p',
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
                       '//div[@class="content_1"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="content_1"]//p//a/text()',
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
