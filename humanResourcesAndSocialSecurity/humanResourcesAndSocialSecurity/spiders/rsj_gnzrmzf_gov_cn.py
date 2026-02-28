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

class RsjGnzrmzfGovCnSpider(BasePortiaSpider):
    name = "rsj_gnzrmzf_gov_cn"
    allowed_domains = ["rsj.gnzrmzf.gov.cn"]
    start_urls = [
        "http://rsj.gnzrmzf.gov.cn/xwzx/gzdt.htm",  # 首页>>新闻资讯>>工作动态
        # "http://rsj.gnzrmzf.gov.cn/xwzx/xwzx1.htm",  # 首页>>新闻资讯>>新闻资讯
        # "http://rsj.gnzrmzf.gov.cn/zcfg1/jycy.htm",  # 首页>>政策法规>>就业创业
        # "http://rsj.gnzrmzf.gov.cn/zcfg1/shbz.htm",  # 首页>>政策法规>>社会保障
        # "http://rsj.gnzrmzf.gov.cn/zcfg1/rsrc.htm",  # 首页>>政策法规>>人事人才
        # "http://rsj.gnzrmzf.gov.cn/zcfg1/ldgx.htm",  # 首页>>政策法规>>劳动关系
        # "http://rsj.gnzrmzf.gov.cn/kszp.htm",  # 首页>>考试招聘
        # "http://rsj.gnzrmzf.gov.cn/zcjd.htm",  # 首页>>政策解读
        # "http://rsj.gnzrmzf.gov.cn/xzzx1.htm",  # 首页>>下载中心
        # "http://rsj.gnzrmzf.gov.cn/ztzl/srxxxcgcddesdjs.htm",  # 首页>>专题专栏>>深入学习宣传贯彻党的二十大精神
        # "http://rsj.gnzrmzf.gov.cn/ztzl/jgdj.htm",  # 首页>>专题专栏>>机关党建
        # "http://rsj.gnzrmzf.gov.cn/ztzl/xczx.htm",  # 首页>>专题专栏>>乡村振兴
        # "http://rsj.gnzrmzf.gov.cn/ztzl/rsbmckdwgjzfzxxd.htm",  # 首页>>专题专栏>>人社部门窗口单位改进作风专项行动
        # "http://rsj.gnzrmzf.gov.cn/ztzl/fzxc.htm",  # 首页>>专题专栏>>法制宣传
        # "http://rsj.gnzrmzf.gov.cn/ztzl/szsc.htm",  # 首页>>专题专栏>>三抓三促
        # "http://rsj.gnzrmzf.gov.cn/ztzl/sbjjjdjb.htm",  # 首页>>专题专栏>>社保基金监督举报
    ]


    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list)
            # cb_kwargs = {'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})


    list_items = [[
        Item(ListItems,
            None,
            'body',
            [
                Field('detail_urls','//div[@class="wzlist"]/ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="wzlist"]/ul//span[@class="date"]/text()',[],type="xpath"),
                # 翻页url
                Field('next_page', '//span[@class="p_next p_fun"]//a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//span[@class="p_pages"]/span[last()-2]/a/text()', [],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//meta[@name="ArticleTitle"]/@content',
                       [], required=False, type='xpath'),

                 Field('publish_time',
                       '//meta[@name="PubDate"]/@content',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('menu',
                       '//div[@class="local"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="zw"]//p',
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
                       '//div[@class="zw"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="zw"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
