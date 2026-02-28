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
    'detail_urls': '//ul[contains(@class, "doc_list")]/li/a/@href',
    'publish_times': '//ul[contains(@class, "doc_list")]/li/span/text()',
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wwz_top"]//a/text()',
    'content': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]',
    'attachment': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]//a/@href',
    'attachment_name': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageSize=(\d+)",
}


class SthjjLuanGovCn(BasePortiaSpider):
    name = "sthjj_luan_gov_cn"
    allowed_domains = ["sthjj.luan.gov.cn"]

    start_urls = [
        'https://sthjj.luan.gov.cn/content/column/6806161?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806181?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806171?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806041?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6820749?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6816061?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6816061?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806081?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6817061?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6817061?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806101?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6818284?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812291?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812321?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812331?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812351?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812391?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812341?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806221?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812401?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812411?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812421?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806211?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806241?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812441?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812451?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6812461?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806261?pageIndex=1',
        'https://sthjj.luan.gov.cn/content/column/6806271?pageIndex=1',
        'https://sthjj.luan.gov.cn/ztzl/ztzl/zfwzgzndbb/index.html',
        'https://sthjj.luan.gov.cn/ztzl/ztzl/yyssydhjbhzxxd/index.html',
        'https://sthjj.luan.gov.cn/ztzl/gdzt/ld2018zrbhqdc/index.html',
        'https://sthjj.luan.gov.cn/ztzl/gdzt/nchjzhzz/index.html',
        'https://sthjj.luan.gov.cn/ztzl/gdzt/lxyzxxjy/index.html',
        'https://sthjj.luan.gov.cn/ztzl/ztzl/ytygs--hbrzxd/index.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('?pageIndex=1', f'?pageIndex={page + 1}')


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
                        Regex(REGEX["total_page"]),  # 第一步：正则提取总页数（返回列表，如['50']或[]）
                        # 第二步：lambda处理空值，匹配不到则返回1（转为字符串避免类型错误）
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
