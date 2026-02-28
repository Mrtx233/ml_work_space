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
    'detail_urls': "//div[@id='ls_navjz']/ul/li/a/@href",
    'publish_times': "//div[@id='ls_navjz']/ul/li/span[@class='right date']/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="wzy_position wza-region_nav"]//a/text()',
    'content': '//div[contains(@class, "j-fontContent")]//p',
    'attachment': '//div[contains(@class, "j-fontContent")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "j-fontContent")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"pageCount:(\d+)",
}


class SthjjHuainanGovCn(BasePortiaSpider):
    name = "sthjj_huainan_gov_cn"
    allowed_domains = ["sthjj.huainan.gov.cn"]

    start_urls = [
        'https://sthjj.huainan.gov.cn/content/column/12876437?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12876469?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12876495?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281794?pageIndex=1',
        'https://sthjj.huainan.gov.cn/zmhd/myzj/index.html',
        'https://sthjj.huainan.gov.cn/content/column/12878445?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/25112648?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878522?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/22848636?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281939?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878535?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281384?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878553?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878557?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878566?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878575?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878584?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/18125225?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/22858966?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/22859007?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/22859263?pageIndex=1',
        'https://sthjj.huainan.gov.cn/hbyw/xmgl/zxysgs/index.html',
        'https://sthjj.huainan.gov.cn/hbyw/ssthj/pwxk/index.html',
        'https://sthjj.huainan.gov.cn/content/column/100465173?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/100473042?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/100473124?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281820?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878878?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878557?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/12878553?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/55623162?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281508?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281538?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/156281893?pageIndex=1',
        'https://sthjj.huainan.gov.cn/ztzl/qyhjxypjzl/index.html',
        'https://sthjj.huainan.gov.cn/content/column/156282322?pageIndex=1',
        'https://sthjj.huainan.gov.cn/content/column/22841730?pageIndex=1',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/zyhbdc/gzjb/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/zyhbdc/mtbd/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/msgczl/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/djgtfwhjwfxwzxxd/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/wmwzcjzl/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/slwqyqlzzzl/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/fkxxgzbdgrdfyyqgzqk/index.html',
        'https://sthjj.huainan.gov.cn/content/column/22841730?pageIndex=1',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/zyhbdc/gzjb/index.html',
        'https://sthjj.huainan.gov.cn/ztzl/gdzt/zyhbdc/mtbd/index.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('pageIndex=1', f'pageIndex={page + 1}')

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
                        lambda x: x[0].strip() if (
                                    isinstance(x, list) and x and x[0] and x[0].strip().isdigit()) else "1"
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
