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
    'detail_urls': "//ul[@id='list']/li/a/@href",
    'publish_times': "//ul[@id='list']/li/span[@class='time']/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="SiteName"]/@content',
    'menu': '//div[@class="crumb js-crumb"]//a//text()',
    'content': '//div[contains(@class, "article-content")]//p',
    'attachment': '//div[contains(@class, "article-appendix none")]//a/@href | //div[contains(@class, "article-content")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "article-appendix none")]//a/text() | //div[contains(@class, "article-content")]//p//a/text()',
    'indexnumber': "//div[@class='meta-main']/ul/li[1]/div[@class='mes syh']/text()",
    'fileno': "//div[@class='meta-main']/ul/li[2]/div[@class='mes wenh']/text()",
    'writtendate': "//div[@class='meta-main']/ul/li[4]/div[@class='mes cwrq']/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r"createPageHTML\('page_div',(\d+),",
}


class CztXinjiangGovCn(BasePortiaSpider):
    name = "czt_xinjiang_gov_cn"
    allowed_domains = ["czt.xinjiang.gov.cn"]

    start_urls = [
        # 新疆财政厅-通用列表页
        'https://czt.xinjiang.gov.cn/xjczt/c114970/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114971/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114975/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115053/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115052/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115051/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115050/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115049/list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115040/list.shtml',
        # 新疆财政厅-政府信息公开列表页
        'https://czt.xinjiang.gov.cn/xjczt/c114984/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114985/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114986/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114987/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114988/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c114989/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115250/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115251/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115252/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115253/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115254/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115255/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115256/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115257/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115258/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115002/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115003/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115004/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115005/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115006/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115007/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115008/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115009/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115011/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115012/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115013/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115015/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115016/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115017/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115018/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115019/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115020/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115021/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115022/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115023/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115024/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115025/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115026/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115027/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115035/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115034/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115033/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115161/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115031/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115030/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115029/zfxxgk_list.shtml',
        'https://czt.xinjiang.gov.cn/xjczt/c115028/zfxxgk_list.shtml',
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('list.shtml')}list_{page + 1}.shtml"

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
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
