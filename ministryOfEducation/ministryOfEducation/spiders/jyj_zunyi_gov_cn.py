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
    "detail_urls": '//div[@class="m-content"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="m-content"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="bt-position"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="Article_zw"]//p',  # 正文内容
    "attachment": '//div[@class="Article_zw"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="Article_zw"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjZunyiGovCnSpider(BasePortiaSpider):
    name = "jyj_zunyi_gov_cn"
    allowed_domains = ["jyj.zunyi.gov.cn"]
    start_urls = [
        "https://jyj.zunyi.gov.cn/jydt/szyw/",  # 教育动态 > 时政要闻
        "https://jyj.zunyi.gov.cn/jydt/sjdt/",  # 教育动态 > 市局动态
        "https://jyj.zunyi.gov.cn/jydt/qxdt/",  # 教育动态 > 区县动态
        "https://jyj.zunyi.gov.cn/jydt/xxdt/",  # 教育动态 > 学校动态
        "https://jyj.zunyi.gov.cn/jygk/jygk_77747/",  # 教育概况 > 教育简介
        "https://jyj.zunyi.gov.cn/jygk/gzzn/",  # 教育概况 > 工作职能
        "https://jyj.zunyi.gov.cn/jygk/jgsz/",  # 教育概况 > 机构设置
        "https://jyj.zunyi.gov.cn/zsks/zk/",  # 招生考试 > 中考
        "https://jyj.zunyi.gov.cn/zsks/ptgk/",  # 招生考试 > 普通高考
        "https://jyj.zunyi.gov.cn/zsks/crks/",  # 招生考试 > 成人考试
        "https://jyj.zunyi.gov.cn/ztzl/xszz/",  # 专题专栏 > 学生资助
        "https://jyj.zunyi.gov.cn/ztzl/jydj/",  # 专题专栏 > 教育党建
        "https://jyj.zunyi.gov.cn/ztzl/jyky/",  # 专题专栏 > 教育科研
        "https://jyj.zunyi.gov.cn/ztzl/jxgy/",  # 专题专栏 > 家校共育
        "https://jyj.zunyi.gov.cn/tzgg/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page}.shtml"

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