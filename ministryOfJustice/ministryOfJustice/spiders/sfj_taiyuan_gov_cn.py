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
    'detail_urls': '//*[@class="List_list"]//li/a/@href | //*[@class="box_list"]//li/a/@href',
    'publish_times': '//*[@class="List_list"]//li/span/text() | //*[@class="box_list"]//li/span/text()',
    # 'next_page': '//div[@class="jspIndex4"]/a[last()]/@href',
    'total_page': '//div[@class="page-large"]/div/a[last()-1]/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//span[@class="tit fl"]//a/text()',
    'content': '//div[contains(@id, "zoom")]//p',
    'attachment': '//div[contains(@id, "zoom")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "zoom")]//p//a/text()',

    "indexnumber": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[2]/text()',
    "fileno": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[4]/text()',
    "category": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[4]/text()',
    "issuer": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[2]/text()',
    "status": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[6]/text()',
    "writtendate": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[6]/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': '\\d{4}-\\d{1,2}-\\d{1,2}',
}


class SfjTaiyuanGovCnSpider(BasePortiaSpider):
    name = "sfj_taiyuan_gov_cn"
    allowed_domains = ["sfj.taiyuan.gov.cn"]

    start_urls = [
        "https://sfj.taiyuan.gov.cn/gzdt.html",
        "https://sfj.taiyuan.gov.cn/tggs.html",
        "https://sfj.taiyuan.gov.cn/xzzf.html",
        "https://sfj.taiyuan.gov.cn/szfgz.html",
        "https://sfj.taiyuan.gov.cn/bmyjs.html",
        "https://sfj.taiyuan.gov.cn/gzyjzj.html",
        "https://sfj.taiyuan.gov.cn/xzfyjds.html",
        "https://sfj.taiyuan.gov.cn/zcwjjjd.html"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base = base_url.removesuffix(".html")
        return f"{base}_{page + 1}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          # cb_kwargs={'base_url': url})
            cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

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
                # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [],
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

                Field('attachment', DETAIL_XPATH["attachment"], [], type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], type='xpath', file_category='attachment'),

                Field('indexnumber',
                      DETAIL_XPATH["indexnumber"],
                      [], required=False, type='xpath'),

                Field('fileno',
                      DETAIL_XPATH["fileno"],
                      [], required=False, type='xpath'),

                Field('category',
                      DETAIL_XPATH["category"],
                      [], required=False, type='xpath'),

                Field('issuer',
                      DETAIL_XPATH["issuer"],
                      [], required=False, type='xpath'),

                Field('status',
                      DETAIL_XPATH["status"],
                      [], required=False, type='xpath'),

                Field('writtendate',
                      DETAIL_XPATH["writtendate"],
                      [], required=False, type='xpath'),
            ]
        )
    ]]
