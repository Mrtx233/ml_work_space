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


# ===================== XPath 常量 =====================
LIST_XPATH = {
    'detail_urls': '//*[@class="float-right opgo_r"]//li/a/@href',
    'publish_times': '//*[@class="float-right opgo_r"]//li/a//time/text()',
    'next_page': '//span[@class="p_pages"]/span[last()-1]/a/@href',
    'total_page': '//span[@class="p_pages"]/span[last()-2]/a/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//p[@class="ncom_tit margin-bottom"]//a/text()',
    'content': '//div[contains(@class, "v_news_content")]//p',
    'attachment': '//div[contains(@class, "v_news_content")]//p//a/@href',
    'attachment_name': '//div[contains(@class, "v_news_content")]//p//a/text()',

    "indexnumber": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[2]/text()',
    "fileno": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[4]/text()',
    "category": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[4]/text()',
    "issuer": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[2]/text()',
    "status": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[2]/td[6]/text()',
    "writtendate": '//div[@class="govinfo_index mg20 lh24 font14"]//tr[1]/td[6]/text()',
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_date': '\\d{4}-\\d{1,2}-\\d{1,2}',
    # 'total_page': 'var maxPageItems = "(\\\\d+)";',
    # 'publish_time': '\\\\s*(\\\\d{4}-\\\\d{2}-\\\\d{2})',
    # 'source': '\\\\s*([^\\\\n\\\\s]+)',
}


class SfjJzGovCnSpider(BasePortiaSpider):
    name = "sfj_jz_gov_cn"
    allowed_domains = ["sfj.jz.gov.cn"]

    start_urls = [
        "https://sfj.jz.gov.cn/zwgk/bszn.htm",
        "https://sfj.jz.gov.cn/zwgk/sfxzdt.htm",
        "https://sfj.jz.gov.cn/zwgk/tzgsgg.htm",
        "https://sfj.jz.gov.cn/fzjs1/xzzfxdjd/xzzfjdgzxx.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jczt.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jcsxhyj.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jcpcsx.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jcbz.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jcjh.htm",
        "https://sfj.jz.gov.cn/fzjs1/sqxzjcgszl/jcws.htm",
        "https://sfj.jz.gov.cn/fzjs1/zflf/dfxfg.htm",
        "https://sfj.jz.gov.cn/fzjs1/xzfy/xz_flgd_zn.htm",
        "https://sfj.jz.gov.cn/fzjs1/xzfy/xzfyjdsgs.htm",
        "https://sfj.jz.gov.cn/fzjs1/zfflgw.htm",
        "https://sfj.jz.gov.cn/fzxc.htm",
        "https://sfj.jz.gov.cn/flfw1/lsfw.htm",
        "https://sfj.jz.gov.cn/flfw1/gzfw.htm",
        "https://sfj.jz.gov.cn/flfw1/flyz.htm",
        "https://sfj.jz.gov.cn/flfw1/flzyzg.htm",
        "https://sfj.jz.gov.cn/flbz1/sfjd.htm",
        "https://sfj.jz.gov.cn/flbz1/rmcyhcjfz.htm",
        "https://sfj.jz.gov.cn/flbz1/jdfc.htm",
        "https://sfj.jz.gov.cn/flbz1/sqjz.htm",
        "https://sfj.jz.gov.cn/dwjs1/lzjs.htm",
        "https://sfj.jz.gov.cn/dwjs1/dwjs.htm",
        "https://sfj.jz.gov.cn/dwjs1/rsgh.htm",
    ]

    # def make_url_base(self, page: int, base_url: str) -> str:
    #     base_url = re.sub(r'/index\.htm$', '', base_url)
    #     return f"{base_url}/index_{page + 1}.htm"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={
                    'base_url': url,
                #     'make_url_name': 'make_url_base',
                #     'use_custom_pagination': True
                }
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field(
                    'publish_times',
                    LIST_XPATH["publish_times"],
                    [Regex(REGEX["publish_date"])],
                    type="xpath"
                ),
                Field('next_page', LIST_XPATH["next_page"], [], type="xpath"),
                Field(
                    'total_page',
                    LIST_XPATH["total_page"],
                    [],
                    type="xpath"
                ),
            ]
        )
    ]]

    # ===================== 详情页配置 =====================
    items = [[
        Item(
            HbeaItem,
            None,
            'body',
            [
                Field('title', DETAIL_XPATH["title"], [], required=False, type='xpath'),

                Field(
                    'publish_time',
                    DETAIL_XPATH["publish_time"],
                    [],
                    type='xpath'
                ),

                Field(
                    'menu',
                    DETAIL_XPATH["menu"],
                    [Text(), Join(separator='>')],
                    type="xpath"
                ),

                Field(
                    'source',
                    DETAIL_XPATH["source"],
                    [],
                    type='xpath',
                    file_category='source'
                ),

                Field(
                    'content',
                    DETAIL_XPATH["content"],
                    [
                        lambda vals: [
                            html_str.strip()
                            .replace('&quot;', '"')
                            .replace('&amp;', '&')
                            for html_str in vals
                            if isinstance(html_str, str) and html_str.strip()
                        ],
                        lambda html_list: [
                            scrapy.Selector(text=html)
                            .xpath('string(.)')
                            .get()
                            .strip()
                            for html in html_list
                        ],
                        Join(separator='\n')
                    ],
                    required=False,
                    type='xpath'
                ),

                Field('attachment', DETAIL_XPATH["attachment"], [], type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], type='xpath', file_category='attachment'),
            ]
        )
    ]]
