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

class RsjYulinGovCnSpider(BasePortiaSpider):
    name = "rsj_yulin_gov_cn"
    allowed_domains = ["rsj.yulin.gov.cn"]
    start_urls = [
        "http://rsj.yulin.gov.cn/zwyw/",  # 首页 > 政务要闻
        "http://rsj.yulin.gov.cn/tzgg/",  # 首页 > 通知公告
        "http://rsj.yulin.gov.cn/ghjh/",  # 首页 > 规划计划
        "http://rsj.yulin.gov.cn/fggz/",  # 首页 > 法规规章
        "http://rsj.yulin.gov.cn/zcjd/",  # 首页 > 政策解读
        "http://rsj.yulin.gov.cn/syqtlm/gzqxgz/",  # 首页 > 首页其他栏目 > 根治欠薪工作
        "http://rsj.yulin.gov.cn/bmzl/shbz/rdbswd/",  # 首页 > 部门专栏 > 社会保障 > 热点办事问答
        "http://rsj.yulin.gov.cn/bmzl/shbz/xzzq/",  # 首页 > 部门专栏 > 社会保障 > 下载专区
        "http://rsj.yulin.gov.cn/tszl/rsrc/jycypx/",  # 首页 > 特色专栏 > 人事人才 > 就业创业培训
        "http://rsj.yulin.gov.cn/tszl/rsrc/rczp/",  # 首页 > 特色专栏 > 人事人才 > 人才招聘
        "http://rsj.yulin.gov.cn/tszl/rsrc/zczl/",  # 首页 > 特色专栏 > 人事人才 > 职称专栏
        "http://rsj.yulin.gov.cn/tszl/rsrc/xzzx/",  # 首页 > 特色专栏 > 人事人才 > 下载中心
        "http://rsj.yulin.gov.cn/tszl/rsrc/sydwzk/",  # 首页 > 特色专栏 > 人事人才 > 事业单位招考
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 移除base_url末尾的/，拼接index_{page}.shtml
        base_url_clean = base_url.rstrip('/')  # 清理末尾的/，避免出现//index_1.shtml
        return f"{base_url_clean}/index_{page + 2}.shtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    list_items = [[
        Item(ListItems,
            None,
            'body',
            [
                Field('detail_urls','//ul[@class="more-list"]//a/@href',[], type="xpath"),
                Field('publish_times','//ul[@class="more-list"]/li/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="page"]//script/text()', [Regex(r"createPageHTML\((\d+)")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//meta[@name="ArticleTitle"]/@content',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//meta[@name="PubDate"]/@content',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('menu',
                       '//div[@class="crumb-nav"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="article-con"]//p',
                       [
                       lambda vals:[
                            html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                            for html_str in vals
                                if isinstance(html_str,str) and html_str.strip()
                       ],
                       lambda html_list: [
                            scrapy.Selector(text=html).xpath('string(.)').get().strip()
                            for html in html_list
                            ], Join(separator='\n')], required=False, type='xpath'),

                 Field('attachment',
                       '//div[@class="downloadfile"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="downloadfile"]//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
