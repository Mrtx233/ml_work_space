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
    "detail_urls": '//div[contains(@class, "m-lst") and not(contains(@class, "m-lst-pg")) and not(contains(@class, "m-lst-nav"))]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[contains(@class, "m-lst")]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="position"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="m-txt-article"]//p',  # 正文内容
    "attachment": '//div[@class="m-txt-article"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="m-txt-article"]//p//a/text()',  # 附件名称
    "indexnumber": '//div[@class="table"]/div[1]/div[2]/text()',
    # "fileno": '//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[2]/text()',
    # "category": '//table[@class="cm-table-fixed szf_zw-table"]//tr[1]/td[2]/text()',
    "issuer": '//*[@id="printContent"]/div[3]/div[3]/div/div[2]/text()',
    # "status": '//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[1]/text()',
    "writtendate": '//div[@class="table"]/div[1]/div[4]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjYananGovCnGkSpider(BasePortiaSpider):
    name = "jyj_yanan_gov_cn_gk"
    allowed_domains = ["jyj.yanan.gov.cn"]
    start_urls = [
        "https://jyj.yanan.gov.cn/zfxxgk/zfxxgkzd/1.html",  # 政府信息公开制度
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/jggk/jgzn/1.html",  # 机构职能
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/jggk/nsks/1.html",  # 内设科室
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/jggk/zsdw/1.html",  # 直属单位
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/hygk/1.html",  # 会议公开
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/ghjh/1.html",  # 规划计划
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/rsxx/1.html",  # 人事信息
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/jyta/1.html",  # 建议提案
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/zcjd/1.html",  # 政策解读
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/shgy/1.html",  # 社会公益
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/zdly/msly/1.html",  # 民生领域
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/zdly/czxx/czyjs/1.html",  # 财政预决算
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/zdly/czxx/sgjf/1.html",  # 三公经费
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/dsxx/1.html",  # 党史学习
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/xzzf/1.html",  # 行政执法
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/jdqd/1.html",  # 监督渠道
        "https://jyj.yanan.gov.cn/zfxxgk/fdzdgknr/ssjccgs/1.html",  # 双随机抽查公示
        "https://jyj.yanan.gov.cn/zfxxgk/zfxxgknb/1.html",  # 政府信息公开年报
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r'(\d+)\.html$', f'{page + 1}.html', base_url)

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'parseInt\(\'(\d+)\'\)')], type="xpath"),
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
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),

                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),

                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]