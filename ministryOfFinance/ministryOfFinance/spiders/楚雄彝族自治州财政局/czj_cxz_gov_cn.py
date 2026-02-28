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
    'detail_urls': "//div[@class='list fr']/ul/li/a/@href | //div[@class='scroll_wrap']/ul/li/a[@class='tit']/@href",
    'publish_times': "//div[@class='list fr']/ul/li/span/text() | //div[@class='scroll_wrap']/ul/li/span[@class='date']/text()",
    'next_page': "//span[@class='p_pages']/span[@class='p_next p_fun']/a/@href",
    'total_page': "//span[@class='p_pages']/span[last()-2]/a/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="current"]//a/text()',
    'content': '//div[contains(@class, "centent-centent")]//p',
    'attachment': '//div[contains(@class, "centent-centent")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "centent-centent")]//p//a/text()',
    'indexnumber': "//ul[@class='ov']/li[@class='fl'][1]/text()",
    'fileno': "//ul[@class='ov']/li[@class='fl'][6]/text()",
    'issuer': "//ul[@class='ov']/li[@class='fl'][3]/text()",
    'writtendate': "//ul[@class='ov']/li[@class='fl'][5]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}[.-]\d{1,2}[.-]\d{1,2}",
    'total_page': r"\d+",
}


class CzjCxzGovCn(BasePortiaSpider):
    name = "czj_cxz_gov_cn"
    allowed_domains = ["czj.cxz.gov.cn"]

    start_urls = [
        # 新闻动态/通知公告类
        'https://czj.cxz.gov.cn/xwdt.htm',
        'https://czj.cxz.gov.cn/xwdt/xscz.htm',
        'https://czj.cxz.gov.cn/xwdt/xwkd.htm',
        'https://czj.cxz.gov.cn/index/tzgg.htm',
        # 专题专栏类
        'https://czj.cxz.gov.cn/ztzl/djzt.htm',
        # 政府信息公开类
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zcfg.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/bmwj.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zcjd.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/fzgh.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/bbmyjsgk.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/bjczyjs.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zjbmys.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zjbmjshsgjfgk.htm',
        # 政府信息公开-惠民惠农类
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/sszc.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/zfcg.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/jjhsfzc.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/shbxf.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/xzsyxsf.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/yhyshj/f_j_yhzc.htm',
        # 政府信息公开-交易提案类
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/jyjta/rddbjy.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/jyjta/zxwyta.htm',
        # 政府信息公开-其他类
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/gyqyxxgk.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/czglzd.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/rzdb.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/xzzfxx.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/czyszx.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zfzw.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zfwznb.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/zxzj.htm',
        'https://czj.cxz.gov.cn/zfxxgk/fdzdgknr/snbt.htm',
        # 政府信息公开年报
        'https://czj.cxz.gov.cn/zfxxgk/zfxxgknb.htm',
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     return f"{base_url.rstrip('/')}/index_{page}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                # cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}
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
                Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
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
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
