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
    'detail_urls': "//ul[@id='newslist']/li/a/@href | //div[@class='data-table']/div[@class='data-table-item clearfix']/div/p[@class='w659']/a/@href",
    'publish_times': "//ul[@id='newslist']/li/span/text() | //div[@class='data-table']/div[@class='data-table-item clearfix']//p[@class='w80']/a/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="info ui-float-right"]//a/text()',
    'content': '//div[contains(@class, "content-box")]//p | //div[contains(@class, "content")]//p',
    'attachment': '//div[contains(@class, "content-box")]//p//a/@href | //div[contains(@class, "content")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "content-box")]//p//a/text() | //div[contains(@class, "content")]//p//a/text()',
    'indexnumber': "//div[@class='content-table']/table//tr[1]/td[2]/text()",
    'fileno': "//div[@class='content-table']/table//tr[4]/td[2]/text()",
    'category': "//div[@class='content-table']/table//tr[1]/td[4]/text()",
    'issuer': "//div[@class='content-table']/table//tr[2]/td[2]/text()",
    'writtendate': "//div[@class='content-table']/table//tr[2]/td[4]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}[.-]\d{1,2}[.-]\d{1,2}",
    'total_page': r"PageIndex\s*>\s*(\d+)\s*\?\s*\1\s*:PageIndex",
}


class CzjKmGovCn(BasePortiaSpider):
    name = "czj_km_gov_cn"
    allowed_domains = ["czj.km.gov.cn"]

    start_urls = [
        # 政务动态类
        'https://czj.km.gov.cn/zwdt/czyw/',
        'https://czj.km.gov.cn/zwdt/mtjj/',
        'https://czj.km.gov.cn/zwdt/tzgg/',
        # 工作专题类
        'https://czj.km.gov.cn/gzzt/djgz/zbhd/',
        'https://czj.km.gov.cn/gzzt/djgz/jgdj/',
        'https://czj.km.gov.cn/gzzt/lxyz/',
        'https://czj.km.gov.cn/gzzt/yzxjpzsjzydfxfyqj/',
        'https://czj.km.gov.cn/gzzt/pfqjfzkm/',
        # 互动交流类
        'https://czj.km.gov.cn/hdjl/rdhy/',
        'https://czj.km.gov.cn/hdjl/zxzj/',
        'https://czj.km.gov.cn/hdjl/cjwtwd/',
        # 政府信息公开类
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zfld/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zzjg/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zcjd/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zfwzgzndbb/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/ghjh/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/czzj/czyjs/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/czzj/sgjf/',
        # 政府信息公开-重点领域信息公开
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcg/jggg/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcg/zcfg/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcg/zlxz/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcg/zdgz/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/zfyjs/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/zfhshzbhzppp/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/zwxx/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/sgjf/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/bmyjs/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/xzsyxsf/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/jsjfxxgk/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/fssrgl/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/xwfb/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zdjc/',
        # 政府信息公开-交易表格（2017-2025）
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2025n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2024n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2023n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2022n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2021n/',
        'https://czj.km.gov.cn/2020n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2019n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2018n/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2017n/',
        # 政府信息公开-行政处罚/其他类
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/xzcfhxzqz/yjxx/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/xzcfhxzqz/jgxx/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/yktgl/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/czzjzdjc/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/czsj/',
        'https://czj.km.gov.cn/zfxxgk/fdzdgknr/zczqy/',
        # 政府信息公开年报/政策文件
        'https://czj.km.gov.cn/zfxxgk/zfxxgknb/',
        'https://czj.km.gov.cn/zfxxgk/zfwj/qtwj/',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page + 1}.shtml"

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
