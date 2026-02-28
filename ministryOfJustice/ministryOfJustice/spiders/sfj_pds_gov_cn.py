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
    'detail_urls': "//div[@class='channel clearfix']/div[@class='channel-fr fr']/ul/li/a/@href",
    'publish_times': "//div[@class='channel clearfix']/div[@class='channel-fr fr']/ul/li/a/span/text()",
    'total_page': "//div[@class='page']/span[@class='total']/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//span[@class="history"]//a/text()',
    'content': '//div[contains(@class, "text")]//p',
    'attachment': '//div[contains(@class, "text")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "text")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"当前第\s*\d+\s*\/\s*(\d+)",
}


class SfjPdsGovCnSpider(BasePortiaSpider):
    name = "sfj_pds_gov_cn"
    allowed_domains = ["sfj.pds.gov.cn"]

    start_urls = [
        "https://sfj.pds.gov.cn/channels/14229.html",
        "https://sfj.pds.gov.cn/channels/14230.html",
        "https://sfj.pds.gov.cn/channels/14651.html",
        "https://sfj.pds.gov.cn/channels/14652.html",
        "https://sfj.pds.gov.cn/channels/14232.html",
        "https://sfj.pds.gov.cn/channels/14234.html",
        "https://sfj.pds.gov.cn/channels/33790.html",
        "https://sfj.pds.gov.cn/channels/14236.html",
        "https://sfj.pds.gov.cn/channels/14237.html",
        "https://sfj.pds.gov.cn/channels/14238.html",
        "https://sfj.pds.gov.cn/channels/14239.html",
        "https://sfj.pds.gov.cn/channels/14240.html",
        "https://sfj.pds.gov.cn/channels/14241.html",
        "https://sfj.pds.gov.cn/channels/14242.html",
        "https://sfj.pds.gov.cn/channels/14629.html",
        "https://sfj.pds.gov.cn/channels/14244.html",
        "https://sfj.pds.gov.cn/channels/14246.html",
        "https://sfj.pds.gov.cn/channels/14247.html",
        "https://sfj.pds.gov.cn/channels/14249.html",
        "https://sfj.pds.gov.cn/channels/36496.html",
        "https://sfj.pds.gov.cn/channels/14267.html",
        "https://sfj.pds.gov.cn/channels/14254.html",
        "https://sfj.pds.gov.cn/channels/14714.html",
        "https://sfj.pds.gov.cn/channels/46700.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base = base_url.rsplit(".html", 1)[0]
        return f"{base}_{page + 1}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
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
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_date"])], type="xpath"),
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
