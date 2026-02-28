from __future__ import absolute_import

import scrapy
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, AgriItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex

class RsjCxzGovCnGfSpider(BasePortiaSpider):
    name = "rsj_cxz_gov_cn_gf"
    allowed_domains = ["rsj.cxz.gov.cn"]
    start_urls = [
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/jyxx1.htm",  # 就业信息
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/cyfc1.htm",  # 创业扶持
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/jybf1.htm",  # 就业帮扶
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/ylbx1.htm",  # 养老保险
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/gsbx1.htm",  # 工伤保险（已统一为https协议）
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/sybx1.htm",  # 失业保险
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/jjjd1.htm",  # 基金监督
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/rcyj1.htm",  # 人才引进
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/rsks1.htm",  # 人事考试
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/sydwrygl1.htm",  # 事业单位人员管理
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zyjsrygl.htm",  # 专业技术人员管理
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/ldgxxd1.htm",  # 劳动关系协调
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/djzc1.htm",  # 调解仲裁
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/ldbzjc1.htm",  # 劳动保障监察
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/gzsrfp.htm",  # 工资收入分配
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zcfg1.htm",  # 政策法规
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zcjd1.htm",  # 政策解读
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/xzzfxxgk.htm",  # 行政执法信息公开
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/rddbjy.htm",  # 人大代表建议
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zxta.htm",  # 政协提案
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/czxx.htm",  # 财政信息
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zdxzjcgk.htm",  # 重大行政决策公开
        "https://rsj.cxz.gov.cn/zfxxgk/fdzdgknr/zcwd.htm",  # 政策问答
    ]


    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          cb_kwargs={'base_url': url})

    list_items = [[
        Item(ListItems,
            None,
            'body',
            [
                Field('detail_urls','//div[@class="scroll_wrap"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="scroll_wrap"]//ul/li/span/text()',[Regex(r'\d{4}[-.]\d{2}[-.]\d{2}')],type="xpath"),
                # 翻页url
                Field('next_page', '//span[@class="p_next p_fun"]//a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="pb_sys_common pb_sys_normal pb_sys_style1"]/span[last()-4]/text()', [Regex(r'/(\d+)')],type="xpath"),
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
                       '//div[@class="map fr"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@id="vsb_content"]//p | //div[@class="v_news_content"]//p | //div[@class="list-page"]//p',
                       [
                       lambda vals:[
                            html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                            for html_str in vals
                                if isinstance(html_str,str) and html_str.strip()
                       ],
                       lambda html_list: [
                            scrapy.Selector(text=html).xpath('string(.)').get().strip()
                            for html in html_list
                            ], Join(separator='\n')], required=True, type='xpath'),

                 Field('attachment',
                       '//div[@class="v_news_content"]//p//a/@href |//div[@class="list-page"]//a/@href ',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="v_news_content"]//p//a//text() | //div[@class="list-page"]//a/text()',
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       '//div[@class="label"]/span[1]/text()',
                       [], required=False, type='xpath'),

                 Field('fileno',
                       '//div[@class="label"]/span[5]/text()',
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       '//div[@class="label"]/span[3]/text()',
                       [], required=False, type='xpath'),

                 Field('status',
                       '//div[@class="label"]/span[2]/text()',
                       [], required=False, type='xpath'),

             ])]]
