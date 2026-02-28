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

def format_date_from_8digit(date_str: str) -> str:
    # 处理空值、非字符串、长度不是8位、非数字的情况
    if not isinstance(date_str, str) or len(date_str) != 8 or not date_str.isdigit():
        return ""
    # 拆分年、月、日
    year = date_str[:4]
    month = date_str[4:6]
    day = date_str[6:]
    # 拼接为YYYY-MM-DD格式
    return f"{year}-{month}-{day}"

class RsjGuiyangGovCnDownloadSpider(BasePortiaSpider):
    name = "rsj_guiyang_gov_cn_Download"
    allowed_domains = ["rsj.guiyang.gov.cn"]
    start_urls = [
        "https://rsj.guiyang.gov.cn/rfwdt/fwdtxzzx/fwdtxzzxshbz/index.html",  # 首页>服务大厅>下载中心>社会保障
        "https://rsj.guiyang.gov.cn/rfwdt/fwdtxzzx/fwdtxzzxjycy/index.html",  # 首页>服务大厅>下载中心>就业创业
        "https://rsj.guiyang.gov.cn/rfwdt/fwdtxzzx/fwdtxzzxrcdwjs/index.html",  # 首页>服务大厅>下载中心>人才队伍建设
        "https://rsj.guiyang.gov.cn/rfwdt/fwdtxzzx/fwdtxzzxrsgl/index.html",  # 首页>服务大厅>下载中心>人事管理
        "https://rsj.guiyang.gov.cn/rfwdt/fwdtxzzx/fwdtxzzxldgx/index.html",  # 首页>服务大厅>下载中心>劳动关系

    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.split('.html')[0]}_{page + 1}.html"

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
                Field('detail_urls','//div[@class="right-li clearfix"]//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="right-li clearfix"]//a/@href',[Regex(r"t(\d{8})_")],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@id="pages"]/script/text()', [Regex(r"createPage\(\s*(\d+)")],type="xpath"),
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
                       '//div[@class="wz"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="text"]//p',
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
                       '//div[@class="text"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="text"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
