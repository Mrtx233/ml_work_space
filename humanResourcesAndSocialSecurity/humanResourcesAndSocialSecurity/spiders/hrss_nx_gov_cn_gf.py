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

class HrssNxGovCnGfSpider(BasePortiaSpider):
    name = "hrss_nx_gov_cn_gf"
    allowed_domains = ["hrss.nx.gov.cn"]
    start_urls = [
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/tfwj/",  # 厅发文件
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/cyjy/",  # 创业就业
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/shbz/",  # 社会保障
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/rsrc/",  # 人才人事
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/srfp/",  # 收入分配
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/ldgx/",  # 劳动关系
        "https://hrss.nx.gov.cn/xxgk/zcj/zcfg/zhld/",  # 综合工作
        "https://hrss.nx.gov.cn/xxgk/zcj/zcjd/wzjd_new/",  # 文字解读
        "https://hrss.nx.gov.cn/xxgk/gkmu/wgjy/gkbz/",  # 公开标准
        "https://hrss.nx.gov.cn/xxgk/gkmu/wgjy/zcwj/",  # 政策文件
        "https://hrss.nx.gov.cn/xxgk/gkmu/wgjy/jycy/",  # 就业创业服务
        "https://hrss.nx.gov.cn/xxgk/gkmu/zqyj/",  # 征求意见与征集结果公开
        "https://hrss.nx.gov.cn/xxgk/gkmu/sfxm/",  # 收费项目
        "https://hrss.nx.gov.cn/xxgk/gkmu/zfcg/",  # 政府采购
        "https://hrss.nx.gov.cn/xxgk/gkmu/ghjh/",  # 规划计划
        "https://hrss.nx.gov.cn/xxgk/gkmu/tjsj/",  # 统计数据
        "https://hrss.nx.gov.cn/xxgk/gkmu/jcgk/",  # 决策公开
        "https://hrss.nx.gov.cn/xxgk/gkmu/hygk/",  # 会议公开
        "https://hrss.nx.gov.cn/xxgk/gkmu/cfgs/qd/",  # 行政许可事项清单
        "https://hrss.nx.gov.cn/xxgk/gkmu/cfgs/gs/",  # 行政许可公示
        "https://hrss.nx.gov.cn/xxgk/gkmu/cfgs/xzqzycf/",  # 行政强制与处罚
        "https://hrss.nx.gov.cn/xxgk/gkmu/ssj/",  # 双随机一公开
        "https://hrss.nx.gov.cn/xxgk/gkmu/jyta/",  # 建议提案
        "https://hrss.nx.gov.cn/xxgk/gkmu/zxft/",  # 在线访谈
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 清理base_url末尾的/，拼接index_{page+2}.html
        base_url_clean = base_url.rstrip('/')
        return f"{base_url_clean}/index_{page + 1}.html"


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
                Field('total_page', '//div[@class="page"]//script/text()', [Regex(r"createPageHTML\((\d+),")],type="xpath"),
            ])]]

    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       '//meta[@name="ArticleTitle"]/@content | //div[@class="title"]//text()',
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       '//meta[@name="PubDate"]/@content | //div[@class="content_jieshi_l"]//text()',
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type='xpath'),

                 Field('menu',
                       '//div[@class="newDetail"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content | //div[@class="content_jieshi_l"]/span[2]/text()',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p | //div[@class="content"]//p',
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
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p//a/@href | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p//a/@href | //div[@class="content"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="view TRS_UEDITOR trs_paper_default trs_web"]//p//a/text() | //div[@class="view TRS_UEDITOR trs_paper_default trs_word"]//p//a/text() | //div[@class="content"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
