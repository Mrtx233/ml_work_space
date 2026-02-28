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
    "detail_urls": '//div[@class="navjz"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="navjz"]//ul/li/span/text()',  # 发布时间
    # "next_page": '//div[@class="pagesx clearfix"]/a[3]/@tagname',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="wz_position"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="wzcon j-fontContent"]//p',  # 正文内容
    "attachment": '//div[@class="wzcon j-fontContent"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="wzcon j-fontContent"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JiaotijuAhszGovCnSpider(BasePortiaSpider):
    name = "jiaotiju_ahsz_gov_cn"
    allowed_domains = ["jiaotiju.ahsz.gov.cn"]
    start_urls = [
        "https://jiaotiju.ahsz.gov.cn/content/column/13591458?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591462?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591468?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591488?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591495?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/167461221?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/xwzx/tyss/index.html",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591503?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591512?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13808828?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13808848?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13808866?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809224?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809230?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809246?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/167450121?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591536?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809432?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809449?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809456?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809469?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13809486?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/21118692?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/21118723?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/21118752?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/167465571?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591574?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591580?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/ztzl/zdzyjyzlndbg/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/gdzt/cjspypaqcs/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/zxxsqlfzgz/index.html",
        "https://jiaotiju.ahsz.gov.cn/content/column/167459991?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/13591567?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/ztzl/xxxcgcddesdjs/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/qqyyglwzbdyjxdzl/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/djxxjy/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/xxgcxjpxsdzgtsshzysxztjy/index.html",
        "https://jiaotiju.ahsz.gov.cn/content/column/16994754?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/ztzl/zfwzgznb/index.html",
        "https://jiaotiju.ahsz.gov.cn/content/column/167449711?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/167465561?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/content/column/167481931?pageIndex=1",
        "https://jiaotiju.ahsz.gov.cn/ztzl/xxxcgcxjpzsjkcahzyjhjszl/index.html",
        "https://jiaotiju.ahsz.gov.cn/ztzl/xxxcddesjszqhjszl/index.html"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r'pageIndex=\d+', f'pageIndex={page + 1}', base_url)

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'pageCount:(\d+)')], type="xpath"),
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