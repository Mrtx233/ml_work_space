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
    'detail_urls': "//div[@id='morelist']/ul[@class='more-list']/li/a/@href",
    'publish_times': "//div[@id='morelist']/ul[@class='more-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="crumb-nav"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class KjtGxzfGovCnSpider(BasePortiaSpider):
    name = "kjt_gxzf_gov_cn"
    allowed_domains = ["kjt.gxzf.gov.cn"]

    start_urls = [
        "http://kjt.gxzf.gov.cn/dtxx_59340/tzgg/",
        "http://kjt.gxzf.gov.cn/dtxx_59340/kjgz/kjtgz/",
        "http://kjt.gxzf.gov.cn/dtxx_59340/kjgz/sxgz/",
        "http://kjt.gxzf.gov.cn/dtxx_59340/kjdt/",
        "http://kjt.gxzf.gov.cn/zthd/2020gxkjlzyz/",
        "http://kjt.gxzf.gov.cn/zthd/jgdj/",
        "http://kjt.gxzf.gov.cn/zthd/srxxgcxjpxsdzgtsshzysxztjy/",
        "http://kjt.gxzf.gov.cn/zthd/qljg/",
        "http://kjt.gxzf.gov.cn/zthd/aqscfzjzxc/",
        "http://kjt.gxzf.gov.cn/zthd/zlzhmzgttys/",
        "http://kjt.gxzf.gov.cn/zmhd/jdjb/",
        "http://kjt.gxzf.gov.cn/zmhd/zjdc/myzj/",
        "http://kjt.gxzf.gov.cn/zmhd/zjdc/yjfk/",
        "http://kjt.gxzf.gov.cn/xxgk/ghjh/zcqgh/",
        "http://kjt.gxzf.gov.cn/xxgk/ghjh/ndjh/",
        "http://kjt.gxzf.gov.cn/xxgk/ghjh/ssfa/",
        "http://kjt.gxzf.gov.cn/xxgk/sjkf/sjfb/",
        "http://kjt.gxzf.gov.cn/xxgk/sjkf/kjqy/",
        "http://kjt.gxzf.gov.cn/xxgk/sjkf/kjcg/",
        "http://kjt.gxzf.gov.cn/xxgk/sjkf/cxjd/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/xzxksx/xzqzqd/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/xzxksx/xzxksx_84696/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/cgxx/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/tzgg_84687/bbmwj/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/yjgl/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/rsxx_84678/klzp/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/tajy/",
        "http://kjt.gxzf.gov.cn/xxgk/zfxxgk/zfxxgkml/rsxx_84678/rsrm/",
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
