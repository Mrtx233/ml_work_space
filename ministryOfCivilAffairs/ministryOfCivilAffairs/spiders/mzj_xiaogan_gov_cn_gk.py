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
    "detail_urls": '//*[@class="news-list"]/li/a[1]/@href',  # 详情页链接
    "publish_times": '//*[@class="news-list"]/li/span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    # "menu": '//div[@class="ty-ws"]//a/text()',  # 面包屑菜单
    "content": '//div[contains(@id, "js_contentBox")]//p',  # 正文内容
    "attachment": '//div[contains(@id, "js_contentBox")]//p//a/@href',  # 附件链接
    "attachment_name": '//div[contains(@id, "js_contentBox")]//p//a/text()',  # 附件名称
    "indexnumber": '//div[@class="news-table"]//tr[1]/td[2]/text()',
    "fileno": '//div[@class="news-table"]//tr[4]/td[2]/text()',
    "category": '//div[@class="news-table"]//tr[1]/td[4]/text()',
    "issuer": '//div[@class="news-table"]//tr[2]/td[2]/text()',
    "status": '//div[@class="news-table"]//tr[4]/td[4]/text()',
    "writtendate": '//div[@class="news-table"]//tr[2]/td[4]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class MzjXiaoganGovCnGkSpider(BasePortiaSpider):
    name = "mzj_xiaogan_gov_cn_gk"
    allowed_domains = ["mzj.xiaogan.gov.cn"]
    start_urls = [
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/qtgkwj2.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/zcjd.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/gfxwj.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/xgsmzjjgbgdzjlxdh2.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/rsxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/zsdw.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/nsjg.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/jgzn.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/tqzxqykxxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/hmhnzchzjff.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/czjs.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/czys.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/gzjz.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/gzgh.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/shjz.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/tjxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/xczx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/xzxkxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/qtdwglfwsxxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/cfqzxx.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/shzz.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/ylfwetfl.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/ylfwetfl.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/etfl1.jhtml",
        "https://mzj.xiaogan.gov.cn/c/xgsmzj/qzqd1.jhtml"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.rsplit('.jhtml')[0] + f'_{page + 2}.jhtml'

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