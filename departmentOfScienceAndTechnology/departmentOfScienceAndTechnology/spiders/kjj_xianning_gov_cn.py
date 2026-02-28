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
    'detail_urls': "//ul[@class='list_list']/li/a/@href | //ul[@class='info-list']/li/a/@href",
    'publish_times': "//ul[@class='list_list']/li/span/text() | //ul[@class='info-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="now-addres-box"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p/a/text()',
    'indexnumber': "//div[@class='mlxl-content-box-one']/div/p[1]/span[1]/span/text()",
    'fileno': "//div[@class='mlxl-content-box-one']/div/p[1]/span[2]/span/text()",
    'category': "//div[@class='mlxl-content-box-one']/div/p[2]/span[1]/span/text()",
    'issuer': "//div[@class='mlxl-content-box-one']/div/p[2]/span[2]/span/text()",
    'status': "//div[@class='mlxl-content-box-one']/div/p[4]/span[1]/span/text()",
    'writtendate': "//div[@class='mlxl-content-box-one']/div/p[3]/span[2]/span/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r'createPageHTML\(\s*["\']?(\d+)["\']?\s*,',
}


class KjjXianningGovCnSpider(BasePortiaSpider):
    name = "kjj_xianning_gov_cn"
    allowed_domains = ["kjj.xianning.gov.cn"]

    start_urls = [
        "http://kjj.xianning.gov.cn/zwdt/gzdt/",
        "http://kjj.xianning.gov.cn/ztzl/whdsq/",
        "http://kjj.xianning.gov.cn/ztzl/dsxxjy/",
        "http://kjj.xianning.gov.cn/ztzl/sswgh/",
        "http://kjj.xianning.gov.cn/ztzl/ggkjcxdzl/",
        "http://kjj.xianning.gov.cn/ztzl/2021qglh/",
        "http://kjj.xianning.gov.cn/ztzl/xxsjd/",
        "http://kjj.xianning.gov.cn/xxgk/zc/wjzl/",
        "http://kjj.xianning.gov.cn/xxgk/zc/qtzdgkwj/",
        "http://kjj.xianning.gov.cn/xxgk/zc/zcjd/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/jgxx/ldbz/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/jgxx/zzjg/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/ghjh/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/tjsj/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/czzj/czyjs/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/czzj/czzxzj/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/rsxx/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/zfcg/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qxbldzmsxqd/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/xzsyxsf/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2025jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2024jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2023jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2022jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2021jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2020jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2019jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/tayabjxx/2018jyta/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/kjcggs/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/kjqy/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zczxjlsqk/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jcygk_29914/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/ssjygk_29918/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/kjcy/bsfwxx/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/kjcy/cyyhzc/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/kjcy/cyfwjg/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zwdc/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/sjbg_29921/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zfhy_29922/",
        "http://kjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/hygq/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.shtml"

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
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('status', DETAIL_XPATH["status"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
