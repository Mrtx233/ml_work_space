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

class RstXinjiangGovCnGfSpider(BasePortiaSpider):
    name = "rst_xinjiang_gov_cn_gf"
    allowed_domains = ["rst.xinjiang.gov.cn"]
    start_urls = [
        "https://rst.xinjiang.gov.cn/xjrst/c112675/zfxxgk_gknrz.shtml",  # 政策解读
        "https://rst.xinjiang.gov.cn/xjrst/c112676/zfxxgk_gknrz.shtml",  # 规划信息
        "https://rst.xinjiang.gov.cn/xjrst/c112678/zfxxgk_gknrz.shtml",  # 公务员招录
        "https://rst.xinjiang.gov.cn/xjrst/c112680/zfxxgk_gknrz.shtml",  # 行政许可
        "https://rst.xinjiang.gov.cn/xjrst/c112677/zfxxgk_gknrz.shtml",  # 重大决策预公开
        "https://rst.xinjiang.gov.cn/xjrst/c112679/zfxxgk_gknrz.shtml",  # 权责清单
        "https://rst.xinjiang.gov.cn/xjrst/c112681/zfxxgk_gknrz.shtml",  # 行政处罚
        "https://rst.xinjiang.gov.cn/xjrst/c120000/zfxxgk_gknrz.shtml",  # 行政检查
        "https://rst.xinjiang.gov.cn/xjrst/qtdwglfw/zfxxgk_gknrz.shtml",  # 其他对外管理服务
        "https://rst.xinjiang.gov.cn/xjrst/c112682/zfxxgk_gknrz.shtml",  # 行政事业性收费
        "https://rst.xinjiang.gov.cn/xjrst/c112683/zfxxgk_gknrz.shtml",  # 建议提案
        "https://rst.xinjiang.gov.cn/xjrst/c112684/zfxxgk_gknrz.shtml",  # 政府采购
        "https://rst.xinjiang.gov.cn/xjrst/c112685/zfxxgk_gknrz.shtml",  # 部门预决算
        "https://rst.xinjiang.gov.cn/xjrst/c112687/zfxxgk_gknrz.shtml",  # 统计公报
        "https://rst.xinjiang.gov.cn/xjrst/xwfbh/zfxxgk_gknrz.shtml",  # 新闻发布会
        "https://rst.xinjiang.gov.cn/xjrst/c1127010/zfxxgk_gknrz.shtml",  # 办事统计
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
                Field('detail_urls','//div[@class="gknr_list"]/dl/dd/a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="gknr_list"]/dl/dd/span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r'createPageHTML\(\'page-div\',(\d+),')],type="xpath"),
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
                       '//meta[@name="ColumnKeywords"]/@content',
                       [],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="gknbxq_detail"]//p',
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
                       '//div[@class="gknbxq_detail"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="gknbxq_detail"]//p//a//text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
