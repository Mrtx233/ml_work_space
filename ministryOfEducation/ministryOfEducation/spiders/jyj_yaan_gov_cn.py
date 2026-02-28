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
    "detail_urls": '//div[@class="id-list id-list-li02 data-list"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="id-list id-list-li02 data-list"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="page-nav02"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="page-text"]//p',  # 正文内容
    "attachment": '//div[@class="page-text"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="page-text"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjYaanGovCnSpider(BasePortiaSpider):
    name = "jyj_yaan_gov_cn"
    allowed_domains = ["jyj.yaan.gov.cn"]
    start_urls = [
        "https://jyj.yaan.gov.cn/xinwen/list/85eadad3-8c72-4622-80dd-e645291de8c4.html?page=1",  # 教育要闻
        "https://jyj.yaan.gov.cn/xinwen/list/b7f348bd-d9bb-4d52-8b3a-e246cbb548ce.html?page=1",  # 公示公告
        "https://jyj.yaan.gov.cn/xinwen/list/4288c853-0266-4f74-81d9-46d02d1ea11e.html?page=1",  # 县区动态
        "https://jyj.yaan.gov.cn/xinwen/list/07789398-d36c-4ff9-a9a2-d629d67df0ba.html?page=1",  # 直属单位
        "https://jyj.yaan.gov.cn/xinwen/list/4555fc06-a254-4bd4-9b69-df997aa41491.html?page=1",  # 校园信息
        "https://jyj.yaan.gov.cn/xinwen/list/c46c9e0e-7466-45e2-86f6-4e5a5755b9d7.html?page=1",  # 教育简报
        "https://jyj.yaan.gov.cn/xinwen/list/1748f4ea-06bb-441a-82a9-1a21935ab7b5.html?page=1",  # 教育文件
        "https://jyj.yaan.gov.cn/xinwen/list/11a3c30d-ce21-4d49-9c03-6d4641481760.html?page=1",  # 政策解读
        "https://jyj.yaan.gov.cn/xinwen/list/f3b3fd55-e0b3-4b1d-b208-5ae2453cf25f.html?page=1",  # 党建工作
        "https://jyj.yaan.gov.cn/xinwen/list/50dd47c0-e74d-4cf2-8e1f-6c7b7d2fd138.html?page=1",  # 校园安全
        "https://jyj.yaan.gov.cn/xinwen/list/779f43b4-5a40-41bd-b5f7-a12d80e249fb.html?page=1",  # 师资建设
        "https://jyj.yaan.gov.cn/xinwen/list/3de450a3-6975-41a7-a49c-50f6f3af4a57.html?page=1",  # 法律法规
        "https://jyj.yaan.gov.cn/xinwen/list/513e383a-df6b-4791-a278-4731469d42d0.html?page=1",  # 政策法规
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace("page=1", f"page={page}")

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'<=\s*(\d+)')], type="xpath"),
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

             ])]]