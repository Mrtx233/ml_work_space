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
    'detail_urls': "//div[@class='lucidity_pgContainer']/li/a/@href | //ul[@class='xxgk_list']/li/a/@href",
    'publish_times': "//div[@class='lucidity_pgContainer']/li/span/text() | //ul[@class='xxgk_list']/li/span/text()",
    'total_page': "//div[@class='lucidity-ui-paging-container']/ul/li[last()]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': "//div[@class='layui-container dqwz']/table//tr/td//a/text()",
    'content': '//div[contains(@id, "content")]//p',
    'attachment': '//div[contains(@id, "content")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "content")]//p//a/text()',
    'indexnumber': "//table[@class='table table-bordered xxsx']//tr[1]/td[@class='cnt'][1]/text()",
    'fileno': "//table[@class='table table-bordered xxsx']//tr[3]/td[@class='cnt'][1]/text()",
    'category': "//table[@class='table table-bordered xxsx']//tr[1]/td[@class='cnt'][2]/text()",
    'issuer': "//table[@class='table table-bordered xxsx']//tr[2]/td[@class='cnt'][1]/text()",
    'status': "//table[@class='table table-bordered xxsx']//tr[3]/td[@class='cnt'][2]/text()",
    'writtendate': "//table[@class='table table-bordered xxsx']//tr[2]/td[@class='cnt'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
}


class SthjjJingmenGovCn(BasePortiaSpider):
    name = "sthjj_jingmen_gov_cn"
    allowed_domains = ["sthjj.jingmen.gov.cn"]

    start_urls = [
        'http://sthjj.jingmen.gov.cn/col/col4958/index.html?uid=18498&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col3292/index.html?uid=18498&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col9287/index.html?uid=27258&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10931/index.html',
        'http://sthjj.jingmen.gov.cn/col/col10937/index.html',
        'http://sthjj.jingmen.gov.cn/col/col11868/index.html',
        'http://sthjj.jingmen.gov.cn/col/col10963/index.html',
        'http://sthjj.jingmen.gov.cn/col/col10964/index.html',
        'http://sthjj.jingmen.gov.cn/col/col16221/index.html',
        'http://sthjj.jingmen.gov.cn/col/col27073/index.html',
        'http://sthjj.jingmen.gov.cn/col/col3293/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10932/index.html?uid=50769&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10938/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10954/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10944/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col11867/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col10947/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col7701/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col7702/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col9529/index.html?uid=50649&pageNum=1',
        'http://sthjj.jingmen.gov.cn/col/col6925/index.html',
        'http://sthjj.jingmen.gov.cn/col/col22851/index.html',
        'http://sthjj.jingmen.gov.cn/col/col22850/index.html?uid=50649&pageNum=1'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        pattern = re.compile(r'pageNum=(\d+)')
        if pattern.search(base_url):
            return pattern.sub(f'pageNum={page + 1}', base_url)

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
