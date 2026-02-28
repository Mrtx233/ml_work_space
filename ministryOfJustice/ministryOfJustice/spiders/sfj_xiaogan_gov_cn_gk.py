from __future__ import absolute_import

import scrapy
import re
from typing import Any, Dict
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, HbeaItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Regex


# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': "//div[@class='card-body']/ul/li/a/@href",
    'publish_times': "//div[@class='card-body']/ul/li/span/text()",
    'total_page': "//div[@class='js_page']/ul/li[last()-2]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@id=""]/span//a/text()',
    'content': '//div[contains(@class, "")]//p',
    'attachment': '//div[contains(@class, "")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
    'publish_time': r"\s*(\d{4}-\d{2}-\d{2})",
    'source': r"\s*([^\n\s]+)",
}


class SfjXiaoganGovCnGkSpider(BasePortiaSpider):
    name = "sfj_xiaogan_gov_cn_gk"
    allowed_domains = ["sfj.xiaogan.gov.cn"]

    start_urls = [
    "https://sfj.xiaogan.gov.cn/c/xgssfj/sjxzxk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/dwglfwsxjg.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/czys.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/czjs.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/tqzxqykxxx.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/yjtjcx.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/xzcfjd.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/xzcfcljz.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/jcygk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/bmhy.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/ssjygk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/yhyshj.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/hygq.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/dfqw.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/dtblqk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/ztqk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/zczxjlsqk.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/gzcnzsxqd.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/zwdc1.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/fzzfjsndgzbg.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/zfcg.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/sswgh.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/lsgh.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/zkly.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2025.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2024n.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2023n1.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2022n.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2021n.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/2020n.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/xzsyxsf.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/fzxcjy1.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/lsfw1.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/rmtj.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/flcx.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/flzxfw.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/ggflfwpt.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/ggflfwbszn.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/qxbldzmsxqd.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/jgzn.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/nsjg.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/ldjjyfg.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/szdw.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/xsq.jhtml",
    "https://sfj.xiaogan.gov.cn/c/xgssfj/gysyjs.jhtml",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base = base_url.removesuffix(".jhtml")
        return f"{base}_{page}.jhtml"

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
                Field('detail_urls', LIST_XPATH["detail_urls"], [], required=False, type='xpath'),
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_date"])], required=False, type='xpath'),
                Field('total_page', LIST_XPATH["total_page"], [Regex(REGEX["total_page"])], required=False, type='xpath'),
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
                Field('menu', DETAIL_XPATH["menu"], [], required=False, type='xpath'),
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
