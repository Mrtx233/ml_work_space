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
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjXiangyangGovCn(BasePortiaSpider):
    name = "sthjj_xiangyang_gov_cn"
    allowed_domains = ["sthjj.xiangyang.gov.cn"]

    start_urls = [
        'http://sthjj.xiangyang.gov.cn/zxzx/hjxw/',
        'http://sthjj.xiangyang.gov.cn/zxzx/tpxw/',
        'http://sthjj.xiangyang.gov.cn/zxzx/gzdt/',
        'http://sthjj.xiangyang.gov.cn/zxzx/xsqdt/',
        'http://sthjj.xiangyang.gov.cn/zxzx/tzgg/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ndzd/sqxzjcgs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ndzd/fzzfjs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ndzd/jzfphlgj/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ywzt/wrfzgjz/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ywzt/jgltjs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ywzt/hjrhpwk/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ywzt/jdchfdlydjx/',
        'http://sthjj.xiangyang.gov.cn/ztzl/ywzt/lsqsxym/',
        'http://sthjj.xiangyang.gov.cn/ztzl/jgdj/shbjddjs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/jgdj/esdjs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/jgdj/sgszl/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/dxal/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/dxjy/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/shfgf/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/lwlb/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/hmssw/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/cjgjhbmfcs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/xysdecqgwrypc/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/nwcxnjsm/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/zyhbdczgjxs/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/tjqysdzl/',
        'http://sthjj.xiangyang.gov.cn/ztzl/qtzl/yqfk/',
        'http://sthjj.xiangyang.gov.cn/wsbs/zxzq/',
        'http://sthjj.xiangyang.gov.cn/wsbs/cjwt/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/dqwrfz/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/swrfz/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/zrst/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/hjjczf/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/gtfwyfs/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/xcjy/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/kjyhz/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/hpsp/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/rhpw/',
        'http://sthjj.xiangyang.gov.cn/hjxx/hjglywxxgk/pwjd/',
        'http://sthjj.xiangyang.gov.cn/hjxx/wryhjjgxxgkl/xzcf/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/zzjg/jgzn/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/zzjg/nsjg/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/zzjg/ldjj/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/zzjg/lxdh/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/ghjh/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/czzj/czys/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/czzj/zxzj/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/sgjf/',
        'http://sthjj.xiangyang.gov.cn/hjxx/wryhjjgxxgkl/hjyj/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/rsxx/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/xzxk/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/jccajcasm/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/zjyjhyjzjqkgk/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/zdjcsxml/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jcygk/bmhygk/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zczx/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/ssjygk/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jytabl/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/sjbg/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/rsrm/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zdhy/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/hygq/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/zwdc/zlmzwdc/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/jsndbg/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/ysqgkjg/',
        'http://sthjj.xiangyang.gov.cn/zwgk/gkml/qtzdgknr/tqkx/'
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
