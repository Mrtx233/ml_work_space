from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ...items import ListItems, HbeaItem
from ...utils.spiders import BasePortiaSpider
from ...utils.starturls import FeedGenerator, FragmentGenerator
from ...utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex


# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': "//div[@class='listnews']/ul/li/a/@href",
    'publish_times': "//div[@class='listnews']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wz_top"]//a/text()',
    'content': '//div[contains(@class, "j-fontContent")]//p',
    'attachment': '//div[contains(@class, "j-fontContent")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "j-fontContent")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageCount:(\d+)",
}


class SthjjBengbuGovCn(BasePortiaSpider):
    name = "sthjj_bengbu_gov_cn"
    allowed_domains = ["sthjj.bengbu.gov.cn"]

    start_urls = [
        'https://sthjj.bengbu.gov.cn/content/column/6807441?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6807451?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6813991?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814001?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/jggk/jgzz/index.html',
        'https://sthjj.bengbu.gov.cn/jggk/ldfg/index.html',
        'https://sthjj.bengbu.gov.cn/jggk/nsjg/index.html',
        'https://sthjj.bengbu.gov.cn/jggk/xsdw/index.html',
        'https://sthjj.bengbu.gov.cn/jggk/pcjg/index.html',
        'https://sthjj.bengbu.gov.cn/content/column/6807531?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/hbyw/hjzl/hjzkgb/index.html',
        'https://sthjj.bengbu.gov.cn/content/column/6814131?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814181?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814191?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814211?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814221?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814231?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/hbyw/hpsp/hjyxpj/bags/index.html',
        'https://sthjj.bengbu.gov.cn/content/column/6814291?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6807601?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6807621?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6818441?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814491?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814511?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814691?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814851?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814501?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6814961?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6820311?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6820321?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6820501?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6820771?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6820891?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6821422?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6821917?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6822075?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/ztzlan/clffyzxxxxcgcqgqssthjbhdhjsdjt/index.html',
        'https://sthjj.bengbu.gov.cn/ztzlan/djxxjy/index.html',
        'https://sthjj.bengbu.gov.cn/content/column/6822779?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6822865?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/ztzlan/ahssthjbhdcbb/dcgz/index.html',
        'https://sthjj.bengbu.gov.cn/content/column/6822982?pageIndex=1',
        'https://sthjj.bengbu.gov.cn/content/column/6822983?pageIndex=1'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('pageIndex=1', f'pageIndex={page + 1}')

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_times"])], type="xpath"),
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [
                        Regex(REGEX["total_page"]),
                        lambda x: x[0].strip() if (
                                    isinstance(x, list) and x and x[0] and x[0].strip().isdigit()) else "1"
                    ],
                    type="xpath"
                )
            ]
        )
    ]]

    # ===================== 详情页配置 =====================
    items = [[
        Item(
            HbeaItem,
            None,
            'body',
            [
                Field('title', DETAIL_XPATH["title"], [], required=False, type='xpath'),
                Field('publish_time', DETAIL_XPATH["publish_time"], [], required=False, type='xpath'),
                Field('source', DETAIL_XPATH["source"], [], required=False, type='xpath'),
                Field('menu', DETAIL_XPATH["menu"], [Text(), Join(separator='>')], type="xpath"),
                Field(
                    'content',
                    DETAIL_XPATH["content"],
                    [
                        lambda vals: [
                            html_str.strip()
                            .replace('&quot;', '"')
                            .replace('&amp;', '&')
                            for html_str in vals
                            if isinstance(html_str, str) and html_str.strip()
                        ],
                        lambda html_list: [
                            scrapy.Selector(text=html)
                            .xpath('string(.)')
                            .get()
                            .strip()
                            for html in html_list
                        ],
                        Join(separator='\n')
                    ],
                    required=False,
                    type='xpath'
                ),
                Field('attachment', DETAIL_XPATH["attachment"], [], required=False, type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], required=False, type='xpath', file_category='attachment'),
            ]
        )
    ]]
