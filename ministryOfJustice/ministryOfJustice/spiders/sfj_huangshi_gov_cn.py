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
    'detail_urls': "//div[@class='list1']/ul/li/a/@href",
    'publish_times': "//div[@class='list1']/ul/li/a/span[@class='time']/text()",
    'total_page': "//script/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@id="crumb"]/span//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\(\s*(\d+)\s*,",
}


class SfjHuangshiGovCnSpider(BasePortiaSpider):
    name = "sfj_huangshi_gov_cn"
    allowed_domains = ["sfj.huangshi.gov.cn"]

    start_urls = [
        "https://sfj.huangshi.gov.cn/gzdt/sfyw/btdt/",
        "https://sfj.huangshi.gov.cn/gzdt/sfyw/bsyw/",
        "https://sfj.huangshi.gov.cn/gzdt/sfyw/qxdt/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/fzdy/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/lfgz/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/fygz/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/xzzf/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/pfxj/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/rmcy/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/ggfl/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/lsgz/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/zyzgks/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/sqjz/",
        "https://sfj.huangshi.gov.cn/gzdt/ywdt/jdgz/",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/zcjd/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gfxwj2020/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gsgg/tz_1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gsgg/tl_1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gsgg/yj_1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gsgg/bf_1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/zc2020/gsgg/qt_1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/gzjg/ldxx/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/gzjg/zsdw/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/ghxx/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/xkfw/xzxk1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/cfqz/xzcfjd1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qxbl/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/czzj/czyjs/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/czzj/zxzj/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/zfcg/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/gysy/fp/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/gysy/ggfl/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/rsxx/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/yjsgk/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/zxqk1/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/ssj/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/jyta/rddbjybl/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/jyta/zxwytabl/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/jyta/jytablsj/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/fzndbg/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2024n_24778/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2024n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2023n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2022n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2021n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2020n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2019n/index.shtml",
        "https://sfj.huangshi.gov.cn/xxgk_17/gknr/qt/sjfb/2019nyq/index.shtml"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        if base_url.endswith(".shtml"):
            base = base_url.rsplit(".shtml", 1)[0]
            return f"{base}_{page + 1}.shtml"
        else:
            if not base_url.endswith("/"):
                base_url = f"{base_url}/"
            return f"{base_url}index_{page + 1}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={
                    'base_url': url,
                    'make_url_name': 'make_url_base',
                    'use_custom_pagination': True
                }
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_date"])], type="xpath"),
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
