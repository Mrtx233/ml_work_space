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
    'detail_urls': "//div[@class='list_content']/div[@class='content_info']/ul/li/a/@href | //ul[@class='col-list']/li/a/@href",
    'publish_times': "//div[@class='list_content']/div[@class='content_info']/ul/li/a/span[@class='time']/text() |//ul[@class='col-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="list_info"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
    'indexnumber': "//div[@class='xy-xxgk-txt']/table//tr[1]/td[2]/text()",
    'fileno': "//div[@class='xy-xxgk-txt']/table//tr[2]/td[2]/text()",
    'category': "//div[@class='xy-xxgk-txt']/table//tr[1]/td[4]/text()",
    'issuer': "//div[@class='xy-xxgk-txt']/table//tr[2]/td[4]/text()",
    'status': "//div[@class='xy-xxgk-txt']/table//tr[3]/td[4]/text()",
    'writtendate': "//div[@class='xy-xxgk-txt']/table//tr[3]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class KjjXianyangGovCnSpider(BasePortiaSpider):
    name = "kjj_xianyang_gov_cn"
    allowed_domains = ["kjj.xianyang.gov.cn"]

    start_urls = [
        "https://kjj.xianyang.gov.cn/kjxw/kjdt/",
        "https://kjj.xianyang.gov.cn/kjxw/xqkj/",
        "https://kjj.xianyang.gov.cn/kjxw/tztg/",
        "https://kjj.xianyang.gov.cn/kjxw/ztzl/hqzc/",
        "https://kjj.xianyang.gov.cn/kjxw/ztzl/kjzt/dzqcykjcgzhxxq/",
        "https://kjj.xianyang.gov.cn/kjxw/ztzl/kjzt/fzzfjs/",
        "https://kjj.xianyang.gov.cn/kjxm/shfz/",
        "https://kjj.xianyang.gov.cn/kjxm/gygg/",
        "https://kjj.xianyang.gov.cn/kjxm/nygg/",
        "https://kjj.xianyang.gov.cn/xz/sjkjxmsb/",
        "https://kjj.xianyang.gov.cn/xz/kjcgps/",
        "https://kjj.xianyang.gov.cn/xz/gxjsqysb/",
        "https://kjj.xianyang.gov.cn/xz/qtbg/",
        "https://kjj.xianyang.gov.cn/hdjl/zjdc/",
        "https://kjj.xianyang.gov.cn/hdjl/cjwt/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/zcwj/xzgfxwj/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/zcwj/rsxx/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/fzgh/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/cwgk/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/xzzq/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/zfwzndbb/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/jyta/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/yshj/",
        "https://kjj.xianyang.gov.cn/zwgk/fdzdgknr/xxgkml/",# pdf
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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
