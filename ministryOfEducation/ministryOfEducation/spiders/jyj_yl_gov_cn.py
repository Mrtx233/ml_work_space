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
    "detail_urls": '//div[@class="content_info"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="content_info"]//ul//span[@class="time"]/text()',  # 发布时间
    "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="list_info mb20"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="mt10 mb10"]//p',  # 正文内容
    "attachment": '//script/text()',  # 附件链接
    "attachment_name": '//script/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjYlGovCnSpider(BasePortiaSpider):
    name = "jyj_yl_gov_cn"
    allowed_domains = ["jyj.yl.gov.cn"]
    start_urls = [
        "https://jyj.yl.gov.cn/xwzx/jyxw/",  # 新闻中心 > 教育新闻
        "https://jyj.yl.gov.cn/xwzx/xqdt/",  # 新闻中心 > 区域动态
        "https://jyj.yl.gov.cn/xwzx/tzgg/",  # 新闻中心 > 通知公告
        "https://jyj.yl.gov.cn/xwzx/qzgz/",  # 新闻中心 > 群众关注
        "https://jyj.yl.gov.cn/xwzx/ttxw/",  # 新闻中心 > 头条新闻
        "https://jyj.yl.gov.cn/jgsz/jgzz/",  # 机构设置 > 机构职责
        "https://jyj.yl.gov.cn/jgsz/jygk/",  # 机构设置 > 教育概况
        "https://jyj.yl.gov.cn/jgsz/ldzc/",  # 机构设置 > 领导之窗
        "https://jyj.yl.gov.cn/jgsz/nsks/",  # 机构设置 > 内设科室
        "https://jyj.yl.gov.cn/jgsz/jsdw/",  # 机构设置 > 局属单位
        "https://jyj.yl.gov.cn/zmhd/dczj/",  # 政民互动 > 调查征集
        "https://jyj.yl.gov.cn/ztzl/spaq/",  # 专题专栏 > 食品安全
        "https://jyj.yl.gov.cn/ztzl/scggl/",  # 专题专栏 > 双常规管理
        "https://jyj.yl.gov.cn/ztzl/jszp/",  # 专题专栏 > 教师招聘
        "https://jyj.yl.gov.cn/ztzl/zszc/xxqk/",  # 专题专栏 > 义务教育 > 学校情况
        "https://jyj.yl.gov.cn/ztzl/zszc/zszc/",  # 专题专栏 > 义务教育 > 招生政策
        "https://jyj.yl.gov.cn/ztzl/zszc/zzjl/",  # 专题专栏 > 义务教育 > 资助奖励
        "https://jyj.yl.gov.cn/ztzl/zszc/lqjggs/",  # 专题专栏 > 义务教育 > 录取结果公示
        "https://jyj.yl.gov.cn/ztzl/xyaq/",  # 专题专栏 > 校园安全
        "https://jyj.yl.gov.cn/ztzl/sjgz/",  # 专题专栏 > 双减工作
        "https://jyj.yl.gov.cn/ztzl/xqjyxcy/",  # 专题专栏 > 学前教育宣传月
        "https://jyj.yl.gov.cn/ztzl/kszs/",  # 专题专栏 > 考试招生
        "https://jyj.yl.gov.cn/ztzl/sqxzjcgszl/",  # 专题专栏 > 涉企行政检查公示专栏
        "https://jyj.yl.gov.cn/ztzl/jszgz/jszgzbfhf/",  # 专题专栏 > 教师资格证 > 教师资格证补发换发
        "https://jyj.yl.gov.cn/ztzl/jszgz/jszgzsxxbg/",  # 专题专栏 > 教师资格证 > 教师资格证书信息变更
        "https://jyj.yl.gov.cn/ztzl/jszgz/jszgrdsqbbb/",  # 专题专栏 > 教师资格证 > 教师资格认定申请表补办
        "https://jyj.yl.gov.cn/ztzl/jszgz/jszgrd/",  # 专题专栏 > 教师资格证 > 教师资格认定
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     # 移除base_url末尾的/，拼接index_{page}.shtml
    #     base_url_clean = base_url.rstrip('/')  # 清理末尾的/，避免出现//index_1.shtml
    #     return f"{base_url_clean}/index_{page + 2}.shtml"

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
                       [Regex(r'href="(\.\/P\d+\.xls)"')], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [Regex(r'附件：([^>]+?\.(xls|doc|docx|pdf))')], type='xpath', file_category='attachment'),

             ])]]