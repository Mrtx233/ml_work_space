from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, HbeaItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex


# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': "//div[@id='op1']/ul/li/a/@href",
    'publish_times': "//div[@id='op1']/ul/li/span/text()",
    'total_page': '//script//text()',
}

DETAIL_XPATH = {
    'title': "//div[@id='title']/h1/text()",
    'publish_time': "//div[@id='title']/p/text()",
    'source': "//div[@id='title']/p/text()",
    'menu': '//div[@id="crumb"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    'publish_time': r"时间：\s*(\d{4}-\d{2}-\d{2})",
    'source': r"来源：\s*(.*?)\s*",
}


class KjjHuangshiGovCnGkSpider(BasePortiaSpider):
    name = "kjj_huangshi_gov_cn_gk"
    allowed_domains = ["kjj.huangshi.gov.cn"]

    start_urls = [
        "https://kjj.huangshi.gov.cn/zfxxgkml/zc/gfxwj/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/zc/qtzdgkwj/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/zc/Zcjd/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/zfgzjg/jgzn/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/zfgzjg/nsjg/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/zfgzjg/zsjg/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/fzjh/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/kjtj/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/bmyjs/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/zfcg/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/qtzdgknr/rsxx/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/qtzdgknr/gzzj/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/qtzdgknr/zxwytabl/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/qtzdgknr/rddbjybl/index.shtml",
        "https://kjj.huangshi.gov.cn/zfxxgkml/fdzdgknr/qtzdgknr/zclszx/index.shtml"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        path, filename = base_url.rstrip('/').rsplit('/', 1)
        return f"{path}/{filename.replace('.shtml', f'_{page}.shtml')}"

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
