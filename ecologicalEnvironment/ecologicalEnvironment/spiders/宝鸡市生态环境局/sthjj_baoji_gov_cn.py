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
    'detail_urls': "//ul/div[@id='12730']/div[@class='default_pgContainer']/li/a/@href | //div[@class='default_pgContainer']/ul/li/a/@href",
    'publish_times': "//ul/div[@id='12730']/div[@class='default_pgContainer']/li/span/text() | //div[@class='default_pgContainer']/ul/li/b/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//div[@class=\'hdpd2\']/div[2]/h2/text() | //meta[@name="ArticleTitle"]/@content',
    'publish_time': '//div[@class=\'hdpd2\']/div[2]/div[@class=\'ly\']/div[@class=\'ly_left\']/span[2]/text() | //meta[@name="PubDate"]/@content',
    'source': '//div[@class=\'hdpd2\']/div[2]/div[@class=\'ly\']/div[@class=\'ly_left\']/span[1]/text() | //meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="adress"]//a/text() | //meta[@name="ColumnName"]/@content',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjBaojiGovCn(BasePortiaSpider):
    name = "sthjj_baoji_gov_cn"
    allowed_domains = ["sthjj.baoji.gov.cn"]

    start_urls = [
        "https://sthjj.baoji.gov.cn/col3670/col3678/",
        "https://sthjj.baoji.gov.cn/col3670/col3677/",
        "https://sthjj.baoji.gov.cn/col3672/col3698/",
        "https://sthjj.baoji.gov.cn/col3672/col3699/",
        "https://sthjj.baoji.gov.cn/col3672/col3700/",
        "https://sthjj.baoji.gov.cn/col3672/col3701/",
        "https://sthjj.baoji.gov.cn/col3672/col3702/",
        "https://sthjj.baoji.gov.cn/col3672/col3703/",
        "https://sthjj.baoji.gov.cn/col3675/col3713/",
        "https://sthjj.baoji.gov.cn/col3675/col3711/",
        "https://sthjj.baoji.gov.cn/col3675/col3714/",
        "https://sthjj.baoji.gov.cn/col3675/col6314/",
        "https://sthjj.baoji.gov.cn/col3675/col16387/",
        "https://sthjj.baoji.gov.cn/col3675/col16833/",
        "https://sthjj.baoji.gov.cn/col3675/col17393/",
        "https://sthjj.baoji.gov.cn/col3675/hbdc0527/",
        "https://sthjj.baoji.gov.cn/col3674/col3742/",
        "https://sthjj.baoji.gov.cn/col3674/col17067/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11093/col16572/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11193/col11196/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11193/col11195/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11193/col11194/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11197/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11198/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col11199/",
        "https://sthjj.baoji.gov.cn/col11091/col11128/col11140/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col13284/",
        "https://sthjj.baoji.gov.cn/col11091/col11092/col16133/",
        "https://sthjj.baoji.gov.cn/col11091/col11187/col11504/",
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
