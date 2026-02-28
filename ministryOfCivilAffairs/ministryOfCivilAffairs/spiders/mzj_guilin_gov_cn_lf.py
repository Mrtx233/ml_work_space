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
    "detail_urls": '//div[@class="lf"]//li[@class="clearfix"]//a/@href',  # 详情页链接
    "publish_times": '//div[@class="lf"]//li[@class="clearfix"]//a/span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//div[@id="main"]/div[2]/div[1]/p/text()',  # 标题
    "publish_time": '//div[@class="lf"]/text()',  # 发布时间
    "source": '//div[@class="lf"]/text()',  # 来源
    "menu": '//div[@id="notice"]//a/text()',  # 面包屑菜单
    "content": '//div[contains(@class, "view") and contains(@class, "TRS_UEDITOR") and contains(@class, "trs_paper_default")]//p',  # 正文内容
    "attachment": '//*[@id="main"]/div[2]/div[2]/a/@href',  # 附件链接
    "attachment_name": '//*[@id="main"]/div[2]/div[2]/a/text()',  # 附件名称
    # "indexnumber": '//table[@class="TonYon"]/tbody/tr[1]/td[1]/text()',
    # "fileno": '//table[@class="TonYon"]/tbody/tr[5]/td[1]/text()',
    # "category": '//table[@class="TonYon"]/tbody/tr[4]/td[1]/text()',
    # "issuer": '//table[@class="TonYon"]/tbody/tr[2]/td[1]/text()',
    # "status": '//table[@class="TonYon"]/tbody/tr[2]/td[2]/text()',
    # "writtendate": '//table[@class="TonYon"]/tbody/tr[3]/td[1]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class MzjGuilinGovCnLfSpider(BasePortiaSpider):
    name = "mzj_guilin_gov_cn_lf"
    allowed_domains = ["mzj.guilin.gov.cn"]
    start_urls = [

        "https://mzj.guilin.gov.cn/bszn/shzzgl/",
        "https://mzj.guilin.gov.cn/bszn/shswyetfl/",
        "https://mzj.guilin.gov.cn/bszn/ylfwycssg/",
        "https://mzj.guilin.gov.cn/bszn/shjz/",
        "https://mzj.guilin.gov.cn/bszn/bgxz/",
        "https://mzj.guilin.gov.cn/ztzl/jjjczl/",
        "https://mzj.guilin.gov.cn/zwzx/zmhf/",
        "https://mzj.guilin.gov.cn/zwzx/dczj/",
        "https://mzj.guilin.gov.cn/xxgk/czxx/",
        "https://mzj.guilin.gov.cn/xxgk/tjxx/",
        "https://mzj.guilin.gov.cn/xxgk/zcwj/",
        "https://mzj.guilin.gov.cn/xxgk/xzxk/"

    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page + 1}.html"

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
                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       DETAIL_XPATH["writtendate"],
                 #       [], required=False, type='xpath'),

             ])]]