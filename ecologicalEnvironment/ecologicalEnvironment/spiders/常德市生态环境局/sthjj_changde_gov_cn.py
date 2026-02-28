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
    'detail_urls': "//ul[@class='newsList']/li/a/@href",
    'publish_times': "//ul[@class='newsList']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="path"]/div[@class="sw"]//a/text()',
    'content': '//div[contains(@class, "conTxt")]//p',
    'attachment': '//div[contains(@class, "conTxt")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "conTxt")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"number\s*>\s*(\d+)",
}


class SthjjChangdeGovCn(BasePortiaSpider):
    name = "sthjj_changde_gov_cn"
    allowed_domains = ["sthjj.changde.gov.cn"]

    start_urls = [
        'https://sthjj.changde.gov.cn/gzdt/cddt',
        'https://sthjj.changde.gov.cn/gzdt/qxxx',
        'https://sthjj.changde.gov.cn/gzdt/hjdt',
        'https://sthjj.changde.gov.cn/gzdt/tzgg',
        'https://sthjj.changde.gov.cn/gzdt/ztzl/hjwfpgt',
        'https://sthjj.changde.gov.cn/gzdt/ztzl/jdcpfgl',
        'https://sthjj.changde.gov.cn/gzdt/ztzl/sjhjr',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719410&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719405&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719404&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719401&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719399&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719397&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719395&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719402&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719411&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719341&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719340&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719339&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?catId=6719343&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?catId=6719344&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?sub=&catId=6719392&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?catId=6719336&nav=3&action=list&type=4&pageIndex=1',
        'https://sthjj.changde.gov.cn/zwgk/public/column/6617357?catId=6719342&nav=3&action=list&type=4&pageIndex=1'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_url = base_url.rstrip('/')
        # 适配带pageIndex参数的URL：替换pageIndex=1为pageIndex=页码
        if 'pageIndex=' in clean_url:
            return clean_url.replace('pageIndex=1', f'pageIndex={page}')
        # 适配纯路径URL：末尾拼接_页码
        else:
            return clean_url + f'_{page}'

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
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [
                        Regex(REGEX["total_page"]),
                        lambda x: x[0] if (x and x[0]) else "1"
                    ],
                    type="xpath"
                )
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
