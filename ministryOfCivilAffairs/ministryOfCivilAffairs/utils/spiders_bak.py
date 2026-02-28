from time import sleep

from scrapy import Request
from scrapy.loader import ItemLoader
from scrapy.spiders import CrawlSpider
from scrapy.utils.response import get_base_url
from itemloaders.processors import Identity, Join
import datetime
import crawlab
import re

# Spider Module
class RequiredFieldMissing(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class PortiaItemLoader(ItemLoader):
    def get_value(self, value, *processors, **kw):
        required = kw.pop('required', False)
        val = super(PortiaItemLoader, self).get_value(value, *processors, **kw)
        if required and not val:
            raise RequiredFieldMissing(
                'Missing required field "{value}" for "{item}"'.format(
                    value=value, item=self.item.__class__.__name__))
        return val
    # def get_output_processor(self, field_name):
    #     # 当前业务固定字段，仅附件需要保留列表,正文列表形式以换行符连接，后续可根据需要调整
    #     keep_list_fields = {'urls', 'attachment', 'attachments', 'images', 'attachment_name', 'detail_urls', 'publish_times'}
    #     if field_name in keep_list_fields:
    #         return Identity()
    #     return Join(separator='\n')


class BasePortiaSpider(CrawlSpider):
    loader = PortiaItemLoader
    items = []

    def __init__(self, target_date=None, **kwargs):
        super().__init__(**kwargs)
        self.input_list = target_date if target_date else []
        self.start_date = None
        self.end_date = None
        self._parse_dates()

    def _parse_dates(self):
        try:
            if len(self.input_list) == 1:
                self.start_date = datetime.datetime.strptime(self.input_list[0], '%Y-%m-%d')
                self.logger.info(f"日期筛选模式：≥ {self.start_date.strftime('%Y-%m-%d')}")
            elif len(self.input_list) == 2:
                date1 = datetime.datetime.strptime(self.input_list[0], '%Y-%m-%d')
                date2 = datetime.datetime.strptime(self.input_list[1], '%Y-%m-%d')
                self.start_date = min(date1, date2)
                self.end_date = max(date1, date2)
                self.logger.info(
                    f"日期筛选模式：区间 [{self.start_date.strftime('%Y-%m-%d')}, {self.end_date.strftime('%Y-%m-%d')}]")
            else:
                self.logger.info("日期筛选模式：未启用，仅执行Crawlab去重")
        except ValueError as e:
            self.start_date = None
            self.end_date = None
            self.logger.error(f"日期解析失败！输入参数：{self.input_list}，错误原因：{str(e)} → 关闭日期筛选，仅执行去重")

    def _check_single_url(self, url):
            """
            检查单个URL是否存在于mongo数据库中
            """
            try:
                filter_payload = crawlab.FilterResultPayload(query={"src_url": url})
                result = crawlab.filter_item(filter_payload)

                if result:
                    return True
                return False
            except Exception as e:
                self.logger.error(f'检查URL异常: {e}')
                return False

    def parse_list(self, response ,current_page=1, repeat_dup_pages=0):
        """
        新增列表页解析
        允许为空
        """
        for sample in getattr(self, 'list_items', []):
            for definition in sample:
                detail_urls = []
                publish_times = []
                current_page = current_page
                total_page = None
                next_page = None
                task_num = 0


                for result in self.load_item(definition, response):

                    if result.get("detail_urls"):
                        for url in result["detail_urls"]:
                            detail_urls.append(response.urljoin(url))

                    if result.get("publish_times"):
                        for publish_time in result["publish_times"]:
                            publish_times.append(publish_time)

                    if result.get("next_page"):
                        next_page = response.urljoin(result["next_page"])

                    if result.get("total_page"):
                        total_page = result["total_page"]

                max_len = max(len(detail_urls), len(publish_times))
                combined = [
                    (
                        detail_urls[i] if i < len(detail_urls) else "",
                        publish_times[i] if i < len(publish_times) else "",
                    )
                    for i in range(max_len)
                ]
                # 发送详情页请求
                for url, pub_time in combined:
                    if url:

                        pub_time = datetime.datetime.strptime(self.extract_date(pub_time), '%Y-%m-%d')
                        cutoff_date_str = self.settings.get('CUTOFF_DATE', '2025-12-1')
                        incremental_mode = self.settings.get('INCREMENTAL_MODE', True)

                        try:
                            cutoff = datetime.datetime.strptime(cutoff_date_str, '%Y-%m-%d')
                        except ValueError:
                            self.logger.warning(f"截止时间格式错误，使用默认值 2025-12-1")
                            cutoff = datetime.datetime(2025, 12, 1)

                        if incremental_mode and pub_time and pub_time < cutoff:
                            self.logger.info(f"{pub_time} 超出范围，跳过")
                            continue

                        if self._check_single_url(url):
                            self.logger.info(f"{url} 已爬取，跳过")
                            continue
                        task_num += 1
                        yield Request(url, callback=self.parse_item)

                self.logger.info(
                    f"[LIST] 当前页爬取任务数：{task_num},  当前页总任务数：{len(combined)}"
                )
                self.logger.info(
                    f"[LIST] 当前页：{current_page}, 总页数：{total_page}"
                )
                # 统计连续重复页
                if task_num == 0:
                    repeat_dup_pages += 1
                else:
                    repeat_dup_pages = 0

                if repeat_dup_pages >= 3:
                    self.logger.info(f"[LIST] 连续{repeat_dup_pages}页均为重复数据，停止翻页")
                    return
                # 下一页
                if next_page:
                    self.logger.info(f"[LIST] 翻页 -> {next_page}")
                    yield Request(next_page, callback=self.parse_list, cb_kwargs={'current_page': current_page + 1, 'repeat_dup_pages': repeat_dup_pages})


    # 解析详情页
    def parse_item(self, response):

        for sample in self.items:
            items = []
            current_definition = None
            try:
                for definition in sample:
                    self.logger.debug(f"Processing definition: {definition}")
                    current_definition = definition
                    items.extend([i for i in self.load_item(definition, response)])
            except RequiredFieldMissing as exc:
                self.logger.warning(str(exc))
            if items and current_definition:
                for item in items:
                    # 为每个item添加页面HTML源码和URL信息
                    item['_response_html'] = response.text
                    current_url = response.url
                    item['_response_url'] = current_url

                    time_value = item.get('publish_time','')
                    if isinstance(time_value, list):
                        time_value = " ".join(time_value)
                    if self.start_date:
                        try:
                            now_date = datetime.datetime.strptime(self.extract_date(time_value), '%Y-%m-%d')
                        except ValueError:
                            self.logger.error(f"URL：{current_url} 提取的日期格式错误：{time_value} → 跳过")
                            continue
                        if self.end_date:
                            if not (self.start_date <= now_date <= self.end_date):
                                self.logger.info(f"{now_date}超出范围 → 跳过")
                                continue
                        else:
                            if not (self.start_date <= now_date):
                                self.logger.info(f"{now_date}超出范围 → 跳过")
                                continue
                    else:
                        if self._check_single_url(current_url):
                            self.logger.info(f"{current_url} 存在于数据库，跳过")
                            continue

                        # filter_payload = crawlab.FilterResultPayload(
                        #     query={"src_url": current_url}
                        # )
                        # result = crawlab.filter_item(filter_payload)
                        # if result:
                        #     self.logger.info(f"{current_url} 存在于数据库 → 跳过")
                        #     continue
                    # 收集text类型字段的数据，用于生成主文档
                    text_content = self._collect_text_content(item, current_definition)
                    if text_content:
                        item['_text_content_for_doc'] = text_content

                    # 收集字段的file_category信息，用于Pipeline判断文件下载类型
                    field_categories = self._collect_field_categories(item, current_definition)
                    if field_categories:
                        item['_field_categories'] = field_categories

                    yield item
                break

    def extract_date(self, text):
        """从文本中提取日期（支持多种格式）"""

        # 新增：匹配时间戳
        text = text.strip()
        if re.fullmatch(r'\d{10,13}', text):
            ts = int(text)
            if len(text) == 13:
                ts = ts / 1000
            dt = datetime.datetime.fromtimestamp(ts)
            return dt.strftime('%Y-%m-%d')

        # 匹配：YYYY-MM-DD、YYYY/MM/DD、YYYY年MM月DD日、YYYY.MM.DD、YYYYMMDD
        match = re.search(
            r'(\d{4})[-/年.](\d{1,2})[-/月.](\d{1,2})[日]?|(\d{4})(\d{2})(\d{2})',
            text
        )
        if match:
            # 处理第一种格式（YYYY-MM-DD等）
            if match.group(1):
                year, month, day = match.group(1), match.group(2), match.group(3)
            # 处理YYYYMMDD格式
            else:
                year, month, day = match.group(4), match.group(5), match.group(6)
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"  # 补零并统一格式
        return ''  # 如果没有匹配到任何格式，返回空字符串

    def _collect_text_content(self, item, definition):
        text_parts = []

        # 遍历字段定义，找到text类型的字段
        for field in definition.fields:
            if hasattr(field, 'fields'):
                # 嵌套字段，递归处理
                nested_content = self._collect_text_content(item, field)
                if nested_content:
                    text_parts.append(nested_content)
            else:
                # 检查字段类型和处理器
                if self._is_text_field(field):
                    field_value = item.get(field.name, '')
                    if field_value:
                        if isinstance(field_value, (list, tuple)):
                            # 如果是列表，每个元素一行
                            for value in field_value:
                                if value:
                                    text_parts.append(str(value))
                        else:
                            text_parts.append(str(field_value))

        return '\n'.join(text_parts)

    def _is_text_field(self, field):
        # 检查字段是否有text相关的处理器
        text_processors = ['Text', 'SafeHtml', 'Regex']

        for processor in field.processors:
            processor_name = processor.__class__.__name__
            if processor_name in text_processors:
                return True

        # 如果没有处理器，默认认为是text类型
        if not field.processors:
            return True

        return False

    def _collect_field_categories(self, item, definition):
        field_categories = {}

        # 遍历字段定义，收集字段的file_category信息
        for field in definition.fields:
            if hasattr(field, 'fields'):
                # 嵌套字段，递归处理
                nested_categories = self._collect_field_categories(item, field)
                field_categories.update(nested_categories)
            else:
                # 检查字段是否有file_category属性
                field_name = field.name
                if field_name and field_name in item:
                    # 获取字段的file_category，默认为空
                    file_category = getattr(field, 'file_category', '')
                    field_categories[field_name] = file_category

        return field_categories

    def load_item(self, definition, response=None, selector=None):
        if selector is None:
            selector = response
        if selector is None:
            return
            
        query = selector.xpath if definition.type == 'xpath' else selector.css


        selectors = query(definition.selector)

        for selector in selectors:
            if selector is None:
                continue
            ld = self.loader(
                item=definition.item(), selector=selector, response=response,
                baseurl=get_base_url(response) if response else '')
            for field in definition.fields:
                if hasattr(field, 'fields'):
                    if field.name is not None:
                        ld.add_value(field.name, self.load_item(field, response, selector))
                elif field.type == 'xpath':
                    ld.add_xpath(field.name, field.selector, *field.processors, required=field.required)
                else:
                    ld.add_css(field.name, field.selector, *field.processors, required=field.required)
            yield ld.load_item()
