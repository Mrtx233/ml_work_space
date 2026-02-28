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
    "detail_urls": '//div[@class="mid-mj-list"]//ul//span/a/@href',  # 详情页链接
    "publish_times": '//div[@class="mid-mj-list"]//ul/li/span[2]/text()',  # 发布时间
    "next_page": '//div[@class="mid-mj-page"]//a[@class="next"]/@href',
    "total_page": '//span[@class="page-tip"]/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="mid-path"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@id="Content"]//p',  # 正文内容
    "attachment": '//div[@id="Content"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@id="Content"]//p//a/text()',  # 附件名称
    "indexnumber": '//ul[@class="info"]/li[1]/text()',
    "fileno": '//ul[@class="info"]/li[8]/text()',
    # "category": '//div[@class="content-table"]//tr[1]/td[4]/text()',
    "issuer": '//ul[@class="info"]/li[2]/text()',
    "status": '//ul[@class="info"]/li[9]/text()',
    "writtendate": '//ul[@class="info"]/li[6]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjZhangzhouGovCnSpider(BasePortiaSpider):
    name = "jyj_zhangzhou_gov_cn"
    allowed_domains = ["jyj.zhangzhou.gov.cn"]
    start_urls = [
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/gzdt/index.html",  # 工作动态
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/tzgg/index.html",  # 通知公告
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/rsxx/index.html",  # 人事信息
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/bbmwj/index.html",  # 部门文件
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/sjwj/index.html",  # 上级文件
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/flfg/index.html",  # 法律法规
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/tjxx/index.html",  # 统计信息
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/bbmczysbg/index.html",  # 部门财政预算报告
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/bbmczjsbg/index.html",  # 部门财政决算报告
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/bbmssdwczysbg/index.html",  # 部门所属单位财政预算报告
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/bbmssdwczjsbg/index.html",  # 部门所属单位财政决算报告
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/zcqfzgh/index.html",  # 中长期发展规划
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/ndjh/index.html",  # 年度计划
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/gzjzqk/index.html",  # 固定资产情况
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xzsyxsf/index.html",  # 行政许可事项服务
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/rddbjyblfw/index.html",  # 人大代表建议办理服务
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/zxwytablfw/index.html",  # 政协委员提案办理服务
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/qzqd/index.html",  # 权责清单
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/ssjjc/index.html",  # 设施设备采购
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xzxkhqtglfwsx/index.html",  # 行政许可和其他管理服务事项
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xzcfhqz/index.html",  # 行政处罚和强制
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xmjs/index.html",  # 项目建设
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/jyzc/index.html",  # 教育政策
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/jszl/index.html",  # 教师资源
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/zsgl/index.html",  # 招生管理
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xqjy/index.html",  # 学前教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xxjy/index.html",  # 小学教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/zxjy/index.html",  # 中学教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/zyjy/index.html",  # 职业教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/tsjy/index.html",  # 特殊教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/mbjy/index.html",  # 民办教育
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/jyjz/index.html",  # 教育资助
        "http://jyj.zhangzhou.gov.cn/cms/html/zzsjyj/xxml/index.html",  # 学校名录
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     return base_url.replace("page=1", f"page={page + 1}")

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url})
            # cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    # 列表页配置：引用LIST_XPATH变量
    list_items = [[
        Item(ListItems,
             None,
             'body',
             [
                 Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type="xpath"),
                 Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'(\d+)')], type="xpath"),
             ])]]

    # 详情页配置：引用DETAIL_XPATH变量
    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       DETAIL_XPATH["title"],
                       [], required=False, type='xpath'),

                 Field('publish_time',
                       DETAIL_XPATH["publish_time"],
                       [Regex('\\d{4}—\\d{1,2}—\\d{1,2}')], type='xpath'),

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