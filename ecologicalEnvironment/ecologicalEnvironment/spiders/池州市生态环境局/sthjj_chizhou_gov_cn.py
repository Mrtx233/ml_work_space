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
    'detail_urls': "//div[@id='div2']/ul/li/a/@href",
    'publish_times': "//div[@id='div2']/ul/li/cite/text()",
    'total_page': '//*[@id="pagination"]/pagination/@pagesize',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="ititle"]//a/text()',
    'content': '//div[contains(@class, "cont_c_c")]//*[self::p or self::div]',
    'attachment': '//div[contains(@class, "cont_c_c")]//*[self::p or self::div]//a/@href',
    'attachment_name': '//div[contains(@class, "cont_c_c")]//*[self::p or self::div]//a/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"\d+",
}


class SthjjChizhouGovCn(BasePortiaSpider):
    name = "sthjj_chizhou_gov_cn"
    allowed_domains = ["sthjj.chizhou.gov.cn"]

    start_urls = [
        'https://sthjj.chizhou.gov.cn/News/showList/5511/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5512/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5513/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5514/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5515/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/8286/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/8252/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/8253/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5621/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5615/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/8410/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5625/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5578/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5585/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5544/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5547/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5572/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5543/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5540/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5539/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5553/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5563/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5557/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5556/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5555/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5552/page_1.html',
        'https://sthjj.chizhou.gov.cn/News/showList/5559/page_1.html'
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace('page_1.html', f'page_{page + 1}.html')

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
