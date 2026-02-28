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
    "detail_urls": '//div[@class="NewsList"]//ul//a/@href | //div[@class="zfxxgk_zdgkc"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="NewsList"]//ul//span/text() | //div[@class="zfxxgk_zdgkc"]//ul//b/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="path"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="Article_zw"]//p',  # 正文内容
    "attachment": '//div[@class="Article_zw"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="Article_zw"]//p//a/text()' , # 附件名称

    "indexnumber": '//div[@class="Article_xx"]//tr[1]/td[2]/text()',
    "fileno": '//div[@class="Article_xx"]//tr[4]/td[2]/text()',
    # "category": '//table[@class="cm-table-fixed szf_zw-table"]//tr[1]/td[2]/text()',
    "issuer": '//div[@class="Article_xx"]//tr[2]/td[2]/text()',
    "status": '//div[@class="Article_xx"]//tr[1]/td[4]/text()',
    "writtendate": '//div[@class="Article_xx"]//tr[2]/td[4]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjAnshunGovCnSpider(BasePortiaSpider):
    name = "jyj_anshun_gov_cn"
    allowed_domains = ["jyj.anshun.gov.cn"]
    start_urls = [
        "https://jyj.anshun.gov.cn/gzdt/bmdt/",  # 工作动态 > 部门动态
        "https://jyj.anshun.gov.cn/gzdt/tzgg/",  # 工作动态 > 通知公告

        "https://jyj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/jcjy/",  # 基础教育
        "https://jyj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/xqjy/",  # 学前教育
        "https://jyj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/zyjy/",  # 职业教育与成人教育
        "https://jyj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/mbmzjy/",  # 民办民族教育
        "https://jyj.anshun.gov.cn/zwgk/zfxxgk/xxgkml/jsgz/",  # 教师工作
        #
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/ggzs/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 综述
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/dsj/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 大事记
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/assfc/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 安顺市风采
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/ryhc/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 荣誉荟萃
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/tssj/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 探索实践
        "https://jyj.anshun.gov.cn/ztzl/dlsnjdwl/wmyxqjyzsn/",  # 专题专栏 > 安顺市学前教育发展十年巡礼 砥砺十年 奠基未来 > 我们与学前教育

        "https://jyj.anshun.gov.cn/ztzl/dsxxjy/",  # 专题专栏 > 党史学习教育
        "https://jyj.anshun.gov.cn/ztzl/sjjwzqh/",  # 专题专栏 > 十九届五中全会
        "https://jyj.anshun.gov.cn/ztzl/2021nqglh/",  # 专题专栏 > 2021年全国两会
        "https://jyj.anshun.gov.cn/ztzl/shzyhxjzg/",  # 专题专栏 > 社会主义核心价值观
        "https://jyj.anshun.gov.cn/ztzl/sjjszqh/",  # 专题专栏 > 十九届四中全会
        "https://jyj.anshun.gov.cn/ztzl/xxsjdjs/",  # 专题专栏 > 学习贯彻党的十九大精神
        "https://jyj.anshun.gov.cn/ztzl/bwcxljsm/",  # 专题专栏 > “不忘初心、牢记使命”主题教育
        "https://jyj.anshun.gov.cn/ztzl/qsjydh/",  # 专题专栏 > 教育大会
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
                       [Regex(r'.+\.(doc|docx|xls|xlsx|pdf)$')], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [Regex(r'.+\.(doc|docx|xls|xlsx|pdf)$')], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 Field('fileno',
                       DETAIL_XPATH["fileno"],
                       [], required=False, type='xpath'),

                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),

                 Field('status',
                       DETAIL_XPATH["status"],
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]