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
    'detail_urls': "//div[@class='djzt_right left ml15']/ul/li/a/@href | //div[@class='zfxxgk_zdgkc']/ul/li/a/@href",
    'publish_times': "//div[@class='djzt_right left ml15']/ul/li/span/text() | //div[@class='zfxxgk_zdgkc']/ul/li/b/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="dqwz_h"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    'publish_time': r"\d{4}-\d{1,2}-\d{1,2}",
    'source': r"\d{4}-\d{1,2}-\d{1,2}",
    'menu': r"\d{4}-\d{1,2}-\d{1,2}",
}


class CzjZunyiGovCn(BasePortiaSpider):
    name = "czj_zunyi_gov_cn"
    allowed_domains = ["czj.zunyi.gov.cn"]

    start_urls = [
        'https://czj.zunyi.gov.cn/czdt_1/lldt/',
        'https://czj.zunyi.gov.cn/czdt_1/czdt/',
        'https://czj.zunyi.gov.cn/tzgg/',
        'https://czj.zunyi.gov.cn/djzt/jgdj/',
        'https://czj.zunyi.gov.cn/czsj/',
        'https://czj.zunyi.gov.cn/bszn/',
        'https://czj.zunyi.gov.cn/zfxjjhxzsyxsfmlqd/',
        'https://czj.zunyi.gov.cn/xzzq/',
        'https://czj.zunyi.gov.cn/zcfg/',
        'https://czj.zunyi.gov.cn/ztzl/wlaqxcz/',
        'https://czj.zunyi.gov.cn/ztzl/wzndbb/',
        'https://czj.zunyi.gov.cn/ztzl/jsjf/',
        'https://czj.zunyi.gov.cn/ztzl/fzxxgk_5825853/',
        'https://czj.zunyi.gov.cn/ztzl/shzazdgz/',
        'https://czj.zunyi.gov.cn/zfxxgk/zfxxgkzd/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/lzyj/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/czcfqz/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/czyjs_5709972/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/sfgk1/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/zfcg_5709973/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/fpzj_5709971/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/zkly/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/qtfdxx/zcwj/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/qtfdxx/xzql_5709974/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/qtfdxx/ssjygk/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/czzjzdjc/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/qzqd/qzqd/',
        'https://czj.zunyi.gov.cn/zfxxgk/fdzdgknr/qzqd/qlyxlct/',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.html"

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
                Field('total_page', LIST_XPATH["total_page"], [Regex(REGEX["total_page"])], type="xpath"),
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
                Field('publish_time', DETAIL_XPATH["publish_time"], [Regex(REGEX["publish_time"])], required=False, type='xpath'),
                Field('source', DETAIL_XPATH["source"], [Regex(REGEX["source"])], required=False, type='xpath'),
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
