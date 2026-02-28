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
    "detail_urls": '//div[@class="xxgk_con clearfix"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="xxgk_con clearfix"]//ul/li/span/text()',  # 发布时间
    "next_page": '//div[@class="pagesx clearfix"]/a[3]/@tagname',
    "total_page": '//span[@class="page_zys"]/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    "source": '//meta[@name="ContentSource"]/@content',  # 来源
    "menu": '//div[@class="xxgk_now"]//a/text()',  # 面包屑菜单
    "content": '//div[@class="TRS_Editor"]//p',  # 正文内容
    "attachment": '//div[@class="TRS_Editor"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="TRS_Editor"]//p//a/text()'  # 附件名称
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JytLnGovCnGkSpider(BasePortiaSpider):
    name = "jyt_ln_gov_cn_gk"
    allowed_domains = ["jyt.ln.gov.cn"]
    start_urls = [
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/lzyj/xzfg/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/lzyj/dfxfg/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/lzyj/szfgfxwj/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/ghxx/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/tjxx/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/xzzf/zccs/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/ys_js/czys/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/ys_js/czjs/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/zdmsxx/zcjc/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/zdmsxx/ssqk/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jdjc/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/2025n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/2024n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/2023n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/2022n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/20212/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/srddbjy/2020n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2025n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2024n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2023n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2022n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2021n/index.shtml",
        "https://jyt.ln.gov.cn/jyt/gk/zfxxgk/fdzdgknr/jyta/szxta/2020n/index.shtml"
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     return re.sub(r'\-(\d+)\.shtml$', f'-{page + 1}.shtml', base_url)

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