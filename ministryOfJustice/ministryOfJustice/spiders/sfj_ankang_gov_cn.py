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
    'detail_urls': "//ul[@class='newlist']/li/a/@href",
    'publish_times': "//ul[@class='newlist']/li/span/text()",
    'total_page': "//div[@class='page']/a[last()]/@href",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="location"]//a/text()',
    'content': '//div[contains(@id, "fontzoom")]//p',
    'attachment': '//div[contains(@id, "fontzoom")]//a/@href',
    'attachment_name': '//div[contains(@id, "fontzoom")]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"_(\d+)\.html$",
}


class SfjAnkangGovCnSpider(BasePortiaSpider):
    name = "sfj_ankang_gov_cn"
    allowed_domains = ["sfj.ankang.gov.cn"]

    start_urls = [
        "https://sfj.ankang.gov.cn/Node-6059.html",
        "https://sfj.ankang.gov.cn/Node-6060.html",
        "https://sfj.ankang.gov.cn/Node-6066.html",
        "https://sfj.ankang.gov.cn/Node-6067.html",
        "https://sfj.ankang.gov.cn/Node-6068.html",
        "https://sfj.ankang.gov.cn/Node-6069.html",
        "https://sfj.ankang.gov.cn/Node-6696.html",
        "https://sfj.ankang.gov.cn/Node-95424.html",
        "https://sfj.ankang.gov.cn/Node-6089.html",
        "https://sfj.ankang.gov.cn/Node-94446.html",
        "https://sfj.ankang.gov.cn/Node-6088.html",
        "https://sfj.ankang.gov.cn/Node-94435.html",
        "https://sfj.ankang.gov.cn/Node-6085.html",
        "https://sfj.ankang.gov.cn/Node-6083.html",
        "https://sfj.ankang.gov.cn/Node-6062.html",
        "https://sfj.ankang.gov.cn/Node-6074.html",
        "https://sfj.ankang.gov.cn/Node-6071.html",
        "https://sfj.ankang.gov.cn/Node-6093.html",
        "https://sfj.ankang.gov.cn/Node-92322.html",
        "https://sfj.ankang.gov.cn/Node-6096.html",
        "https://sfj.ankang.gov.cn/Node-6097.html",
        "https://sfj.ankang.gov.cn/Node-6098.html",
        "https://sfj.ankang.gov.cn/Node-6099.html",
        "https://sfj.ankang.gov.cn/Node-6100.html",
        "https://sfj.ankang.gov.cn/Node-6102.html",
        "https://sfj.ankang.gov.cn/Node-6103.html",
        "https://sfj.ankang.gov.cn/Node-91555.html",
        "https://sfj.ankang.gov.cn/Node-6079.html",
        "https://sfj.ankang.gov.cn/Node-6105.html",
        "https://sfj.ankang.gov.cn/Node-94252.html",
        "https://sfj.ankang.gov.cn/Node-94253.html",
        "https://sfj.ankang.gov.cn/Node-94940.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 兼容 Python<3.9：不要用 removesuffix
        base = base_url[:-5] if base_url.endswith(".html") else base_url
        return f"{base}_{page + 1}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url,callback=self.parse_list,
                # cb_kwargs={'base_url': url}
                cb_kwargs={'base_url': url,'make_url_name': 'make_url_base','use_custom_pagination': True}
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
