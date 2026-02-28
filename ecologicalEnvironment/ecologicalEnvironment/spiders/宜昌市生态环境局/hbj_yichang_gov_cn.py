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
    'detail_urls': "//div[@class='txtlist-con']/li//a/@href | //ul/li[@class='txt1 txt1-n']/a/@href",
    'publish_times': "//div[@class='txtlist-con']/li/div[@class='txtlisty2']/text() | //ul/li[@class='date1']/text()",
    'total_page': "//div[@id='pages']/a[last()-1]/text() | //div[@id='Paging_040112705824705663']/ul/li[last()-3]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="txtlist-map"]//a/text()',
    'content': '//div[contains(@class, "txtcontent-div")]//p',
    'attachment': '//div[contains(@class, "txtcontent-div")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "txtcontent-div")]//p//a/text()',
    'indexnumber': "//div[@class='col-md-4'][4]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
    'fileno': "//div[@class='col-md-4'][6]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
    'category': "//div[@class='col-md-4'][8]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
    'issuer': "//div[@class='col-md-4'][1]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
    'status': "//div[@class='col-md-4'][5]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
    'writtendate': "//div[@class='col-md-4'][2]/div[@class='xxgknrxg-div']/div[@class='xxgknrxg-txt2']/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
}


class HbjYichangGovCn(BasePortiaSpider):
    name = "hbj_yichang_gov_cn"
    allowed_domains = ["hbj.yichang.gov.cn"]

    start_urls = [
        'http://hbj.yichang.gov.cn/list-42461-1.html',
        'http://hbj.yichang.gov.cn/list-42462-1.html',
        'http://hbj.yichang.gov.cn/list-42463-1.html',
        'http://hbj.yichang.gov.cn/list-44431-1.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        pattern = re.compile(r'-(\d+)\.html$')
        if pattern.search(base_url):
            return pattern.sub(f'-{page + 1}.html', base_url)
        else:
            return f"{base_url.rstrip('.html')}-{page + 1}.html"

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
                Field('total_page', LIST_XPATH["total_page"], [], type="xpath"),
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
