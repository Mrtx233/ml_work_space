from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, AgriItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex

# ===================== 抽离的XPath常量（核心改造） =====================
# 列表页XPath
LIST_XPATH = {
    "detail_urls": '//*[@class="lbcc-nr"]//li/a/@href | //div[@id="mCSB_1_container"]//ul//a/@href | //div[@class="jgxx-r-box"]/table/tbody/tr/td[2]/a/@href',  # 详情页链接
    "publish_times": '//*[@class="lbcc-nr"]//li/span/text() | //div[@id="mCSB_1_container"]//ul//span/text() | //div[@class="jgxx-r-box"]/table/tbody/tr/td[3]/text()',  # 发布时间
    "next_page": '//div[@class="jspIndex4"]/a[last()]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="breadcrumb no-margin"]//a/text()',  # 面包屑菜单
    "content": '//div[contains(@class, "xl-xqnr")]//p',  # 正文内容
    "attachment": '//div[contains(@class, "xl-xqnr")]//p//a/@href',  # 附件链接
    "attachment_name": '//div[contains(@class, "v")]//p//a/text()',  # 附件名称
    # "indexnumber": '//div[@class="article"]/table[1]/tbody/tr[1]/td[1]/text()',
    # "fileno": '//div[@class="article"]/table[1]/tbody/tr[3]/td[2]/text()',
    # "category": '//div[@class="article"]/table[1]/tbody/tr[4]/td[1]/text()',
    # "issuer": '//div[@class="article"]/table[1]/tbody/tr[2]/td[1]/text()',
    # "status": '//div[@class="article"]/table[1]/tbody/tr[4]/td[2]/text()',
    # "writtendate": '//div[@class="article"]/table[1]/tbody/tr[1]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class XtmzXiangtanGovCnSpider(BasePortiaSpider):
    name = "xtmz_xiangtan_gov_cn"
    allowed_domains = ["xtmz.xiangtan.gov.cn"]
    start_urls = [
        "https://xtmz.xiangtan.gov.cn/13634/27144/index.htm",
        "https://xtmz.xiangtan.gov.cn/19383/index.htm",
        "https://xtmz.xiangtan.gov.cn/19120/index.htm",
        "https://xtmz.xiangtan.gov.cn/13612/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13716/13727/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13716/13726/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13728/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13716/13725/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13713/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13715/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/20375/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/29665/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/29664/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/29663/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/29662/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/29540/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/21414/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/20292/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13729/index.htm",
        "https://xtmz.xiangtan.gov.cn/13609/13613/index.htm",
        "https://xtmz.xiangtan.gov.cn/13691/13711/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/20376/index.htm",
        "https://xtmz.xiangtan.gov.cn/13654/13655/20375/index.htm",

    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/index.htm')}/index_{page + 1}.htm"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url})
            # cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    # 列表页配置：引用LIST_XPATH变量
    list_items = [[
        Item(ListItems,
             None,
             'body',
             [
                 Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type="xpath"),
                 Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'var maxPageItems = "(\d+)";')], type="xpath"),
             ])]]

    # 详情页配置：引用DETAIL_XPATH变量
    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       DETAIL_XPATH["title"],
                       [], required=False, type='xpath'),

                 Field('publish_time',
                       DETAIL_XPATH["publish_time"],
                       [Regex(r'时间：\s*(\d{4}-\d{2}-\d{2})')], type='xpath'),

                 Field('menu',
                       DETAIL_XPATH["menu"],
                       [Text(), Join(separator='>')],type="xpath"),

                 Field('source',
                       DETAIL_XPATH["source"],
                       [Regex(r'来源：\s*([^\n\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       DETAIL_XPATH["content"],
                       [
                           lambda vals: [
                               html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                               for html_str in vals
                               if isinstance(html_str, str) and html_str.strip()
                           ],
                           lambda html_list: [
                               scrapy.Selector(text=html).xpath('string(.)').get().strip()
                               for html in html_list
                           ], Join(separator='\n')], required=False, type='xpath'),

                 Field('attachment',
                       DETAIL_XPATH["attachment"],
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [], type='xpath', file_category='attachment'),

                 # Field('indexnumber',
                 #       DETAIL_XPATH["indexnumber"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       DETAIL_XPATH["issuer"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       DETAIL_XPATH["status"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       DETAIL_XPATH["writtendate"],
                 #       [], required=False, type='xpath'),

             ])]]