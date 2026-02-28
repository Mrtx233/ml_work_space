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

class HrssYnGovCnSpider(BasePortiaSpider):
    name = "hrss_yn_gov_cn"
    allowed_domains = ["hrss.yn.gov.cn"]
    start_urls = [
        # 要闻类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=365&page=1",  # 国内要闻
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=526&page=1",  # 云南要闻
        # 公告/奖励类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=558&page=1",  # 通知公告
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=643&page=1",  # 表彰奖励
        # 招考招聘类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=458&page=1",  # 招考招聘
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=602&page=1",  # 事业单位招聘
        # 人社动态类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=362&page=1",  # 人社动态
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=556&page=1",  # 部省要情
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=647&page=1",  # 厅内动态
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=660&page=1",  # 媒体聚焦
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=662&page=1",  # 政策解读
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=369&page=1",  # 州市信息
        # 专项计划/政策类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=950&page=1",  # “三支一扶”计划
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=560&page=1",  # 政策文件
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=682&page=1",  # 法律法规
        # 业务类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=372&page=1",  # 社会保障
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=374&page=1",  # 人才队伍
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=377&page=1",  # 劳动关系
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=378&page=1",  # 农民工工作
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=649&page=1",  # 提前退休
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=671&page=1",  # 信用信息公示
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=997&page=1",  # 调解仲裁公告
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=384&page=1",  # 图片新闻
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=642&page=1",  # 资料下载
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=1110&page=1",  # 政府网站年度工作报表
        # 专题栏目
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=949&page=1",  # “学先进、当先进”
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=966&page=1",  # 根治欠薪进行时
        # 规划/提案类
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=659&page=1",  # 规划计划
        "https://hrss.yn.gov.cn/NewsLsit.aspx?ClassID=863&page=1",  # 建议提案办理
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r"page=\d+", f"page={page + 2}", base_url)

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
                Field('detail_urls','//div[@class="listBox mt5"]//ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="listBox mt5"]//ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//div[@class="pages"]/a[4]/@href', [Regex(r"page=(\d+)")],type="xpath"),
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
                       '//div[@class="readBox mt5"]/h1/a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="readBox mt5"]//span/p',
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
                       '//div[@class="readBox mt5"]//span/p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="readBox mt5"]//span/p//a/text()',
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
