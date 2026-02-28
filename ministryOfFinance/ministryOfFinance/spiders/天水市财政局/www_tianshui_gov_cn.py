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
    'detail_urls': "//ul[@class='txtList']/li/a/@href | //div[@class='govnewslista1083164']/li/a/@href",
    'publish_times': "//ul[@class='txtList']/li/span/text() | //div[@class='govnewslista1083164']/li/span/text()",
    'next_page': "//span[@class='p_pages']/span[@class='p_next p_fun']/a/@href",
    'total_page': "//div[@class='pagebar']/span[@class='p_goto']/a/@onclick",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="posi"]//a/text()',
    'content': '//div[contains(@id, "vsb_content")]//p | //div[contains(@id, "content_div")]//p',
    'attachment': '//div[contains(@id, "vsb_content")]//p//a/@href | //div[contains(@id, "content_div")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "vsb_content")]//p//a/text() | //div[contains(@id, "content_div")]//p//a/text()',
    'indexnumber': "//div[@class='dtl-list']/ul/li[1]/em/text()",
    'fileno': "//div[@class='dtl-list']/ul/li[5]/em/text()",
    'category': "//div[@class='dtl-list']/ul/li[2]/em/text()",
    'issuer': "//div[@class='dtl-list']/ul/li[3]/em/text()",
    'writtendate': "//div[@class='dtl-list']/ul/li[4]/em/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"_simple_list_gotopage_fun\((\d+)",
    'source': r"\d{4}-\d{1,2}-\d{1,2}",
}


class WwwTianshuiGovCn(BasePortiaSpider):
    name = "www_tianshui_gov_cn"
    allowed_domains = ["www.tianshui.gov.cn"]

    start_urls = [
        'https://www.tianshui.gov.cn/czj/tzgg.htm',
        'https://www.tianshui.gov.cn/czj/czxw.htm',
        'https://www.tianshui.gov.cn/czj/index/jgdj.htm',
        'https://www.tianshui.gov.cn/czj/index/zwfwsx.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgkzd.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/ldbz.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/jgsz.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/zfyjs/zfys.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/zfyjs/zfjs.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/bmyjs/bmys.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/bmyjs/bmjs.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/jsjf.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/hygq.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/jytabl.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/zcjd.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/czxx/xzsyxsf.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/fdnrzdgk/czxx/zfzw.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2024.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2023.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2022.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2021.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2020.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2019.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2018.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2017.htm',
        'https://www.tianshui.gov.cn/czj/zfxxgk/zfxxgknb/a2016.htm',
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
                Field('source', DETAIL_XPATH["source"], [Regex(REGEX["source"])], required=False, type='xpath'),
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
