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
    'detail_urls': "//div[@class='ty_list_main']/ul/li/a/@href",
    'publish_times': "//div[@class='ty_list_main']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="article_site clearfix"]//a//text()',
    'content': '//div[contains(@class, "p_box")]//p',
    'attachment': '//div[contains(@class, "p_box")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "p_box")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('paging',(\d+),",
}


class WwwHuaihuaGovCn(BasePortiaSpider):
    name = "www_huaihua_gov_cn"
    allowed_domains = ["www.huaihua.gov.cn"]

    start_urls = [
        'https://www.huaihua.gov.cn/sthjj/c100577/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100587/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100580/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100581/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100582/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100599/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115426/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115427/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115428/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100592/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115423/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115424/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c135687/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115430/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115431/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115432/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c133234/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115439/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115438/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c132362/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c132363/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c115440/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100601/list.shtml',
        'https://www.huaihua.gov.cn/sthjj/c100617/list.shtml'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.rstrip('/').replace('list.shtml', f'list_{page + 1}.shtml')

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
