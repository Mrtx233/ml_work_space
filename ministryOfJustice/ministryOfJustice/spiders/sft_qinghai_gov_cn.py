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
    'detail_urls': "//div[@class='newslist']/li/a/@href | //div[@class='bd']//li/a/@href",
    'publish_times': "//div[@class='newslist']/li/span/text() | //div[@class='bd']//li/span/text()",
    'total_page': "//ul[@class='pager']/li[@class='total']/span[@class='total']/text() | //div[@class='page']/span[@class='total']/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="path"]//a/text()',
    'content': '//div[contains(@class, "conTxt")]//p',
    'attachment': '//div[contains(@class, "conTxt")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "conTxt")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\/共\s*(\d+)\s*页",
}


class SftQinghaiGovCnSpider(BasePortiaSpider):
    name = "sft_qinghai_gov_cn"
    allowed_domains = ["sft.qinghai.gov.cn"]

    start_urls = [
        "https://sft.qinghai.gov.cn/zwdt/ywxx",
        "https://sft.qinghai.gov.cn/zwdt/ywzx",
        "https://sft.qinghai.gov.cn/zwdt/tzgg",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/fzgz1/hzlf2",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/fzgz1/hzzf2",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/fzgz1/xszh",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/fzgz1/ggflfw",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/fzgz1/zhbz",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/qmyfzs1/jcbs",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/qmyfzs1/fzzfjs",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/qmyfzs1/dydc",
        "https://sft.qinghai.gov.cn/zwdt/ywxx/qtxx",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/ssftbszn",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/rsrm",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/qlhzrqd",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/bmyjs",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/sfxm",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/zfcg",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/jcgk1",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/hzxkgs",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/hzcfjggs",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/rdjyjzxta",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/ssjygk",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/zkly",
        "https://sft.qinghai.gov.cn/zwgk/fdzdgknr/qt",
        "https://sft.qinghai.gov.cn/zwgk/fgwj/zcfg2",
        "https://sft.qinghai.gov.cn/zwgk/fgwj/swwj",
        "https://sft.qinghai.gov.cn/zwgk/fgwj/szfwj",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url}_{page + 1}"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url,callback=self.parse_list,
                # cb_kwargs={'base_url': url}
                cb_kwargs={'base_url': url,'make_url_name': 'make_url_base','use_custom_pagination': True}
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
