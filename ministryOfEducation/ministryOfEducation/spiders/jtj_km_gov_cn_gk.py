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
    "detail_urls": '//p[@class="w659"]/a/@href',  # 详情页链接
    "publish_times": '//p[@class="w80"]/a/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    # "menu": '//div[@class="dqwz_content"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="activity"]//p',  # 正文内容
    "attachment": '//div[@class="activity"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="activity"]//p//a/text()',  # 附件名称
    "indexnumber": '//div[@class="content-table"]//tr[1]/td[2]/text()',
    "fileno": '//div[@class="content-table"]//tr[4]/td[2]/text()',
    "category": '//div[@class="content-table"]//tr[1]/td[4]/text()',
    "issuer": '//div[@class="content-table"]//tr[2]/td[2]/text()',
    # "status": '//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[1]/text()',
    "writtendate": '//div[@class="content-table"]//tr[2]/td[4]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JtjKmGovCnGkSpider(BasePortiaSpider):
    name = "jtj_km_gov_cn_gk"
    allowed_domains = ["jtj.km.gov.cn"]
    start_urls = [
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/jgzn/",  # 组织机构
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/gsgg/",  # 公示公告
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zcjd/",  # 政策解读
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zfwzgzndbb/",  # 政府网站工作年度报表
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/ghjh/",  # 规划计划
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/xzzfgs/yjxx/",  # 依据信息
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/xzzfgs/jgxx/xzxk/",  # 行政许可
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/xzzfgs/zfxx/",  # 执法信息
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdgzxx/",  # 重点工作信息
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/xwfb/",  # 新闻发布
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/czyjs/",  # 财政预决算
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/sjczyjs/sgjf/",  # “三公”经费
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/rdhy/",  # 热点回应
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcgjgmfw/",  # 政府采购及购买服务
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zdjcgk/",  # 重大决策公开
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/shgysyzfxx/",  # 社会公益事业政府信息
        "https://jtj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/tjzdjsxmpzhsslyzfxx/",  # 推进重大建设项目批准和实施领域政府信息
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page + 1}.shtml"

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
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex(r'(\d{4}\.\d{2}\.\d{2})')], type="xpath"),
                 # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'\?(\d+):PageIndex;')], type="xpath"),
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

                 # Field('menu',
                 #       DETAIL_XPATH["menu"],
                 #       [Text(), Join(separator='>')],type="xpath"),

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

                 Field('fileno',
                       DETAIL_XPATH["fileno"],
                       [], required=False, type='xpath'),

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

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