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
    "detail_urls": '//div[@class="col ml20"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="col ml20"]//ul//span/text()',  # 发布时间
    # "next_page": '//*[@id="page"]/a[last()]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="list_info"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="mt10 mb10"]//p',  # 正文内容
    "attachment": '//div[@class="mt10 mb10"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="mt10 mb10"]//p//a/text()',  # 附件名称
    "indexnumber": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[1]/td[2]/text()',
    "fileno": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[2]/td[2]/text()',
    "category": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[1]/td[4]/text()',
    "issuer": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[2]/td[4]/text()',
    "status": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[3]/td[4]/text()',
    "writtendate": '//div[@class="xy-xxgk-txt"]/table/tbody/tr[3]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjXianyangGovCnGkSpider(BasePortiaSpider):
    name = "jyj_xianyang_gov_cn_gk"
    allowed_domains = ["jyj.xianyang.gov.cn"]
    start_urls = [
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/zcwj/wjzq/",  # 市教育局文件
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/zcwj/xzgfxwj/",  # 行政规范性文件
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/zcwj/zcfg/",  # 政策法规
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/ysjs/",  # 财政预决算
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/rsxxzkly/rsrm/",  # 人事任免
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/rsxxzkly/zkzl/",  # 招考招录
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/jyta00/rdjy/",  # 人大建议
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/jyta00/zxta/",  # 政协提案
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/fzgh/",  # 规划计划
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/jcygk/",  # 决策预公开
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/ywjyxxgk/",  # 义务教育信息公开
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/ywgk/",  # 其他重点信息公开
        "https://jyj.xianyang.gov.cn/zwgk/fdzdgknr/zcjd/",  # 政策解读
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        # 拼接index_页码.html（page+1对应实际页码）
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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'createPage\((\d+),')], type="xpath"),
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
