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
    'detail_urls': "//div[@class='content-only-text show']/ul/li/a/@href",
    'publish_times': "//div[@class='content-only-text show']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@id="crub"]/span//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\(\s*(\d+)\s*,",
}


class SfjXiaoganGovCnSpider(BasePortiaSpider):
    name = "sfj_xiaogan_gov_cn"
    allowed_domains = ["sfj.xiaogan.gov.cn"]

    start_urls = [
        "https://sfj.xiaogan.gov.cn/bmgz/zwdt/",
        "https://sfj.xiaogan.gov.cn/bmgz/ztzl/ggflfwtsn/",
        "https://sfj.xiaogan.gov.cn/bmgz/tzgg/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/xn/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/hc/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/al/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/dw/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/ym/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/xc/",
        "https://sfj.xiaogan.gov.cn/bmgz/xsqcz/yc/",
        "https://sfj.xiaogan.gov.cn/ywgz01/fzjs/",
        "https://sfj.xiaogan.gov.cn/ywgz01/fggz/",
        "https://sfj.xiaogan.gov.cn/ywgz01/fyys/",
        "https://sfj.xiaogan.gov.cn/ywgz01/sqjz01/",
        "https://sfj.xiaogan.gov.cn/ywgz01/zfjd/",
        "https://sfj.xiaogan.gov.cn/ywgz01/pfxc/",
        "https://sfj.xiaogan.gov.cn/ywgz01/jcsf01/",
        "https://sfj.xiaogan.gov.cn/ywgz01/ggflfw/",
        "https://sfj.xiaogan.gov.cn/ywgz01/lsfk/",
        "https://sfj.xiaogan.gov.cn/ywgz01/jdgl01/",
        "https://sfj.xiaogan.gov.cn/ywgz01/rszg/",
        "https://sfj.xiaogan.gov.cn/ywgz01/zhyw/",
        "https://sfj.xiaogan.gov.cn/bsfw/bgxz/",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        if not base_url.endswith("/"):
            base_url = f"{base_url}/"
        return f"{base_url}index_{page}.shtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={
                    'base_url': url,
                    'make_url_name': 'make_url_base',
                    'use_custom_pagination': True
                }
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
