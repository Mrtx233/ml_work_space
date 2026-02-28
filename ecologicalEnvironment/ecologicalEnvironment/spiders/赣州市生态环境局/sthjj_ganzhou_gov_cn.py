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
    'detail_urls': "//div[@class='pageList listContent infoList']/li/h4/a/@href",
    'publish_times': "//div[@class='pageList listContent infoList']/li/h4/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="crumb"]//a//text()',
    'content': '//div[contains(@class, "article-content")]//p',
    'attachment': '//div[contains(@class, "article-content")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "article-content")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('page_div',(\d+),",
}


class SthjjGanzhouGovCn(BasePortiaSpider):
    name = "sthjj_ganzhou_gov_cn"
    allowed_domains = ["sthjj.ganzhou.gov.cn"]

    start_urls = [
        'https://sthjj.ganzhou.gov.cn/gzssthjj/tzgg/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/tpxw/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c102928/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/xwfb/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c103287/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c103291/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c103292/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c103294/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/c115381/common_list.shtml',
        'https://sthjj.ganzhou.gov.cn/gzssthjj/qyhjxx/common_list.shtml'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('common_list.shtml', f'common_list_{page + 1}.shtml')

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
