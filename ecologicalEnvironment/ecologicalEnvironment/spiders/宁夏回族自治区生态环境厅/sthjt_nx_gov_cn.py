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
    'detail_urls': "//table[@id='dataListSearch']//tr/td[@class='text-left']/a/@href | //table[@id='newsListWrap']//tr/td[@class='text-left']/a/@href | //ul[@id='JGDJMoreWrap']/li/a/@href",
    'publish_times': "//table[@id='dataListSearch']//tr/td[3]/text() | //table[@id='newsListWrap']//tr/td[3]/text() | //ul[@id='JGDJMoreWrap']/li/span/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': "//div[@class='w-1200 m-auto crumbsNav']//a/text()",
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPage(?:HTML)?\(\s*(\d+)\s*,",
}


class SthjtNxGovCn(BasePortiaSpider):
    name = "sthjt_nx_gov_cn"
    allowed_domains = ["sthjt.nx.gov.cn"]

    start_urls = [
        'https://sthjt.nx.gov.cn/xwzx/qnxw/',
        'https://sthjt.nx.gov.cn/xwzx/gsgg/',
        'https://sthjt.nx.gov.cn/xwzx/ttxw/',
        'https://sthjt.nx.gov.cn/dwgk/jbxx/',
        'https://sthjt.nx.gov.cn/dwgk/jgdj/stmppcj/',
        'https://sthjt.nx.gov.cn/dwgk/zdjclsqk/',
        'https://sthjt.nx.gov.cn/dwgk/jgdj/zbgfhjs/',
        'https://sthjt.nx.gov.cn/dwgk/jgdj/dsxxjy/',
        'https://sthjt.nx.gov.cn/dwgk/dflz/',
        'https://sthjt.nx.gov.cn/hjzl/shjzl/shjzk/',
        'https://sthjt.nx.gov.cn/hjzl/shjzl/dbsszyb/',
        'https://sthjt.nx.gov.cn/hjzl/dqhjzl/cskqzl/',
        'https://sthjt.nx.gov.cn/hjzl/dqhjzl/hjkqzlyb/',
        'https://sthjt.nx.gov.cn/hjzl/shhjzl/',
        'https://sthjt.nx.gov.cn/hjzl/trhj/',
        'https://sthjt.nx.gov.cn/hjzl/zrst/',
        'https://sthjt.nx.gov.cn/hjzl/hjzkgb/',
        'https://sthjt.nx.gov.cn/yqhy/dczj/',
        'https://sthjt.nx.gov.cn/yqhy/zxft/',
        'https://sthjt.nx.gov.cn/yqhy/rdhy/',
        'https://sthjt.nx.gov.cn/zwgk/fgbz/flfg_63326/',
        'https://sthjt.nx.gov.cn/zwgk/fgbz/bzgf_63327/',
        'https://sthjt.nx.gov.cn/zwgk/rsxx/',
        'https://sthjt.nx.gov.cn/zwgk/czgk/czyjs/',
        'https://sthjt.nx.gov.cn/zwgk/czgk/zbcg_63336/',
        'https://sthjt.nx.gov.cn/zwgk/hjgh/zxgh/',
        'https://sthjt.nx.gov.cn/zwgk/hjgh/xdjh/',
        'https://sthjt.nx.gov.cn/zwgk/hjgh/hhlystbh/',
        'https://sthjt.nx.gov.cn/zwgk/zcjd/',
        'https://sthjt.nx.gov.cn/zwgk/jytabl/',
        'https://sthjt.nx.gov.cn/zwgk/stbc/',
        'https://sthjt.nx.gov.cn/zwgk/hygk/',
        'https://sthjt.nx.gov.cn/zwgk/hjjc/zdpwdwml/',
        'https://sthjt.nx.gov.cn/zwgk/hjjc/zjswrfkqymd/',
        'https://sthjt.nx.gov.cn/zwgk/hjpj_63348/zdgc/',
        'https://sthjt.nx.gov.cn/zwgk/hjpj_63348/hjyxpjsl/',
        'https://sthjt.nx.gov.cn/zwgk/hjpj_63348/hjyxpjnscsp/',
        'https://sthjt.nx.gov.cn/zwgk/hjpj_63348/hjyxpjpfwj/',
        'https://sthjt.nx.gov.cn/zwgk/hjpj_63348/qtlm/',
        'https://sthjt.nx.gov.cn/zwgk/wrfz/zljp/',
        'https://sthjt.nx.gov.cn/zwgk/xzcf/xk/',
        'https://sthjt.nx.gov.cn/zwgk/sthjzf/zfjc/',
        'https://sthjt.nx.gov.cn/zwgk/sthjzf/ssjygk/',
        'https://sthjt.nx.gov.cn/zwgk/sthjzf/sthjzfdlb/',
        'https://sthjt.nx.gov.cn/zwgk/sthjzf/pgt/',
        'https://sthjt.nx.gov.cn/zwgk/gfgl_63361/wxfwjyxkzbfqk/',
        'https://sthjt.nx.gov.cn/zwgk/gfgl_63361/wxfwkszyspqk/',
        'https://sthjt.nx.gov.cn/zwgk/gfgl_63361/fqdqdzcpcjclqydclqk/',
        'https://sthjt.nx.gov.cn/zwgk/fsjg/fsxkzbfqk/',
        'https://sthjt.nx.gov.cn/zwgk/fsjg/fsxtwszrsp/',
        'https://sthjt.nx.gov.cn/zwgk/hjyj/yjya_63370/',
        'https://sthjt.nx.gov.cn/zwgk/hjyj/fstdzdhjsjqymd/'
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
            ]
        )
    ]]
