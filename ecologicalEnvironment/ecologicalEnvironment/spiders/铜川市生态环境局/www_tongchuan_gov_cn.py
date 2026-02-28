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
    'detail_urls': "//div[@class='list']/ul/li/a/@href | //div[@class='list']/ul/li/a/@href",
    'publish_times': "//div[@class='list']/ul/li/span/text() | //div[@class='list']/ul/li/span/text()",
    'total_page': "//div[@class='cms_page']/span[1]/span[2]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position border"]//a/text()',
    'content': '//div[contains(@class, "show-text")]//p',
    'attachment': '//div[contains(@class, "show-text")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "show-text")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
}


class WwwTongchuanGovCn(BasePortiaSpider):
    name = "www_tongchuan_gov_cn"
    allowed_domains = ["www.tongchuan.gov.cn"]

    start_urls = [
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=4164&orgId=90&channlId=4164&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=4165&orgId=90&channlId=4165&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=973&orgId=90&channlId=973&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=5467&orgId=90&channlId=5467&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=5472&orgId=90&channlId=5472&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=5473&orgId=90&channlId=5473&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=5474&orgId=90&channlId=5474&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=5466&orgId=90&channlId=5466&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=6665&orgId=90&channlId=6665&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=4169&orgId=90&channlId=4169&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=4948&orgId=90&channlId=4948&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=4947&orgId=90&channlId=4947&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=1391&orgId=90&channlId=1391&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=2022&orgId=90&channlId=2022&pageNo=1',
        'https://www.tongchuan.gov.cn/news_list.rt?channlCid=6916&orgId=90&channlId=6916&pageNo=1'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r'pageNo=\d+', f'pageNo={page + 1}', base_url)

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
