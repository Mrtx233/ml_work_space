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
    'detail_urls': "//ul[@class='list_ul fs']/li/a/@href | //div[@class='zfxxgk_zdgkc']/ul/li/a/@href",
    'publish_times': "//ul[@class='list_ul fs']/li/span[@class='times03']/text() | //div[@class='zfxxgk_zdgkc']/ul/li/b/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="lo_t"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//a/text()',
    'indexnumber': "//table[@class='zm-table3']/tbody/tr[1]/td[1]/text()",
    'fileno': "//table[@class='zm-table3']/tbody/tr[1]/td[2]/text()",
    'issuer': "//table[@class='zm-table3']/tbody/tr[2]/td[2]/text()",
    'status': "//table[@class='zm-table3']/tbody/tr[2]/td[1]/text()",
    'writtendate': "//table[@class='zm-table3']/tbody/tr[1]/td[3]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class KjtNxGovCnSpider(BasePortiaSpider):
    name = "kjt_nx_gov_cn"
    allowed_domains = ["kjt.nx.gov.cn"]

    start_urls = [
        "https://kjt.nx.gov.cn/kjdt/kjtdt/",
        "https://kjt.nx.gov.cn/kjdt/tzgg/",
        "https://kjt.nx.gov.cn/zcfg/tfwj/",
        "https://kjt.nx.gov.cn/zcfg/gfxwj/",
        "https://kjt.nx.gov.cn/zcfg/fl/",
        "https://kjt.nx.gov.cn/zcfg/xzfg/",
        "https://kjt.nx.gov.cn/zcfg/dfxfg/",
        "https://kjt.nx.gov.cn/zcfg/zfgz/",
        "https://kjt.nx.gov.cn/kjzy/cxtx/cxtd/",
        "https://kjt.nx.gov.cn/kjzy/cxtx/gxjscykfq/",
        "https://kjt.nx.gov.cn/kjzy/cxtx/jscxzx/",
        "https://kjt.nx.gov.cn/kjzy/cxtx/gcjsyjzx/",
        "https://kjt.nx.gov.cn/kjzy/cxtx/zdsys/",
        "https://kjt.nx.gov.cn/kjzy/cggb/2024/",
        "https://kjt.nx.gov.cn/kjzy/cggb/2023/",
        "https://kjt.nx.gov.cn/kjzy/cggb/cggb2022/",
        "https://kjt.nx.gov.cn/kjzy/cggb/cggb2021/",
        "https://kjt.nx.gov.cn/kjzy/cggb/cggb2020/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/kjjl2021/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/kjjl2020/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2019nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2018nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2017nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2015nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2014nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2013nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2011nd/",
        "https://kjt.nx.gov.cn/kjzy/kjjl/sjxm2010nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2022nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2021nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2020nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2019nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2018nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2017nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2016nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2015nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2014nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2013nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2012nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2011nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2010nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2009nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2008nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2007nd/",
        "https://kjt.nx.gov.cn/kjzy/jshtxgsj/2006nd/",
        "https://kjt.nx.gov.cn/gzhd/wsdc/",
        "https://kjt.nx.gov.cn/gzhd/yjzjjgfk/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/jyta/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/zcjd/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/hygk/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/zxgk/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/qzqd/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/czyjs/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/zdjcygk/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/ghxx/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/xzxk/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/xzcf/",
        "https://kjt.nx.gov.cn/zwgk/fdgk/xzsyxsf/",
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
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
