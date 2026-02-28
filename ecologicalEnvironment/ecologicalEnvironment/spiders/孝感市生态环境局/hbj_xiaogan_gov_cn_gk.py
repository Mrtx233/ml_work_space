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
    'detail_urls': "//ul[@class='news-list']/li/a/@href",
    'publish_times': "//ul[@class='news-list']/li/span/text()",
    'total_page': "//div[@class='js_page']/ul/li[@class='xl-total']/text()",
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="p-content-top"]//a/text()',
    'content': '//div[contains(@id, "js_contentBox")]//p',
    'attachment': '//div[contains(@id, "js_contentBox")]//p//a/@href',
    'attachment_name': '//div[contains(@id, "js_contentBox")]//p//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"共(\d+)条",
}


class HbjXiaoganGovCnGk(BasePortiaSpider):
    name = "hbj_xiaogan_gov_cn_gk"
    allowed_domains = ["hbj.xiaogan.gov.cn"]

    start_urls = [
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/dwzz.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/ldxx.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/jgsz.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/czyjs.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/tqzxqykxxx.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/fp.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/tfhjsj.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/hjxc.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/stjs.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/jbts.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zysthjbhdc.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/sjsthjbhdc.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zdjsxm.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/tjxx.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/hjzlnb.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/hjzlyb.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zdwryjdxjc.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/xzxkjg.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/xzcfjd1.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zkly.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/sswgh.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/lsgh.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/jcygk.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/hygq.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/ssjygk.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/jytabl.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/yhyshj.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/ggqsydwxxgk.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zfcg1.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zfhy.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/scjggzbz.jhtml',
        'https://hbj.xiaogan.gov.cn/c/xgssthjj/zwdc.jhtml'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        pattern = re.compile(r'(.+)(\.jhtml)$')
        match = pattern.search(base_url)
        if match:
            filename = match.group(1)
            suffix = match.group(2)
            return f"{filename}_{page}{suffix}"
        else:
            return f"{base_url.rstrip('/')}/index_{page + 2}.html"

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
                        Regex(REGEX["total_page"]),  # 第一步：提取列表，如['42']
                        # 第二步：计算后转为字符串（关键！）
                        lambda x: str(max((int(x[0].strip()) + 14) // 15, 1))
                        if (isinstance(x, list) and x and x[0] and x[0].strip() and x[0].strip().isdigit())
                        else "1"  # 空值返回字符串"1"，而非整数1
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
