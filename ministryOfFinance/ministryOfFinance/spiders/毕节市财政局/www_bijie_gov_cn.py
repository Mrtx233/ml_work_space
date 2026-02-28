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
    'detail_urls': "//ul[@class='NewsList']/li/a/@href",
    'publish_times': "//ul[@class='NewsList']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="Address Box"]//a/text()',
    'content': '//div[contains(@id, "Zoom")]//p',
    'attachment': '//div[contains(@id, "Zoom")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "Zoom")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    'publish_time': r"\d{4}-\d{1,2}-\d{1,2}",
    'source': r"\d{4}-\d{1,2}-\d{1,2}",
    'title': r"\d{4}-\d{1,2}-\d{1,2}",
}


class WwwBijieGovCn(BasePortiaSpider):
    name = "www_bijie_gov_cn"
    allowed_domains = ["www.bijie.gov.cn"]

    start_urls = [
        'https://www.bijie.gov.cn/bm/bjsczj/dt/czdt/',
        'https://www.bijie.gov.cn/bm/bjsczj/dt/tzgg/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/xxgknb/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/xxgkzd/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/jggk/dwzn/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/jggk/nsjzsjg/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/zcwjjzcjd/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/czxx/bmyjs/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/czxx/czsz/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/czxx/szfyjs/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/czxx/czfpzj/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/qzqd/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/zfcg_cz/jdgl_cz/',
        'https://www.bijie.gov.cn/bm/bjsczj/zwgk/zfcg_cz/cgzn_cz/',
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
                Field('title', DETAIL_XPATH["title"], [Regex(REGEX["title"])], required=False, type='xpath'),
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
