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
    'detail_urls': "//div[@id='rightBox']/div[@id='op1']/ul/li/a/@href",
    'publish_times': "//div[@id='rightBox']/div[@id='op1']/ul/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': "/div[@id='title']/h1/text()",
    'publish_time': "//div[@id='title']/p/text()",
    'source': "//div[@id='title']/p/text()",
    'menu': '//div[@id="crumb"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //div[@class=\'fjfj\']/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //div[@class=\'fjfj\']/a/@href',
    'indexnumber': "//table[@class='TonYon']//tr[1]/td[1]/text()",
    'fileno': "//table[@class='TonYon']//tr[5]/td[1]/text()",
    'category': "//table[@class='TonYon']//tr[4]/td[1]/text()",
    'issuer': "//table[@class='TonYon']//tr[2]/td[1]/text()",
    'status': "//table[@class='TonYon']//tr[2]/td[2]/text()",
    'writtendate': "//table[@class='TonYon']//tr[3]/td[1]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjHuangshiGovCn(BasePortiaSpider):
    name = "sthjj_huangshi_gov_cn"
    allowed_domains = ["sthjj.huangshi.gov.cn"]

    start_urls = [
        'https://sthjj.huangshi.gov.cn/xwzx/hbxw/index.html',
        'http://sthjj.huangshi.gov.cn/sjzx/hjzkgb/index.html',
        'http://sthjj.huangshi.gov.cn/sjzx/dbszyb/index.html',
        'http://sthjj.huangshi.gov.cn/sjzx/kqzlyb/index.html',
        'http://sthjj.huangshi.gov.cn/sjzx/syjcbg/index.html',
        'http://sthjj.huangshi.gov.cn/sjzx/qywryjd/index.html',
        'https://sthjj.huangshi.gov.cn/gzhd/myzj/index.html',
        'https://sthjj.huangshi.gov.cn/ztzl/sjhbdczgjxs/dcdt/index.html',
        'https://sthjj.huangshi.gov.cn/ztzl/sjhbdczgjxs/mtbd2/index.html',
        'https://sthjj.huangshi.gov.cn/ztzl/sjhbdczgjxs/bdbg/index.html',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/ssj/index.html',
        'https://sthjj.huangshi.gov.cn/zwgk/zc/gfxwj/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/zc/zcjd/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/wsgs/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/hbgh/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/czzj/czgk/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/czzj/czgk/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/rsxx/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/zfcg/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/zdlygk2/sthj/flfggz/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/jcygk/jcca/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/jcygk/jgfk/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/wjtz/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/fdzdgk/rsxx/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/zfhy/index.shtml',
        'https://sthjj.huangshi.gov.cn/zwgk/qtzdgknr/hygq/index.shtml'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 移除基础URL末尾的index.html/index.shtml
        clean_base = base_url.rstrip('index.html').rstrip('index.shtml').rstrip('/')
        # 判断是否包含zwgk关键词
        if re.search(r'zwgk', base_url):
            return f"{clean_base}/index_{page}.shtml"
        else:
            return f"{clean_base}/index_{page}.html"

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
