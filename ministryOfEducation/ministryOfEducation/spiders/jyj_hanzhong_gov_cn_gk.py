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

# ===================== 抽离的XPath常量（核心改造） =====================
# 列表页XPath
LIST_XPATH = {
    "detail_urls": '//div[@class="listZhian"]//ul//a/@href',  # 详情页链接
    "publish_times": '//div[@class="listZhian"]//ul//span/text()',  # 发布时间
    # "next_page": '//div[@class="xy-page mt40 mb40"]//a[@class="pagenext"]/@href',
    "total_page": '//div[@class="listZhian"]//ul//script/text()'  # 总页数
}

# 详情页XPath
DETAIL_XPATH = {
    "title": '//meta[@name="ArticleTitle"]/@content',  # 标题
    "publish_time": '//meta[@name="PubDate"]/@content',  # 发布时间
    # "menu": '//div[@class="dqwz_content"]//a/text()',  # 面包屑菜单
    "source": '//table[@class="xxgk_table"]//tr[2]/td[2]/text()',  # 来源
    "content": '//div[@class="wz_zoom  scroll_cont ScrollStyle"]//p',  # 正文内容
    "attachment": '//div[@class="wz_zoom  scroll_cont ScrollStyle"]//p//a/@href',  # 附件链接
    "attachment_name": '//div[@class="wz_zoom  scroll_cont ScrollStyle"]//p//a/text()',  # 附件名称
    "indexnumber": '//table[@class="xxgk_table"]//tr[1]/td[2]/text()',
    # "fileno": '//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[2]/text()',
    # "category": '//table[@class="cm-table-fixed szf_zw-table"]//tr[1]/td[2]/text()',
    "issuer": '//table[@class="xxgk_table"]//tr[2]/td[4]/text()',
    # "status": '//table[@class="cm-table-fixed szf_zw-table"]//tr[3]/td[1]/text()',
    "writtendate": '//table[@class="xxgk_table"]//tr[1]/td[4]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class JyjHanzhongGovCnGkSpider(BasePortiaSpider):
    name = "jyj_hanzhong_gov_cn_gk"
    allowed_domains = ["jyj.hanzhong.gov.cn"]
    start_urls = [
        "https://jyj.hanzhong.gov.cn/hzsjyjx/gknr/xxgk_gknb_list.shtml",  # 政府信息公开指南
        "https://jyj.hanzhong.gov.cn/hzsjyjx/jgzn/xxgk_gknb_list.shtml",  # 机构职能
        "https://jyj.hanzhong.gov.cn/hzsjyjx/rsxx/xxgk_gknb_list.shtml",  # 人事信息
        "https://jyj.hanzhong.gov.cn/hzsjyjx/zcfg/xxgk_list.shtml",  # 政策法规
        "https://jyj.hanzhong.gov.cn/hzsjyjx/czyjs/xxgk_gknb_list.shtml",  # 财政预决算
        "https://jyj.hanzhong.gov.cn/hzsjyjx/wjtz/xxgk_gknb_list.shtml",  # 文件通知
        "https://jyj.hanzhong.gov.cn/hzsjyjx/xzzf/xxgk_gknb_list.shtml",  # 行政执法
        "https://jyj.hanzhong.gov.cn/hzsjyjx/gfxwj/xxgk_gknb_list.shtml",  # 规范性文件
        "https://jyj.hanzhong.gov.cn/hzsjyjx/jcygk/xxgk_gknb_list.shtml",  # 决策预公开
        "https://jyj.hanzhong.gov.cn/hzsjyjx/czyjsa/xxgk_gknb_list.shtml",  # 六稳六保
        "https://jyj.hanzhong.gov.cn/hzsjyjx/czyjsb/xxgk_gknb_list.shtml",  # 建议、提案公开专栏
        "https://jyj.hanzhong.gov.cn/hzsjyjx/gsgg/xxgk_gknb_list.shtml",  # 公示公告
        "https://jyj.hanzhong.gov.cn/hzsjyjx/ssjccsx/xxgk_gknb_list.shtml",  # 信用＋双随机、一公开
        "https://jyj.hanzhong.gov.cn/hzsjyjx/dczj/xxgk_gknb_list.shtml",  #调查征集
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return base_url.replace(".shtml", f"_{page + 1}.shtml")

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(url, callback=self.parse_list,
                          # cb_kwargs={'base_url': url})
            cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True})

    # 列表页配置：引用LIST_XPATH变量
    list_items = [[
        Item(ListItems,
             None,
             'body',
             [
                 Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                 Field('publish_times',LIST_XPATH["publish_times"], [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type="xpath"),
                 # Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r'createPageHTML\(\'page_div\',(\d+),')], type="xpath"),
             ])]]

    # 详情页配置：引用DETAIL_XPATH变量
    items = [[
        Item(AgriItem,
             None,
             'body',
             [
                 Field('title',
                       DETAIL_XPATH["title"],
                       [], required=True, type='xpath'),

                 Field('publish_time',
                       DETAIL_XPATH["publish_time"],
                       [Regex('\\d{4}-\\d{1,2}-\\d{1,2}')], type='xpath'),

                 # Field('menu',
                 #       DETAIL_XPATH["menu"],
                 #       [Text(), Join(separator='>')],type="xpath"),

                 Field('source',
                       DETAIL_XPATH["source"],
                       [], type='xpath', file_category='source'),

                 Field('content',
                       DETAIL_XPATH["content"],
                       [
                           lambda vals: [
                               html_str.strip().replace('&quot;', '"').replace('&amp;', '&')
                               for html_str in vals
                               if isinstance(html_str, str) and html_str.strip()
                           ],
                           lambda html_list: [
                               scrapy.Selector(text=html).xpath('string(.)').get().strip()
                               for html in html_list
                           ], Join(separator='\n')], required=False, type='xpath'),

                 Field('attachment',
                       DETAIL_XPATH["attachment"],
                       [], type='xpath', file_category='attachment'),

                 Field('attachment_name',
                       DETAIL_XPATH["attachment_name"],
                       [], type='xpath', file_category='attachment'),

                 Field('indexnumber',
                       DETAIL_XPATH["indexnumber"],
                       [], required=False, type='xpath'),

                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),

                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),

                 Field('issuer',
                       DETAIL_XPATH["issuer"],
                       [], required=False, type='xpath'),

                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),

                 Field('writtendate',
                       DETAIL_XPATH["writtendate"],
                       [], required=False, type='xpath'),

             ])]]