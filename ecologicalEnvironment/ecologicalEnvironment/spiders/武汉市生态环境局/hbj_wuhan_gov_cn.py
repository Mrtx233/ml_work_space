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
    'detail_urls': "//div[@class='lsj-list']/ul/li/a/@href | //ul[@class='info-list']/li/a/@href",
    'publish_times': "//div[@class='lsj-list']/ul/li/a/i/text() | //ul[@class='info-list']/li/a/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="where mb20"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //div[@id=\'pfileattach\']/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //div[@id=\'pfileattach\']/a/text()',
    'indexnumber': "//table[@class='table table-bordered']//tr[1]/td[1]/text()",
    'fileno': "//table[@class='table table-bordered']//tr[3]/td[1]/text()",
    'category': "//table[@class='table table-bordered']//tr[1]/td[2]/text()",
    'issuer': "//table[@class='table table-bordered']//tr[2]/td[1]/text()",
    'status': "//table[@class='table table-bordered']//tr[4]/td[1]/text()",
    'writtendate': "//table[@class='table table-bordered']//tr[2]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class HbjWuhanGovCn(BasePortiaSpider):
    name = "hbj_wuhan_gov_cn"
    allowed_domains = ["hbj.wuhan.gov.cn"]

    start_urls = [
        'https://hbj.wuhan.gov.cn/hjxw/',
        'https://hbj.wuhan.gov.cn/gzdt/',
        'https://hbj.wuhan.gov.cn/gkxx/',
        'https://hbj.wuhan.gov.cn/sjzywjfg/fg/',
        'https://hbj.wuhan.gov.cn/sjzywjfg/wj1/',
        'https://hbj.wuhan.gov.cn/hdjl_19/lxgs/',
        'https://hbj.wuhan.gov.cn/hdjl_19/ftyg/',
        'https://hbj.wuhan.gov.cn/hjsj/ztzl/hjxj/lwhjr/',
        'https://hbj.wuhan.gov.cn/hjsj/ztzl/hjxj/swdyx/',
        'https://hbj.wuhan.gov.cn/hjsj/ztzl/hjxj/dtrxc/',
        'https://hbj.wuhan.gov.cn/hjsj/ztzl/hjxj/mlzgwsxdz/',
        'https://hbj.wuhan.gov.cn/hjsj/ztzl/hjxj/sskf/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zdjsxm/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/gysyjs1/tqkx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/gysyjs1/xczx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/gysyjs1/tfggsj/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/qtzdgk/jcxx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/qtzdgk/jytabl/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/qtzdgk/zfhy/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/qtzdgk/scjggzbz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/hjzkgb/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/jcxx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/dbsjjzsyysydjcbg/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/kqjcbg/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/zsjcbg/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjjc/wryjdxjc/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/kjybz/kjgl/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/kjybz/hjbz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/swrfz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/dqwrfz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/jdchjgl/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/trwrfz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/gtfwwrfz/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/hyfsaq/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/wrfz/qjscshqk/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/zljp/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/hjpj/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/zrst/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/zxxd/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/jcxx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/zdwryjbxx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/hjyj/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/qyhjxypjjg/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zwgk/jczf/12369hjxf/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/rsxx/',
        'https://hbj.wuhan.gov.cn/fbjd_19/xxgkml/zkly/'
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
