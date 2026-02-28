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
    'detail_urls': "//div[@class='ls-column-list']/ul/li/a/@href",
    'publish_times': "//div[@class='ls-column-list']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="ls-crumbs"]//a/text()',
    'content': "//div[@id='wenzhang']/div[@class='ls-article-info minh500 j-fontContent']//p",
    'attachment': "//div[@id='wenzhang']/div[@class='ls-article-info minh500 j-fontContent']//p//a/@href",
    'attachment_name': "//div[@id='wenzhang']/div[@class='ls-article-info minh500 j-fontContent']//p//a/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageSize=(\d+)",
}


class HbjHgGovCn(BasePortiaSpider):
    name = "hbj_hg_gov_cn"
    allowed_domains = ["hbj.hg.gov.cn"]

    start_urls = [
        'https://hbj.hg.gov.cn/content/column/6792870?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6792873?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6798665?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6798592?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6792849?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6798514?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6797230?pageIndex=1',
        'https://hbj.hg.gov.cn/content/column/6798377?pageIndex=1',
        'https://hbj.hg.gov.cn/ztzl/sqxzjcgszl/index.html',
        'https://hbj.hg.gov.cn/hdjl/dczj/index.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        pattern = re.compile(r'pageIndex=(\d+)')
        if pattern.search(base_url):
            return pattern.sub(f'pageIndex={page + 1}', base_url)

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
                        Regex(REGEX["total_page"]),  # 第一步：正则提取总页数（返回列表，如['50']或[]）
                        # 第二步：lambda处理空值，匹配不到则返回1（转为字符串避免类型错误）
                        lambda x: x[0].strip() if (
                                    isinstance(x, list) and x and x[0] and x[0].strip().isdigit()) else "1"
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
