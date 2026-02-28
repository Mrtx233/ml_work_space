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
    'detail_urls': "//div[@id='ls_navjz']/ul/li/a/@href",
    'publish_times': "//div[@id='ls_navjz']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wzy_position wza-region_nav"]//a/text()',
    'content': '//div[contains(@class, "newscontnet")]//*[self::p or self::div]',
    'attachment': '//div[contains(@class, "newscontnet")]//*[self::p or self::div]//a/@href',
    'attachment_name': '//div[contains(@class, "newscontnet")]//*[self::p or self::div]//a/text()',
    'indexnumber': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[1]/td[@class='pmingcheng'][1]/text()",
    'fileno': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[4]/td[@class='pmingcheng'][2]/text()",
    'category': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[2]/td[@class='pmingcheng'][2]/text()",
    'issuer': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[2]/td[@class='pmingcheng'][1]/text()",
    'status': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[6]/td[@class='pmingcheng'][2]/text()",
    'writtendate': "//table[@class='table_suoyin hidden-sm hidden-xs']//tr[5]/td[@class='pmingcheng'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageCount:(\d+)",
}


class SthjjChuzhouGovCn(BasePortiaSpider):
    name = "sthjj_chuzhou_gov_cn"
    allowed_domains = ["sthjj.chuzhou.gov.cn"]

    start_urls = [
        'https://sthjj.chuzhou.gov.cn/content/column/7284654?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284667?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284644?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284753?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284772?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284803?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284813?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284824?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284836?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7284853?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7286123?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/7286130?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/zmhd/zxft/index.html',
        'https://sthjj.chuzhou.gov.cn/hjgk/rsxx/lqxx/index.html',
        'https://sthjj.chuzhou.gov.cn/zmhd/hdzd/index.html',
        'https://sthjj.chuzhou.gov.cn/zmhd/zxdc/index.html',
        'https://sthjj.chuzhou.gov.cn/hjgk/nsjgou/index.html',
        'https://sthjj.chuzhou.gov.cn/hjgk/rsxx/rsrm/index.html',
        'https://sthjj.chuzhou.gov.cn/hjgk/rsxx/zkzx/index.html',
        'https://sthjj.chuzhou.gov.cn/content/column/7284944?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/10052926?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/10052932?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/10052943?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/10052976?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/content/column/10053005?pageIndex=1',
        'https://sthjj.chuzhou.gov.cn/hjgk/xzql/xzqlqd/index.html',
        'https://sthjj.chuzhou.gov.cn/hjgk/xzql/sqsfhzjjg/index.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.rstrip('/').replace('pageIndex=1', f'pageIndex={page + 1}')

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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
