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
    'detail_urls': "//div[@class='m-lst36']/ul/li/a/@href | //div[@class='m-lst']/ul/li/a/@href",
    'publish_times': "//div[@class='m-lst36']/ul/li/span/text() | //div[@class='m-lst']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text()',
    'content': '//div[contains(@id, "article")]//p',
    'attachment': '//div[contains(@id, "article")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "article")]//p//a/text()',
    'indexnumber': "//div[@class='table']/div[@class='table-tr'][1]/div[@class='table-td table-p38'][1]/text()",
    'fileno': "//div[@class='table']/div[@class='table-tr'][1]/div[@class='table-td table-p38'][1]/text()",
    'category': "//div[@class='table']/div[@class='table-tr'][1]/div[@class='table-td table-p38'][2]/text()",
    'issuer': "//div[@class='table']/div[@class='table-tr'][3]/div[@class='table-td table-p38'][1]/text()",
    'status': "//div[@class='table']/div[@class='table-tr'][3]/div[@class='table-td table-p38'][2]/text()",
    'writtendate': "//div[@class='table']/div[@class='table-tr'][2]/div[@class='table-td table-p38'][2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"maxPage\s*=\s*parseInt\('(\d+)'\)",
}


class SfjWeinanGovCnSpider(BasePortiaSpider):
    name = "sfj_weinan_gov_cn"
    allowed_domains = ["sfj.weinan.gov.cn"]

    start_urls = [
        # 新闻资讯类
        "https://sfj.weinan.gov.cn/xwzx/zsdt/1.html",
        "https://sfj.weinan.gov.cn/xwzx/bsdt/1.html",
        "https://sfj.weinan.gov.cn/xwzx/qxdt/1.html",
        "https://sfj.weinan.gov.cn/xwzx/tpxw/1.html",
        "https://sfj.weinan.gov.cn/xwzx/tzgg/1.html",
        # 政民互动类
        "https://sfj.weinan.gov.cn/zmhd/tajy/zxta/1.html",
        "https://sfj.weinan.gov.cn/zmhd/tajy/rdjy/1.html",
        "https://sfj.weinan.gov.cn/zmhd/fggzyjzj/1.html",
        # 专题栏目类
        "https://sfj.weinan.gov.cn/ztlm/ljwhjy/1.html",
        "https://sfj.weinan.gov.cn/ztlm/sqjzgzzl/1.html",
        "https://sfj.weinan.gov.cn/ztlm/lggz/gzxx/1.html",
        "https://sfj.weinan.gov.cn/ztlm/lggz/bszn/1.html",
        "https://sfj.weinan.gov.cn/ztlm/ggflfw/gzxx/1.html",
        "https://sfj.weinan.gov.cn/ztlm/ggflfw/bszn/1.html",
        "https://sfj.weinan.gov.cn/ztlm/tjal/1.html",
        "https://sfj.weinan.gov.cn/ztlm/xxxcgcddesjszqhjs/1.html",
        # 政务信息公开类
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/jfwj/ybwj/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/zcfg/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/zcjd/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/czxx/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/zffz/lfyhzgfxwj/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/zffz/fzzf/1.html",
        "https://sfj.weinan.gov.cn/zfxxgk/fdzdgknr/zffz/hzfyys/1.html",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_base = base_url.rsplit('/', 1)[0].rstrip('/')
        return f"{clean_base}/{page + 1}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url,callback=self.parse_list,
                # cb_kwargs={'base_url': url}
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
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
