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
    "detail_urls": '//div[@class="mid-mj-list"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="mid-mj-list"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//span[@class="page-tip"]/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="position fs-16"]//a/text()',  # 面包屑菜单
    "content": '//div[@id="Content"]//p',  # 正文内容
    "attachment": '//div[@id="Content"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@id="Content"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjNpGovCnSpider(BasePortiaSpider):
    name = "jyj_np_gov_cn"
    allowed_domains = ["jyj.np.gov.cn"]
    start_urls = [
        "https://jyj.np.gov.cn/cms/html/jyj/jxjy-pjyj/index.html",  # 继续教育 > 培训研修
        "https://jyj.np.gov.cn/cms/html/jyj/sy-mbjy/index.html",  # 事业发展 > 民办教育
        "https://jyj.np.gov.cn/cms/html/jyj/zkxx1/index.html",  # 招考信息
        "https://jyj.np.gov.cn/cms/html/jyj/zzzc/index.html",  # 政策咨询
        "https://jyj.np.gov.cn/cms/html/jyj/jydd1/index.html",  # 教育督导
        "https://jyj.np.gov.cn/cms/html/jyj/szyw/index.html",  # 时政要闻
        "https://jyj.np.gov.cn/cms/html/jyj/zwggl/index.html",  # 政务公开栏
        "https://jyj.np.gov.cn/cms/html/jyj/zcwj1/index.html",  # 政策文件
        "https://jyj.np.gov.cn/cms/html/jyj/zcfg2/index.html",  # 政策法规
        "https://jyj.np.gov.cn/cms/html/jyj/gsl2/index.html",  # 公示栏
        "https://jyj.np.gov.cn/cms/html/jyj/jyjjjc/index.html",  # 教育经费监管
        "https://jyj.np.gov.cn/cms/html/jyj/rsxx1/index.html",  # 人事信息
        "https://jyj.np.gov.cn/cms/html/jyj/jysf/index.html",  # 教育收费
        "https://jyj.np.gov.cn/cms/html/jyj/ndjh1/index.html",  # 年度计划
        "https://jyj.np.gov.cn/cms/html/jyj/bgxz/index.html",  # 表格下载
        "https://jyj.np.gov.cn/cms/html/jyj/jyxc/index.html",  # 教育宣传
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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'共(\d+)页')], type="xpath"),
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