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

class RsjKmGovCnGfSpider(BasePortiaSpider):
    name = "rsj_km_gov_cn_gf"
    allowed_domains = ["rsj.km.gov.cn"]
    start_urls = [
        "https://rsj.km.gov.cn/zfxxgk/zcwj/qtwj/",  # 其他文件
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/jgzn/",  # 机构职能
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zcjd/",  # 政策解读
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zfwzgzndbb/",  # 政府网站工作年度报表
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/ghjh/",  # 规划计划
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zfcgjgmfw/",  # 政府采购及购买服务
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/czzjxx/czyjsgk/",  # 财政预决算公开
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/czzjxx/sgjfxx/",  # 三公经费信息
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/jycy/zczy/",  # 政策指引
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/jycy/fwjg/",  # 服务机构
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/jycy/jctj/",  # 监测统计
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zdlyxxgk/zdjcygk/",  # 重大决策公开
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/xwfb/",  # 新闻发布
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2025n/",  # 建议提案办理2025
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2024n/",  # 建议提案办理2024
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/jytabl/2023n/",  # 建议提案办理2023
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/xzzf/jgxx/",  # 行政执法
        "https://rsj.km.gov.cn/zfxxgk/fdzdgknr/zczqy/",  # 政策找企业
        "https://rsj.km.gov.cn/zfxxgk/zfxxgknb/",  # 政府信息公开年报
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
                Field('detail_urls','//div[contains(@class, "item-url")]/p[1]/a[1]/@href',[], type="xpath"),
                Field('publish_times','//div[contains(@class, "item-url")]/p[2]/a[1]/text() |//div[contains(@class, "item-url")]/p[3]/a[1]/text()',[Regex(r"\d{4}\.\d{2}\.\d{2}")],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"ele\.value>(\d+)")],type="xpath"),
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

                 Field('content',
                       '//div[@class="activity"]//p',
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
                       '//div[@class="activity"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="activity"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       '//div[@class="content-table"]//tr[1]/td[2]/text()',
                       [], required=False, type='xpath'),

                 Field('fileno',
                       '//div[@class="content-table"]//tr[4]/td[2]/text()',
                       [], required=False, type='xpath'),

                 Field('category',
                       '//div[@class="content-table"]//tr[1]/td[4]/text()',
                       [], required=False, type='xpath'),

                 Field('issuer',
                       '//div[@class="content-table"]//tr[2]/td[2]/text()',
                       [], required=False, type='xpath'),



             ])]]
