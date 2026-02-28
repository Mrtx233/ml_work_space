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
    "detail_urls": '//div[@class="navjz listnews"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="navjz listnews"]//ul/li/span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="position_list wzpos"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="j-fontContent newscontnet minh500"]//p',  # 正文内容
    "attachment": '//div[@class="j-fontContent newscontnet minh500"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="j-fontContent newscontnet minh500"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjCnbzGovCnSpider(BasePortiaSpider):
    name = "jyj_cnbz_gov_cn"
    allowed_domains = ["jyj.cnbz.gov.cn"]
    start_urls = [
        "https://jyj.cnbz.gov.cn/content/column/6790741?pageIndex=1",  # 信息公开 > 政务动态 > 时政要闻
        "https://jyj.cnbz.gov.cn/content/column/6790751?pageIndex=1",  # 信息公开 > 政务动态 > 公示公告
        "https://jyj.cnbz.gov.cn/content/column/6790781?pageIndex=1",  # 信息公开 > 政务动态 > 教育要闻
        "https://jyj.cnbz.gov.cn/content/column/6790791?pageIndex=1",  # 信息公开 > 政务动态 > 区县动态
        "https://jyj.cnbz.gov.cn/content/column/6790801?pageIndex=1",  # 信息公开 > 政务动态 > 学校动态
        "https://jyj.cnbz.gov.cn/content/column/6816771?pageIndex=1",  # 信息公开 > 政务动态 > 热点关注
        "https://jyj.cnbz.gov.cn/content/column/6790851?pageIndex=1",  # 专题专栏 > 廉政建设
        "https://jyj.cnbz.gov.cn/content/column/6790871?pageIndex=1",  # 专题专栏 > 全面改薄
        "https://jyj.cnbz.gov.cn/content/column/6790891?pageIndex=1",  # 专题专栏 > 依法治市
        "https://jyj.cnbz.gov.cn/content/column/6808071?pageIndex=1",  # 专题专栏 > 创建标准
        "https://jyj.cnbz.gov.cn/content/column/6808081?pageIndex=1",  # 专题专栏 > 工作动态
        "https://jyj.cnbz.gov.cn/content/column/6790921?pageIndex=1",  # 专题专栏 > 教师队伍建设
        "https://jyj.cnbz.gov.cn/content/column/6790931?pageIndex=1",  # 专题专栏 > 职业教育
        "https://jyj.cnbz.gov.cn/content/column/6790941?pageIndex=1",  # 专题专栏 > 双公示
        "https://jyj.cnbz.gov.cn/content/column/6808101?pageIndex=1",  # 专题专栏 > 双随机一公开 > 结果公开
        "https://jyj.cnbz.gov.cn/content/column/6808111?pageIndex=1",  # 专题专栏 > 双随机一公开 > 推进情况
        "https://jyj.cnbz.gov.cn/content/column/6808161?pageIndex=1",  # 专题专栏 > 五公开 > 决策公开
        "https://jyj.cnbz.gov.cn/content/column/6808171?pageIndex=1",  # 专题专栏 > 五公开 > 执行公开
        "https://jyj.cnbz.gov.cn/content/column/6808131?pageIndex=1",  # 专题专栏 > 五公开 > 管理公开
        "https://jyj.cnbz.gov.cn/content/column/6808141?pageIndex=1",  # 专题专栏 > 五公开 > 服务公开
        "https://jyj.cnbz.gov.cn/content/column/6808151?pageIndex=1",  # 专题专栏 > 五公开 > 结果公开
        "https://jyj.cnbz.gov.cn/content/column/6817091?pageIndex=1",  # 专题专栏 > 未命名栏目（column_6817091）
        "https://jyj.cnbz.gov.cn/content/column/6823001?pageIndex=1",  # 专题专栏 > 未命名栏目（column_6823001）
        "https://jyj.cnbz.gov.cn/content/column/6824121?pageIndex=1",  # 专题专栏 > 未命名栏目（column_6824121）
        "https://jyj.cnbz.gov.cn/content/column/6825761?pageIndex=1",  # 专题专栏 > 学前教育宣传展 > 幼教动态
        "https://jyj.cnbz.gov.cn/content/column/6817101?pageIndex=1",  # 教育资源
        "https://jyj.cnbz.gov.cn/content/column/6792681?pageIndex=1",  # 未命名栏目（column_6792681）
        "https://jyj.cnbz.gov.cn/content/column/6792621?pageIndex=1",  # 未命名栏目（column_6792621）
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace("pageIndex=1", f"pageIndex={page}")

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'pageCount:(\d+),')], type="xpath"),
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