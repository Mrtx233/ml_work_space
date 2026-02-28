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
    'detail_urls': "//div[@class='gl-list']/li/a/@href | //ul[@class='cm-news-list']/li/a/@href",
    'publish_times': "//div[@class='gl-list']/li/span/text() | //ul[@class='cm-news-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="cwx-local"]//text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/span/text()',
    'indexnumber': "//table[@class='szf_zw-table']//tr[1]/td[1]/text()",
    'fileno': "//table[@class='szf_zw-table']//tr[3]/td[2]/text()",
    'category': "//table[@class='szf_zw-table']//tr[1]/td[2]/text()",
    'issuer': "//table[@class='szf_zw-table']//tr[2]/td[1]/text()",
    'status': "//table[@class='szf_zw-table']//tr[3]/td[1]/text()",
    'writtendate': "//table[@class='szf_zw-table']//tr[2]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class CzjXiningGovCn(BasePortiaSpider):
    name = "czj_xining_gov_cn"
    allowed_domains = ["czj.xining.gov.cn"]

    start_urls = [
        'https://czj.xining.gov.cn/sy/tzgg/',
        'https://czj.xining.gov.cn/sy/dtyw/',
        'https://czj.xining.gov.cn/sy/czxx/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmys/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/zcwj/xzgfxwj/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/zcwj/qtgw/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/zcwj/rsrm/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/ysjs/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/sfxm/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/zfwzndgzbb/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/czzjzdjc/',
        'https://czj.xining.gov.cn/zwgk/fdzdgknr/zdms/',
        'https://czj.xining.gov.cn/sy/ztzl/djxx/',
        'https://czj.xining.gov.cn/sy/ztzl/czjxgl/',
        'https://czj.xining.gov.cn/sy/ztzl/jsjf/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/xzzfkfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/jkwkfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/jjjskfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/shbzkfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/nynckfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/zhkfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/qykfgdw2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4636/ycczj2024/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/xzzfkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/jkwkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/jjjskfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/shbzkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/nynckfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/zhkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/qykfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd_4580/ycczj2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/xzzfkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/jkwkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/jjjskfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/shbzkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/nynckfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/zhkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/qykfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2022nd/ycczj2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/xzzfkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/jkwkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/jjjskfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/shbzkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/nynckfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/zhkfgdw2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/qykfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2021nd/ycczj2021/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/xzzfkfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/jkwkfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/jjjskfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/shbzkfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/nynckfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/zhkfgdw2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/ycczj2020/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2020nd/qit/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/xzzfkfgdw_4264/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/jkwkfgdw_4265/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/jjjskfgdw_4266/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/shbzkfgdw_4267/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/nynckfgdw_4268/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/zhkfgdw_4269/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2019nd/yqczj/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/zhkfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/xzzfkfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/jkwkfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/jjjskfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/shbzkfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2018nd/nynckfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/zhcfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/xzzfcfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/jkwcfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/jjjscfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/shbzcfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/2017nd/nmcfgdw/',
        'https://czj.xining.gov.cn/sy/ztzl/czyjsgkzl/bmjs/lngksj/',
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
