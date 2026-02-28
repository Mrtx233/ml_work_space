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
    'detail_urls': "//div[@class='m-lst36']/ul/li/a/@href | //div[@class='m-lst']/ul/li/a/@href | //div[@class='m-2lst36']/ul/li/a/@href",
    'publish_times': "//div[@class='m-lst36']/ul/li/span/text() | //div[@class='m-lst']/ul/li/span/text() | //div[@class='m-2lst36']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text()',
    'content': '//div[@class="pure-g"]//p',
    'attachment': '//div[@class="pure-g"]//p//a/@href',
    'attachment_name': '//div[@class="pure-g"]//p//a/text()',
    'indexnumber': "//div[@class='table']/div[@class='table-tr']/div[@class='table-td table-p38 bd-bottom'][1]/text()",
    'writtendate': "//div[@class='table']/div[@class='table-tr']/div[@class='table-td table-p38 bd-bottom'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"maxPage = parseInt\('(\d+)'",
}


class CzjYananGovCn(BasePortiaSpider):
    name = "czj_yanan_gov_cn"
    allowed_domains = ["czj.yanan.gov.cn"]

    start_urls = [
        'https://czj.yanan.gov.cn/xwzx/czyw/1.html',
        'https://czj.yanan.gov.cn/xwzx/qxdt/1.html',
        'https://czj.yanan.gov.cn/xwzx/gsgg/1.html',
        'https://czj.yanan.gov.cn/jdhy/zjdc/1.html',
        'https://czj.yanan.gov.cn/ggfw/xzzx/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/zfxxgkzd/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/bmjg/nsjg/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/bmjg/jsdw/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/rsxx/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zfzw/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/jcygk/jcyj/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/jcygk/jcca/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/jcygk/yjqd/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/xmxx/xmxx/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/czsz/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/czyjs/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zfwj/gfxwj/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zfwj/zcfg/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/ghjh/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zcjd/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zjysap/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/czxx/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/jyta/rdjy/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/jyta/zxta/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/zxgk/hzzf/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yhyshj/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2025n/bmysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2025n/bmssdwysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2024n/bmysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2024n/bmssdwysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2023n/bmssdwysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2023n/bmysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2022n/bmysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmysgkpt/2022n/bmssdwysgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmjsgkpt/2024n/bmssdwjsgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmjsgkpt/2023n/bmssdwjsgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmjsgkpt/2022n/bmssdwjsgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/fdzdgknr/yasbmjsgkpt/2021n/bmssdwjsgkml/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/zfxxgknb/1.html',
        'https://czj.yanan.gov.cn/zfxxgk/wzgzndbb/1.html',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url = base_url.rstrip('/')
        path, fname = base_url.rsplit('/', 1)
        return f"{path}/{page}.html"

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
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
