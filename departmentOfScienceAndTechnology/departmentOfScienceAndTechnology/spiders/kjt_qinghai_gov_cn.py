from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, HbeaItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex


# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': "//ul[@class='list_ul']/li/a/@href",
    'publish_times': "//ul[@class='list_ul']/li/a/span/text()",
    'next_page': "//div[@id='myTabContent']/div/a[last()-1]/@href | //div[@class='lists_p']/a[last()]/@href",
    'total_page': "//div[@id='myTabContent']/div/a[last()]/@data-ci-pagination-page | //div[@class='lists_p']/span[last()-1]/a/@data-ci-pagination-page",
}

DETAIL_XPATH = {
    'title': "//div[@class='show_title']/h1/text()",
    'publish_time': "//div[@class='show_title']/p/text()",
    'source': "//div[@class='show_title']/p/text()",
    'menu': '//div[@class="show_top"]//a/text()',
    'content': '//div[contains(@class, "show_p")]//p',
    'attachment': '//div[contains(@class, "show_p")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "show_p")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'publish_time': r"发布时间：(\d{4}-\d{2}-\d{2})",
    'source': r"信息来源：(.*?)\n",
}


class KjtQinghaiGovCnSpider(BasePortiaSpider):
    name = "kjt_qinghai_gov_cn"
    allowed_domains = ["kjt.qinghai.gov.cn"]

    start_urls = [
        "https://kjt.qinghai.gov.cn/content/lists/cid/8/pid/26/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/89/pid/26/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/5/pid/26/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/91/pid/20/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/22/pid/20/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/21/pid/20/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/27/pid/3/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/28/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/74/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/61/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/75/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/29/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/30/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/31/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/32/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/33/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/34/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/35/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/73/pid/3/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/36/pid/2/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/37/pid/2/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/39/pid/4/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/41/pid/4/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/80/pid/44/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/81/pid/44/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/82/pid/44/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/85/pid/45/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/86/pid/45/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/87/pid/45/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/47/pid/24/page/",
        "https://kjt.qinghai.gov.cn/content/lists/cid/71/pid/24/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/49/pid/24/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/50/pid/24/page",
        "https://kjt.qinghai.gov.cn/content/lists/cid/62/pid/58/page",
        "https://kjt.qinghai.gov.cn/content/view/cate_id/88/page",
        "https://kjt.qinghai.gov.cn/content/view/cate_id/79/page",
        "https://kjt.qinghai.gov.cn/content/view/cate_id/78/page",
        "https://kjt.qinghai.gov.cn/content/view/cate_id/53/page",
        "https://kjt.qinghai.gov.cn/content/view/cate_id/52/page",
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
                Field('publish_time', DETAIL_XPATH["publish_time"], [Regex(REGEX["publish_time"])], required=False, type='xpath'),
                Field('source', DETAIL_XPATH["source"], [Regex(REGEX["source"])], required=False, type='xpath'),
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
