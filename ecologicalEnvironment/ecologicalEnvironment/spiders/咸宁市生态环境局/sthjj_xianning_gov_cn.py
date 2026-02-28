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
    'detail_urls': "//ul[@class='mess_ul']/li/a/@href | //div[@class='article-box']/ul[@class='info-list']/li/a[1]/@href",
    'publish_times': "//ul[@class='mess_ul']/li/span/text() | //div[@class='article-box']/ul[@class='info-list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="where mb20"]//a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //ul[@id=\'appendixlist\']/li/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //ul[@id=\'appendixlist\']/li/a/text()',
    'indexnumber': "//div[@class='mlxl-content-box-one']/div/p[1]/span[1]/span/text()",
    'fileno': "//div[@class='mlxl-content-box-one']/div/p[1]/span[2]/span/text()",
    'category': "//div[@class='mlxl-content-box-one']/div/p[2]/span[1]/span/text()",
    'issuer': "//div[@class='mlxl-content-box-one']/div/p[2]/span[2]/span/text()",
    'status': "//div[@class='mlxl-content-box-one']/div/p[4]/span[1]/span/text()",
    'writtendate': "//div[@class='mlxl-content-box-one']/div/p[4]/span[2]/span/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjjXianningGovCn(BasePortiaSpider):
    name = "sthjj_xianning_gov_cn"
    allowed_domains = ["sthjj.xianning.gov.cn"]

    start_urls = [
        'http://sthjj.xianning.gov.cn/gsgg/',
        'http://sthjj.xianning.gov.cn/hbdt/',
        'http://sthjj.xianning.gov.cn/xxgk/zc/gfxwj/',
        'http://sthjj.xianning.gov.cn/xxgk/zc/zcjd/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/jgjj/zzjg/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/jgjj/jssydw/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/ghxx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/tjxx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qxbldzmsxqd_30338/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/xzsyxsf/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/rsxx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/zfcg/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/zdjsxm/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/fpxczx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/wrfz_30357/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/jbtscl/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hpsp/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/zrst/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hyfsaq/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/xcjy/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hjjc/zdwryjbxx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hjjc/hjwfpgt/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/wryjdxjc/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hjjc1/yysydjg/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/sthj_30351/hjjc1/kqzlzk/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/tfggsj/yjya/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/tfggsj/yjxx/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/gysyjs/tfggsj/ydqk/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jcygk/jcca/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jcygk/yjzj/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jcygk/jgfk/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/ssjygk/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2025jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2024jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2023jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2022jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2021jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2020jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/jytabl/2019jyta/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zwdc/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/sjbg_30388/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zfhy/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/hygq/',
        'http://sthjj.xianning.gov.cn/xxgk/fdzdgknr/qtzdgknr/zczxjlsqk/'
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
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [
                        Regex(REGEX["total_page"]),  # 第一步：正则提取总页数（返回列表，如['50']或[]）
                        # 第二步：lambda处理空值，匹配不到则返回1（转为字符串避免类型错误）
                        lambda x: x[0].strip() if (
                                isinstance(x, list) and x and x[0] and x[0].strip().isdigit()) else "1"
                    ],
                    type="xpath"
                )
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
