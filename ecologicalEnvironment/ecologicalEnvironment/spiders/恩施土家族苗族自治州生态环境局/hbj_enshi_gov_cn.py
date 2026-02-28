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
    'detail_urls': "//ul[@class='mt10 clear']/li/a/@href | //ul[@class='info-list']/li/a/@href",
    'publish_times': "//ul[@class='mt10 clear']/li/span[@class='date']/text() | //ul[@class='info-list']/li/a/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@id="bread"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': "//div[@class='apendix']//a/@href",
    'attachment_name': "//div[@class='apendix']//a/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class HbjEnshiGovCn(BasePortiaSpider):
    name = "hbj_enshi_gov_cn"
    allowed_domains = ["hbj.enshi.gov.cn"]

    start_urls = [
        'http://hbj.enshi.gov.cn/xwzx/hbyw/',
        'http://hbj.enshi.gov.cn/xwzx/xsdt/',
        'http://hbj.enshi.gov.cn/xwzx/xygz/',
        'http://hbj.enshi.gov.cn/tzgg/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/bs/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/jd/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/ls/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/pl/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/zc/',
        'http://hbj.enshi.gov.cn/hbzl/wrfzgjz/bsfw/',
        'http://hbj.enshi.gov.cn/hbzl/sjhjr/',
        'http://hbj.enshi.gov.cn/dczj/',
        'http://hbj.enshi.gov.cn/xxgk/zc/zcjd/',
        'http://hbj.enshi.gov.cn/xxgk/xxgkzl/',
        'http://hbj.enshi.gov.cn/xxgk/gkzd/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/jgzn/jld/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/jgzn/jsdw/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/jgzn/kssz/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/zgrs/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/cgzb/cgssqk/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/ghcw/czyjs/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/yhyshj/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/xygs/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/sthj/wrfz/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/sthj/gtfw/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/hjjcxxg/jdxjcxx/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/hjjcxxg/hjjczhx/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/hjzl/kqhjzl/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/hjzl/dbshjzl/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/shgysy/hjzl/shjzlzk/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/ghxx/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/qtgk/ssj_1/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/qtgk/jyta/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/qtgk/zwdc/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/xzjczt/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/xzjcscyj/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/xzjcpcsx/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/xzjcbz/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/zxjcjh/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/sqxzjcgs/xzjcws/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/xkfw/xzxkjg/hfsjg/',
        'http://hbj.enshi.gov.cn/xxgk/zdgk/cfqz/xzzfsxg/'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.shtml"

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
