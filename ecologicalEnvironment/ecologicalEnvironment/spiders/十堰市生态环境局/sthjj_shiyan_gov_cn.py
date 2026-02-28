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
    'detail_urls': "//div[@class='col-12']/div/a/@href | //ul[@class='list-group']/li/a/@href",
    'publish_times': "//div[@class='col-12']/div/a/div[@class='card-footer text-right']/small/text() | //ul[@class='list-group']/li/span[1]/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//ol[@class="breadcrumb"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //div[contains(@class, "doc-content")]//p[@class=\'upload\']/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //div[contains(@class, "doc-content")]//p[@class=\'upload\']/a/text()',
    'indexnumber': "//div[@class='col border-top border-left'][1]/div[@class='row']/div[@class='col-12 col-md-8 lh-300']/text()",
    'fileno': "//div[@class='col border-top border-left'][5]/div[@class='row']/div[@class='col-12 col-md-8 lh-300']/text()",
    'category': "//div[@class='col border-top border-left'][2]/div[@class='row']/div[@class='col-12 col-md-8 lh-300']/text()",
    'issuer': "//div[@class='col border-top border-left'][4]/div[@class='row']/div[@class='col-12 col-md-8 lh-300']/text()",
    'writtendate': "//div[@class='col border-top border-left'][3]/div[@class='row']/div[@class='col-12 col-md-8 lh-300']/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r'(\d{4})(?:年|-)(\d{2})(?:月|-)(\d{2})(?:日|)',
    'total_page': r"createPageHTML\(\"(\d+)\",",
}


class SthjjShiyanGovCn(BasePortiaSpider):
    name = "sthjj_shiyan_gov_cn"
    allowed_domains = ["sthjj.shiyan.gov.cn"]

    start_urls = [
        'http://sthjj.shiyan.gov.cn/xwzx/hbdt/',
        'http://sthjj.shiyan.gov.cn/xwzx/gnhbxw/',
        'http://sthjj.shiyan.gov.cn/ztlm/sqxzjcgs/',
        'http://sthjj.shiyan.gov.cn/ztlm/ltbwz/',
        'http://sthjj.shiyan.gov.cn/ztlm/dlb/',
        'http://sthjj.shiyan.gov.cn/ztlm/xjc/',
        'http://sthjj.shiyan.gov.cn/ztlm/cjrhpwksyzz/',
        'http://sthjj.shiyan.gov.cn/ztlm/xds/',
        'http://sthjj.shiyan.gov.cn/ztlm/bgt/',
        'http://sthjj.shiyan.gov.cn/gzcy/zxft/',
        'http://sthjj.shiyan.gov.cn/gzcy/wsdc/',
        'http://sthjj.shiyan.gov.cn/gzcy/xwfbh/',
        'http://sthjj.shiyan.gov.cn/gzcy/myzj/',
        'http://sthjj.shiyan.gov.cn/hjgl/hjyxpj/hpgs/',
        'http://sthjj.shiyan.gov.cn/hjgl/hjyxpj/hpgg/',
        'http://sthjj.shiyan.gov.cn/hjgl/hjyj/',
        'http://sthjj.shiyan.gov.cn/hjjc/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/gysyjs/xczx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/gysyjs/hbdc/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jcygk/jcca/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/zkly/',
        'http://sthjj.shiyan.gov.cn/shjbhj/zc/zcwj/',
        'http://sthjj.shiyan.gov.cn/shjbhj/zc/zfwj/',
        'http://sthjj.shiyan.gov.cn/shjbhj/zc/zcfgjgfxwj_1328/',
        'http://sthjj.shiyan.gov.cn/shjbhj/zc/tzgg_1/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/jggk_1322/nsjg_1325/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/jggk_1322/xsjg_1326/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/ghjh_1332/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/czzj/czzj_1338/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/czzj/czjs/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/zfcg/cgqk/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/gysyjs/sthj/hjzljcxx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/ggqsydw/jszx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/ggqsydw/glzx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/ggqsydw/jdzx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/ggqsydw/dczx/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/ssjygk/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/zfhy/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/zczxqk/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2025/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2024/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2023/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2022/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2021/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2020/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2020_71497/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2018/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2025/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2024/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2023/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2022/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2021/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2020/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2020_71497/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/jyhtabl/zxta/2018/',
        'http://sthjj.shiyan.gov.cn/shjbhj/sfgwgkml/qtzdgknr/hygq/'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.shtml"

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
