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
    "detail_urls": '//div[@class="zfxxgk_zdgkc"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="zfxxgk_zdgkc"]//ul//b/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    # "menu": '//div[@class="dqwza"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="scroll_cont ScrollStyle"]//p',  # 正文内容
    "attachment": '//div[@class="scroll_cont ScrollStyle"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="scroll_cont ScrollStyle"]//p//a/text()',  # 附件名称
    # "indexnumber": '//table[@class="TonYon"]/tbody/tr[1]/td[1]/text()',
    # "fileno": '//table[@class="TonYon"]/tbody/tr[5]/td[1]/text()',
    # "category": '//table[@class="TonYon"]/tbody/tr[4]/td[1]/text()',
    # "issuer": '//table[@class="TonYon"]/tbody/tr[2]/td[1]/text()',
    # "status": '//table[@class="TonYon"]/tbody/tr[2]/td[2]/text()',
    # "writtendate": '//table[@class="TonYon"]/tbody/tr[3]/td[1]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class MzjGzlpsGovCnGkSpider(BasePortiaSpider):
    name = "mzj_gzlps_gov_cn_gk"
    allowed_domains = ["mzj.gzlps.gov.cn"]
    start_urls = [
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/zdly/jbmsbz_5712739/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/zdly/jbshfw_5712740/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/zdly/jcshzl_5712741/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/rsxx_5806295/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/jhzj_5806296/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/tjxx_5806297/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/bmwj_5806298/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/czxx_5806299/bmczjsjsgjf_5806300/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/czxx_5806299/bmczysjsgjf_5806301/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/jytabl_5806302/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/zcfg_5832217/flfg_5832218/",
        "https://mzj.gzlps.gov.cn/bmxxgk/zfxxgk_5712730/fdzdgknr/zcfg_5832217/zcjd_5832219/"
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

                 # Field('menu',
                 #       DETAIL_XPATH["menu"],
                 #       [Text(), Join(separator='>')],type="xpath"),

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