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
    'detail_urls': "//ul[@class='newlist']/li/a/@href",
    'publish_times': "//ul[@class='newlist']/li/span/text()",
    'total_page': "//div[@class='page']/a[last()]/@href",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="location"]//a/text()',
    'content': '//div[contains(@class, "xqCent")]//p',
    'attachment': '//div[contains(@class, "xqCent")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "xqCent")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"_(\d+)\.html$",
}


class HbjAnkangGovCn(BasePortiaSpider):
    name = "hbj_ankang_gov_cn"
    allowed_domains = ["hbj.ankang.gov.cn"]

    start_urls = [
        "https://hbj.ankang.gov.cn/Node-5359.html",
        "https://hbj.ankang.gov.cn/Node-5360.html",
        "https://hbj.ankang.gov.cn/Node-5361.html",
        "https://hbj.ankang.gov.cn/Node-5362.html",
        "https://hbj.ankang.gov.cn/Node-5363.html",
        "https://hbj.ankang.gov.cn/Node-5465.html",
        "https://hbj.ankang.gov.cn/Node-5466.html",
        "https://hbj.ankang.gov.cn/Node-5467.html",
        "https://hbj.ankang.gov.cn/Node-5375.html",
        "https://hbj.ankang.gov.cn/Node-5374.html",
        "https://hbj.ankang.gov.cn/Node-5376.html",
        "https://hbj.ankang.gov.cn/Node-5468.html",
        "https://hbj.ankang.gov.cn/Node-5382.html",
        "https://hbj.ankang.gov.cn/Node-5378.html",
        "https://hbj.ankang.gov.cn/Node-5381.html",
        "https://hbj.ankang.gov.cn/Node-5514.html",
        "https://hbj.ankang.gov.cn/Node-5373.html",
        "https://hbj.ankang.gov.cn/Node-90515.html",
        "https://hbj.ankang.gov.cn/Node-5372.html",
        "https://hbj.ankang.gov.cn/Node-90474.html",
        "https://hbj.ankang.gov.cn/Node-5388.html",
        "https://hbj.ankang.gov.cn/Node-5390.html",
        "https://hbj.ankang.gov.cn/Node-5369.html",
        "https://hbj.ankang.gov.cn/Node-5368.html",
        "https://hbj.ankang.gov.cn/Node-5367.html",
        "https://hbj.ankang.gov.cn/Node-5366.html",
        "https://hbj.ankang.gov.cn/Node-5473.html",
        "https://hbj.ankang.gov.cn/Node-5474.html",
        "https://hbj.ankang.gov.cn/Node-5475.html",
        "https://hbj.ankang.gov.cn/Node-5477.html",
        "https://hbj.ankang.gov.cn/Node-90703.html",
        "https://hbj.ankang.gov.cn/Node-91456.html",
        "https://hbj.ankang.gov.cn/Node-91455.html",
        "https://hbj.ankang.gov.cn/Node-92714.html",
        "https://hbj.ankang.gov.cn/Node-92735.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_url = re.sub(r'_\d+(?=\.html$)', '', base_url)
        return f"{clean_url.rstrip('.html')}_{page + 1}.html"

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
