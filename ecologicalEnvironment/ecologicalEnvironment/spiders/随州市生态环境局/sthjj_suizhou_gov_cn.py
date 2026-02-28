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
from datetime import datetime

# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': "//div[@class='documents']/ul/li/a/@href",
    'publish_times': "//div[@class='documents']/ul/li/i/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="crumbs"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{2}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjSuizhouGovCn(BasePortiaSpider):
    name = "sthjj_suizhou_gov_cn"
    allowed_domains = ["sthjj.suizhou.gov.cn"]

    start_urls = [
        'http://sthjj.suizhou.gov.cn/fbjd_15/ywdt/tpxw/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/ywdt/hjxw/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/ywdt/sjdt/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/ywdt/xqdt/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/sthjbhdczgjxs/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/deldc/dcdt/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/deldc/bdbg/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/deldc/dcjb/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/deldc/tszn/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/wrfzgjz/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/hjwfpgt/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/bwcxljsmztjy/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/dslhjbhdc/dcdt/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/dslhjbhdc/bdbg/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/dslhjbhdc/tszn/',
        'http://sthjj.suizhou.gov.cn/bmdt_15/ztzl/sqxzjcgszl/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/zc/qtzdgkwj/gggs/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/jgzn/nsjg/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/jgzn/zsdw/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ghjh/lsgh/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ghjh/sswgh/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/tjxx/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/czgk/czyjs/czjssgjf/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/czgk/czyjs/czyssgjf/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/czgk/czzxzjj/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/zkly/sydwzk/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/sthjfg/gjflfg/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/sthjfg/dfxfggz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/sthjbz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/hjzlzk/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/kqhjzl/hjkqzlyb/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/shjzl/dbshj/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/syhjzl/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/zdwr/zdwryjbxx/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/hjzlsj/zdwr/wryjdxjcjg/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/wrfz/dqwrfz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/wrfz/swrfz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/wrfz/trwrfz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/wrfz/gtfw/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/wrfz/ydywrfz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/cpxk/zljp/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/cpxk/pwxkgl/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/cpxk/hjyxpj/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/ydqhbh/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/zrsthjbh/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/sthjzf/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/hjbh/xcjy/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/xczx/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/szssthjlygk/ggqsydwbf/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/ggjgxx/tqzxqy/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/scgz/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/tzgg/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/xwfbh/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/hykf/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/zczxjlsqk/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/hygq/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/sthbdc/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/jytabl/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/yjsgk/jcca/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/yjsgk/yjzj/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/yjsgk/fkqk/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/yjsgk/zdjcsxml/',
        'http://sthjj.suizhou.gov.cn/fbjd_15/zwgk/xxgkml/qtzdgknr/ssjygk/ccjhygzqk/'
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
                Field(
                    'publish_times',
                    LIST_XPATH["publish_times"],
                    [
                        Regex(REGEX["publish_times"]),
                        lambda vals: [
                            datetime.strptime(v.strip(), "%y-%m-%d").strftime("%Y-%m-%d")
                            if re.match(r"^\d{2}-", v.strip()) else
                            datetime.strptime(v.strip(), "%Y-%m-%d").strftime("%Y-%m-%d")
                            for v in vals if isinstance(v, str) and v.strip()
                        ]
                    ],
                    type="xpath"
                ),

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
