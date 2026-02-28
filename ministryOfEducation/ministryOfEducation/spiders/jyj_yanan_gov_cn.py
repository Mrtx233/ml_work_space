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
    "detail_urls": '//div[@class="m-lst36"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="m-lst36"]//ul//span/text()',  # 发布时间
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
    "attachment_name": '//div[@class="m-txt-article"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjYananGovCnSpider(BasePortiaSpider):
    name = "jyj_yanan_gov_cn"
    allowed_domains = ["jyj.yanan.gov.cn"]
    start_urls = [
        "https://jyj.yanan.gov.cn/xwzx/bsjydt/1.html",  # 新闻中心 > 本市教育动态
        "https://jyj.yanan.gov.cn/xwzx/tzgg/1.html",  # 新闻中心 > 通知公告
        "https://jyj.yanan.gov.cn/xwzx/zyzz/1.html",  # 新闻中心 > 重要转载
        "https://jyj.yanan.gov.cn/jyjx/zkzx/1.html",  # 教育教学 > 招考咨讯
        "https://jyj.yanan.gov.cn/jyjx/jydd/1.html",  # 教育教学 > 教育督导
        "https://jyj.yanan.gov.cn/jyjx/jyjy/1.html",  # 教育教学 > 教育教研
        "https://jyj.yanan.gov.cn/jyjx/ktnw/1.html",  # 教育教学 > 课堂内外
        "https://jyj.yanan.gov.cn/jyjx/jxgy/1.html",  # 教育教学 > 家校共育
        "https://jyj.yanan.gov.cn/jyjx/ssfc/1.html",  # 教育教学 > 师生风采
        "https://jyj.yanan.gov.cn/jyjx/spxx/1.html",  # 教育教学 > 视频信息
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

             ])]]