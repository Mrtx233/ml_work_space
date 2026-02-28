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
    'detail_urls': "//div[@class='lbcc-nr']/ul/li/a/@href",
    'publish_times': "//div[@class='lbcc-nr']/ul/li/span/text()",
    'total_page': "//div[@class='page']/a[last()-1]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="breadcrumb no-margin"]//a/text()',
    'content': '//div[contains(@class, "detail-text")]//p',
    'attachment': '//div[contains(@class, "detail-text")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "detail-text")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
}


class WwwYiyangGovCn(BasePortiaSpider):
    name = "www_yiyang_gov_cn"
    allowed_domains = ["www.yiyang.gov.cn"]

    start_urls = [
        'https://www.yiyang.gov.cn/yyshjbhj/3451/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3452/3462/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3452/3463/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3452/3464/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3452/3465/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/40582/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/38292/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/39833/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/12346/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/35880/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/35549/35550/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/35549/35551/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/35549/35552/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/12245/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3455/4965/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/4051/31581/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3450/40771/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3449/3456/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3449/3457/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3450/40403/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3454/3637/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3450/39270/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3450/3458/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/34746/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3454/5227/5231/default.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3450/40774/index.htm',
        'https://www.yiyang.gov.cn/yyshjbhj/3454/3634/default.htm'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_url = base_url.rstrip('/')
        if 'index.htm' in clean_url:
            return clean_url.replace('index.htm', f'index_{page}.htm')
        elif 'default.htm' in clean_url:
            return clean_url.replace('default.htm', f'default_{page}.htm')
        return clean_url

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
                        Regex(REGEX["total_page"]),
                        lambda x: x[0] if (x and x[0]) else "1"
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
