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
    "detail_urls": '//div[@class="list_txtsbg"]//dl//a/@href',  # 详情页链接
    "publish_times": '//div[@class="list_txtsbg"]//dl//dd/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="tl_r"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="txtcen"]//p',  # 正文内容
    "attachment": '//div[@class="txtcen"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="txtcen"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JtjKmGovCnSpider(BasePortiaSpider):
    name = "jtj_km_gov_cn"
    allowed_domains = ["jtj.km.gov.cn"]
    start_urls = [
        "https://jtj.km.gov.cn/gzdt/",  # 教育工作 > 工作动态
        "https://jtj.km.gov.cn/dflz/",  # 教育工作 > 党风廉政
        "https://jtj.km.gov.cn/jygz/jyxw/",  # 教育工作 > 教育新闻
        "https://jtj.km.gov.cn/jygz/zsks/",  # 教育工作 > 招生考试
        "https://jtj.km.gov.cn/jygz/dyxc/",  # 教育工作 > 德育工作
        "https://jtj.km.gov.cn/jygz/jyxxh/",  # 教育工作 > 教育信息化
        "https://jtj.km.gov.cn/jygz/zjdt/",  # 教育工作 > 职教动态
        "https://jtj.km.gov.cn/jygz/jygg/",  # 教育工作 > 教研公告
        "https://jtj.km.gov.cn/jygz/jyrc/",  # 教育工作 > 教育人才
        "https://jtj.km.gov.cn/jygz/kcbxjdzl/",  # 教育工作 > 控辍保学监督专栏
        "https://jtj.km.gov.cn/hdjl/hdgs/",  # 互动交流 > 互动公示
        "https://jtj.km.gov.cn/fwzn/bszn/",  # 服务指南 > 办事指南
        "https://jtj.km.gov.cn/fwzn/cjwthdzl/",  # 服务指南 > 常见问题问答专栏
        "https://jtj.km.gov.cn/sjrcyshj/",  # 四季如春营商环境
        "https://jtj.km.gov.cn/spaqzl/",  # 食品安全专栏
        "https://jtj.km.gov.cn/xszz/tzgg/",  # 学生资助 > 通知公告
        "https://jtj.km.gov.cn/xszz/zcwj/",  # 学生资助 > 政策文件
        "https://jtj.km.gov.cn/xszz/zzyr/",  # 学生资助 > 资助育人
        "https://jtj.km.gov.cn/xszz/zzzn/",  # 学生资助 > 资助指南
        "https://jtj.km.gov.cn/xszz/zlxz/",  # 学生资助 > 资料下载
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page + 1}.shtml"

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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'\?(\d+):PageIndex;')], type="xpath"),
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
                       [Regex(r'.+\.(doc|docx|xls|xlsx|pdf)$')], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [Regex(r'.+\.(doc|docx|xls|xlsx|pdf)$')], type='xpath', file_category='attachment'),

             ])]]