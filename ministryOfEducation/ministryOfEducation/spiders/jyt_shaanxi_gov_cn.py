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
    "detail_urls": '//div[@class=" rt w-gl-w868"]//ul//a/@href | //div[@class="w-gl-w868"]//ul//a/@href | //div[@class="con-rt pd30 rt gk-lists"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class=" rt w-gl-w868"]//ul//span | //div[@class="w-gl-w868"]//ul//span/text() | //div[@class="con-rt pd30 rt gk-lists"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="navigation"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="lfNewsDetail"]//p | //div[@class="lfNewsDetail content"]//p | //div[@class="clearfix news-detail"]//div',  # 正文内容
    "attachment": '//div[@class="lfNewsDetail"]//p//a/@href | //div[@class="lfNewsDetail content"]//p//a/@href | //div[@class="clearfix news-detail"]//div//a/@href',  # 附件链接
    "attachment_name": '//div[@class="lfNewsDetail"]//p//a/text() | //div[@class="lfNewsDetail content"]//p//a/text() | //div[@class="clearfix news-detail"]//div//a/text()' , # 附件名称
    "indexnumber": '//table[@class="cm-table-fixed zw-table"]//tr[1]/td[1]/text()',
    # "fileno": '//div[@class="content-table"]//tr[4]/td[2]/text()',
    "category": '//table[@class="cm-table-fixed zw-table"]//tr[2]/td[1]/text()',
    "issuer": '//table[@class="cm-table-fixed zw-table"]//tr[3]/td[1]/text()',
    "status": '//table[@class="cm-table-fixed zw-table"]//tr[3]/td[2]/text()',
    "writtendate": '//table[@class="cm-table-fixed zw-table"]//tr[4]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytShaanxiGovCnSpider(BasePortiaSpider):
    name = "jyt_shaanxi_gov_cn"
    allowed_domains = ["jyt.shaanxi.gov.cn"]
    start_urls = [
        "https://jyt.shaanxi.gov.cn/index/tt/",
        "https://jyt.shaanxi.gov.cn/index/szyw/",
        "https://jyt.shaanxi.gov.cn/index/dtyw/",
        "https://jyt.shaanxi.gov.cn/index/dsyw/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/shgy/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/jzzz/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/zgcy/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/jsdwjs/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xyjy/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/zylx/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xyaq/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xsd/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xcjyzx/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xszz/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/xljk/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/yzs/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/tzgz/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/jydd/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/jjjc/gzdt/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/jjjc/zcfg/",
        "https://jyt.shaanxi.gov.cn/index/ztzl/dctj/",
        "https://jyt.shaanxi.gov.cn/hd/dczj/",
        "https://jyt.shaanxi.gov.cn/gk/fdnr/ghxx/",
        "https://jyt.shaanxi.gov.cn/gk/fdnr/gsgggk/",
        "https://jyt.shaanxi.gov.cn/gk/fdnr/yjs/",
        "https://jyt.shaanxi.gov.cn/gk/fdnr/xzzf/",
        "https://jyt.shaanxi.gov.cn/gk/fdnr/tjxx/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 移除base_url末尾的/，拼接index_{page}.shtml
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

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]