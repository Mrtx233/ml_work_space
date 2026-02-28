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

class RsjCxzGovCnSpider(BasePortiaSpider):
    name = "rsj_cxz_gov_cn"
    allowed_domains = ["rsj.cxz.gov.cn"]
    start_urls = [
        "https://rsj.cxz.gov.cn/rsdt/tpxw.htm",  # 人社动态 > 图片新闻
        "https://rsj.cxz.gov.cn/rsdt/zxdt.htm",  # 人社动态 > 最新动态
        "https://rsj.cxz.gov.cn/rsdt/xsdt.htm",  # 人社动态 > 县市动态
        "https://rsj.cxz.gov.cn/xwzx/tzgg.htm",  # 新闻中心 > 通知公告
        "https://rsj.cxz.gov.cn/ztzl/rddbjy.htm",  # 专题专栏 > 人大代表建议
        "https://rsj.cxz.gov.cn/ztzl/zxwyta.htm",  # 专题专栏 > 政协委员提案
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
                Field('detail_urls','//div[@class="list-word"]/ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list-word"]/ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                Field('next_page', '//span[@class="p_next p_fun"]//a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//span[@class="p_t"]/text()', [Regex(r'\/(\d+)')],type="xpath"),
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
                       '//div[@class="map-word"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="v_news_content"]//p | //div[@class="list-page"]//p',
                       [
                       lambda vals:[
                            html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                            for html_str in vals
                                if isinstance(html_str,str) and html_str.strip()
                       ],
                       lambda html_list: [
                            scrapy.Selector(text=html).xpath('string(.)').get().strip()
                            for html in html_list
                            ], Join(separator='\n')], required=True, type='xpath'),

                 Field('attachment',
                       '//div[@class="v_news_content"]//p//a/@href |//div[@class="list-page"]//a/@href ',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="v_news_content"]//p//a//text() | //div[@class="list-page"]//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
