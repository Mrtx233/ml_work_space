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
    "detail_urls": '//div[@class="list_div mar-top2 "]//a/@href',  # 详情页链接
    "publish_times": '//div[@class="list_div mar-top2 "]//td/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="listpo"]//a/text()',  # 面包屑菜单
    "content": '//div[@id="zoom"]//p | //div[contains(@class, "trs_paper_default")]//p',  # 正文内容
    "attachment": '//div[@id="zoom"]//p//a/@href | //div[contains(@class, "trs_paper_default")]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@id="zoom"]//p//a/text() | //div[contains(@class, "trs_paper_default")]//p//a/text()',  # 附件名称
    "indexnumber": '//*[@id="headContainer"]/tbody/tr[1]/td/table/tbody/tr/td[1]/text()',
    "fileno": '//*[@id="headContainer"]/tbody/tr[4]/td/table/tbody/tr/td[1]/text()',
    "category": '//*[@id="headContainer"]/tbody/tr[1]/td/table/tbody/tr/td[2]/text()',
    "issuer": '//*[@id="headContainer"]/tbody/tr[2]/td/table/tbody/tr/td[1]/text()',
    "status": '//table[@class="TonYon"]/tbody/tr[2]/td[2]/text()',
    "writtendate": '//*[@id="headContainer"]/tbody/tr[2]/td/table/tbody/tr/td[1]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class HksmzHaikouGovCnSpider(BasePortiaSpider):
    name = "hksmz_haikou_gov_cn"
    allowed_domains = ["hksmz.haikou.gov.cn"]
    start_urls = [
        "https://hksmz.haikou.gov.cn/ywdt/zwdt/",
        "https://hksmz.haikou.gov.cn/xxgk/gsgg/",
        "https://hksmz.haikou.gov.cn/xxgk/zcwj/bmwj/",
        "https://hksmz.haikou.gov.cn/xxgk/zcwj/fzsxwj/",
        "https://hksmz.haikou.gov.cn/xxgk/ghjh/",
        "https://hksmz.haikou.gov.cn/xxgk/rsxx/",
        "https://hksmz.haikou.gov.cn/xxgk/czgk/",
        "https://hksmz.haikou.gov.cn/jdhy/zxjd/",
        "https://hksmz.haikou.gov.cn/jdhy/hygq/",
        "https://hksmz.haikou.gov.cn/hdjl/zjdc/",
        "https://hksmz.haikou.gov.cn/ztlm/01/",
        "https://hksmz.haikou.gov.cn/ztlm/gmsfbz/",
        "https://hksmz.haikou.gov.cn/ztlm/zdlyxxgk/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/bmwj/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/ghjh/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/gwztc/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/xzsp/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/ywgz/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/czgk/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/rsxx/",
        "https://hksmz.haikou.gov.cn/xxgk/fdzdgknr/qtxx/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page + 1}.shtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          # cb_kwargs={'base_url': url})
            cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    # 列表页配置：引用LIST_XPATH变量
    list_items = [[
        Item(ListItems,
             None,
             'body',
             [
                 Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type="xpath"),
                 # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'createPageHTML\(\s*(\d+)\s*,')], type="xpath"),
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

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 Field('fileno',
                       DETAIL_XPATH["fileno"],
                       [], required=False, type='xpath'),

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),

                 # Field('status',
                 #       DETAIL_XPATH["status"],
                 #       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]