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
    "detail_urls": '//div[@class="new-box"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="new-box"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="position fs-16"]//a/text()',  # 面包屑菜单
    "content": '//div[@id="Zoom"]//p',  # 正文内容
    "attachment": '//div[@id="Zoom"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@id="Zoom"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytyjPanzhihuaGovCnSpider(BasePortiaSpider):
    name = "jytyj_panzhihua_gov_cn"
    allowed_domains = ["jytyj.panzhihua.gov.cn"]
    start_urls = [
        "http://jytyj.panzhihua.gov.cn/zfxxgk/gzdt/jtxw/index.shtml",  # 政务公开 > 工作动态 > 教体新闻
        "http://jytyj.panzhihua.gov.cn/zfxxgk/gzdt/zsdt/index.shtml",  # 政务公开 > 工作动态 > 招生动态
        "http://jytyj.panzhihua.gov.cn/zfxxgk/gzdt/qxdt/index.shtml",  # 政务公开 > 工作动态 > 区县动态
        "http://jytyj.panzhihua.gov.cn/zfxxgk/gzdt/dldt/index.shtml",  # 政务公开 > 工作动态 > 督导动态
        "http://jytyj.panzhihua.gov.cn/zfxxgk/tzgg/index.shtml",  # 政务公开 > 通知公告
        "http://jytyj.panzhihua.gov.cn/zfxxgk/ldhd/index.shtml",  # 政务公开 > 领导活动
        "http://jytyj.panzhihua.gov.cn/ztzl/dsx/index.shtml",  # 专题专栏 > 党史学习
        "http://jytyj.panzhihua.gov.cn/ztzl/lxyzzt/index.shtml",  # 专题专栏 > 两学一做专题
        "http://jytyj.panzhihua.gov.cn/ztzl/xzzfxxgszl/xzzfztjxzzfryxx/index.shtml",
        "http://jytyj.panzhihua.gov.cn/ztzl/xzzfxxgszl/xzzfygxx/index.shtml",  # 专题专栏 > 乡村振兴信息公开专栏 > 乡村振兴有关信息
        "http://jytyj.panzhihua.gov.cn/ztzl/jtsj/index.shtml",  # 专题专栏 > 教体数据
        "http://jytyj.panzhihua.gov.cn/ztzl/djgz/index.shtml",  # 专题专栏 > 党建工作
        "http://jytyj.panzhihua.gov.cn/ztzl/dygz/index.shtml",  # 专题专栏 > 德育工作
        "http://jytyj.panzhihua.gov.cn/ztzl/xqjyxc/index.shtml",  # 专题专栏 > 学前教育宣传
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace("index.shtml", f"index_{page + 1}.shtml")

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'parseInt\((\d+)\)')], type="xpath"),
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