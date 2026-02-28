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

class RsjHaikouGovCnSpider(BasePortiaSpider):
    name = "rsj_haikou_gov_cn"
    allowed_domains = ["rsj.haikou.gov.cn"]
    start_urls = [
        "https://rsj.haikou.gov.cn/ywdt/zwdt/",  # 海口市人力资源和社会保障局 >> 要闻动态 >> 政务动态
        # "https://rsj.haikou.gov.cn/jdhy/zxjd/",  # 海口市人力资源和社会保障局 >> 解读回应 >> 最新解读
        # "https://rsj.haikou.gov.cn/jdhy/hygq/",  # 海口市人力资源和社会保障局 >> 解读回应 >> 回应关切
        # "https://rsj.haikou.gov.cn/xxgk/cwgk/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 财政公开
        # "https://rsj.haikou.gov.cn/xxgk/gsgg/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 公告公示
        # "https://rsj.haikou.gov.cn/xxgk/rsxx/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 人事信息
        # "https://rsj.haikou.gov.cn/xxgk/ghjh/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 规划计划
        # "https://rsj.haikou.gov.cn/xxgk/xxgkzd/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府信息公开制度
        # "https://rsj.haikou.gov.cn/xxgk/xxgkzn/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府信息公开指南
        # "https://rsj.haikou.gov.cn/xxgk/xxgkml/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府信息公开目录
        # "https://rsj.haikou.gov.cn/xxgk/xxgknb/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府信息公开年报
        # "https://rsj.haikou.gov.cn/xxgk/wzndbb/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府网站年度报表
        # "https://rsj.haikou.gov.cn/xxgk/jdjb/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 监督举报
        # "https://rsj.haikou.gov.cn/xxgk/xzxkhxzcf/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 行政许可和行政处罚
        # "https://rsj.haikou.gov.cn/xxgk/zfcg/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政府采购
        # "https://rsj.haikou.gov.cn/ztbd/sydwzp/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 事业单位招聘
        # "https://rsj.haikou.gov.cn/ztbd/zpxxfb/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 招聘信息发布
        # "https://rsj.haikou.gov.cn/ztbd/lwlb/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 六稳六保
        # "https://rsj.haikou.gov.cn/ztbd/shbzk/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 社会保障卡
        # "https://rsj.haikou.gov.cn/ztbd/jyzd/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 公共就业服务
        # "https://rsj.haikou.gov.cn/ztbd/cyzd/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 创业指导
        # "https://rsj.haikou.gov.cn/ztbd/xfaq/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 消防安全
        # "https://rsj.haikou.gov.cn/ztbd/xxjy/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 学习教育
        # "https://rsj.haikou.gov.cn/ztbd/zdlyxxgk/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 重点领域信息公开
        # "https://rsj.haikou.gov.cn/ztbd/zqbzgz/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 根治欠薪工作
        # "https://rsj.haikou.gov.cn/ztbd/ldjpf/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 国际劳动节普法宣传
        # "https://rsj.haikou.gov.cn/ztbd/srjdflz/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 市人社系统党风廉政建设
        # "https://rsj.haikou.gov.cn/ztbd/gsyf/",  # 海口市人力资源和社会保障局 >> 专题报道 >> 工伤预防
        # "https://rsj.haikou.gov.cn/xxgk/zcfg/bmzcwj/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政策文件 >> 部门政策文件
        # "https://rsj.haikou.gov.cn/xxgk/zcfg/fzxswn/",  # 海口市人力资源和社会保障局 >> 信息公开 >> 政策文件 >> 废止失效政策文件
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}{''  f'/index_{page +1}.shtml'}"

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
                Field('detail_urls','//div[@class="list_div"]/div//a/@href',[], type="xpath"),
                Field('publish_times','//div[@class="list_div"]//span[1]/text()',[Regex('\\d{4}-\\d{1,2}-\\d{1,2}')],type="xpath"),
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
                       '//div[@class="location"]//a/text()',
                       [Text(), Join(separator='>')],
                       required=False, type="xpath"),

                 Field('source',
                       '//meta[@name="ContentSource"]/@content',
                       [Regex(r'来源：\s*([^\s]+)')], type='xpath', file_category='source'),

                 Field('content',
                       '//div[@class="trs_editor_view TRS_UEDITOR trs_paper_default trs_web"]//p | //div[@class="TRS_Editor"]//p | //div[@class="con_cen line mar-t2 main-content"]//p',
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
                       '//div[@class="other-word"]//a/@href',
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       '//div[@class="other-word"]//a//text()',
                       [], type='xpath', file_category='attachment'),

                 Field('status',
                       '//div[@class="maincon-info"]/div[5]/div[1]/text()',
                       [], required=False, type='xpath'),

                 Field('fileno',
                       '//div[@class="maincon-info"]/div[1]/div[2]/text()',
                       [], required=False, type='xpath'),

                 Field('writtendate',
                       '//div[@class="maincon-info"]/div[3]/div[1]/text()',
                       [], required=False, type='xpath'),

                 Field('issuer',
                       '//div[@class="maincon-info"]/div[1]/div[1]/text()',
                       [], required=False, type='xpath'),

             ])]]
