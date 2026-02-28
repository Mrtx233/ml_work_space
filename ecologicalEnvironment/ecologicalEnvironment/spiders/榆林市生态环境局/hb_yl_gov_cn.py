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
    'detail_urls': "//ul[@class='list-item ']/li/a/@href | //ul[@class='gov-com-list']/li[@class='clearfix']/a/@href",
    'publish_times': "//ul[@class='list-item ']/li/span/text() | //ul[@class='gov-com-list']/li[@class='clearfix']/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': "//div[@id='printContent']/h1[@class='title']/text()",
    'publish_time': "//div[@id='printContent']/div[@class='source-box']/span[1]/text()",
    'source': "//div[@id='printContent']/div[@class='source-box']/span[2]/text()",
    'menu': '//div[@class="location-box"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"countPage\s*=\s*(\d+)",
    'attachment': r"^(?!mailto:).*$",
}


class HbYlGovCn(BasePortiaSpider):
    name = "hb_yl_gov_cn"
    allowed_domains = ["hb.yl.gov.cn"]

    start_urls = [
        'https://hb.yl.gov.cn/xwzx/hbyw/',
        'https://hb.yl.gov.cn/xwzx/gzdt/',
        'https://hb.yl.gov.cn/xwzx/xqkx/',
        'https://hb.yl.gov.cn/xwzx/tzgg/',
        'https://hb.yl.gov.cn/zmhd/yjzj/',
        'https://hb.yl.gov.cn/zmhd/wsdc/',
        'https://hb.yl.gov.cn/wsbs/bszn/',
        'https://hb.yl.gov.cn/wsbs/xzyd/',
        'https://hb.yl.gov.cn/hbyw/wrfz/',
        'https://hb.yl.gov.cn/hbyw/zrst/',
        'https://hb.yl.gov.cn/hbyw/zlkz/',
        'https://hb.yl.gov.cn/hbyw/gtfw/',
        'https://hb.yl.gov.cn/hbyw/xzxk/',
        'https://hb.yl.gov.cn/hbyw/xcjy/',
        'https://hb.yl.gov.cn/hbyw/hjjc/',
        'https://hb.yl.gov.cn/hbyw/hjzf/',
        'https://hb.yl.gov.cn/zfxxgk/zfxxgkzd/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zfjg/nzjg/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zfjg/zsjg/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zcfg/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zcwj/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/rsxx/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zcjd/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/ghjh/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/czxx/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zdjcygk/',
        'http://hb.yl.gov.cn/zfxxgk/fdzdgknr/tajy/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zdlygk/',
        'https://hb.yl.gov.cn/zfxxgk/fdzdgknr/zfxxgkml/',
        'https://hb.yl.gov.cn/zfxxgk/zfxxgknb/',
        'https://hb.yl.gov.cn/zfxxgk/zfgzwzbb/'
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
                Field('attachment', DETAIL_XPATH["attachment"], [Regex(REGEX["attachment"])], required=False, type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], required=False, type='xpath', file_category='attachment'),
            ]
        )
    ]]
