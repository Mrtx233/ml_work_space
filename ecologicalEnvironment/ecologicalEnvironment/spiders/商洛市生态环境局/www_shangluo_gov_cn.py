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
    'detail_urls': "//ul[@class='gg-list']/li/a/@href | //ul[@class='lzyjList']/li/a/@href",
    'publish_times': "//ul[@class='gg-list']/li/span/text() | //ul[@class='lzyjList']/li/span/text()",
    'next_page': "//span[@class='p_pages']/span[@class='p_next p_fun']/a/@href",
    'total_page': "//span[@class='p_pages']/span[last()-2]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text()',
    'content': '//div[contains(@id, "vsb_content")]//*[self::p or self::span]',
    'attachment': '//div[contains(@id, "vsb_content")]//*[self::p or self::span]//a/@href',
    'attachment_name': '//div[contains(@id, "vsb_content")]//*[self::p or self::span]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
}


class WwwShangluoGovCn(BasePortiaSpider):
    name = "www_shangluo_gov_cn"
    allowed_domains = ["www.shangluo.gov.cn"]

    start_urls = [
        "https://www.shangluo.gov.cn/hjj/index/gzdt.htm",
        "https://www.shangluo.gov.cn/hjj/index/tzgg.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/ldzc.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/czxx.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/ghjh.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/jytabl.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/hpgl.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/gtfwwrfz.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/hjzf.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/hjgl/shj.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/hjgl/dqhj.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/hbdc.htm",
        "https://www.shangluo.gov.cn/hjj/zfxxgk1/fdzdgknr/xzcf.htm",
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     return f"{base_url.rstrip('/')}/index_{page}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                # cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}
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
                Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
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
