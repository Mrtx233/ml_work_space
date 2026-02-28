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
    'detail_urls': "//ul[@class='gg-list']/li/a/@href | //ul[@class='lzyjList']/li/a/@href",
    'publish_times': "//ul[@class='gg-list']/li/span/text() | //ul[@class='lzyjList']/li/span[@class='date']/text()",
    'next_page': "//span[@class='p_pages']/span[@class='p_next p_fun']/a/@href",
    'total_page': "//span[@class='p_pages']/span[last()-2]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="px1200"]//a/text()',
    'content': '//div[contains(@class, "v_news_content")]//p | //div[@id=\'vsb_content_93\']//p',
    'attachment': '//div[contains(@class, "v_news_content")]//p//a/@href | //div[@class=\'fjnew\']/span/a/@href',
    'attachment_name': '//div[contains(@class, "v_news_content")]//p//a/text() | //div[@class=\'fjnew\']/span/a/text()',
    'indexnumber': "//table[@class='xxgkcont']//tr[1]/td[@class='title_govinfocontent'][1]/text()",
    'category': "//table[@class='xxgkcont']//tr[2]/td[@class='title_govinfocontent'][1]/text()",
    'issuer': "//table[@class='xxgkcont']//tr[1]/td[@class='title_govinfocontent'][2]/text()",
    'writtendate': "//table[@class='xxgkcont']//tr[2]/td[@class='title_govinfocontent'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
}


class WwwShangluoGovCn(BasePortiaSpider):
    name = "www_shangluo_gov_cn"
    allowed_domains = ["www.shangluo.gov.cn"]

    start_urls = [
        'https://www.shangluo.gov.cn/czj/index/gzdt.htm',
        'https://www.shangluo.gov.cn/czj/index/tzgg.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/zc/bmwj.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/ldzc.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/jgsz.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/sjyjsxx.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/zfcg.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/xjzj.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/bmyjsxx.htm',
        'https://www.shangluo.gov.cn/czj/zfxxgk1/fdzdgknr/jytabl.htm',
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     return f"{base_url.rstrip('/')}/index_{page}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                # cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}
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
                Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
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
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
