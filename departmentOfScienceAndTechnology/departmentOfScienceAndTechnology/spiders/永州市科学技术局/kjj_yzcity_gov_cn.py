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
    'detail_urls': "//div[@class='list_div mar-top2 ']/div[@class='list-right_title fon_1']/a/@href",
    'publish_times': "//div[@class='list_div mar-top2 ']/table//tr//td[1]/text()",
    'total_page': "//script/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': "//div[@id='xxgk']/div[@class='con_title_left fl_left']//text()",
    'content': '//div[contains(@class, "zwgk_comr3 line")]//p',
    'attachment': '//div[contains(@class, "zwgk_comr3 line")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "zwgk_comr3 line")]//p//a/text()',
    'indexnumber': "//div[@class='zwgk_comr1']/table//tr[1]/td[2]/text()",
    'fileno': "//div[@class='zwgk_comr1']/table//tr[4]/td[2]/text()",
    'category': "//div[@class='zwgk_comr1']/table//tr[1]/td[4]/text()",
    'issuer': "//div[@class='zwgk_comr1']/table//tr[2]/td[2]/text()",
    'writtendate': "//div[@class='zwgk_comr1']/table//tr[2]/td[4]/publishtime/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('page_div',(\d+),",
}


class KjjYzcityGovCn(BasePortiaSpider):
    name = "kjj_yzcity_gov_cn"
    allowed_domains = ["kjj.yzcity.gov.cn"]

    start_urls = [
        'https://kjj.yzcity.gov.cn/kjj/0201/bmlist2.shtml',
        'https://kjj.yzcity.gov.cn/kjj/0202/bmlist2.shtml',
        'https://kjj.yzcity.gov.cn/kjj/0204/bmlist2.shtml',
        'https://kjj.yzcity.gov.cn/kjj/0203/bmlist2.shtml',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url = base_url.rstrip('/')
        path, fname = base_url.rsplit('/', 1)
        prefix, suffix = fname.split('.', 1)
        return f"{path}/{prefix}_{page}.{suffix}"

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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
