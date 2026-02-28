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
    'detail_urls': "//ul[@id='share']/li/a/@href | //ul[@class='info-list']/li/a/@href",
    'publish_times': "//ul[@id='share']/li/a/span/text() | //ul[@class='info-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="where mb20"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': "//ul[@id='list']/li/a/@href",
    'attachment_name': "//ul[@id='list']/li/a/text()",
    'indexnumber': "//table[@class='table table-bordered']//tr[1]/td[1]/text()",
    'fileno': "//table[@class='table table-bordered']//tr[3]/td[1]/text()",
    'category': "//table[@class='table table-bordered']//tr[1]/td[2]/text()",
    'issuer': "//table[@class='table table-bordered']//tr[2]/td[1]/text()",
    'status': "//table[@class='table table-bordered']//tr[3]/td[2]/text()",
    'writtendate': "//table[@class='table table-bordered']//tr[2]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r'createPageHTML\(\s*["\']?(\d+)["\']?\s*,',
}


class KjtHubeiGovCnSpider(BasePortiaSpider):
    name = "kjt_hubei_gov_cn"
    allowed_domains = ["kjt.hubei.gov.cn"]

    start_urls = [
        "https://kjt.hubei.gov.cn/kjdt/kjtgz/",
        "https://kjt.hubei.gov.cn/kjdt/sxkj/",
        "https://kjt.hubei.gov.cn/kjdt/mtjj/",
        "https://kjt.hubei.gov.cn/kjdt/tzgg/",
        "https://kjt.hubei.gov.cn/hdjl/lxgs/",
        "https://kjt.hubei.gov.cn/kjdt/ztzl/xxgcddesj/",
        "https://kjt.hubei.gov.cn/kjdt/ztzl/fzxczl/xxxjpfzsx/",
        "https://kjt.hubei.gov.cn/kjdt/ztzl/fzxczl/pfxcc/kjlflfg/",
        "https://kjt.hubei.gov.cn/kjdt/ztzl/fzxczl/pfxcc/kjzcl/",
        "https://kjt.hubei.gov.cn/kjdt/ztzl/fzxczl/pfxcc/fzdt/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/zc2020/zcjd/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/jgzn/nsjg/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/jgzn/zsdw/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/ghjh/ghjd/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/ghjh/135gh/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/ghjh/125gh/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/ghjh/115gh/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/ghjh/qtlsgh/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/xkfw/xkjl/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/xkfw/cgdjgs/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/cfqz/xzcfjd/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/cfqz/xzcfcljz/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qxblzm/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/czgk/czyjs/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/xzsysfn/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/zfcg/jzcgssqk/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/zklyz/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/ssjygk/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/jytabl/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/zwdch/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/xzzftjnb/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/fzzfjsnb/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/hygq/",
        "https://kjt.hubei.gov.cn/zfxxgk_GK2020/xxgkml/qtzdzdgk/scjggzbz/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.shtml"

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
