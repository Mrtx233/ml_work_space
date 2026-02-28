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

class RstXinjiangGovCnSpider(BasePortiaSpider):
    name = "rst_xinjiang_gov_cn"
    allowed_domains = ["rst.xinjiang.gov.cn"]
    start_urls = [
        "https://rst.xinjiang.gov.cn/xjrst/c112660/list.shtml",  # 新闻中心 > 图片新闻
        "https://rst.xinjiang.gov.cn/xjrst/c112487/list.shtml",  # 新闻中心 > 公示公告
        "https://rst.xinjiang.gov.cn/xjrst/c112483/list.shtml",  # 新闻中心 > 国家要闻
        "https://rst.xinjiang.gov.cn/xjrst/c112484/list.shtml",  # 新闻中心 > 新疆要闻
        "https://rst.xinjiang.gov.cn/xjrst/c112485/list.shtml",  # 新闻中心 > 工作动态
        "https://rst.xinjiang.gov.cn/xjrst/dzdt/list.shtml",  # 新闻中心 > 地州动态
        "https://rst.xinjiang.gov.cn/xjrst/c112702/list.shtml",  # 互动交流 > 资料下载
        "https://rst.xinjiang.gov.cn/xjrst/c113126/list.shtml",  # 互动交流 > 互动直播
        "https://rst.xinjiang.gov.cn/xjrst/c113125/list.shtml",  # 互动交流 > 舆情聚焦
        "https://rst.xinjiang.gov.cn/xjrst/c112719/list.shtml",  # 就业创业 > 政策文件
        "https://rst.xinjiang.gov.cn/xjrst/c112720/list.shtml",  # 就业创业 > 工作动态
        "https://rst.xinjiang.gov.cn/xjrst/jycyx/list.shtml",  # 就业创业 > 就业创业
        "https://rst.xinjiang.gov.cn/xjrst/c112723/list.shtml",  # 就业创业 > 职业能力
        "https://rst.xinjiang.gov.cn/xjrst/c112722/list.shtml",  # 就业创业 > 人力资源
        "https://rst.xinjiang.gov.cn/xjrst/c112721/list.shtml",  # 就业创业 > 就业服务
        "https://rst.xinjiang.gov.cn/xjrst/c112732/list.shtml",  # 社会保障 > 政策文件
        "https://rst.xinjiang.gov.cn/xjrst/c112733/list.shtml",  # 社会保障 > 工作动态
        "https://rst.xinjiang.gov.cn/xjrst/c112734/list.shtml",  # 社会保障 > 养老保险
        "https://rst.xinjiang.gov.cn/xjrst/c112737/list.shtml",  # 社会保障 > 失业保险
        "https://rst.xinjiang.gov.cn/xjrst/c112735/list.shtml",  # 社会保障 > 工伤保险
        "https://rst.xinjiang.gov.cn/xjrst/jjjd/list.shtml",  # 社会保障 > 基金监督
        "https://rst.xinjiang.gov.cn/xjrst/c1127312/list.shtml",  # 社会保障 > 我与社保的故事
        "https://rst.xinjiang.gov.cn/xjrst/c112739/list.shtml",  # 人才人事 > 政策文件
        "https://rst.xinjiang.gov.cn/xjrst/c112740/list.shtml",  # 人才人事 > 工作动态
        "https://rst.xinjiang.gov.cn/xjrst/c112746/list.shtml",  # 人才人事 > 事业单位
        "https://rst.xinjiang.gov.cn/xjrst/c112742/list.shtml",  # 人才人事 > 专技人才 > 各系列任职资格条件
        "https://rst.xinjiang.gov.cn/xjrst/c112743/list.shtml",  # 人才人事 > 专技人才 > 专业技术人才队伍建设
        "https://rst.xinjiang.gov.cn/xjrst/c112744/list.shtml",  # 人才人事 > 专技人才 > 专业技术人员继续教育
        "https://rst.xinjiang.gov.cn/xjrst/c112745/list.shtml",  # 人才人事 > 专技人才 > 新疆少数民族特培
        "https://rst.xinjiang.gov.cn/xjrst/c112727/list.shtml",  # 人才人事 > 技能人才
        "https://rst.xinjiang.gov.cn/xjrst/c113773/list.shtml",  # 人才人事 > 高层次人才
        "https://rst.xinjiang.gov.cn/xjrst/c112752/list.shtml",  # 劳动关系 > 政策文件
        "https://rst.xinjiang.gov.cn/xjrst/c112753/list.shtml",  # 劳动关系 > 工作动态
        "https://rst.xinjiang.gov.cn/xjrst/c112845/list.shtml",  # 劳动关系 > 劳动协调
        "https://rst.xinjiang.gov.cn/xjrst/c112846/list.shtml",  # 劳动关系 > 调解仲裁
        "https://rst.xinjiang.gov.cn/xjrst/c112754/list.shtml",  # 劳动关系 > 劳动监察
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
                Field('detail_urls','//div[@class="r-box"]/ul/li/a[1]/@href',[], type="xpath"),
                Field('publish_times','//div[@class="r-box"]/ul/li/span[2]/span[1]/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r'createPageHTML\(\'page_div\',(\d+),')],type="xpath"),
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
                       '//div[@class="clearfix1 bc-nav-wp "]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//ul[@class="clearfix1 ccp-info-list"]/li[2]/div[@class="cil-box"]/span[@class="cil-t"]/text()',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="article-detail"]//p',
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
                       '//div[@class="article-detail"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="article-detail"]//p//a//text()',
                       [], type='xpath', file_category='attachment'),

             ])]]
