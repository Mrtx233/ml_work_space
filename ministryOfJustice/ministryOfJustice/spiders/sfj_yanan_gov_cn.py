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
    'detail_urls': "//div[@class='m-lst36']/ul/li/a/@href | //div[@class='m-lst']/ul/li/a/@href",
    'publish_times': "//div[@class='m-lst36']/ul/li/span/text() | //div[@class='m-lst']/ul/li/span/text()",
    'total_page': "//div[@class='m-lst-pg']/ul/li[6]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text()',
    'content': '//div[contains(@id, "article")]//p',
    'attachment': ' //div[contains(@id, "article")]//p//iframe/@src',
    'attachment_name': '//div[contains(@id, "article")]//p//iframe/@src',
    'indexnumber': "//div[@class='table hidden-sm']/div[@class='table-tr'][1]/div[@class='table-td table-p38'][1]/text()",
    'fileno': "//div[@class='table hidden-sm']/div[@class='table-tr'][2]/div[@class='table-td table-p38'][1]/text()",
    'issuer': "//div[@class='table hidden-sm']/div[@class='table-tr'][3]/div[@class='table-td table-p38'][1]/text()",
    'status': "//div[@class='table hidden-sm']/div[@class='table-tr'][3]/div[@class='table-td table-p38'][2]/text()",
    'writtendate': "//div[@class='table hidden-sm']/div[@class='table-tr'][2]/div[@class='table-td table-p38'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
}


class SfjYananGovCnSpider(BasePortiaSpider):
    name = "sfj_yanan_gov_cn"
    allowed_domains = ["sfj.yanan.gov.cn"]

    start_urls = [
        "https://sfj.yanan.gov.cn/sfzx/sfyw/1.html",
        "https://sfj.yanan.gov.cn/sfzx/qxdt/1.html",
        "https://sfj.yanan.gov.cn/sfzx/tzgg/1.html",
        "https://sfj.yanan.gov.cn/sfzx/zyhy/1.html",
        "https://sfj.yanan.gov.cn/zffz/xzfy/1.html",
        "https://sfj.yanan.gov.cn/zffz/gfxwj/1.html",
        "https://sfj.yanan.gov.cn/zffz/lfjh/dffg/1.html",
        "https://sfj.yanan.gov.cn/hdjl/dczj/1.html",
        "https://sfj.yanan.gov.cn/hdjl/zcjd/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/zcwj/bmwj/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/ghjh/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/rsxx/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/qlyxgk/zdgzzxlsqk/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/qlyxgk/xzzf/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/czxx/czyjs/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/czxx/sgjf/1.html",
        "https://sfj.yanan.gov.cn/zfxxgk/fdzdgknr/tajy/1.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_base = base_url.rsplit('/', 1)[0].rstrip('/')
        return f"{clean_base}/{page + 1}.html"

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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
