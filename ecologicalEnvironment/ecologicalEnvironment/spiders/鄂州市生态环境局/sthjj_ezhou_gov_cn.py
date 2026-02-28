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
    'detail_urls': "//div[@class='list']/ul/li/a/@href",
    'publish_times': "//div[@class='list']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="crumbs"]//a/text()',
    'content': '//div[contains(@class, "TRS_Editor")]//p',
    'attachment': '//div[contains(@class, "TRS_Editor")]//p//a/@href | //div[@class="xqym"]/div[@class="fujian"]/p/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_Editor")]//p//a/text() | //div[@class="xqym"]/div[@class="fujian"]/p/a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjEzhouGovCn(BasePortiaSpider):
    name = "sthjj_ezhou_gov_cn"
    allowed_domains = ["sthjj.ezhou.gov.cn"]

    start_urls = [
        'https://sthjj.ezhou.gov.cn/hjxw/xwdt/',
        'https://sthjj.ezhou.gov.cn/hjxw/tzgg/',
        'https://sthjj.ezhou.gov.cn/hjxw/gqkx/',
        'https://sthjj.ezhou.gov.cn/hjsj/sthjbz/',
        'https://sthjj.ezhou.gov.cn/hjsj/hjzlyb/',
        'https://sthjj.ezhou.gov.cn/hjsj/hjzlnb/',
        'https://sthjj.ezhou.gov.cn/hjsj/wryhjjgxx/gjzdjkqywryjdxjcjg/',
        'https://sthjj.ezhou.gov.cn/hjsj/wryhjjgxx/qjsc/',
        'https://sthjj.ezhou.gov.cn/hjsj/dqhjzl/kqzlyb/',
        'https://sthjj.ezhou.gov.cn/hjsj/dqhjzl/dqyjyb/',
        'https://sthjj.ezhou.gov.cn/hjsj/trhjzl/',
        'https://sthjj.ezhou.gov.cn/hjsj/hjzl/',
        'https://sthjj.ezhou.gov.cn/hjsj/shjzl/dbsszyb/',
        'https://sthjj.ezhou.gov.cn/hjsj/hpjcxx/',
        'https://sthjj.ezhou.gov.cn/gzhd/xwfbh/',
        'https://sthjj.ezhou.gov.cn/gzhd/lxhf/',
        'https://sthjj.ezhou.gov.cn/gzhd/wsdc/',
        'https://sthjj.ezhou.gov.cn/gzhd/gzgq/rdhy/',
        'https://sthjj.ezhou.gov.cn/gzhd/myzj/',
        'https://sthjj.ezhou.gov.cn/gzhd/zxft/'
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
            ]
        )
    ]]
