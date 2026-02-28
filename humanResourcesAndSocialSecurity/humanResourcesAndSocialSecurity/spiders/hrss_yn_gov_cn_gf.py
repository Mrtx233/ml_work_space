from __future__ import absolute_import
import re
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

class HrssYnGovCnGfSpider(BasePortiaSpider):
    name = "hrss_yn_gov_cn_gf"
    allowed_domains = ["hrss.yn.gov.cn"]
    start_urls = [
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1129&pid=971&page=1&kw=",  # 公务员招录及事业单位招聘
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=896&pid=971&page=1&kw=",  # 新闻发布会
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1076&pid=1125&page=1&kw=",  # 意见征集
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1140&pid=1125&page=1&kw=",  # 重大行政决策制度
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1124&pid=971&page=1&kw=",  # 采购公开
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1108&pid=971&page=1&kw=",  # 办事统计
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1068&pid=971&page=1&kw=",  # 行政处罚和行政强制
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1067&pid=971&page=1&kw=",  # 行政许可
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1064&pid=971&page=1&kw=",  # 稳岗就业
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=371&pid=971&page=1&kw=",  # 就业创业信息公开
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=558&pid=971&page=1&kw=yjs",  # 通知公告（含kw=yjs参数）
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1142&pid=971&page=1&kw=",  # 绩效评价结果公开
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=863&pid=971&page=1&kw=",  # 建议提案办理
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1062&pid=971&page=1&kw=",  # 预案措施
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1135&pid=971&page=1&kw=",  # 双随机
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1143&pid=971&page=1&kw=",  # 行政事业性收费公开
        "https://hrss.yn.gov.cn/InfoPublic.aspx?cid=1019&pid=971&page=1&kw=",  # 政府信息公开年报
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        page_num = page + 2
        return re.sub(r"page=\d+", f"page={page_num}", base_url)


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
                Field('detail_urls','//div[@class="info-list"]/p/a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="info-list"]/p/span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="pages"]/a[last()]/@href', [Regex(r"page=(\d+)")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//div[@class="rightnav"]/h1/text()',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//div[@class="rightnav"]/p[@class="sub-title"]/text()',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type='xpath'),

                 Field('content',
                       '//div[@class="news-info"]//p',
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
                       '//div[@class="news-info"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="news-info"]//p//a/span/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
