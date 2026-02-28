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
    'detail_urls': "//ul[@class='cm-news-list gl-news-list']/li[@class='clearfix']/a/@href | //div[@class='con-rt pd30 rt']/ul/li/a/@href",
    'publish_times': "//ul[@class='cm-news-list gl-news-list']/li[@class='clearfix']/span/text() | //div[@class='con-rt pd30 rt']/ul/li/span/text()",
    'total_page': "//script/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="navigation"]//li//text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p | //div[@class="lfNewsDetail content"]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //div[@class="lfNewsDetail content"]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //div[@class="lfNewsDetail content"]//p//a/text()',
    'indexnumber': "//table[@class='cm-table-fixed zw-table']//tr[1]/td[1]/text()",
    'category': "//table[@class='cm-table-fixed zw-table']//tr[2]/td[1]/text()",
    'issuer': "//table[@class='cm-table-fixed zw-table']//tr[3]/td[1]/text()",
    'status': "//table[@class='cm-table-fixed zw-table']//tr[3]/td[2]/text()",
    'writtendate': "//table[@class='cm-table-fixed zw-table']//tr[4]/td[1]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjtShaanxiGovCn(BasePortiaSpider):
    name = "sthjt_shaanxi_gov_cn"
    allowed_domains = ["sthjt.shaanxi.gov.cn"]

    start_urls = [
        'https://sthjt.shaanxi.gov.cn/sy/tt/',
        'https://sthjt.shaanxi.gov.cn/sy/tpxw/',
        'https://sthjt.shaanxi.gov.cn/sy/szyw/',
        'https://sthjt.shaanxi.gov.cn/sy/hjyw/',
        'https://sthjt.shaanxi.gov.cn/sy/stdt/',
        'https://sthjt.shaanxi.gov.cn/sy/sxdt/',
        'https://sthjt.shaanxi.gov.cn/sy/tzgg/',
        'https://sthjt.shaanxi.gov.cn/sy/gs/',
        'https://sthjt.shaanxi.gov.cn/hd/zjdc/',
        'https://sthjt.shaanxi.gov.cn/hd/bxgz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shdz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shf/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shzh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shbf/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shbh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcwj/shpf/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/czzj/zbcg/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/czzj/czysjs/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/czzj/sgzc/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/jgbm/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/pcjg/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zsdw/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/guiz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/gfwj/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcjd/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hbdc/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/rsxx/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/gzlxm/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/tajy/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/dqzl/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/shj/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/shjzl/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/fshj/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/hjgb/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzl/hjzl/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/yjgl/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/zcgh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/kjcw/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/pwxk/pwxk/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/pwxk/qhbh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/sthj/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/dqwrfz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/swrfz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/trwrfz/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/gf/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/fyfs/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjpj/hjyx/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjpj/hjgc/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjjc/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjzf/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/xcjy/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/hjxxh/',
        'https://sthjt.shaanxi.gov.cn/xxgk/fdnr/qjsc/'
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
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
