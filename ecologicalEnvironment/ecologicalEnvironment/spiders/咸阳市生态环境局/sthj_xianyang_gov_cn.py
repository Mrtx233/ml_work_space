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
    'detail_urls': "//div[@class='r_bottom']/ul[@class='bfc']/li/a/@href | //div[@class='col ml20']/ul[@class='col-list']/li/a/@href",
    'publish_times': "//div[@class='r_bottom']/ul[@class='bfc']/li/span/text() | //div[@class='col ml20']/ul[@class='col-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': "//div[@class='title']/text()",
    'publish_time': "//div[@class='xy-msg']/div[@class='section lf'][1]/span/text()",
    'source': "//div[@class='xy-msg']/div[@class='section lf'][2]/span/text()",
    'menu': '//div[@class="dqwz"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
    'indexnumber': "//div[@class='xy-xxgk-txt']/table//tr[1]/td[2]/text()",
    'fileno': "//div[@class='xy-xxgk-txt']/table//tr[2]/td[2]/text()",
    'category': "//div[@class='xy-xxgk-txt']/table//tr[1]/td[4]/text()",
    'issuer': "//div[@class='xy-xxgk-txt']/table//tr[2]/td[4]/text()",
    'status': "//div[@class='xy-xxgk-txt']/table//tr[3]/td[4]/text()",
    'writtendate': "//div[@class='xy-xxgk-txt']/table//tr[3]/td[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    'publish_time': r"\s*(\d{4}-\d{2}-\d{2})",
}


class SthjXianyangGovCn(BasePortiaSpider):
    name = "sthj_xianyang_gov_cn"
    allowed_domains = ["sthj.xianyang.gov.cn"]

    start_urls = [
        "https://sthj.xianyang.gov.cn/xwzx/gzdt/",
        "https://sthj.xianyang.gov.cn/xwzx/ggtz/",
        "https://sthj.xianyang.gov.cn/xwzx/tpxw/",
        "https://sthj.xianyang.gov.cn/xwzx/tt/",
        "https://sthj.xianyang.gov.cn/xwzx/jgdj/",
        "https://sthj.xianyang.gov.cn/xwzx/yw/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/ffqdczltfw/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/xfbl/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/srgczybx/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/sqxzjcgszl/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/swrfzsyq/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/sthbly/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/wfcs/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/tdfhtzh/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/fzzfjssf/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/sspxcx/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/dqwrfzfzbst/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/rdzt/qlhhstbh/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/24nzt/jswmjs/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2023zt/yshj/xzxkl/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2023zt/yshj/bal/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2023zt/yshj/zcfwjqtl/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2022zt/jfsx/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2021nzt/hbssgzkf/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2021nzt/dsxxzl/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2021nzt/gjwscsfs/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2021nzt/yqfk/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2020nzt/stwmmlxywspyxzpzb/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2020nzt/jktxxbk/hbkpxbk/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2020nzt/jktxxbk/jkgygg/",
        "https://sthj.xianyang.gov.cn/xwzx/ztzl/lszt/2019nzt/shce/",
        "https://sthj.xianyang.gov.cn/hbyw/dqwrfz/",
        "https://sthj.xianyang.gov.cn/hbyw/swrfz/",
        "https://sthj.xianyang.gov.cn/hbyw/trwrfz/",
        "https://sthj.xianyang.gov.cn/hbyw/zljp/",
        "https://sthj.xianyang.gov.cn/hbyw/sthjjcyyj/",
        "https://sthj.xianyang.gov.cn/hbyw/sthj/",
        "https://sthj.xianyang.gov.cn/hbyw/gffs/",
        "https://sthj.xianyang.gov.cn/hbyw/jdc/",
        "https://sthj.xianyang.gov.cn/hbyw/zssthjbhdc/ssthjbhdc/",
        "https://sthj.xianyang.gov.cn/hbyw/zssthjbhdc/hjbhjc/",
        "https://sthj.xianyang.gov.cn/zcfg/gjflv/",
        "https://sthj.xianyang.gov.cn/zcfg/gjbz/",
        "https://sthj.xianyang.gov.cn/zcfg/dfgf/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/zcwj/szfwj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/zcwj/xzgfxwj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/sydwxxgk/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/jcygk/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/ysjs_1/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/jyta_25543/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/rsgl/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/ndbg/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/zhzfzd/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/qdfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/wcfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/xpfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/bzfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/syfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/jyfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/qxfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/lqfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/ysfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/cwfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/xyfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/chfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/wgfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/gxfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzcf/jkfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xbzfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xsyfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xlqfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xcwfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xchfj/",
        "https://sthj.xianyang.gov.cn/zwgk_2534/fdzdgknr/xzxk/xjkfj/",
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
                Field('publish_time', DETAIL_XPATH["publish_time"], [Regex(REGEX["publish_time"])], required=False, type='xpath'),
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
