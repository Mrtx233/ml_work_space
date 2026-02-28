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
    "detail_urls": '//div[@class="child_Item child_Item_text"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="child_Item child_Item_text"]//ul//div[@class="newsTime"]/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="dqwz_content"]//a/text()',  # 面包屑菜单
    "source": '//div[@class="laiyuan"]/span[@class="laiyuan_value"]/text()',  # 来源
    "content": '//div[@class="xwxq_content"]//p',  # 正文内容
    "attachment": '//div[@class="xwxq_content"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="xwxq_content"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjHanzhongGovCnSpider(BasePortiaSpider):
    name = "jyj_hanzhong_gov_cn"
    allowed_domains = ["jyj.hanzhong.gov.cn"]
    start_urls = [
        "https://jyj.hanzhong.gov.cn/hzsjyjx/tpxw/secondLevelChannel.shtml",  # 教育新闻 > 图片新闻
        "https://jyj.hanzhong.gov.cn/hzsjyjx/jyyw/secondLevelChannel.shtml",  # 教育新闻 > 教育要闻
        "https://jyj.hanzhong.gov.cn/hzsjyjx/gzdt/secondLevelChannel.shtml",  # 教育新闻 > 工作动态
        "https://jyj.hanzhong.gov.cn/hzsjyjx/xykx/secondLevelChannel.shtml",  # 教育新闻 > 校园快讯
        "https://jyj.hanzhong.gov.cn/hzsjyjx/jyxx/secondLevelChannel.shtml",  # 教育新闻 > 教育信息
        "https://jyj.hanzhong.gov.cn/hzsjyjx/szyw/secondLevelChannel.shtml",  # 教育新闻 > 时政要闻
        "https://jyj.hanzhong.gov.cn/hzsjyjx/xqjy/secondLevelChannel.shtml",  # 各类教育 > 学前教育
        "https://jyj.hanzhong.gov.cn/hzsjyjx/ywjy/secondLevelChannel.shtml",  # 各类教育 > 义务教育
        "https://jyj.hanzhong.gov.cn/hzsjyjx/gzjy/secondLevelChannel.shtml",  # 各类教育 > 高中教育
        "https://jyj.hanzhong.gov.cn/hzsjyjx/zyjy/secondLevelChannel.shtml",  # 各类教育 > 职业教育
        "https://jyj.hanzhong.gov.cn/hzsjyjx/tsjy/secondLevelChannel.shtml",  # 各类教育 > 特殊教育
        "https://jyj.hanzhong.gov.cn/hzsjyjx/jydd/common_list.shtml",  # 教育督导
        "https://jyj.hanzhong.gov.cn/hzsjyjx/sdjs/secondLevelChannel.shtml",  # 党风廉政 > 师德建设
        "https://jyj.hanzhong.gov.cn/hzsjyjx/lzwh/secondLevelChannel.shtml",  # 党风廉政 > 廉政文化
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace(".shtml", f"_{page + 1}.shtml")

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'createPageHTML\(\'page_div\',(\d+),')], type="xpath"),
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