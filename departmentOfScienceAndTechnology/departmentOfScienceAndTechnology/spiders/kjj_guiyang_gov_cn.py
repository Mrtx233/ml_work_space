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
    'detail_urls': "//div[@class='right_main']/ul/div[@id='ajaxpage-list']/li/a/@href | //div[@class='zfxxgk_zdgkc']/ul/li/a/@href",
    'publish_times': "//div[@class='right_main']/ul/div[@id='ajaxpage-list']/li/span[@class='pull-right']/text() | //div[@class='zfxxgk_zdgkc']/ul/li/b/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wz"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
    'fileno': "//table[@class='tablec']/tbody/tr[1]/td[2]/text()",
    'issuer': "//table[@class='tablec']/tbody/tr[1]/td[4]/text()",
    'status': "//table[@class='tablec']/tbody/tr[3]/td[2]/text()",
    'writtendate': "//table[@class='tablec']/tbody/tr[2]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class KjjGuiyangGovCnSpider(BasePortiaSpider):
    name = "kjj_guiyang_gov_cn"
    allowed_domains = ["kjj.guiyang.gov.cn"]

    start_urls = [
        "https://kjj.guiyang.gov.cn/xwdt/gykjdt/",
        "https://kjj.guiyang.gov.cn/xwdt/gnkjxw/",
        "https://kjj.guiyang.gov.cn/kjzc/gyszcfg/",
        "https://kjj.guiyang.gov.cn/kjzc/zcjd/",
        "https://kjj.guiyang.gov.cn/kjzc/wjxghsxfz/",
        "https://kjj.guiyang.gov.cn/gzcy/cjwt/",
        "https://kjj.guiyang.gov.cn/gzcy/hygq/",
        "https://kjj.guiyang.gov.cn/ztlm/dwgk/",
        "https://kjj.guiyang.gov.cn/ztlm/zdjcygk/",
        "https://kjj.guiyang.gov.cn/ztlm/dflzjs/",
        "https://kjj.guiyang.gov.cn/ztlm/gbjypxgztl/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/fggw/fggz/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/fggw/bmwj/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/jhgh/tjxx/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/jhgh/gh/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/jhgh/jhzj/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/czxx/czyjsjsgjf/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zfcg/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/rsxx/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/tzgg/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/jyta/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/cxtxjs/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zypzygl/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/kjjdycxjs/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/gxjs/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/nynckj/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/shfzkj/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/cgzhyqycx/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/kjxmgl/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/wgzjkjrcgl/",
        "https://kjj.guiyang.gov.cn/zfxxgk/fdzdgknr/qlzrqd/",
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
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
