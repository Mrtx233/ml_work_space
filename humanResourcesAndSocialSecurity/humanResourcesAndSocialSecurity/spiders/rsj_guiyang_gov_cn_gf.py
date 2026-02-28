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

class RsjGuiyangGovCnGfSpider(BasePortiaSpider):
    name = "rsj_guiyang_gov_cn_gf"
    allowed_domains = ["rsj.guiyang.gov.cn"]
    start_urls = [
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/zh/index.html",  # 综合
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/jycy/index.html",  # 就业创业
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/rcdwjs/index.html",  # 人才队伍建设
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/shbx/index.html",  # 社会保险
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/zynljs/index.html",  # 职业能力建设
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/fggwbmwj/ldgx/index.html",  # 劳动关系
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/zcfgzcjd/zcjd/index.html",  # 政策解读
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkfggw/zcfgzcjd/mtjd/index.html",  # 媒体解读
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkjhgh/jhghgh/index.html",  # 发展规划
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkjhgh/jhghjhzj/index.html",  # 计划总结
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkczxx/zfysjsjsgjf/index.html",  # 政府预算决算及“三公”经费
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkczxx/xzsysf/index.html",  # 行政事业性收费
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkrsxx/rmxx/index.html",  # 任免信息
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfxxgkrsxx/rszk/index.html",  # 人事招考
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/jycjgl/index.html",  # 就业促进管理
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/rlzyscgl/index.html",  # 人力资源市场管理
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/zynljsgl/index.html",  # 职业能力建设管理
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/zyjsrygl/index.html",  # 专业技术人员管理
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/ldgx/index.html",  # 劳动关系
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/tjzc/index.html",  # 调解仲裁
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/ldjc/index.html",  # 劳动监察
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/jlbz/index.html",  # 奖励表彰
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/rcypp/index.html",  # 人才引聘
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/fdzdgklmzdlygk/zdlygkjycy/bmfwjyxedbdk/index.html",  # 小额担保贷款
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/jytagk/index.html",  # 建议提案公开
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/zfcg/index.html",  # 政府采购
        "https://rsj.guiyang.gov.cn/zfxxgk/fdzdgklm/sgs/xzcf/index.html",  # 行政处罚

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
                Field('detail_urls','//div[@class="zfxxgk_zdgkc"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="zfxxgk_zdgkc"]//ul//b/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="page"]/script/text()', [Regex(r"createPageHTML\(\s*(\d+)")],type="xpath"),
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
                       '//div[@class="scroll_cont ScrollStyle"]//p',
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
                       '//div[@class="scroll_cont ScrollStyle"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="scroll_cont ScrollStyle"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       '//div[@class="scroll_main"]/table[1]//tr[1]/td[2]/text()',
                       [], required=False, type='xpath'),

                 Field('fileno',
                       '//div[@class="scroll_main"]/table[1]//tr[2]/td[2]/text()',
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       '//div[@class="scroll_main"]/table[1]//tr[2]/td[4]/text()',
                       [], required=False, type='xpath'),

                 Field('issuer',
                       '//div[@class="scroll_main"]/table[1]//tr[3]/td[2]/text()',
                       [], required=False, type='xpath'),

                 Field('status',
                       '//div[@class="scroll_main"]/table[1]//tr[3]/td[4]/text()',
                       [], required=False, type='xpath'),

             ])]]
