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
    'detail_urls': '//*[@class="view right"]//li/a/@href | //*[@class="textnews-list"]//li/a/@href',
    'publish_times': '//*[@class="view right"]//li/span/text() | //*[@class="textnews-list"]//li/span/text()',
    'next_page': '//div[@class="jspIndex4"]/a[last()]/@href',
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="pos"]//a/text()',
    'content': '//div[contains(@class, "trs_editor_view")]//p',
    'attachment': '//div[contains(@class, "trs_editor_view")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "trs_editor_view")]//p//a/text()',
    "indexnumber": '//table[@class="affairs-detail-head"]//tr[1]/td[2]/text()',
    "fileno": '//table[@class="affairs-detail-head"]//tr[4]/td[2]/text()',
    "category": '//table[@class="affairs-detail-head"]//tr[1]/td[4]/text()',
    "issuer": '//table[@class="affairs-detail-head"]//tr[2]/td[2]]/text()',
    "status": '//table[@class="affairs-detail-head"]//tr[1]/td[4]/text()',
    "writtendate": '//table[@class="affairs-detail-head"]//tr[2]/td[4]/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': '\\d{4}-\\d{1,2}-\\d{1,2}',
    'total_page': 'createPageHTML\(\s*(\d+)\s*,',
}


class SfjJcgovGovCnSpider(BasePortiaSpider):
    name = "sfj_jcgov_gov_cn"
    allowed_domains = ["sfj.jcgov.gov.cn"]

    start_urls = [
        "http://sfj.jcgov.gov.cn/gzdt_1/index.shtml",
        "http://sfj.jcgov.gov.cn/flgzzd/index.shtml",
        "http://sfj.jcgov.gov.cn/ggflfw/flyz/index.shtml",
        "http://sfj.jcgov.gov.cn/ggflfw/jcgz/index.shtml",
        "http://sfj.jcgov.gov.cn/ggflfw/jczc/index.shtml",
        "http://sfj.jcgov.gov.cn/ggtz/index.shtml",
        "http://sfj.jcgov.gov.cn/ddjs/index.shtml",
        "http://sfj.jcgov.gov.cn/qmyfzs/jgjj/index.shtml",
        "http://sfj.jcgov.gov.cn/qmyfzs/jcbs/index.shtml",
        "http://sfj.jcgov.gov.cn/qmyfzs/fzgz/index.shtml",
        "http://sfj.jcgov.gov.cn/qmyfzs/xzlf/index.shtml",
        "http://sfj.jcgov.gov.cn/qmyfzs/xszx/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/gzdt_31218/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/ghjh_31219/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/rsxx_31220/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/czxx_31221/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/fgwj_31222/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/ggflfwly/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/mlqd/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/xzzfgk/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/tadf_sfj/index.shtml",
        "https://xxgk.jcgov.gov.cn/szfgzbm/jcssfj/fdzdgknr_31212/sfj_zdxzjc/index.shtml"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base = base_url.removesuffix(".shtml")
        return f"{base}_{page + 1}.shtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          # cb_kwargs={'base_url': url})
            cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field(
                    'publish_times',
                    LIST_XPATH["publish_times"],
                    [Regex(REGEX["publish_date"])],
                    type="xpath"
                ),
                # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [Regex(REGEX["total_page"])],
                    type="xpath"
                ),
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

                Field(
                    'publish_time',
                    DETAIL_XPATH["publish_time"],
                    [],
                    type='xpath'
                ),

                Field(
                    'menu',
                    DETAIL_XPATH["menu"],
                    [Text(), Join(separator='>')],
                    type="xpath"
                ),

                Field(
                    'source',
                    DETAIL_XPATH["source"],
                    [],
                    type='xpath',
                    file_category='source'
                ),

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

                Field('attachment', DETAIL_XPATH["attachment"], [], type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], type='xpath', file_category='attachment'),

                Field('fileno',
                      DETAIL_XPATH["fileno"],
                      [], required=False, type='xpath'),

                Field('category',
                      DETAIL_XPATH["category"],
                      [], required=False, type='xpath'),

                Field('issuer',
                      DETAIL_XPATH["issuer"],
                      [], required=False, type='xpath'),

                Field('status',
                      DETAIL_XPATH["status"],
                      [], required=False, type='xpath'),

                Field('writtendate',
                      DETAIL_XPATH["writtendate"],
                      [], required=False, type='xpath'),
            ]
        )
    ]]
