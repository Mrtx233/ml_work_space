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

class HrssNxGovCnSpider(BasePortiaSpider):
    name = "hrss_nx_gov_cn"
    allowed_domains = ["hrss.nx.gov.cn"]
    start_urls = [
        "https://hrss.nx.gov.cn/gzdt/szyw/",  # 首页>资讯中心>时政要闻
        "https://hrss.nx.gov.cn/gzdt/tpxx/",  # 首页>资讯中心>图片新闻
        "https://hrss.nx.gov.cn/gzdt/rsyw/",  # 首页>资讯中心>工作动态
        "https://hrss.nx.gov.cn/gzdt/gsgg/",  # 首页>资讯中心>公示公告
        "https://hrss.nx.gov.cn/gzdt/sxdt/",  # 首页>资讯中心>市县动态
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 清理base_url末尾的/，拼接index_{page+2}.html
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page + 1}.html"


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
                Field('detail_urls','//div[@class="newList_specifics_value"]//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="newList_specifics_shijian"]/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r'createPageHTML\(\s*(\d+)\s*,')],type="xpath"),
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
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type='xpath'),

                 Field('menu',
                       '//div[@class="newDetail"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p',
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
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p//a/@href | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p//a/text() | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
