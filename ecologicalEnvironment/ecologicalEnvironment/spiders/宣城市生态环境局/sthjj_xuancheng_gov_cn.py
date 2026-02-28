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
    'detail_urls': "//div[@class='listright-box']/ul/li/a/@href",
    'publish_times': "//div[@class='listright-box']/ul/li/span/text()",
    'total_page': '//*[@id="pagination"]/pagination/@pagesize',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="m-location"]//a/text()',
    'content': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]',
    'attachment': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]//a/@href',
    'attachment_name': '//div[contains(@class, "j-fontContent")]//*[self::p or self::div]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
}


class SthjjXuanchengGovCn(BasePortiaSpider):
    name = "sthjj_xuancheng_gov_cn"
    allowed_domains = ["sthjj.xuancheng.gov.cn"]

    start_urls = [
        'https://sthjj.xuancheng.gov.cn/News/showList/45258/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43277/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43276/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43279/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43275/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/45257/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43310/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43309/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43308/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43301/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/45045/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43287/page_1.html',
        'https://sthjj.xuancheng.gov.cn/News/showList/43283/page_1.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('page_1.html', f'page_{page + 1}.html')

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
