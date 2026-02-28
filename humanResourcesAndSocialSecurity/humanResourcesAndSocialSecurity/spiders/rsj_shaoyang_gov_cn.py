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


class RsjShaoyangGovCnSpider(BasePortiaSpider):
    name = "rsj_shaoyang_gov_cn"
    allowed_domains = ["rsj.shaoyang.gov.cn"]

    start_urls = [
        # "https://rsj.shaoyang.gov.cn/syrsj/gzdt/rlist.shtml",  # 首页 > 工作动态
        # "https://rsj.shaoyang.gov.cn/syrsj/wmcj/rlist.shtml",  # 首页 > 专题专栏 > 文明创建
        # "https://rsj.shaoyang.gov.cn/syrsj/sydwgkzp/rlist.shtml",  # 首页 > 专题专栏 > 事业单位公开招聘
        # "https://rsj.shaoyang.gov.cn/syrsj/jycy/rlist.shtml",  # 首页 > 专题专栏 > 就业创业
        # "https://rsj.shaoyang.gov.cn/syrsj/jnts/rlist.shtml",  # 首页 > 专题专栏 > 职业技能提升
        # "https://rsj.shaoyang.gov.cn/syrsj/ldjc/rlist.shtml",  # 首页 > 专题专栏 > 劳动监察
        # "https://rsj.shaoyang.gov.cn/syrsj/xfjs/rlist.shtml",  # 首页 > 专题专栏 > 行风建设
        # "https://rsj.shaoyang.gov.cn/syrsj/xzzx/rlist.shtml",  # 首页 > 专题专栏 > 下载中心
        # "https://rsj.shaoyang.gov.cn/syrsj/rszchsx/rlist.shtml",  # 首页 > 专题专栏 > 人社政策惠三湘
        # "https://rsj.shaoyang.gov.cn/syrsj/sszdms/rlist.shtml",  # 首页 > 专题专栏 > 省市重点民生实事宣传专栏
        # "https://rsj.shaoyang.gov.cn/syrsj/tzgg/rlist.shtml",  # 首页 > 信息公开 > 通知公告
        # "https://rsj.shaoyang.gov.cn/syrsj/gknb/rlist.shtml",  # 首页 > 信息公开 > 信息公开年度报告
        # "https://rsj.shaoyang.gov.cn/syrsj/gfxwj/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 政策文件 > 规范性文件
        # "https://rsj.shaoyang.gov.cn/syrsj/wjjd/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 政策文件 > 部门文件解读
        # "https://rsj.shaoyang.gov.cn/syrsj/ghjh/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 规划计划
        # "https://rsj.shaoyang.gov.cn/syrsj/rsxx/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 人事信息
        # "https://rsj.shaoyang.gov.cn/syrsj/czxx/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 财政信息
        # "https://rsj.shaoyang.gov.cn/syrsj/xzxk/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 行政许可
        # "https://rsj.shaoyang.gov.cn/syrsj/gsxx/rlist.shtml",  # 首页 > 信息公开 > 法定主动公开内容 > 公示信息
        "https://rsj.shaoyang.gov.cn/syrsj/gwyzlks/rlist.shtml",  # 首页 > 人事考试 > 公务员招录考试
        "https://rsj.shaoyang.gov.cn/syrsj/sydwzpks/rlist.shtml",  # 首页 > 人事考试 > 事业单位招聘考试
        "https://rsj.shaoyang.gov.cn/syrsj/zyjszgks/rlist.shtml",  # 首页 > 人事考试 > 专业技术资格考试
        "https://rsj.shaoyang.gov.cn/syrsj/zcjsjks/rlist.shtml",  # 首页 > 人事考试 > 职称计算机考试

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
                Field('detail_urls','//div[@class="list_right"]/ul/li/a[@target="_blank"]/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list_right"]/ul/li/span',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"createPageHTML\([^,]+,(\d+)")],type="xpath"),
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
                       '//meta[@name="ContentSource "]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@id="zoomcon"]//p',
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
                       '//div[@id="zoomcon"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@id="zoomcon"]//a/text()',
                       [], type='xpath', file_category='attachment'),



             ])]]
