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
    "menu": '//div[@class="position fs-16"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@id="Zoom"]//p',  # 正文内容
    "attachment": '//a[@id="xzdllj"]//@href | //div[@id="Zoom"]//p//a/@href',  # 附件链接
    "attachment_name": '//a[@id="xzdllj"]//text() | //div[@id="Zoom"]//p//a/text()',  # 附件名称
    # "indexnumber": '//div[@class="content-table"]//tr[1]/td[2]/text()',
    # "fileno": '//div[@class="scroll_main"]//tr[1]/td[2]/text()',
    # "category": '//div[@class="content-table"]//tr[1]/td[4]/text()',
    # "issuer": '//div[@class="scroll_main"]//tr[1]/td[4]/text()',
    # "status": '//div[@class="scroll_main"]//tr[3]/td[2]/text()',
    # "writtendate": '//div[@class="scroll_main"]//tr[2]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytyjPanzhihuaGovCnGkSpider(BasePortiaSpider):
    name = "jytyj_panzhihua_gov_cn_gk"
    allowed_domains = ["jytyj.panzhihua.gov.cn"]
    start_urls = [
        "http://jytyj.panzhihua.gov.cn/zfxxgk/zfxxgkzd/index.shtml",  # 政务公开 > 政府信息公开制度
        "http://jytyj.panzhihua.gov.cn/zfxxgk/zfxxgknb/index.shtml",  # 政务公开 > 政府信息公开年报
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/zcfg/zcjd/index.shtml",  # 政务公开 > 法定主动公开内容 > 政策法规 > 政策解读
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/zcfg/flfg/index.shtml",  # 政务公开 > 法定主动公开内容 > 政策法规 > 法律法规
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/ghjh/index.shtml",  # 政务公开 > 法定主动公开内容 > 规划计划
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/tjsj/index.shtml",  # 政务公开 > 法定主动公开内容 > 统计数据
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/ysjs/index.shtml",  # 政务公开 > 法定主动公开内容 > 预决算
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/rsxx/index.shtml",  # 政务公开 > 法定主动公开内容 > 人事信息
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/qzqd/index.shtml",  # 政务公开 > 法定主动公开内容 > 权责清单
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/sgszl/index.shtml",  # 政务公开 > 法定主动公开内容 > 三公经费
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyta/rddbjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 建议提案 > 人大代表建议
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyta/zxta/index.shtml",  # 政务公开 > 法定主动公开内容 > 建议提案 > 政协提案
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/shxytxjs/xzxk/index.shtml",# 政务公开 > 法定主动公开内容 > 社会组织及相关机构 > 行政许可
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/shxytxjs/xzcf/index.shtml",# 政务公开 > 法定主动公开内容 > 社会组织及相关机构 > 行政处罚
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/shxytxjs/sgsml/index.shtml",# 政务公开 > 法定主动公开内容 > 社会组织及相关机构 > 社会组织名录
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/shxytxjs/xygzdt/index.shtml",# 政务公开 > 法定主动公开内容 > 社会组织及相关机构 > 校园工作动态
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/shxytxjs/xyzd/index.shtml",# 政务公开 > 法定主动公开内容 > 社会组织及相关机构 > 校园制度
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/wgktj/jcgk/index.shtml",  # 政务公开 > 法定主动公开内容 > 五公开 > 决策公开
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/wgktj/zxgk/index.shtml",  # 政务公开 > 法定主动公开内容 > 五公开 > 执行公开
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/wgktj/glgk/index.shtml",  # 政务公开 > 法定主动公开内容 > 五公开 > 管理公开
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/wgktj/fwgk/index.shtml",  # 政务公开 > 法定主动公开内容 > 五公开 > 服务公开
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/wgktj/jggk/index.shtml",  # 政务公开 > 法定主动公开内容 > 五公开 > 结果公开
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/zdxmjs/index.shtml",  # 政务公开 > 法定主动公开内容 > 重点项目建设
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/msgc/index.shtml",  # 政务公开 > 法定主动公开内容 > 民生工程
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/xzzf/index.shtml",  # 政务公开 > 法定主动公开内容 > 乡村振兴
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/tsjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 特殊教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/jxjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 继续教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/xqjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 学前教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/ywjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 义务教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/gzjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 高中教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/zyjy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 职业教育
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/zk/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 中考
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/gk/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 高考
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/jyjzyzz/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 教育机构执业许可
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/wlrkjd/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 外来务工子女就读
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/xxbzhyxxh/index.shtml",# 政务公开 > 法定主动公开内容 > 教育服务 > 学校标准化建设
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/jyfw/tysy/index.shtml",  # 政务公开 > 法定主动公开内容 > 教育服务 > 体育赛事
        "http://jytyj.panzhihua.gov.cn/zfxxgk/fdzdgknr_1/ddpg/dddt/index.shtml",  # 政务公开 > 法定主动公开内容 > 督导评估 > 督导动态
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
                       [], required=False, type='xpath'),

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

                 # Field('indexnumber',
                 #       DETAIL_XPATH["indexnumber"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       DETAIL_XPATH["issuer"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       DETAIL_XPATH["status"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       DETAIL_XPATH["writtendate"],
                 #       [], required=False, type='xpath'),

             ])]]