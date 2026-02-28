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
    "publish_times": '//div[@class="content_info"]//ul//a/@href',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//div[@class="page"]/a[last()]/@href'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="list_info"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="mt10 mb10"]//p',  # 正文内容
    "attachment": '//div[@class="mt10 mb10"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="mt10 mb10"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjXianyangGovCnSpider(BasePortiaSpider):
    name = "jyj_xianyang_gov_cn"
    allowed_domains = ["jyj.xianyang.gov.cn"]
    start_urls = [
        "https://jyj.xianyang.gov.cn/xwzx/szyw/",  # 新闻中心 > 要闻
        "https://jyj.xianyang.gov.cn/xwzx/tzgg/",  # 新闻中心 > 通知公告
        "https://jyj.xianyang.gov.cn/xwzx/twfd/",  # 新闻中心 > 图文翻动
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/cjqgwmcs/",  # 新闻中心 > 专题专栏 > 创建全国文明城市
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/kzljflgjmhjy/",  # 新闻中心 > 专题专栏 > 开展垃圾分类 共建美好家园
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/wlaqxc/",  # 新闻中心 > 专题专栏 > 网络安全宣传
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/fzzfjssfcj/",  # 新闻中心 > 专题专栏 > 法治政府建设示范创建
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/sqxzjcgszl/",  # 新闻中心 > 专题专栏 > 涉企行政检查公示专栏
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/qsss2025njsjrkl/grfc/",  # 新闻中心 > 专题专栏 > 2025年教师节专栏 > 个人风采
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/qsss2025njsjrkl/tdfc/",  # 新闻中心 > 专题专栏 > 2025年教师节专栏 > 团队风采
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/ywjyzs1/",  # 新闻中心 > 专题专栏 > 历史专题 > 义务教育招生
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/ptgzkszs/",  # 新闻中心 > 专题专栏 > 历史专题 > 普通高中考试招生
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/yqfkzt/",  # 新闻中心 > 专题专栏 > 历史专题 > 疫情防控专题
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/sqszpgzhwybjqzrx/",  # 新闻中心 > 专题专栏 > 历史专题 > “三全”思政培根铸魂 “五育”并举启智润心
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/sxhxjzgzzzmxyr/",  # 新闻中心 > 专题专栏 > 历史专题 > 实行核心价值观 争做最美咸阳人
        "https://jyj.xianyang.gov.cn/xwzx/ztzl/lszt/hyjyjjs/",  # 新闻中心 > 专题专栏 > 历史专题 > 弘扬教育家精神 争做时代“大先生”
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url_clean = base_url.rstrip('/')
        # 拼接index_页码.html（page+1对应实际页码）
        return f"{base_url_clean}/index_{page + 1}.html"

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
                 Field('detail_urls', LIST_XPATH["detail_urls"], [Regex(r'^\./\d{6}/t\d+_\d+\.html$')], type="xpath"),
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex(r't(\d{8})_')], type="xpath"),
                 # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'index_(\d+)\.html')], type="xpath"),
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