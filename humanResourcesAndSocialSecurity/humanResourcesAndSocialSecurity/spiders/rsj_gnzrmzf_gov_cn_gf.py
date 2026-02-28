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

class RsjGnzrmzfGovCnGfSpider(BasePortiaSpider):
    name = "rsj_gnzrmzf_gov_cn_gf"
    allowed_domains = ["rsj.gnzrmzf.gov.cn"]
    start_urls = [
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/jgzn.htm",  # 机构职能
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/jjjc.htm",  # 纪检监察
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/ldfg.htm",  # 领导分工
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/jjjd.htm",  # 基金监督
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/yjya.htm",  # 应急预案
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/zwsp/spgk.htm",  # 审批公开
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/fzgh.htm",  # 发展规划
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/sbxxpl.htm",  # 社保信息披露
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/shbxjf.htm",  # 社会保险缴费
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/rddbjybl.htm",  # 人大代表建议办理
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/zxwytabl.htm",  # 政协委员提案办理
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/zfwzgznb.htm",  # 政府网站工作年报
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/sydwfrnb.htm",  # 事业单位法人年报
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/ylbx.htm",  # 养老保险
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/fdzdgknei_rong/wgjy.htm",  # 稳岗就业
        "http://rsj.gnzrmzf.gov.cn/zfxxgk1/zfxxgknb.htm",  # 政府信息公开年报
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        # 步骤1：移除base_url末尾的.htm后缀
        base_url_clean = re.sub(r"\.htm$", "", base_url)
        # 步骤2：拼接分页路径（保留原page+1计算逻辑）
        target_page = page + 1  # 原逻辑：page值+1作为最终页码
        # 若无需+1，直接用 target_page = page
        return f"{base_url_clean}/{target_page}.htm"

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
                Field('detail_urls','//ul[@class="content-list"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//ul[@class="content-list"]//ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//span[@class="p_pages"]/span[last()-2]//text()', [],type="xpath"),
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

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="v_news_content"]//p | //div[@class="v_news_content"]//span',
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
                       '//div[@class="v_news_content"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="v_news_content"]//p//a/text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
