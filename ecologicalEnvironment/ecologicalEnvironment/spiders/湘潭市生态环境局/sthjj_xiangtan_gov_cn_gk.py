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
    'detail_urls': "//div[@class='gkgd-con']/ul/li/a/@href",
    'publish_times': "//div[@class='gkgd-con']/ul/li/span/text()",
    'total_page': "//div[@id='pagination']/span[1]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="breadcrumb no-margin"]//a/text()',
    'content': '//div[contains(@class, "xl-xqnr")]//p',
    'attachment': '//div[contains(@class, "xl-xqnr")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "xl-xqnr")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"/(\d+)页",
}


class SthjjXiangtanGovCnGk(BasePortiaSpider):
    name = "sthjj_xiangtan_gov_cn_gk"
    allowed_domains = ["sthjj.xiangtan.gov.cn"]

    start_urls = [
        'https://sthjj.xiangtan.gov.cn/6250/21686/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6255/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6262/6266/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6262/6269/index.htm',
        'https://sthjj.xiangtan.gov.cn/6240/6243/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6262/6265/index.htm',
        'https://sthjj.xiangtan.gov.cn/6240/6241/index.htm',
        'https://sthjj.xiangtan.gov.cn/6240/24651/index.htm',
        'https://sthjj.xiangtan.gov.cn/6240/24650/index.htm',
        'https://sthjj.xiangtan.gov.cn/6240/24647/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6262/6268/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/21677/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/21678/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/24701/27905/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/24701/27906/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/24701/27907/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/21722/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/18136/index.htm',
        'https://sthjj.xiangtan.gov.cn/6250/6261/index.htm'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_base_url = base_url.rstrip('/').replace('index.htm', '')
        return f"{clean_base_url}index_{page}.htm"

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
                        lambda x: x[0] if (x and x[0]) else "1"
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
