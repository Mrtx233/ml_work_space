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
    'detail_urls': "//div[@class='nav1Cont']/ul/li/a/@href | //div[@class='nav1Cont']/ul[@class='has_line']/li/a/@href",
    'publish_times': "//div[@class='nav1Cont']/ul/li/span/text() | //div[@class='nav1Cont']/ul[@class='has_line']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="breakcrumb ma"]//a/text()',
    'content': '//div[contains(@class, "trs_editor_view")]//p',
    'attachment': '//div[contains(@class, "trs_editor_view")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "trs_editor_view")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\(\s*(\d+)\s*,",
}


class SfNanningGovCnSpider(BasePortiaSpider):
    name = "sf_nanning_gov_cn"
    allowed_domains = ["sf.nanning.gov.cn"]

    start_urls = [
        # 政务动态类
        "https://sf.nanning.gov.cn/zwdt/zwyw/",
        "https://sf.nanning.gov.cn/tzgg/",
        # 业务工作类
        "https://sf.nanning.gov.cn/ywgz/ggflfu/",
        "https://sf.nanning.gov.cn/ywgz/zffzgz/zflf/",
        "https://sf.nanning.gov.cn/ywgz/zffzgz/xzgfxwjgl/",
        "https://sf.nanning.gov.cn/ywgz/zffzgz/qtzffzgz/",
        "https://sf.nanning.gov.cn/ywgz/gjtyflzyzgks/gzxx/",
        "https://sf.nanning.gov.cn/ywgz/gjtyflzyzgks/zcyj/",
        "https://sf.nanning.gov.cn/ywgz/gjtyflzyzgks/xybz/",
        "https://sf.nanning.gov.cn/ywgz/gjtyflzyzgks/zsk_53410/",
        # 互动交流类
        "https://sf.nanning.gov.cn/hdjl/dczj/",
        # 专题专栏类
        "https://sf.nanning.gov.cn/ztzl/xyjs/",
        "https://sf.nanning.gov.cn/ztzl/lszt/xyesd/",
        "https://sf.nanning.gov.cn/ztzl/lszt/kjyq/",
        "https://sf.nanning.gov.cn/ztzl/lszt/dsjy/",
        "https://sf.nanning.gov.cn/ztzl/lszt/xjpfgxkcdy/",
        "https://sf.nanning.gov.cn/ztzl/lszt/zfdwjyzd/",
        "https://sf.nanning.gov.cn/ztzl/lszt/cjwmcs/",
        # 信息公开类
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/ghjh/zcqjh/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/ghjh/ndjh/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/jgsz/jj/ld/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/rsxx/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/zcfg/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/czxx/czys/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/czxx/czjs/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/qzqd/",
        "https://sf.nanning.gov.cn/xxgk/fdzdgknr/taya/",
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
            ]
        )
    ]]
