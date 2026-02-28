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
    'detail_urls': '//ul[@class="list-group list-Special"]/li//div[@class="text-overflow"]/a/@href',
    'publish_times': '//ul[@class="list-group list-Special"]/li//div[@class="layout-fixed"]/text()',
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="breadcrumb-navigation"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "downloadfile")]//a/@href',
    'attachment_name': '//div[contains(@class, "downloadfile")]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class LzsczLiuzhouGovCn(BasePortiaSpider):
    name = "lzscz_liuzhou_gov_cn"
    allowed_domains = ["lzscz.liuzhou.gov.cn"]

    # 柳州财政局爬虫的起始URL列表
    start_urls = [
        'http://lzscz.liuzhou.gov.cn/xwzx/czdt/',
        'http://lzscz.liuzhou.gov.cn/xwzx/tzgg/',
        'http://lzscz.liuzhou.gov.cn/xwzx/czj_tpxw/',
        'http://lzscz.liuzhou.gov.cn/hdjl/zmhd/cjwthb/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/czszzsjzwsqb/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/sfssrglj_62225/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/scztzpszx/xmpsywblzn/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/scztzpszx/xmpsywsszlmx/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/scztzpszx/xxhxmpsywblzn/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/scztzpszx/xxhxmpsywsszlmx/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/hjglk/',
        'http://lzscz.liuzhou.gov.cn/wsbs/xzzx/zcglk_62229/',
        'http://lzscz.liuzhou.gov.cn/jdhy/zcjd/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/qlcz/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/tjlwgz/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/xlfzyfw/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/jsjf/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/djxx/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/xczxgzzt/',
        'http://lzscz.liuzhou.gov.cn/ztzl/zthd/zlzhmzgttys/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lsghdzc/ls_gzbj/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lsghdzc/ghdzc/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lsghdzc/ghpgzjzycg/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/xszcdrzzl1n/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lgyytl/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/ffsnjqlz/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/xyjs/zcfg/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/xyjs/xydt/xydt_62247/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/xyjs/xydt/tzgg_62248/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/xyjs/xydxaljfkqk/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/zdzj/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/2020nzfhshzbhzppp/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/czxzclqjz/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lzsczj2016ndgfxwjmljwb/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lzsczjgy2016nhjjdjcqkdgg/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lzsczjxzzfgs/',
        'http://lzscz.liuzhou.gov.cn/ztzl/lszt/lzskzgxsbqbjhjrcpygc/'

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
            ]
        )
    ]]
