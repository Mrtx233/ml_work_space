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

class RsjGuiyangGovCnSpider(BasePortiaSpider):
    name = "rsj_guiyang_gov_cn"
    allowed_domains = ["rsj.guiyang.gov.cn"]
    start_urls = [
        "https://rsj.guiyang.gov.cn/rzxzx/gzdt/qxdt/index.html",  # 首页>资讯中心>工作动态>区县动态
        "https://rsj.guiyang.gov.cn/rzxzx/gzdt/yw/index.html",  # 首页>资讯中心>工作动态>要闻
        "https://rsj.guiyang.gov.cn/rzxzx/xxgg/index.html",  # 首页>资讯中心>信息公告
        "https://rsj.guiyang.gov.cn/rzxzx/dwgk4036dwgknrgzdt/index.html",  # 首页>资讯中心>基层党建
        "https://rsj.guiyang.gov.cn/rhdcy/hdcyyjzj/index.html",  # 首页>互动参与>意见征集
        "https://rsj.guiyang.gov.cn/rhdcy/hygq/index.html",  # 首页>互动参与>回应关切
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
                Field('detail_urls','//div[@class="right-li clearfix"]//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="right-li clearfix"]/a/p/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@id="pages"]/script/text()', [Regex(r"createPage\(\s*(\d+)")],type="xpath"),
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
                       '//div[@class="wz"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

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
                       '//div[@class="text"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="text"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
