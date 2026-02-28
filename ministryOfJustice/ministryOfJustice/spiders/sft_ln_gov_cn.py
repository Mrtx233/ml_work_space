from __future__ import absolute_import

import scrapy
import re
from scrapy import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, Join
from scrapy.spiders import Rule

from ..items import ListItems, HbeaItem
from ..utils.spiders import BasePortiaSpider
from ..utils.starturls import FeedGenerator, FragmentGenerator
from ..utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex

# ===================== 抽离的XPath常量（核心改造） =====================
# 列表页XPath
LIST_XPATH = {
    'detail_urls': '//*[@class="listBox"]//li/a/@href',
    'publish_times': '//*[@class="listBox"]//li/span/text()',
    'next_page': '//div[@class="jspIndex4"]/a[last()]/@href',
    'total_page': '//*[@class="easysite-total-page"]//span/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="currbox"]//a/text()',
    'content': '//div[contains(@class, "TRS_Editor")]//p',
    'attachment': '//div[contains(@class, "TRS_Editor")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "TRS_Editor")]//p//a/text()',
    # "indexnumber": '//div[@class="article"]/table[1]/tbody/tr[1]/td[1]/text()',
    # "fileno": '//div[@class="article"]/table[1]/tbody/tr[3]/td[2]/text()',
    # "category": '//div[@class="article"]/table[1]/tbody/tr[4]/td[1]/text()',
    # "issuer": '//div[@class="article"]/table[1]/tbody/tr[2]/td[1]/text()',
    # "status": '//div[@class="article"]/table[1]/tbody/tr[4]/td[2]/text()',
    # "writtendate": '//div[@class="article"]/table[1]/tbody/tr[1]/td[2]/text()',
}

# ===================== 爬虫逻辑（仅引用变量，无其他修改） =====================
class SftLnGovCnSpider(BasePortiaSpider):
    name = "sft_ln_gov_cn"
    allowed_domains = ["sft.ln.gov.cn"]
    start_urls = [
        # "https://sft.ln.gov.cn/sft/gcsy/f4541bf0-1.shtml",
        # "https://sft.ln.gov.cn/sft/qmyfzs/tszs/e534d12b-1.shtml",
        # "https://sft.ln.gov.cn/sft/qmyfzs/gzdt/28b1cf7e-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/zflf/bagz/4bba9aa8-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/xzsp/b41863ef-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/sqjz/7b56a3f3-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/xzfy/543c1bcf-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/zfflgw/jcfw/86ac24c8-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/zfflgw/xzys/3b8437bc-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/xzzfjd/xzzfjdgzxx/85401ad7-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/pfyyfzl/pfgz/6e8dcdc1-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/pfyyfzl/pfcp/17fcb812-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/rmcyhcjfz/0d945ea5-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/ggflfw/e67bd956-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/lsgz/c6a1d717-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/flzyzggl/f64a6b61-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/dwjs/gbrs/b7f4fd54-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/dwjs/jwgl/8a80d1bf-1.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/dwsxjs/2a660699-1.shtml",
        # "https://sft.ln.gov.cn/sft/hdjl/fggzzqyj/17efb89b-1.shtml",
        # "https://sft.ln.gov.cn/sft/qmyfzs/jgjj/index.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/zflf/xfsd/index.shtml",
        # "https://sft.ln.gov.cn/sft/ywgz/zflf/gzjd/index.shtml",

    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return re.sub(r"-\d+\.shtml$", f"-{page + 1}.shtml", base_url)


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
                 Field('total_page', LIST_XPATH["total_page"], [Regex(r"createPageHTML\('paging',(\d+),")], type="xpath"),
             ])]]

    # 详情页配置：引用DETAIL_XPATH变量
    items = [[
        Item(HbeaItem,
             None,
             'body',
             [
                 Field('title',
                       DETAIL_XPATH["title"],
                       [], required=False, type='xpath'),

                 Field('publish_time',
                       DETAIL_XPATH["publish_time"],
                       [Regex(r'时间：\s*(\d{4}-\d{2}-\d{2})')], type='xpath'),

                 Field('menu',
                       DETAIL_XPATH["menu"],
                       [Text(), Join(separator='>')],type="xpath"),

                 Field('source',
                       DETAIL_XPATH["source"],
                       [Regex(r'来源：\s*([^\n\s]+)')], type='xpath', file_category='source'),

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

                 # Field('indexnumber',
                 #       DETAIL_XPATH["indexnumber"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('fileno',
                 #       DETAIL_XPATH["fileno"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('category',
                 #       DETAIL_XPATH["category"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('issuer',
                 #       DETAIL_XPATH["issuer"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('status',
                 #       DETAIL_XPATH["status"],
                 #       [], required=False, type='xpath'),
                 #
                 # Field('writtendate',
                 #       DETAIL_XPATH["writtendate"],
                 #       [], required=False, type='xpath'),

             ])]]
