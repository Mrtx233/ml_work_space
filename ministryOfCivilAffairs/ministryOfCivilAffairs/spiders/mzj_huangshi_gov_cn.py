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
    "detail_urls": '//div[@id="op1"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@id="op1"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//div[@id="title"]/h1/text()',  # 标题
    "publish_time": '//div[@id="title"]/p/text()',  # 发布时间
    "menu": '//div[@id="crumb"]//a/text()',  # 面包屑菜单
    "source": '//div[@id="title"]/p/text()',  # 来源
    "content": '//div[@class="content"]//p | //div[@id="content"]//p',  # 正文内容
    "attachment": '//div[@class="content"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="content"]//p//a/text()',  # 附件名称
    "indexnumber": '//table[@class="TonYon"]/tbody/tr[1]/td[1]/text()',
    "fileno": '//table[@class="TonYon"]/tbody/tr[5]/td[1]/text()',
    "category": '//table[@class="TonYon"]/tbody/tr[4]/td[1]/text()',
    "issuer": '//table[@class="TonYon"]/tbody/tr[2]/td[1]/text()',
    "status": '//table[@class="TonYon"]/tbody/tr[2]/td[2]/text()',
    "writtendate": '//table[@class="TonYon"]/tbody/tr[3]/td[1]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class MzjHuangshiGovCnSpider(BasePortiaSpider):
    name = "mzj_huangshi_gov_cn"
    allowed_domains = ["mzj.huangshi.gov.cn"]
    start_urls = [
        "https://mzj.huangshi.gov.cn/xw/rdgz/index.html",
        "https://mzj.huangshi.gov.cn/xw/bdmz/index.html",
        "https://mzj.huangshi.gov.cn/xw/xsqxw/index.html",
        "https://mzj.huangshi.gov.cn/zt/xjpxsdzg/index.html",
        "https://mzj.huangshi.gov.cn/zt/zybxgd/index.html",
        "https://mzj.huangshi.gov.cn/zt/djxxjyzl/index.html",
        "https://mzj.huangshi.gov.cn/zt/ylfw/index.html",
        "https://mzj.huangshi.gov.cn/zt/bzfwzl/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/xzjczt/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/xzjcsxjyj/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/xzjcpcsx/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/xzjcbz/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/zxjcjh/index.html",
        "https://mzj.huangshi.gov.cn/zt/sqxzjcgs/xzjcws/index.html",
        "https://mzj.huangshi.gov.cn/hd/wsdc/index.html",
        "https://mzj.huangshi.gov.cn/hd/zxft/index.html",
        "https://mzj.huangshi.gov.cn/hd/lxslfk/index.html",
        "https://mzj.huangshi.gov.cn/gk/zc/gkwj/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/zc/zcjd/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/zc/qtzdgkwj/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/tzgg/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/zfcg/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/czyjs/czyjs1/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/czyjs/czzxzj/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/czyjs/ykt/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/rsxx/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/gysyjs/shzz/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/gysyjs/shbz/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/ghxx/index.shtml",
        "https://mzj.huangshi.gov.cn/gk/fdzdgknr/qtzdgknr/zczxjlsqk/index.shtml"
    ]

    import re

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r'index\.(\w+)$', f'index_{page + 1}.\\1', base_url)

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'createPageHTML\((\d+),')], type="xpath"),
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

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]