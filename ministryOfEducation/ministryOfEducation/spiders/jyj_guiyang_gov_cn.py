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
    "detail_urls": '//div[@class="right-cont"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="right-cont"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="breadcrumb"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="detail-cont"]//p',  # 正文内容
    "attachment": '//div[@class="detail-cont"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="detail-cont"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjGuiyangGovCnSpider(BasePortiaSpider):
    name = "jyj_guiyang_gov_cn"
    allowed_domains = ["jyj.guiyang.gov.cn"]
    start_urls = [
        "https://jyj.guiyang.gov.cn/newsite/xwzx/jyyw/",  # 新闻资讯 > 教育要闻
        "https://jyj.guiyang.gov.cn/newsite/xwzx/gzdt/",  # 新闻资讯 > 工作动态
        "https://jyj.guiyang.gov.cn/newsite/xwzx/qxdt/",  # 新闻资讯 > 区县动态
        "https://jyj.guiyang.gov.cn/newsite/xwzx/xyxw/",  # 新闻资讯 > 校园新闻
        "https://jyj.guiyang.gov.cn/newsite/xwzx/tzgg/",  # 新闻资讯 > 通知公告
        "https://jyj.guiyang.gov.cn/newsite/xwzx/tpxw/",  # 新闻资讯 > 图片新闻
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/dlhyjyjsjkjsjyqg/",# 新闻资讯 > 专题专栏 > 热点专题 > 大力弘扬教育家精神 加快建设教育强国
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/jsjf/",  # 新闻资讯 > 专题专栏 > 热点专题 > 教师减负
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/aqjy/",  # 新闻资讯 > 专题专栏 > 热点专题 > 安全教育
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/zrcqsh/",  # 新闻资讯 > 专题专栏 > 热点专题 > 筑人才 强省会
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/ljfl/",  # 新闻资讯 > 专题专栏 > 热点专题 > 垃圾分类
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/xxgcesdgyjyzxd/",  # 新闻资讯 > 专题专栏 > 热点专题 > 学习贯彻党的二十大 贵阳教育在行动
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/saxy/",  # 新闻资讯 > 专题专栏 > 热点专题 > 食安校园
        "https://jyj.guiyang.gov.cn/newsite/xwzx/zttl/rdzl/zlxsqmfz/",  # 新闻资讯 > 专题专栏 > 热点专题 > 开展“十个一”活动 助力学生全面发展
        "https://jyj.guiyang.gov.cn/newsite/gzcy/zxft/",  # 公众参与 > 在线访谈
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/jcjy/",  # 政务公开 > 重点领域信息公开 > 基础教育
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/xqjy/",  # 政务公开 > 重点领域信息公开 > 学前教育
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/zyjyycrjy/",  # 政务公开 > 重点领域信息公开 > 职业教育与成人教育
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/gdjy/",  # 政务公开 > 重点领域信息公开 > 高等教育
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/jsgz/",  # 政务公开 > 重点领域信息公开 > 教师工作
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/tyywsysjy/",  # 政务公开 > 重点领域信息公开 > 体育与卫生艺术教育
        "https://jyj.guiyang.gov.cn/newsite/zwgk/zdlyxxgk/mbjy/",  # 政务公开 > 重点领域信息公开 > 民办教育
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

             ])]]