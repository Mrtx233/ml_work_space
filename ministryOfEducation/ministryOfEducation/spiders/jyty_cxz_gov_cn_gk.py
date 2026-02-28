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
    "detail_urls": '//div[@class="fr list"]//ul/li/a/@href | //div[@class="scroll_wrap"]//ul/li/a/@href',  # 详情页链接
    "publish_times": '//div[@class="fr list"]//ul/li/span/text() | //div[@class="scroll_wrap"]//ul/li/span/text()',  # 发布时间
    "next_page": '//div[@class="pb_sys_common pb_sys_normal pb_sys_style1"]//span[@class="p_next p_fun"]/a/@href',
    "total_page": '//span[@class="p_pages"]/span[last()-2]'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="navigation"]//a/text() | //div[@class="house cleafix"]//a/text()',  # 面包屑菜单
    "content": '//div[@id="vsb_content_4"]//p | //div[@class="v_news_content"]//p | //div[@id="vsb_content"]//p',  # 正文内容
    "attachment": '//div[@id="vsb_content_4"]//p//a/@href | //div[@class="v_news_content"]//p//a/@href | //div[@id="vsb_content"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@id="vsb_content_4"]//p//a/text() | //div[@class="v_news_content"]//p//a/text() | //div[@id="vsb_content"]//p//a/text()',  # 附件名称
    "indexnumber": '//div[@class="label"]//span[1]/text()',
    "fileno": '//div[@class="label"]//span[5]/text()',
    # "category": '//div[@class="content-table"]//tr[1]/td[4]/text()',
    # "issuer": '//div[@class="scroll_main"]//tr[1]/td[4]/text()',
    "status": '//div[@class="label"]//span[2]/text()',
    "writtendate": '//div[@class="label"]//span[3]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytyCxzGovCnGkSpider(BasePortiaSpider):
    name = "jyty_cxz_gov_cn_gk"
    allowed_domains = ["jyty.cxz.gov.cn"]
    start_urls = [
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/bmwjyjd.htm",  # 政务公开 > 法定主动公开内容 > 部门权责清单
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/rsxx.htm",  # 政务公开 > 法定主动公开内容 > 人事信息
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/ghzj.htm",  # 政务公开 > 法定主动公开内容 > 规划总结
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/czxx.htm",  # 政务公开 > 法定主动公开内容 > 财政信息
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/jyta/rddbjy.htm",  # 政务公开 > 法定主动公开内容 > 建议提案 > 人大代表建议
        "https://jyty.cxz.gov.cn/info/1596/31008.htm",  # 政务公开 > 重点信息公开（单页面文章）
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/zdlygk.htm",  # 政务公开 > 法定主动公开内容 > 重点领域公开
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/ywjy.htm",  # 政务公开 > 法定主动公开内容 > 义务教育
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/xzzfxxgk.htm",  # 政务公开 > 法定主动公开内容 > 乡村振兴信息公开
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/dxsjyxx.htm",  # 政务公开 > 法定主动公开内容 > 大学生就业信息
        "https://jyty.cxz.gov.cn/zfxxgk/fdzdgknr/zcwd.htm",  # 政务公开 > 法定主动公开内容 > 政策问答
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     # 移除base_url末尾的/，拼接index_{page}.shtml
    #     base_url_clean = base_url.rstrip('/')
    #     return f"{base_url_clean}/index_{page}.html"

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
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex(r'\d{4}\.\d{2}\.\d{2}')], type="xpath"),
                 Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [], type="xpath"),
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

                 Field('fileno',
                       DETAIL_XPATH["fileno"],
                       [], required=False, type='xpath'),
                 #
                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       DETAIL_XPATH["issuer"],
                 #       [], required=False, type='xpath'),
                 #
                 Field('status',
                       DETAIL_XPATH["status"],
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]