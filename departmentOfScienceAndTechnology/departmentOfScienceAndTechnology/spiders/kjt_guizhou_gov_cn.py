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
    'detail_urls': "//div[@class='right-list-box']/ul/li/a/@href | //table[@class='bg_tb']/tbody[@id='idData']/tr[@class='c']/td[@class='tn4']/a/@href",
    'publish_times': "//div[@class='right-list-box']/ul/li/span/text() | //table[@class='bg_tb']/tbody[@id='idData']/tr[@class='c']/td[@class='tn5']/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': "//div[@class='Article_bt']/text()",
    'publish_time': "//div[@class='Article_ly']/span[1]/text()",
    'source': "//div[@class='Article_ly']/span[2]/text()",
    'menu': '//div[@class="path"]//a/text()',
    'content': '//div[contains(@class, "Article_zw")]//p',
    'attachment': '//div[contains(@class, "Article_zw")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "Article_zw")]//p//a/text()',
    'indexnumber': "//div[@class='Article_xx']/table/tbody/tr[1]/td[2]/text()",
    'fileno': "//div[@class='Article_xx']/table/tbody/tr[3]/td[2]/text()",
    'category': "//div[@class='Article_xx']/table/tbody/tr[1]/td[4]/text()",
    'issuer': "//div[@class='Article_xx']/table/tbody/tr[2]/td[2]/text()",
    'status': "//div[@class='Article_xx']/table/tbody/tr[3]/td[4]/text()",
    'writtendate': "//div[@class='Article_xx']/table/tbody/tr[2]/td[4]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\(\s*(\d+)\s*,",
}


class KjtGuizhouGovCnSpider(BasePortiaSpider):
    name = "kjt_guizhou_gov_cn"
    allowed_domains = ["kjt.guizhou.gov.cn"]

    start_urls = [
        "https://kjt.guizhou.gov.cn/xwzx/tzgg_73876/",
        "https://kjt.guizhou.gov.cn/xwzx/szyw/",
        "https://kjt.guizhou.gov.cn/xwzx/dtyw/",
        "https://kjt.guizhou.gov.cn/xwzx/jckj_73877/",
        "https://kjt.guizhou.gov.cn/xwzx/mtjj/",
        "https://kjt.guizhou.gov.cn/dfjs/",
        "https://kjt.guizhou.gov.cn/wzzt/pfzl/pfzl/",
        "https://kjt.guizhou.gov.cn/wzzt/pfzl/yasf/",
        "https://kjt.guizhou.gov.cn/wzzt/hmzcmbk/",
        "https://kjt.guizhou.gov.cn/wzzt/gjwlaqxcz/",
        "https://kjt.guizhou.gov.cn/wzzt/gzkjs/",

        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zcwj/gzdfzc/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jggk/jgzn/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jggk/jgsz/kjtcs/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jggk/jgsz/zsjg/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/rsxx/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zcwj/wjxgfz/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jyta/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jdhy/hygq/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jdhy/zcjd/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jdhy/xwfbh/fbjg/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/jdhy/xwfbh/xwfbh_5821144/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/zjxx/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/qlhzrqd/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kyxmgl/sbzn/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kyxmgl/zxzjfpjg/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kyxmgl/zxzjjxxx/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kyxmgl/gs/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/xzzf/xzcf/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/zfcgh/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kjfzjh/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kjtzgg/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/zypzyguanl/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/zdkjjz/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/cyyshsyfz/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/kjjdpg/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/cgzhcx/",
        "https://kjt.guizhou.gov.cn/zwgk/xxgkml/zdlyxxgk/dwhza/",
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
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
