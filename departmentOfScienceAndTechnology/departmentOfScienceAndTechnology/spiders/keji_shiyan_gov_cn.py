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
    'detail_urls': "//ul[@class='gl_list']/li/a/@href | //ul[@class='list-group']/li/a/@href",
    'publish_times': "//ul[@class='gl_list']/li/span/text() | //ul[@class='list-group']/li/span[1]/text()",
    'total_page': '//script/text()',
}

DETAIL_XPATH = {
    'title': '//meta[@name="ArticleTitle"]/@content',
    'publish_time': '//meta[@name="PubDate"]/@content',
    'source': '//meta[@name="ContentSource"]/@content',
    'menu': '//div[@class="position"]//a/text() | //ol[@class="breadcrumb"]/a/text()',
    'content': '//div[contains(@class, "TRS_UEDITOR")]//p',
    'attachment': '//div[contains(@class, "TRS_UEDITOR")]//p//a/@href | //div[@class="doc-content"]/div/p/a/@href',
    'attachment_name': '//div[contains(@class, "TRS_UEDITOR")]//p//a/text() | //div[@class="doc-content"]/div/p/a/text()',
    'indexnumber': "//div[@class='doc-title']/div/div[1]/div/div[2]/text()",
    'fileno': "//div[@class='doc-title']/div/div[5]/div/div[2]/text()",
    'category': "//div[@class='doc-title']/div/div[2]/div/div[2]/text()",
    'issuer': "//div[@class='doc-title']/div/div[4]/div/div[2]/text()",
    'writtendate': "//div[@class='doc-title']/div/div[3]/div/div[2]/text()",
}


# ===================== Regex 常量 =====================
REGEX = {
    'publish_times': r"\d{4}-\d{1,2}-\d{1,2}",
    'total_page': r'createPageHTML\(\s*["\']?(\d+)["\']?\s*,',
}


class KejiShiyanGovCnSpider(BasePortiaSpider):
    name = "keji_shiyan_gov_cn"
    allowed_domains = ["keji.shiyan.gov.cn"]

    start_urls = [
        "http://keji.shiyan.gov.cn/xwzx/",
        "http://keji.shiyan.gov.cn/xwzx/tpxw/",
        "http://keji.shiyan.gov.cn/xwzx/xsqdt/",
        "http://keji.shiyan.gov.cn/xwzx/tzgg/",
        "http://keji.shiyan.gov.cn/wsbs/bdxz/",
        "http://keji.shiyan.gov.cn/wsbs/dczj/",
        "http://keji.shiyan.gov.cn/gzhd/",
        "http://keji.shiyan.gov.cn/zcfg/syskjzcfg/",
        "http://keji.shiyan.gov.cn/ztzl/qzftnl/",
        "http://keji.shiyan.gov.cn/ztzl/ddmf/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/jddh_32506/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/gzjb_32507/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/stzt_32509/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/xjdx_32511/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/gzdt_32513/",
        "http://keji.shiyan.gov.cn/ztzl/lzjz/gzbs_32514/",
        "http://keji.shiyan.gov.cn/ztzl/lxyz/gzdt_32526/",
        "http://keji.shiyan.gov.cn/ztzl/lxyz/ztjb_32517/",
        "http://keji.shiyan.gov.cn/ztzl/lxyz/xxfd_32519/",
        "http://keji.shiyan.gov.cn/ztzl/lxyz/apbs_32521/",
        "http://keji.shiyan.gov.cn/ztzl/lxyz/dzdg_32523/",
        "http://keji.shiyan.gov.cn/ztzl/kjglfwjstjj/",
        "http://keji.shiyan.gov.cn/ztzl/skjjcxgczt_32527/zwcx_32532/",
        "http://keji.shiyan.gov.cn/ztzl/skjjcxgczt_32527/hhbfb_32530/",
        "http://keji.shiyan.gov.cn/ztzl/skjjcxgczt_32527/cxwh_32531/",
        "http://keji.shiyan.gov.cn/ztzl/skjjcxgczt_32527/syhrb_32529/",
        "http://keji.shiyan.gov.cn/ztzl/skjjcxgczt_32527/cxgs_32528/",
        "http://keji.shiyan.gov.cn/ztzl/syssztjy_32533/zypl_32539/",
        "http://keji.shiyan.gov.cn/ztzl/syssztjy_32533/xxfd_32541/",
        "http://keji.shiyan.gov.cn/ztzl/syssztjy_32533/zxdt_32542/",
        "http://keji.shiyan.gov.cn/ztzl/syssztjy_32533/wjjs_32543/",
        "http://keji.shiyan.gov.cn/ztzl/skjjddqzlxjysjhd_32552/gzjb_32558/",
        "http://keji.shiyan.gov.cn/ztzl/skjjddqzlxjysjhd_32552/xxjl_32560/",
        "http://keji.shiyan.gov.cn/ztzl/skjjddqzlxjysjhd_32552/zlhb_32561/",
        "http://keji.shiyan.gov.cn/ztzl/skjjddqzlxjysjhd_32552/xxzl_32562/",
        "http://keji.shiyan.gov.cn/ztzl/skjjddqzlxjysjhd_32552/hddt_32563/",
        "http://keji.shiyan.gov.cn/ztzl/2012ndskjjmzpyxf_32570/gzjb_32572/",
        "http://keji.shiyan.gov.cn/ztzl/2012ndskjjmzpyxf_32570/dtxx_32573/",
        "http://keji.shiyan.gov.cn/ztzl/2012ndskjjmzpyxf_32570/xgwj_32574/",
        "http://keji.shiyan.gov.cn/ztzl/zywzwmzxd_32580/xgwjjxxnr_32581/",
        "http://keji.shiyan.gov.cn/ztzl/zywzwmzxd_32580/zywzgzdt_32582/",
        "http://keji.shiyan.gov.cn/ztzl/zywzwmzxd_32580/ldjhjs_32583/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/mryw_32587/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/wmly_32588/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/zssc_32589/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/cjdt_32590/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/xgwj_32592/",
        "http://keji.shiyan.gov.cn/ztzl/skjjwclczt_32584/gcsd_32593/",
        "http://keji.shiyan.gov.cn/ztzl/qskjcxjldh_32594/dtxx_32596/",
        "http://keji.shiyan.gov.cn/ztzl/qskjcxjldh_32594/jlfycl_32597/",
        "http://keji.shiyan.gov.cn/ztzl/qskjcxjldh_32594/xgwj_32599/",
        "http://keji.shiyan.gov.cn/ztzl/qskjcxjldh_32594/ldjh_32601/",
        "http://keji.shiyan.gov.cn/ztzl/skjjzxcywgjshdzt_32605/cyhddt_32606/",
        "http://keji.shiyan.gov.cn/ztzl/skjjzxcywgjshdzt_32605/cydydh_32607/",
        "http://keji.shiyan.gov.cn/ztzl/nsbdzxgcsyqjsybhkjzt_32612/",
        "http://keji.shiyan.gov.cn/ztzl/xds/",
        "http://keji.shiyan.gov.cn/kjjxxgk/zc/gfxwj/",
        "http://keji.shiyan.gov.cn/kjjxxgk/zc/qtzdgkwj/",
        "http://keji.shiyan.gov.cn/kjjxxgk/zc/zcfgjgfxwj_776/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/ghjh_780/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/tjxx/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/xkfw/xkjg/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/czzj_784/czys/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/czzj_784/czjs/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/zfcg/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/zkly/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jcygk/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2025/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2024/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2023/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2022/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2020/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2019/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/rdjy/2018/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/zwdc/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/sjbg/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/zfhy/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/hygq/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/zczxjlsqk/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qxbldzmsxqd/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2025/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2024/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2023/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2022/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2021/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2020/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2019/",
        "http://keji.shiyan.gov.cn/kjjxxgk/sfgwgkml/qtzdgknr/jyhtabl/zxta/2018/"
    ]

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{base_url.rstrip('/')}/index_{page}.shtml"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {url}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
                Field('detail_urls', LIST_XPATH["detail_urls"], [], type="xpath"),
                Field('publish_times', LIST_XPATH["publish_times"], [Regex(REGEX["publish_times"])], type="xpath"),
                Field('total_page', LIST_XPATH["total_page"], [Regex(REGEX["total_page"])], type="xpath"),
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
                Field('publish_time', DETAIL_XPATH["publish_time"], [], required=False, type='xpath'),
                Field('source', DETAIL_XPATH["source"], [], required=False, type='xpath'),
                Field('menu', DETAIL_XPATH["menu"], [Text(), Join(separator='>')], type="xpath"),
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
                Field('attachment', DETAIL_XPATH["attachment"], [], required=False, type='xpath', file_category='attachment'),
                Field('attachment_name', DETAIL_XPATH["attachment_name"], [], required=False, type='xpath', file_category='attachment'),
                Field('indexnumber', DETAIL_XPATH["indexnumber"], [], required=False, type='xpath'),
                Field('fileno', DETAIL_XPATH["fileno"], [], required=False, type='xpath'),
                Field('category', DETAIL_XPATH["category"], [], required=False, type='xpath'),
                Field('issuer', DETAIL_XPATH["issuer"], [], required=False, type='xpath'),
                Field('writtendate', DETAIL_XPATH["writtendate"], [], required=False, type='xpath'),
            ]
        )
    ]]
