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

class HrssGzlpsGovCnGfSpider(BasePortiaSpider):
    name = "hrss_gzlps_gov_cn_gf"
    allowed_domains = ["hrss.gzlps.gov.cn"]
    start_urls = [
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/zfxxgkzd/",  # 政府信息公开制度
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/qzqd/",  # 权责清单
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zdly/jycy_5711896/",  # 就业创业
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zdly/ldgx/",  # 劳动关系
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zdly/shbx_5711898/",  # 社会保险
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/rsrc_5805162/sydwrsgl/",  # 事业单位人事管理
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/rsrc_5805162/rcfw/",  # 人才服务
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/rsrc_5805162/zcks_5805165/",  # 职称考试
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/rsrc_5805162/zyjsrygl_5805166/",  # 专业技术人员管理
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zcwj_5806048/bmwj/",  # 部门文件
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zcwj_5806048/zcfg_5806049/",  # 政策法规
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/zcwj_5806048/zcjd/",  # 政策解读
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/jhzj/",  # 计划总结
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/tjxx/",  # 统计信息
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/czxx/xzsyxsf_5805171/",  # 行政事业性收费
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/czxx/czjsjsgjf_5805172/",  # 财政决算及三公经费
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/czxx/czysjsgjf_5805173/",  # 财政预算及三公经费
        "https://hrss.gzlps.gov.cn/bmxxgk/zfxxgk/fdzdgknr/jytabl/",  # 建议提案办理
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        base_url = base_url.rstrip('/') + '/'
        return f"{base_url}index_{page + 1}.html"

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
                Field('detail_urls','//div[@class="zfxxgk_zdgkc"]//ul//a/@href | //div[@class="scroll_wrap"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="zfxxgk_zdgkc"]//ul//b/text() | //div[@class="scroll_wrap"]//ul//b/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
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

                 Field('menu',
                       '//meta[@name="ContentSource"]/@content',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

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

                 # Field('indexnumber',
                 #       '//div[@class="scroll_main"]/table[1]//tr[1]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       '//div[@class="scroll_main"]/table[1]//tr[2]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       '//div[@class="scroll_main"]/table[1]//tr[2]/td[4]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       '//div[@class="scroll_main"]/table[1]//tr[3]/td[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       '//div[@class="scroll_main"]/table[1]//tr[3]/td[4]/text()',
                 #       [], required=False, type='xpath'),

             ])]]
