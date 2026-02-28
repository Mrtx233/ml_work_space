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

class HrssHainanGovCnSpider(BasePortiaSpider):
    name = "hrss_hainan_gov_cn"
    allowed_domains = ["hrss.hainan.gov.cn"]
    start_urls = [
        "https://hrss.hainan.gov.cn/hrss/zwdt/list3.shtml",  # 首页 > 要闻动态 > 政务动态
        "https://hrss.hainan.gov.cn/hrss/mtbd/list3.shtml",  # 首页 > 要闻动态 > 媒体报道
        "https://hrss.hainan.gov.cn/hrss/zxjd/list3.shtml",  # 首页 > 政策解读 > 最新解读
        "https://hrss.hainan.gov.cn/hrss/hygq/list3.shtml",  # 首页 > 解读回应 > 回应关切
        "http://hrss.hainan.gov.cn/hrss/xzzq/list3.shtml",  # 首页 > 下载专区
        "https://hrss.hainan.gov.cn/hrss/zcws/list3.shtml",  # 首页 > 热点专题 > 仲裁文书公开
        "https://hrss.hainan.gov.cn/hrss/zytzgg/list3.shtml",  # 首页 > 职业技能提升专栏 > 通知公告
        "https://hrss.hainan.gov.cn/hrss/zybgxz/list3.shtml",  # 首页 > 职业技能提升专栏 > 表格下载
        "https://hrss.hainan.gov.cn/hrss/0400/list3.shtml",  # 首页 > 信息公开 > 公示公告
        "https://hrss.hainan.gov.cn/hrss/1000/list3.shtml",  # 首页 > 信息公开 > 重点领域信息公开
        "https://hrss.hainan.gov.cn/hrss/0800/list3.shtml",  # 首页 > 信息公开 > 规划计划
        "https://hrss.hainan.gov.cn/hrss/0600/list3.shtml",  # 首页 > 信息公开 > 人事信息
        "https://hrss.hainan.gov.cn/hrss/ssjygks/list3.shtml",  # 首页 > 信息公开 > 双随机一公开
        "https://hrss.hainan.gov.cn/hrss/0701/list3.shtml",  # 首页 > 财政公开 > 财政预决算
        "https://hrss.hainan.gov.cn/hrss/jsxyy/list3.shtml",  # 首页 > 职业技能提升专栏 > 竞赛宣传

    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.split('.shtml')[0]}_{page + 2}.shtml"

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
                Field('detail_urls','//div[@class="list_div mar-top2 "]//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list_div mar-top2 "]//tr/td/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"createPageHTML\('page_div',(\d+)")],type="xpath"),
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
                       '//div[@class="powz"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="con_cen line mar-t2 xxgk_content_content"]//p | //div[@id="zoomcon"]//p',
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
                       '//div[@class="con_cen line mar-t2 xxgk_content_content"]//a/@href | //div[@id="zoomcon"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="con_cen line mar-t2 xxgk_content_content"]//a//text() | //div[@id="zoomcon"]//a//text()',
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       '//div[@class="zwgk_comr1"]/ul/li[1]/span[1]/text()',
                       [], required=False, type='xpath'),

                 Field('category',
                       '//div[@class="zwgk_comr1"]/ul/li[1]/span[2]/text()',
                       [], required=False, type='xpath'),

                 Field('fileno',
                       '//div[@class="zwgk_comr1"]/ul/li[4]/span[1]/text()',
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       '//div[@class="zwgk_comr1"]/ul/li[2]/span[1]/text()',
                       [], required=False, type='xpath'),

                 Field('issuer',
                       '//div[@class="zwgk_comr1"]/ul/li[6]/span[2]//text()',
                       [], required=False, type='xpath'),



             ])]]
