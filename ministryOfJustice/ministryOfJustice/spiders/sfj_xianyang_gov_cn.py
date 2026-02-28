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
    'detail_urls': "//div[@class='content_info']/ul/li/a/@href",
    'publish_times': "//div[@class='content_info']/ul/li/a/span[2]/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="list_info pl20"]//a/text()',
    'content': '//div[contains(@class, "trs_editor_view")]//p',
    'attachment': '//div[contains(@class, "trs_editor_view")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "trs_editor_view")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage\(\s*(\d+)\s*,",
}


class SfjXianyangGovCnSpider(BasePortiaSpider):
    name = "sfj_xianyang_gov_cn"
    allowed_domains = ["sfj.xianyang.gov.cn"]

    start_urls = [
        # 新闻资讯类（基础路径型，分页：index_1.html/index_2.html）
        "https://sfj.xianyang.gov.cn/sfxw/zxxw/",
        "https://sfj.xianyang.gov.cn/sfxw/tzgg/",
        "https://sfj.xianyang.gov.cn/sfxw/jcdt/",
        # 专题专栏类（基础路径型）
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/fzzfjssfcj/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/frxypfjt/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/dsxxjy/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/hhyyhxy/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/zzjs/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/bwpfcgz/",
        "https://sfj.xianyang.gov.cn/sfxw/ztzl/dzzmpfr/",
        # 法律服务类（基础路径型）
        "https://sfj.xianyang.gov.cn/qmyfzs/jgjj1/",
        "https://sfj.xianyang.gov.cn/flfw/bszn/",
        "https://sfj.xianyang.gov.cn/flfw/bgxz/",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.html"

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
            ]
        )
    ]]
