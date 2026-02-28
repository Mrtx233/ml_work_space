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
    "detail_urls": '//div[@class="PageMainBox aBox"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="PageMainBox aBox"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="Address aBox w1400 auto"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="Box"]//p',  # 正文内容
    "attachment": '//div[@class="Box"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="Box"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytGuizhouGovCnSpider(BasePortiaSpider):
    name = "jyt_guizhou_gov_cn"
    allowed_domains = ["jyt.guizhou.gov.cn"]
    start_urls = [
        "https://jyt.guizhou.gov.cn/ywdt/szyw/",  # 要闻动态 > 时政要闻
        "https://jyt.guizhou.gov.cn/ywdt/gzdt/",  # 要闻动态 > 工作动态
        "https://jyt.guizhou.gov.cn/ywdt/zxlb/",  # 要闻动态 > 战线联播
        "https://jyt.guizhou.gov.cn/zwgk/tzgg/",  # 政务公开 > 通知公告
        "https://jyt.guizhou.gov.cn/zwgk/zcjd/",  # 政务公开 > 政策解读
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/qzqd/",  # 政务公开 > 重点领域信息公开 > 权责清单
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/czzj/cwxx/",  # 政务公开 > 重点领域信息公开 > 财政资金 > 财务信息
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/xqjy/",  # 政务公开 > 重点领域信息公开 > 学前教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/jcjy/",  # 政务公开 > 重点领域信息公开 > 基础教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/gdjy/",  # 政务公开 > 重点领域信息公开 > 高等教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/zyjy/",  # 政务公开 > 重点领域信息公开 > 职业教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/mbjy/",  # 政务公开 > 重点领域信息公开 > 民办教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/mzjy/",  # 政务公开 > 重点领域信息公开 > 民族教育
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/jsgz/",  # 政务公开 > 重点领域信息公开 > 教师工作
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/kxyj/",  # 政务公开 > 重点领域信息公开 > 科学研究
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/yywzgz/",  # 政务公开 > 重点领域信息公开 > 语言文字工作
        "https://jyt.guizhou.gov.cn/zwgk/zdlyxxgk/tywsyysjy/",  # 政务公开 > 重点领域信息公开 > 体育卫生与艺术教育
        "https://jyt.guizhou.gov.cn/zwgk/jytabl/rddbjy/",  # 政务公开 > 建议提案办理 > 人大代表建议
        "https://jyt.guizhou.gov.cn/zwgk/jytabl/zxwyta/",  # 政务公开 > 建议提案办理 > 政协委员提案
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page}.html"

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