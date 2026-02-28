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

class RsjQjGovCnGfSpider(BasePortiaSpider):
    name = "rsj_qj_gov_cn_gf"
    allowed_domains = ["rsj.qj.gov.cn"]
    start_urls = [
        "https://rsj.qj.gov.cn/list/system/auto/99.html",  # 政府信息公开制度
        # "https://rsj.qj.gov.cn/list/jyta/auto/195.html",  # 建议提案
        # "https://rsj.qj.gov.cn/list/zzjg/auto/193.html",  # 组织机构
        # "https://rsj.qj.gov.cn/list/zcjd/auto/191.html",  # 政策解读
        # "https://rsj.qj.gov.cn/list/czyjs/auto/192.html",  # 财政预决算
        # "https://rsj.qj.gov.cn/list/zdgztb/auto/196.html",  # 重点工作通报
        # "https://rsj.qj.gov.cn/list/zdhytb/auto/197.html",  # 重大会议通报
        # "https://rsj.qj.gov.cn/list/xzcf/auto/200.html",  # 行政处罚和行政强制
        # "https://rsj.qj.gov.cn/list/xzsyxsf/auto/201.html",  # 行政事业性收费
        # "https://rsj.qj.gov.cn/list/xzxk/auto/224.html",  # 行政许可
        # "https://rsj.qj.gov.cn/list/ylfw/auto/206.html",  # 养老服务
        # "https://rsj.qj.gov.cn/list/xxgknb/auto/124.html",  # 政府信息公开年报
        # "https://rsj.qj.gov.cn/list/qtwj/auto/141.html",  # 其他文件
    ]


    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url})

    list_items = [[
        Item(ListItems,
            None,
            'body',
            [
                Field('detail_urls','//ul[contains(@class, "p-list")]//a/@href',[], type="xpath"),
                Field('publish_times','//ul[contains(@class, "p-list")]/li/text()',[Regex(r"\d{4}\-\d{2}\-\d{2}")],type="xpath"),
                # 翻页url
                Field('next_page', '//div[@class="page"]/ul/li[last()]/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="page"]/ul/li[last()-1]/a/text()', [],type="xpath"),
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

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="public_web_con des"]//p',
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
                       '//div[@class="public_web_con des"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="public_web_con des"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

                 # Field('indexnumber',
                 #       '//div[@class="content-table"]//tr[1]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       '//div[@class="content-table"]//tr[4]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('category',
                 #       '//div[@class="content-table"]//tr[1]/td[4]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       '//div[@class="content-table"]//tr[2]/td[2]/text()',
                 #       [], required=False, type='xpath'),



             ])]]
