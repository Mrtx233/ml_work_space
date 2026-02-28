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
    'detail_urls': "//div[@class='m-lst36']/ul/li[@class='hidden-xs']/a/@href | //ul[@class='xxgk_list']/li/a/@href",
    'publish_times': "//div[@class='m-lst36']/ul/li[@class='hidden-xs']/span/text() | //ul[@class='xxgk_list']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="dangqianweizhi"]//a//text()',
    'content': '//div[contains(@class, "nrCon")]//p | //div[@class="wz_zoom  scroll_cont ScrollStyle"]//p',
    'attachment': '//div[contains(@class, "nrCon")]//p//a/@href | //div[@class="wz_zoom  scroll_cont ScrollStyle"]//p/@href',
    'attachment_name': '//div[contains(@class, "nrCon")]//p//a/text() | //div[@class="wz_zoom  scroll_cont ScrollStyle"]//p/text()',
    'indexnumber': "///table[@class='xxgk_table']//tr[1]/td[2]/text()",
    'issuer': "//table[@class='xxgk_table']//tr[2]/td[4]/text()",
    'writtendate': "//table[@class='xxgk_table']//tr[1]/td[4]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('page_div',(\d+),",
}


class HbjHanzhongGovCn(BasePortiaSpider):
    name = "hbj_hanzhong_gov_cn"
    allowed_domains = ["hbj.hanzhong.gov.cn"]

    start_urls = [
        "https://hbj.hanzhong.gov.cn/hzsthjwz/tzgg/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/sjdt/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/qxdt/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/hbfl/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/zyxc/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/hbdc2024/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/dczg/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/sgn/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/fzzfxj/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/jczn/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/djgz/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/bgt/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/szl/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/dqzl/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/zlgb/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/pwxk/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/wrfz/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/dqwr/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/trwr/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/fsaq/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/gfgl/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/hjyj/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/hpxx/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/zrst/secondLevelChannel.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/jgzn/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/zwdt/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/czzj/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/zcjd/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/tajy/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/123/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/xzxk/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/xzcf/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/yjzj/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/wzbbv/xxgk_gknb_list.shtml",
        "https://hbj.hanzhong.gov.cn/hzsthjwz/rdhy/xxgk_gknb_list.shtml",
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        clean_url = re.sub(r'_\d+(?=\.shtml$)', '', base_url)
        stem = clean_url.removesuffix('.shtml')
        return f"{stem}_{page + 1}.shtml"

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
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
