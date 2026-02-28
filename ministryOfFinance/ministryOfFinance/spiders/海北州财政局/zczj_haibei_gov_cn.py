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
    'detail_urls': "//ul[contains(@class, 'doc_list')]/li/a | //ul[@class='clearfix xxgk_nav_list t4']/li/a/@href",
    'publish_times': "//ul[contains(@class, 'doc_list')]/li/span/text() | //ul[@class='clearfix xxgk_nav_list t4']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wzy_position"]//a/text() | //div[@class="ls-position clearfix"]//a/text()',
    'content': '//div[contains(@class, "j-fontContent")]//*[self::p or self::span]',
    'attachment': '//div[contains(@class, "j-fontContent")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "j-fontContent")]//p//a/text()',
    'indexnumber': "//table[@class='table_suoyin hidden-xs']//tr[1]/td[@class='pmingcheng'][1]/text()",
    'fileno': "//table[@class='table_suoyin hidden-xs']//tr[4]/td[@class='pmingcheng'][1]/text()",
    'category': "//table[@class='table_suoyin hidden-xs']//tr[1]/td[@class='pmingcheng'][2]/text()",
    'issuer': "//table[@class='table_suoyin hidden-xs']//tr[2]/td[@class='pmingcheng'][2]/text()",
    'status': "//table[@class='table_suoyin hidden-xs']//tr[4]/td[@class='pmingcheng'][2]/text()",
    'writtendate': "//table[@class='table_suoyin hidden-xs']//tr[3]/td[@class='pmingcheng'][1]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageCount:(\d+),",
}


class ZczjHaibeiGovCn(BasePortiaSpider):
    name = "zczj_haibei_gov_cn"
    allowed_domains = ["zczj.haibei.gov.cn"]

    start_urls = [
        'http://zczj.haibei.gov.cn/content/column/6797011?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6797041?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6808051?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6808061?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6808071?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6814241?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6808091?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6796771?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6797101?pageIndex=1',
        'http://zczj.haibei.gov.cn/content/column/6812341?pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?sub=&catId=6721221&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?catId=6721681&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?catId=6721691&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?catId=6721231&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?catId=6721461&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/public/column/6616411?catId=6721191&nav=3&action=list&type=4&pageIndex=1',
        'http://zczj.haibei.gov.cn/jgsz/ldzc/index.html',
        'http://zczj.haibei.gov.cn/jgsz/gclszyjrgzhyjsztft/index.html',
        'http://zczj.haibei.gov.cn/jgsz/jgzn/index.html',
        'http://zczj.haibei.gov.cn/xwdt/ztzl/hjkstz/index.html',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&action=list&nav=3&sub=&catId=6721101',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&action=list&nav=3&sub=&catId=6721151',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&action=list&nav=3&sub=&catId=6721141',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&action=list&nav=3&sub=&catId=6724881',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&catId=6721751&action=list&nav=3',
        'http://zczj.haibei.gov.cn/public/column/6616411?type=4&action=list&nav=3&sub=&catId=6721631',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)

        target_page = page + 1
        query_params['pageIndex'] = [str(target_page)]  # parse_qs返回值为列表，需用列表赋值

        new_query = urlencode(query_params, doseq=True)
        new_parsed = parsed._replace(query=new_query)
        return urlunparse(new_parsed)

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
                Field('total_page', LIST_XPATH["total_page"], [Text(),Regex(REGEX["total_page"]),lambda x: x if x and x[0].isdigit() else ["1"]], type="xpath"),
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
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
