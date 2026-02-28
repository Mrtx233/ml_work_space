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
    'detail_urls': "//div[@class='NewsList']/ul/li/a/@href | //div[@class='zfxxgk_zdgkc']/ul/li/a/@href",
    'publish_times': "//div[@class='NewsList']/ul/li/span/text() | //div[@class='zfxxgk_zdgkc']/ul/li/b/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="path"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
    'indexnumber': "//div[@class='Article_xx']/table/tbody/tr[1]/td[2]/text()",
    'fileno': "//div[@class='Article_xx']/table/tbody/tr[4]/td[2]/text()",
    'issuer': "//div[@class='Article_xx']/table/tbody/tr[2]/td[2]/text()",
    'status': "//div[@class='Article_xx']/table/tbody/tr[1]/td[4]/text()",
    'writtendate': "//div[@class='Article_xx']/table/tbody/tr[2]/td[4]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class KjjAnshunGovCnSpider(BasePortiaSpider):
    name = "kjj_anshun_gov_cn"
    allowed_domains = ["kjj.anshun.gov.cn"]

    start_urls = [
        "https://kjj.anshun.gov.cn/gzdt/bmdt/",
        "https://kjj.anshun.gov.cn/gzdt/tzgg/",
        "https://kjj.anshun.gov.cn/ywgz/kjgz/",
        "https://kjj.anshun.gov.cn/ywgz/kjjl/",
        "https://kjj.anshun.gov.cn/ztzl/jssc/",
        "https://kjj.anshun.gov.cn/ztzl/xqkj_72408/",
        "https://kjj.anshun.gov.cn/ztzl/dflzjs/",
        "https://kjj.anshun.gov.cn/ztzl/kjwx/",
        "https://kjj.anshun.gov.cn/ztzl/tszs/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/kjcx/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/rsxx/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/jhzj/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/tjxx/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/bmwj/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/czxx/bmczjsjsgjf/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/czxx/bmczysjsgjf/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/qzqd/qlqd/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/qzqd/zrqd/",
        "https://kjj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/wzgzndbb/",
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
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]

