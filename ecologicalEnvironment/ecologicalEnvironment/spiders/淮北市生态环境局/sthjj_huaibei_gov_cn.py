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
    'detail_urls': "//div[@class='ls-column-list']/ul/li/a[@class='left']/@href",
    'publish_times': "//div[@class='ls-column-list']/ul/li/span[@class='right date']/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="ls-crumbs"]//a/text()',
    'content': '//div[contains(@class, "ls-article-info")]//p',
    'attachment': '//div[contains(@class, "ls-article-info")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "ls-article-info")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageCount:(\d+)",
}


class SthjjHuaibeiGovCn(BasePortiaSpider):
    name = "sthjj_huaibei_gov_cn"
    allowed_domains = ["sthjj.huaibei.gov.cn"]

    start_urls = [
        'https://sthjj.huaibei.gov.cn/content/column/4701861?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4701871?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4701891?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14151121?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/zmhd1/hdzd/index.html',
        'https://sthjj.huaibei.gov.cn/zmhd1/cjwt/index.html',
        'https://sthjj.huaibei.gov.cn/content/column/4701651?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4701681?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14149191?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/hbyw/jgld/ldjj/index.html',
        'https://sthjj.huaibei.gov.cn/content/column/4702961?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/hbyw/jgsz/nsjg/index.html',
        'https://sthjj.huaibei.gov.cn/content/column/4703051?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703111?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703211?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703221?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703231?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703241?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703151?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4704611?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4701641?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4702091?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4702101?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4702111?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14149851?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14149061?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14149211?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/4703351?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14151841?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/content/column/14149711?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/ztzl/2023nahssdgysthjbhzxdc/index.html',
        'https://sthjj.huaibei.gov.cn/content/column/14153996?pageIndex=1',
        'https://sthjj.huaibei.gov.cn/ztzl/rhrhpwkjdgl/index.html',
        'https://sthjj.huaibei.gov.cn/content/column/14154037?pageIndex=1'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('pageIndex=1', f'pageIndex={page + 1}')

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
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [
                        Regex(REGEX["total_page"]),
                        lambda x: x[0].strip() if (
                                    isinstance(x, list) and x and x[0] and x[0].strip().isdigit()) else "1"
                    ],
                    type="xpath"
                )
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
