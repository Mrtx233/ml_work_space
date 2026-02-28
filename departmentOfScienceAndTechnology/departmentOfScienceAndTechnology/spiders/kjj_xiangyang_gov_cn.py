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
    'detail_urls': "//ul[@class='news-list news-list9']/li/a/@href | //ul[@class='info-list']/li/a/@href",
    'publish_times': "//ul[@class='news-list news-list9']/li/time/text() | //ul[@class='info-list']/li/a/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//nav[@class="loc"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
    'indexnumber': "//table[@class='a-info']//tr[1]/td[2]/text()",
    'fileno': "//table[@class='a-info']//tr[4]/td[2]/text()",
    'category': "//table[@class='a-info']//tr[1]/td[4]/text()",
    'issuer': "//table[@class='a-info']//tr[2]/td[2]/text()",
    'writtendate': "//table[@class='a-info']//tr[2]/td[4]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\((\d+),",
}


class KjjXiangyangGovCnSpider(BasePortiaSpider):
    name = "kjj_xiangyang_gov_cn"
    allowed_domains = ["kjj.xiangyang.gov.cn"]

    # 襄阳市科技局爬虫起始URL列表
    start_urls = [
        "http://kjj.xiangyang.gov.cn/zxzx/jgzdt/",
        "http://kjj.xiangyang.gov.cn/zxzx/tpxw/",
        "http://kjj.xiangyang.gov.cn/zxzx/ttxw/",
        "http://kjj.xiangyang.gov.cn/ztzl/xzjczl/",
        "http://kjj.xiangyang.gov.cn/ztzl/ywzl/zcwdzsk/",
        "http://kjj.xiangyang.gov.cn/ztzl/ywzl/zcwdzsk/zswd/gxjscy/",
        "http://kjj.xiangyang.gov.cn/ztzl/ywzl/zcwdzsk/zswd/kjxzxqy/",
        "http://kjj.xiangyang.gov.cn/ztzl/ywzl/zcwdzsk/zswd/qtywzswd/",
        "http://kjj.xiangyang.gov.cn/ztzl/ywzl/zcwdzsk/zswd/rezsk/",
        "http://kjj.xiangyang.gov.cn/ztzl/cxylwl/",
        "http://kjj.xiangyang.gov.cn/ztzl/kjxx/gzkz/",
        "http://kjj.xiangyang.gov.cn/ztzl/kjxx/qkzj/",
        "http://kjj.xiangyang.gov.cn/ztzl/gjz/",
        "http://kjj.xiangyang.gov.cn/ztzl/lwlb/",
        "http://kjj.xiangyang.gov.cn/ztzl/jzfp/",
        "http://kjj.xiangyang.gov.cn/ztzl/zfjsn/",
        "http://kjj.xiangyang.gov.cn/ztzl/yshj/",
        "http://kjj.xiangyang.gov.cn/ztzl/fzzl/",
        "http://kjj.xiangyang.gov.cn/ztzl/cjqgwmcszl/",
        "http://kjj.xiangyang.gov.cn/ztzl/xjc/",
        "http://kjj.xiangyang.gov.cn/ztzl/yqfk/",
        "http://kjj.xiangyang.gov.cn/hdjl/zjdc/",
        "http://kjj.xiangyang.gov.cn/zwgk/zc/zcfg/",
        "http://kjj.xiangyang.gov.cn/zwgk/zc/zcjd/",
        "http://kjj.xiangyang.gov.cn/zwgk/zc/qtgk/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zzjg/jgzn/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zzjg/nsjg/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zzjg/ldjj/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zzjg/lxdh/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/ghjh/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/tjsj/ndsj/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/tjsj/lssj/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/xk_fw/xzxk/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zmsxqd/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/czzj/czys/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/czzj/sgjf/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/zfcg/cgssqk/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/rsxx/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/jcygk/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/hykf/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zwdc/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/sjbg/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zczx/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jyta/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/tzgg/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/hygq/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zdhy/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/tqzk/",
        "http://kjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/hmhnhqzc/bfzc/",
        "http://kjj.xiangyang.gov.cn/zwgk/gknb/",
        "http://kjj.xiangyang.gov.cn/zwgk/zfwzndbb/"
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
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
