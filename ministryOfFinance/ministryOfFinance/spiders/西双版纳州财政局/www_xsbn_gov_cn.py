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
    'detail_urls': "//ul[@class='widget-list']/li[@class='widget-list-item widget-list-icon  widget-dotted widget-lineheight']/a/@href",
    'publish_times': "//ul[@class='widget-list']/li[@class='widget-list-item widget-list-icon  widget-dotted widget-lineheight']/span/text()",
    'total_page': "//ul[@class='pagination']/li[last()-2]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//ol[@class="breadcrumb"]//a/text()',
    'content': '//div[@class="news"]//p',
    'attachment': '//div[@class="news"]//p//a/@href',
    'attachment_name': '//div[@class="news"]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
}


class WwwXsbnGovCn(BasePortiaSpider):
    name = "www_xsbn_gov_cn"
    allowed_domains = ["www.xsbn.gov.cn"]

    start_urls = [
        'https://www.xsbn.gov.cn/czj/93625.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93668.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93662.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93643.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93657.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93682.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93704.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/325103.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93672.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93667.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/93679.news.list.dhtml',
        'https://www.xsbn.gov.cn/czj/325132.news.list.dhtml',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        separator = '&' if '?' in base_url else '?'
        return f"{base_url}{separator}page={page + 1}"

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
                Field('total_page', LIST_XPATH["total_page"], [], type="xpath"),
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
