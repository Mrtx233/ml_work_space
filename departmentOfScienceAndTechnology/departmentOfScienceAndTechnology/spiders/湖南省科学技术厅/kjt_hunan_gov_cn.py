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
    'detail_urls': "//ul[@class='list']/li/a/@href | //ul[@class='list_gkzd_content']/li/a/@href | //div[@class='container']/div[@class='right']/ul/li/a/@href | //div[@class='column_right']/ul/li/a/@href",
    'publish_times': "//div[@class='con-right']/div[@class='list']/ul/li/span/text() | //ul[@class='list_gkzd_content']/li/span/text() | //div[@class='container']/div[@class='right']/ul/li/span/text() | //div[@class='column_right']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="container"]//a//text() | //div[@class="dqwz"]/a//text()',
    'content': '//div[contains(@class, "article_content")]//p | //div[contains(@id, "content")]//p | //div[@class="article"]//p',
    'attachment': '//div[contains(@class, "article_content")]//p//a/@href | //div[contains(@id, "content")]//p//a/@href | //div[@class="article"]//p//a/@href',
    'attachment_name': '//div[contains(@class, "article_content")]//p//a/text()  | //div[contains(@id, "content")]//p//a/text() | //div[@class="article"]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('paging',(\d+),",
}


class KjtHunanGovCn(BasePortiaSpider):
    name = "kjt_hunan_gov_cn"
    allowed_domains = ["kjt.hunan.gov.cn"]

    start_urls = [
        'https://kjt.hunan.gov.cn/kjt/xxgk/gzdt/kjzx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/gzdt/kjkx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/gzdt/mtgz/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/gzdt/szdt/index.html',
        'https://kjt.hunan.gov.cn/kjt/xmxx/xmsb/index.html',
        'https://kjt.hunan.gov.cn/kjt/xmxx/xmlx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xmxx/jfxd/index.html',
        'https://kjt.hunan.gov.cn/kjt/xmxx/xmys/index.html',
        'https://kjt.hunan.gov.cn/kjt/jgdj/jgdj_1/index.html',
        'https://kjt.hunan.gov.cn/kjt/jgdj/djtzgg/index.html',
        'https://kjt.hunan.gov.cn/kjt/jgdj/dflz_1/index.html',
        'https://kjt.hunan.gov.cn/kjt/jgdj/qtgz/index.html',
        'https://kjt.hunan.gov.cn/kjt/jgdj/jswm/index.html',
        'https://kjt.hunan.gov.cn/kjt/ztzl/zzcx/gzdt_2/index.html',
        'https://kjt.hunan.gov.cn/kjt/ztzl/kcxfz/tzgg_77776/index.html',
        'https://kjt.hunan.gov.cn/kjt/ztzl/kcxfz/zxdt/index.html',
        'https://kjt.hunan.gov.cn/kjt/ztzl/zzcx/zcwj/index.html',
        'https://kjt.hunan.gov.cn/kjt/jjjc/gzdt_1/index.html',
        'https://kjt.hunan.gov.cn/kjt/jjjc/djtg/index.html',
        'https://kjt.hunan.gov.cn/kjt/jjjc/sjjs/index.html',
        'https://kjt.hunan.gov.cn/kjt/jjjc/jsjy/index.html',
        'https://kjt.hunan.gov.cn/kjt/jjjc/jdjc/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/tzgg/tzgg_1/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/tzgg/kjbtzgg/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/zcfg/fggz/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/zcfg/gjgfxwj/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/zcfg/sbgfxwj/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/zcfg/tgfxwj/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/zcfg/zcjd/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/ghjh/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/rsxx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/czxx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/cgxx/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/kjtj/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/yata/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/kjcg/yyjscg/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/kjcg/rkxu/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/kjcg/jcllg/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/xzzf/sqgs/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/xzzf/sggs/index.html',
        'https://kjt.hunan.gov.cn/kjt/xxgk/wzgznb/index.html',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('index.html')}index_{page + 1}.html"

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
            ]
        )
    ]]
