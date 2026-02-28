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
    "detail_urls": '//div[@class="information-l-content"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="information-l-content"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "menu": '//div[@class="content content-o"]//a/text()',  # 面包屑菜单
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "content": '//div[@class="zwxl-article"]//p',  # 正文内容
    "attachment": '//div[@class="zwxl-article"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="zwxl-article"]//p//a/text()',  # 附件名称
    "indexnumber": '//table[@class="zwxl-table"]//tr[1]/td[2]/text()',
    "fileno": '//table[@class="zwxl-table"]//tr[1]/td[4]/text()',
    "category": '//table[@class="zwxl-table"]//tr[2]/td[2]/text()',
    "issuer": '//table[@class="zwxl-table"]//tr[3]/td[2]/text()',
    # "status": '//div[@class="scroll_main"]//tr[3]/td[2]/text()',
    "writtendate": '//table[@class="zwxl-table"]//tr[4]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JwCqGovCnSpider(BasePortiaSpider):
    name = "jw_cq_gov_cn"
    allowed_domains = ["jw.cq.gov.cn"]
    start_urls = [
        "https://jw.cq.gov.cn/zwxx_209/bmdt/zhxx/",  # 政务信息 > 部门动态 > 综合信息
        "https://jw.cq.gov.cn/zwxx_209/bmdt/qxxx/",  # 政务信息 > 部门动态 > 区县信息
        "https://jw.cq.gov.cn/zwxx_209/bmdt/gxxx/",  # 政务信息 > 部门动态 > 高校信息
        "https://jw.cq.gov.cn/zwxx_209/bmdt/zsdwxx/",  # 政务信息 > 部门动态 > 直属单位信息
        "https://jw.cq.gov.cn/zwxx_209/bmdt/mtxx/spxw/",  # 政务信息 > 部门动态 > 媒体信息 > 视频新闻
        "https://jw.cq.gov.cn/jygz/yywzgz/zxtz/",  # 教育工作 > 语言文字工作 > 最新通知
        "https://jw.cq.gov.cn/jygz/yywzgz/gzdt/",  # 教育工作 > 语言文字工作 > 工作动态
        "https://jw.cq.gov.cn/jygz/twygfjy/zxtz_21522/",  # 教育工作 > 体育卫生与艺术教育 > 最新通知
        "https://jw.cq.gov.cn/jygz/twygfjy/cjgs/",  # 教育工作 > 体育卫生与艺术教育 > 成果公示
        "https://jw.cq.gov.cn/jygz/jyfz/fzjyzy/",  # 教育工作 > 教育发展 > 发展教育资源
        "https://jw.cq.gov.cn/jygz/jyfz/zxtz2/",  # 教育工作 > 教育发展 > 最新通知2
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/zcwj/qtwj/",  # 政务公开 > 政府信息公开目录 > 政策文件 > 其他文件
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/zcjd/wzjd/",  # 政务公开 > 政府信息公开目录 > 政策解读 > 文字解读
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/zcjd/zcwjk/",  # 政务公开 > 政府信息公开目录 > 政策解读 > 政策问答库
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/jytablfh/",  # 政务公开 > 政府信息公开目录 > 建议提案办理回复
        "https://jw.cq.gov.cn/zwgk_209/zfwzgznb/",  # 政务公开 > 政府网站工作年报
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/zdjcygk/",  # 政务公开 > 政府信息公开目录 > 重点领域信息公开
        "https://jw.cq.gov.cn/zwgk/zfxxgkml/czzjzdjc/",  # 政务公开 > 政府信息公开目录 > 财政资金直达基层
        "https://jw.cq.gov.cn/zwgk_209/fzzfjsndbg/",  # 政务公开 > 法治政府建设年度报告
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
            base_url_clean = base_url.rstrip('/')  # 兼容链接末尾是否带斜杠
            return f"{base_url_clean}/index_{page}.html"  # page=0→第1页（index_1.html）

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

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 Field('fileno',
                       DETAIL_XPATH["fileno"],
                       [], required=False, type='xpath'),

                 Field('category',
                       DETAIL_XPATH["category"],
                       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       DETAIL_XPATH["status"],
                 #       [], required=False, type='xpath'),
                 #
                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]