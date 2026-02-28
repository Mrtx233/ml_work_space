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
    'detail_urls': "//div[@class='news-list dot-b']/a/@href",
    'publish_times': "//div[@class='news-list dot-b']/a/em/text()",
    'total_page': "//div[@class='page-tile']/a[last()-1]/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//span[@class="location clearfix"]//a/text()',
    'content': '//div[contains(@class, "news_content_content")]//p',
    'attachment': '//div[contains(@class, "news_content_attachments")]//a/@href',
    'attachment_name': '//div[contains(@class, "news_content_attachments")]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
    'publish_time': r"\s*(\d{4}-\d{2}-\d{2})",
    'source': r"\s*([^\n\s]+)",
}


class ZzsfjZhengzhouGovCnSpider(BasePortiaSpider):
    name = "zzsfj_zhengzhou_gov_cn"
    allowed_domains = ["zzsfj.zhengzhou.gov.cn"]

    start_urls = [
        "https://zzsfj.zhengzhou.gov.cn/jcdt/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/fzyaowen/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/szyw/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/tzgg/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/zfdwjy/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/sbby/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/fyldgz/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/xfaqzl/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/xzzfzl/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/gzjb/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/shce/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/suggestion/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/yfxzzd/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/zflf/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/xzzfjd/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/xzfy/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/gfxwjgl/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/jyjdgl/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/lsgz/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/gzgz/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/sqjz/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/zxjj.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/flzyzgks/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/pfyyfzl/index.jhtml",
        "https://zzsfj.zhengzhou.gov.cn/rmtj/index.jhtml"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base = base_url.rsplit(".jhtml", 1)[0]
        return f"{base}_{page + 1}.jhtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={'base_url': url,'make_url_name': 'make_url_base','use_custom_pagination': True}
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_date"])], type="xpath"),
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
