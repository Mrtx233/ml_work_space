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
    "detail_urls": '//div[@class="regime-con cm-container"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="regime-con cm-container"]//ul//span/text()',  # 发布时间
    "next_page": '//div[@class="xbzy_pager clearfix"]//a[@class="next"]/@href',
    "total_page": '//div[@class="xbzy_pager clearfix"]//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="cm-location"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="xl-con"]//p',  # 正文内容
    "attachment": '//div[@class="xl-con"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="xl-con"]//p//a/text()',  # 附件名称
    "indexnumber":'//table[@class="cm-table-fixed szf_zw-table"]//tr[1]/td[1]/text()',
    "fileno":'//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[2]/text()',
    "category":'//table[@class="cm-table-fixed szf_zw-table"]//tr[1]/td[2]/text()',
    "issuer":'//table[@class="cm-table-fixed szf_zw-table"]//tr[2]/td[1]/text()',
    "status":'//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[1]/text()',
    "writtendate":'//table[@class="cm-table-fixed szf_zw-table"]//tr[2]/td[2]/text()',

}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjYlGovCnGkSpider(BasePortiaSpider):
    name = "jyj_yl_gov_cn_gk"
    allowed_domains = ["jyj.yl.gov.cn"]
    start_urls = [
        "https://jyj.yl.gov.cn/zfxxgk/fdzdgknr/zcjd/",  # 政策解读
        "https://jyj.yl.gov.cn/zfxxgk/fdzdgknr/rsxx/",  # 人事信息
        "https://jyj.yl.gov.cn/zfxxgk/fdzdgknr/cwgk/",  # 财务公开
        "https://jyj.yl.gov.cn/zfxxgk/fdzdgknr/ghjh/",  # 规划计划
        "https://jyj.yl.gov.cn/zfxxgk/fdzdgknr/tajybl/",  # 提案建议办理
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 清理base_url末尾的/，避免拼接出//index_1.html
        base_url_clean = base_url.rstrip('/')
        # 核心逻辑：page=0对应index_1.html，page=1对应index_2.html，以此类推
        return f"{base_url_clean}/index_{page + 1}.html"

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'var countPage = (\d+)')], type="xpath"),
             ])]]

    # 详情页配置：引用DETAIL_XPATH变量
    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       DETAIL_XPATH["title"],
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       DETAIL_XPATH["publish_time"],
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type='xpath'),

                 Field('menu',
                       DETAIL_XPATH["menu"],
                       [Text(), Join(separator='>')],type="xpath"),

                 Field('source',
                       DETAIL_XPATH["source"],
                       [], type='xpath', file_category='source'),

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
                       [Regex(r'href="(\.\/P\d+\.xls)"')], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [Regex(r'附件：([^>]+?\.(xls|doc|docx|pdf))')], type='xpath', file_category='attachment'),

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