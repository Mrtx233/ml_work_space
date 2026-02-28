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


class SthjjAhszGovCn(BasePortiaSpider):
    name = "sthjj_ahsz_gov_cn"
    allowed_domains = ["sthjj.ahsz.gov.cn"]

    start_urls = [
        'https://sthjj.ahsz.gov.cn/content/column/127111497?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/127111522?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/127111569?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/127111597?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167461311?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320914?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320617?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320673?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130321002?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320621?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320645?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130320641?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130321032?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167451951?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167473151?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/130321041?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889110?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889224?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/134793726?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889280?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889349?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889360?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889318?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889180?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889133?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/131889379?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167484251?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167481941?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/content/column/167484251?pageIndex=1',
        'https://sthjj.ahsz.gov.cn/hbyw/hjzlxx/hjzkgb/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/zfwzgznb/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/lszt/zyhbdc/tpxw/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/lszt/zyhbdc/gzjb/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/lszt/zyhbdc/mtbd/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/lzzc/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/hbzyzzxd/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/szs2021njnxczhdtr/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/djxxjy/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/qyhjxypjzl/index.html',
        'https://sthjj.ahsz.gov.cn/ztzl/xxgcddesjszqhjs/index.html'
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
