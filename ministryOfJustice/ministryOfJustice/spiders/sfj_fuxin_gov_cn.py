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
    'detail_urls': '//*[@class="list1-ul"]//li//a/@href | //*[@class="xxgk_rul xxgk_rul_auto"]//li//a/@href',
    'publish_times': '//*[@class="tabs2Right-part2"]/text() | //*[@class="xxgk_rul xxgk_rul_auto"]//li//a/span/text()',
    'next_page': '//ul[@class="pagination"]/li[last()-1]/a/@href',
    'total_page': '//div[@class="page-inner"]/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="breadcrumbs"]//a/text()',
    'content': '//div[contains(@class, "Detailcontent_inner f16")]//p',
    'attachment': '//div[contains(@class, "Detailcontent_inner f16")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "Detailcontent_inner f16")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': '\\d{4}-\\d{1,2}-\\d{1,2}',
    'total_page': '共\\s*(\\d+)',
}


class SfjFuxinGovCnSpider(BasePortiaSpider):
    name = "sfj_fuxin_gov_cn"
    allowed_domains = ["sfj.fuxin.gov.cn"]

    start_urls = [
        "https://sfj.fuxin.gov.cn/channel/list/12897.html",
        "https://sfj.fuxin.gov.cn/channel/list/11677.html",
        "https://sfj.fuxin.gov.cn/channel/list/18980.html",
        "https://sfj.fuxin.gov.cn/channel/list/11685.html",
        "https://sfj.fuxin.gov.cn/channel/list/15742.html",
        "https://sfj.fuxin.gov.cn/channel/list/11683.html",
        "https://sfj.fuxin.gov.cn/channel/list/15488.html",

        "https://sfj.fuxin.gov.cn/channel/list/17724.html",
        "https://sfj.fuxin.gov.cn/channel/list/14440.html",
        "https://sfj.fuxin.gov.cn/channel/list/14442.html",
        "https://sfj.fuxin.gov.cn/channel/list/13524.html",
        "https://sfj.fuxin.gov.cn/channel/list/22336.html",
        "https://sfj.fuxin.gov.cn/channel/list/21963.html",
        "https://sfj.fuxin.gov.cn/channel/list/19778.html",
        "https://sfj.fuxin.gov.cn/channel/list/19038.html",
        "https://sfj.fuxin.gov.cn/channel/list/16934.html",
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     base_url = re.sub(r'/index\.htm$', '', base_url)
    #     return f"{base_url}/index_{page + 1}.htm"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={
                    'base_url': url,
                #     'make_url_name': 'make_url_base',
                #     'use_custom_pagination': True
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
                Field(
                    'publish_times',
                    LIST_XPATH["publish_times"],
                    [Regex(REGEX["publish_date"])],
                    type="xpath"
                ),
                Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [Regex(REGEX["total_page"])],
                    type="xpath"
                ),
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

                Field(
                    'publish_time',
                    DETAIL_XPATH["publish_time"],
                    [],
                    type='xpath'
                ),

                Field(
                    'menu',
                    DETAIL_XPATH["menu"],
                    [Text(), Join(separator='>')],
                    type="xpath"
                ),

                Field(
                    'source',
                    DETAIL_XPATH["source"],
                    [],
                    type='xpath',
                    file_category='source'
                ),

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
