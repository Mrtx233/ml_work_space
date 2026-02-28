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

class RstGuizhouGovCnSpider(BasePortiaSpider):
    name = "rst_guizhou_gov_cn"
    allowed_domains = ["rst.guizhou.gov.cn"]
    start_urls = [
        "https://rst.guizhou.gov.cn/xwzx/xwdt/index.html",  # 首页 > 新闻中心 > 新闻动态
        "http://rst.guizhou.gov.cn/xwzx/szdt/index.html",  # 首页 > 新闻中心 > 市州动态
        "https://rst.guizhou.gov.cn/xwzx/gggs/index.html",  # 首页 > 新闻中心 > 公告公示
        "https://rst.guizhou.gov.cn/zwgk/jdhy/zcwj/index.html",  # 首页 > 政务公开 > 政策文件 > 政策文件
        "https://rst.guizhou.gov.cn/zwgk/jdhy/zcjd/index.html",  # 首页 > 政务公开 > 政策文件 > 政策解读
        "https://rst.guizhou.gov.cn/zwgk/jdhy/gfxwjqlxx/index.html",  # 首页 > 政务公开 > 政策文件 > 规范性文件清理信息
        "https://rst.guizhou.gov.cn/zwgk/hmzcmbk/shbz/index.html",  # 首页 > 政务公开 > 惠企利民政策明白卡 > 社会保障
        "https://rst.guizhou.gov.cn/zwgk/hmzcmbk/jy/index.html",  # 首页 > 政务公开 > 惠企利民政策明白卡 > 就业
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/ldgx_5750859/index.html",  # 首页 > 政务公开 > 重点领域信息 > 劳动关系
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/wgjy/index.html",  # 首页 > 政务公开 > 重点领域信息 > 稳岗就业
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/cjjyzl/ncldlzyjy/index.html",  # 首页 > 政务公开 > 重点领域信息 > 促进就业专栏 > 就业创业服务
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/cjjyzl/gxbysjy/index.html",  # 首页 > 政务公开 > 重点领域信息 > 促进就业专栏 > 高校毕业生就业
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/rcdwjs_5750847/index.html",  # 首页 > 政务公开 > 重点领域信息 > 人才队伍建设
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/jyjrcfw/zyjnjdjg/index.html",  # 首页 > 政务公开 > 重点领域信息 > 就业及人才服务 > 职业技能鉴定机构
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/jyjrcfw/gzsjgxxtxl/index.html",  # 首页 > 政务公开 > 重点领域信息 > 就业及人才服务 > 贵州省技工学校通讯录
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/jyjrcfw/qzzpxx/index.html",  # 首页 > 政务公开 > 重点领域信息 > 就业及人才服务 > 求职招聘信息
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/zyjszcpp/zyjszwps/index.html",  # 首页 > 政务公开 > 重点领域信息 > 专业技术职称评聘 > 专业技术职务评审
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/zyjszcpp/zyjszwpy/index.html",  # 首页 > 政务公开 > 重点领域信息 > 专业技术职称评聘 > 专业技术职务聘用
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/sydwgkzp/index.html",  # 首页 > 政务公开 > 重点领域信息 > 事业单位公开招聘
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/zh_5766700/index.html",  # 首页 > 政务公开 > 重点领域信息 > 综合
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/sbxx/index.html",  # 首页 > 政务公开 > 重点领域信息 > 社保信息
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/gsbxgl/index.html",  # 首页 > 政务公开 > 重点领域信息 > 工伤保险管理
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/qsldrszyzcjg/index.html",  # 首页 > 政务公开 > 重点领域信息 > 全省劳动人事争议仲裁机构
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/ldjc/index.html",  # 首页 > 政务公开 > 重点领域信息 > 劳动监察
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/jlbzgl/index.html",  # 首页 > 政务公开 > 重点领域信息 > 奖励表彰管理
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/jgsydwylbxzdgg/index.html",  # 首页 > 政务公开 > 重点领域信息 > 职工养老保险
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/nmggzgl/index.html",  # 首页 > 政务公开 > 重点领域信息 > 农民工工作管理
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/czxx/index.html",  # 首页 > 政务公开 > 重点领域信息 > 财政信息
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/rlzyfwjgml/index.html",  # 首页 > 政务公开 > 重点领域信息 > 人力资源市场管理
        "https://rst.guizhou.gov.cn/zwgk/zdlyxx/zyjntsxdzcfg/index.html",  # 首页 > 政务公开 > 重点领域信息 > 职业能力建设管理
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
                Field('detail_urls','//div[@class="right-list-box"]/ul//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="right-list-box"]/ul//span/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
                # 翻页url
                # Field('next_page', '//*[@id="page_div"]/div[8]/span/a/@href', [], type="xpath"),
                # 规范抓取总页数
                Field('total_page', '//script/text()', [Regex(r"createPageHTML\((\d+)")],type="xpath"),
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
                       '//div[@class="dqwz"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="Article_zw"]//p',
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
                       '//div[@class="trs_editor_view TRS_UEDITOR trs_paper_default trs_word"]//p//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="trs_editor_view TRS_UEDITOR trs_paper_default trs_word"]//p//a//text()',
                       [], type='xpath', file_category='attachment'),
                 #
                 # Field('status',
                 #       '//div[@class="maincon-info"]/div[5]/div[1]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       '//div[@class="maincon-info"]/div[1]/div[2]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       '//div[@class="maincon-info"]/div[3]/div[1]/text()',
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       '//div[@class="maincon-info"]/div[1]/div[1]/text()',
                 #       [], required=False, type='xpath'),

             ])]]
