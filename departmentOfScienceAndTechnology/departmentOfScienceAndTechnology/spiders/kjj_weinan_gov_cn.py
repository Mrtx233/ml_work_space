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
    'detail_urls': "//div[@class='m-lst36']//li/a/@href | //div[@class='m-lst']/ul/li/a/@href",
    'publish_times': "//div[@class='m-lst36']//li/span/text() | //div[@class='m-lst']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text()',
    'content': '//div[contains(@class, "m-txt-article")]//p',
    'attachment': '//div[contains(@class, "m-txt-article")]//p//a/@href | //div[contains(@class, "m-txt-article")]//p//iframe/@src',
    'attachment_name': '//div[contains(@class, "m-txt-article")]//p//a/text() | //div[contains(@class, "m-txt-article")]//p//iframe/@src',
    'indexnumber': "//div[@class='table']/div[@class='table-tr']/div[@class='table-td table-p38 bd-bottom'][1]/text()",
    'issuer': "//div[@class='table gk'][1]/div[@class='table-tr']/div[@class='table-td table-p88 bd-bottom']/text()",
    'writtendate': "//div[@class='table']/div[@class='table-tr']/div[@class='table-td table-p38 bd-bottom'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"maxPage\s*=\s*parseInt\('(\d+)'\)",
}


class KjjWeinanGovCnSpider(BasePortiaSpider):
    name = "kjj_weinan_gov_cn"
    allowed_domains = ["kjj.weinan.gov.cn"]

    start_urls = [
        "https://kjj.weinan.gov.cn/xwzx/kjdt/1.html",
        "https://kjj.weinan.gov.cn/xwzx/ywgz/1.html",
        "https://kjj.weinan.gov.cn/xwzx/kxjspj/1.html",
        "https://kjj.weinan.gov.cn/xwzx/xczx/1.html",
        "https://kjj.weinan.gov.cn/xwzx/tzgg/1.html",
        "https://kjj.weinan.gov.cn/xwzx/jcdj/1.html",
        "https://kjj.weinan.gov.cn/xwzx/lzjs/1.html",
        "https://kjj.weinan.gov.cn/rdzt/djxxjy/1.html",
        "https://kjj.weinan.gov.cn/rdzt/wncxcyfhq/1.html",
        "https://kjj.weinan.gov.cn/rdzt/fzxcjy/1.html",
        "https://kjj.weinan.gov.cn/rdzt/dsxxjy/1.html",
        "https://kjj.weinan.gov.cn/rdzt/srgczybxgdjsxxjy/1.html",
        "https://kjj.weinan.gov.cn/zfxxgk/fdzdgknr/jgsz/1.html",
        "https://kjj.weinan.gov.cn/zfxxgk/fdzdgknr/xsdw/1.html",
        "https://kjj.weinan.gov.cn/zfxxgk/fdzdgknr/kjgh/1.html",
        "https://kjj.weinan.gov.cn/zfxxgk/fdzdgknr/czxx/1.html",
        "https://kjj.weinan.gov.cn/zfxxgk/fdzdgknr/hzgfxwj/1.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_base = base_url.rsplit('/', 1)[0]
        return f"{clean_base}/{page + 1}.html"

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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
