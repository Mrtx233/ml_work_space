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
    'detail_urls': "//ul[@class='serv-ul gl-ul']/li/a/@href",
    'publish_times': "//ul[@class='serv-ul gl-ul']/li/span/text()",
    'total_page': "//div[@class='yj-page mb63 mt46']/a[last()]/@href",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//p[@class="position"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}[-/]\d{1,2}[-/]\d{1,2}",
    'total_page': r"index_(\d+)\.html",
}


class ShjXiningGovCn(BasePortiaSpider):
    name = "shj_xining_gov_cn"
    allowed_domains = ["shj.xining.gov.cn"]

    start_urls = [
        'https://shj.xining.gov.cn/gzdt/qxdt/',
        'https://shj.xining.gov.cn/gzdt/hjjc/',
        'https://shj.xining.gov.cn/gzdt/hjzf/',
        'https://shj.xining.gov.cn/gzdt/hbywxx/',
        'https://shj.xining.gov.cn/gzdt/tpxw/',
        'https://shj.xining.gov.cn/xwdt/zfyw/',
        'https://shj.xining.gov.cn/xwdt/hjxw/',
        'https://shj.xining.gov.cn/hdjl/hbkp/',
        'https://shj.xining.gov.cn/ztzl/zxzt/hjzlzk/hsszyb/',
        'https://shj.xining.gov.cn/ztzl/zxzt/hjzlzk/kqzlzk/',
        'https://shj.xining.gov.cn/ztzl/zxzt/hjzlzk/shjzl/',
        'https://shj.xining.gov.cn/ztzl/zxzt/sthjbhdc/',
        'https://shj.xining.gov.cn/ztzl/zxzt/qfxd/',
        'https://shj.xining.gov.cn/ztzl/zxzt/jgdjdflz/',
        'https://shj.xining.gov.cn/ztzl/zxzt/cjwfcs/',
        'https://shj.xining.gov.cn/ztzl/zxzt/cjhxmhcs/',
        'https://shj.xining.gov.cn/ztzl/zxzt/cjdsxx/',
        'https://shj.xining.gov.cn/ztzl/lszt/decwrypc/',
        'https://shj.xining.gov.cn/tzgg/'
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
