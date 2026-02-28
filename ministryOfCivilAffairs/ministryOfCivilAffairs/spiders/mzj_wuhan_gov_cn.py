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
    "detail_urls": '//*[@id="share"]/li/a/@href | //div[@class="article-box"]//ul//a/@href | //ul[@class="info-list mb20"]//div[@class="col-md-9"]/p/a[2]/@href',  # 详情页链接
    "publish_times": '//*[@id="share"]/li/a/p/text() | //div[@class="article-box"]//ul//a/span/text() | //ul[@class="info-list mb20"]//li[@class="row"]//div[@class="col-md-2"]/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="where mb20"]//a/text()',  # 面包屑菜单
    "content": '//div[contains(@class, "trs_paper_default")]//p',  # 正文内容
    "attachment": '//div[contains(@class, "article-box")]//a/@href',  # 附件链接
    "attachment_name": '//div[contains(@class, "article-box")]//a/text()',  # 附件名称
    "indexnumber": '//div[@class="article"]/table[1]/tbody/tr[1]/td[1]/text()',
    "fileno": '//div[@class="article"]/table[1]/tbody/tr[3]/td[2]/text()',
    "category": '//div[@class="article"]/table[1]/tbody/tr[4]/td[1]/text()',
    "issuer": '//div[@class="article"]/table[1]/tbody/tr[2]/td[1]/text()',
    "status": '//div[@class="article"]/table[1]/tbody/tr[4]/td[2]/text()',
    "writtendate": '//div[@class="article"]/table[1]/tbody/tr[1]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class MzjWuhanGovCnSpider(BasePortiaSpider):
    name = "mzj_wuhan_gov_cn"
    allowed_domains = ["mzj.wuhan.gov.cn"]
    start_urls = [
        "https://mzj.wuhan.gov.cn/mzdt_912/tpxw_916/",
        "https://mzj.wuhan.gov.cn/mzdt_912/mzyw/",
        "https://mzj.wuhan.gov.cn/zwgk_918/zc/zcfg/tzgg_953/",
        "https://mzj.wuhan.gov.cn/zwgk_918/zc/zcjd/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/ghxx/ghxx/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/ghxx/sswgh/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/ghxx/lsgh/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/tjxx/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/czzj/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/gysyjs/shbz/ylfw/ylzc/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/gysyjs/shbz/ylfw/ylxm/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/gysyjs/shbz/shfl/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/gysyjs/shbz/shjz/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/zkly/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/jcygk/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/rsxx/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/cgxx/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/sgszl/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/jytabl/gzgk/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/jytabl/mzj_sjyta1/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/zfhy/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/ssj/",
        "https://mzj.wuhan.gov.cn/zwgk_918/fdzdgk/qtzdgknr/sqxzjcgszl/",
        "https://mzj.wuhan.gov.cn/zwgk_918/xxgknb/",
        "https://mzj.wuhan.gov.cn/zwgk_918/zfwzndbb/",
        "https://mzj.wuhan.gov.cn/bmfw/shzz/tzgg/",
        "https://mzj.wuhan.gov.cn/bmfw/shzz/shzzzcfg/sjzcfg/",
        "https://mzj.wuhan.gov.cn/bmfw/shzz/zlxz/",
        "https://mzj.wuhan.gov.cn/hdjl/yjzj/",
        "https://mzj.wuhan.gov.cn/hdjl/jzxxlxxd/"

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

                 Field('status',
                       DETAIL_XPATH["status"],
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]