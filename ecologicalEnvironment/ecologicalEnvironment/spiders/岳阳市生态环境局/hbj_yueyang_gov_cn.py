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
    'detail_urls': "//ul[@class='contents-list mt-1']/li/div[@class='title-wrapper']/div[@class='title text-truncate']/a/@href | //ul[@class='xxdk-news-list pd30']/li/a/@href",
    'publish_times': "//ul[@class='contents-list mt-1']/li/div[@class='title-wrapper']/div[@class='date']/text() | //ul[@class='xxdk-news-list pd30']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': "//ol[@class='breadcrumb bg-white']/a/text()",
    'content': '//div[contains(@class, "content-wrapper")]//p',
    'attachment': '//div[contains(@class, "content-wrapper")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "content-wrapper")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"else if\(num>(\d+)\)",
}


class HbjYueyangGovCn(BasePortiaSpider):
    name = "hbj_yueyang_gov_cn"
    allowed_domains = ["hbj.yueyang.gov.cn"]

    start_urls = [
        'https://hbj.yueyang.gov.cn/6790/6791/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6792/default.htm',
        'https://hbj.yueyang.gov.cn/6836/67704/index.htm',
        'https://hbj.yueyang.gov.cn/6836/25319/default.htm',
        'https://hbj.yueyang.gov.cn/6836/66959/index.htm',
        'https://hbj.yueyang.gov.cn/6836/6837/default.htm',
        'https://hbj.yueyang.gov.cn/6836/64095/index.htm',
        'https://hbj.yueyang.gov.cn/6836/63907/index.htm',
        'https://hbj.yueyang.gov.cn/6836/65101/index.htm',
        'https://hbj.yueyang.gov.cn/6836/63942/index.htm',
        'https://hbj.yueyang.gov.cn/6836/54630/index.htm',
        'https://hbj.yueyang.gov.cn/6836/49609/index.htm',
        'https://hbj.yueyang.gov.cn/6836/9784/10009/default.htm',
        'https://hbj.yueyang.gov.cn/6836/49578/index.htm',
        'https://hbj.yueyang.gov.cn/6836/6839/default.htm',
        'https://hbj.yueyang.gov.cn/6836/6838/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6826/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6827/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6829/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6830/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6833/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6833/22949/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6831/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6832/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6825/default.htm',
        'https://hbj.yueyang.gov.cn/6824/6828/default.htm',
        'https://hbj.yueyang.gov.cn/6824/23623/default.htm',
        'https://hbj.yueyang.gov.cn/6824/55621/index.htm',
        'https://hbj.yueyang.gov.cn/6824/63045/index.htm',
        'https://hbj.yueyang.gov.cn/6824/63046/index.htm',
        'https://hbj.yueyang.gov.cn/6790/6804/6805/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6807/6808/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6793/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6812/59627/65931/index.htm',
        'https://hbj.yueyang.gov.cn/6790/6797/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6801/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6809/default.htm',
        'https://hbj.yueyang.gov.cn/6790/54369/index.htm',
        'https://hbj.yueyang.gov.cn/6790/22373/22429/default.htm',
        'https://hbj.yueyang.gov.cn/6790/22373/22430/default.htm',
        'https://hbj.yueyang.gov.cn/6790/6812/59627/75663/index.htm'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_url = base_url.rstrip('/').replace('default.htm', f'default_{page}.htm')
        return clean_url

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
            ]
        )
    ]]
