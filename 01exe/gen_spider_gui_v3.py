import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse
import subprocess
import sys
import os
import re
import platform

# ===================== Spider 模板 =====================
SPIDER_TEMPLATE = """from __future__ import absolute_import

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
LIST_XPATH = {list_xpath}

DETAIL_XPATH = {detail_xpath}


{regex_section}


class {class_name}(BasePortiaSpider):
    name = "{spider_name}"
    allowed_domains = ["{allowed_domain}"]

    start_urls = {start_urls}

    def make_url_base(self, page: int, base_url: str) -> str:
        return f"{{base_url.rstrip('/')}}/index_{{page}}.html"

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"_start_url: {{url}}")
            yield Request(
                url,
                callback=self.parse_list,
                cb_kwargs={{'base_url': url, 'make_url_name': 'make_url_base', 'use_custom_pagination': True}}
            )

    # ===================== 列表页配置 =====================
    list_items = [[
        Item(
            ListItems,
            None,
            'body',
            [
{list_fields}
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
{detail_fields}
            ]
        )
    ]]
"""

# ===================== 默认字段 =====================
DEFAULT_LIST_FIELDS = {
    "detail_urls": '//*[@class="List_list"]//li/a/@href',
    "publish_times": '//*[@class="List_list"]//li/span/text()',
    "next_page": '',
    "total_page": '//div[@class="pagelarge"]/div/a[last()-1]/text()'
}

DEFAULT_DETAIL_FIELDS = {
    "title": '//meta[@name="ArticleTitle"]/@content',
    "publish_time": '//meta[@name="PubDate"]/@content',
    "source": '//meta[@name="ContentSource"]/@content',
    "menu": '//div[@class=""]//a/text()',
    "content": '//div[contains(@class, "")]//p',
    "attachment": '//div[contains(@class, "")]//p//a/@href',
    "attachment_name": '//div[contains(@class, "")]//p//a/text()',
}

# ✅ 政府索引字段
GOV_DETAIL_FIELDS = {
    "indexnumber": '//div[@class=""]//tr[1]/td[2]/text()',
    "fileno": '//div[@class=""]//tr[2]/td[4]/text()',
    "category": '//div[@class=""]//tr[1]/td[4]/text()',
    "issuer": '//div[@class=""]//tr[2]/td[2]/text()',
    "status": '//div[@class=""]//tr[2]/td[6]/text()',
    "writtendate": '//div[@class=""]//tr[1]/td[6]/text()',
}

# ✅ 默认正则配置
DEFAULT_REGEX = {
    "publish_times": r"\d{4}-\d{1,2}-\d{1,2}",
    "total_page": r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    "publish_time": r"时间：\s*(\d{4}-\d{2}-\d{2})",
    "writtendate": r"\s*(\d{4}-\d{2}-\d{2})",
    "source": r"来源：\s*(.*?)\s*",
}

DEFAULT_ENABLE_REGEX = {
    "publish_times": True,
    "total_page": True,
}

# ===================== IDE风格配色（PyCharm-ish）=====================
IDE_BG = "#2B2B2B"
IDE_BG2 = "#313335"
IDE_PANEL = "#3C3F41"
IDE_FG = "#A9B7C6"
IDE_MUTED = "#808080"
IDE_ACCENT = "#4E8ABE"
IDE_WARN = "#FFCC66"
IDE_ERR = "#FF6666"
IDE_OK = "#6AAB73"

FONT_UI = ("Microsoft YaHei UI", 10)
FONT_CODE = ("Consolas", 10)
FONT_CODE_SM = ("Consolas", 9)

selected_path = ""
list_widgets = {}
detail_widgets = {}

# ===================== 工具函数 =====================
def to_regex_literal(user_text: str) -> str:
    s = user_text.strip()
    if not s:
        return 'r""'
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        return s
    return f'r"{s}"'

def pretty_dict_ordered(d: dict, keys_order: list, indent=4) -> str:
    pad = " " * indent
    lines = ["{"]
    for k in keys_order:
        if k in d:
            lines.append(f"{pad}{repr(k)}: {repr(d[k])},")
    for k in d:
        if k not in keys_order:
            lines.append(f"{pad}{repr(k)}: {repr(d[k])},")
    lines.append("}")
    return "\n".join(lines)

def pretty_regex_dict(d: dict, keys_order: list, indent=4) -> str:
    pad = " " * indent
    lines = ["{"]
    for k in keys_order:
        if k in d:
            lines.append(f"{pad}{repr(k)}: {to_regex_literal(d[k])},")
    for k in d:
        if k not in keys_order:
            lines.append(f"{pad}{repr(k)}: {to_regex_literal(d[k])},")
    lines.append("}")
    return "\n".join(lines)

def get_text_value(widget: tk.Text) -> str:
    raw = widget.get("1.0", "end").strip()
    if not raw:
        return ""
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    return " | ".join(lines)

def find_spiders_dir(base_path):
    if os.path.isdir(os.path.join(base_path, "spiders")):
        return os.path.join(base_path, "spiders")
    for name in os.listdir(base_path):
        candidate = os.path.join(base_path, name, "spiders")
        if os.path.isdir(candidate):
            return candidate
    return None

def extract_spider_info(spider_file):
    with open(spider_file, "r", encoding="utf-8") as f:
        content = f.read()

    def find(pattern, name):
        m = re.search(pattern, content)
        if not m:
            raise ValueError(f"❌ 无法解析 {name}，pattern={pattern}")
        return m.group(1)

    class_name = find(r"class\s+(\w+)\s*\(", "class_name")
    spider_name = find(r"name\s*=\s*['\"]([^'\"]+)['\"]", "spider_name")
    allowed_domain = find(r"allowed_domains\s*=\s*\[\s*['\"]([^'\"]+)['\"]\s*\]", "allowed_domains")
    start_urls = find(r"start_urls\s*=\s*(\[[\s\S]*?\])", "start_urls")
    return class_name, spider_name, allowed_domain, start_urls

def field_processors_code(info):
    if not info["enable_var"].get():
        return "[]"
    return f'[Regex(REGEX["{info["regex_key"]}"])]'

def should_process_field(field_name, widget_dict):
    if field_name in GOV_DETAIL_FIELDS and not enable_gov_fields.get():
        return False
    if field_name in widget_dict:
        return widget_dict[field_name]["use_field_var"].get()
    return True

def build_xpath_dict(widget_dict):
    result = {}
    for k, v in widget_dict.items():
        if not should_process_field(k, widget_dict):
            continue
        val = get_text_value(v["xpath"])
        if val:
            result[k] = val
    return result

def build_regex_dict(widget_dict):
    result = {}
    for field, info in widget_dict.items():
        if not should_process_field(field, widget_dict):
            continue
        if not info["enable_var"].get():
            continue
        regex_key = info["regex_key"]
        text = info["regex_entry"].get().strip()
        if regex_key and text:
            result[regex_key] = text
    return result

def generate_list_fields_code(widget_dict):
    lines = []
    for field_name, info in widget_dict.items():
        xpath = get_text_value(info["xpath"])
        if not xpath:
            continue
        processors = field_processors_code(info)
        lines.append(
            f"                Field('{field_name}', LIST_XPATH[\"{field_name}\"], {processors}, type=\"xpath\"),"
        )
    return "\n".join(lines)

def generate_detail_fields_code(widget_dict):
    lines = []
    for field_name, info in widget_dict.items():
        if not should_process_field(field_name, widget_dict):
            continue

        xpath = get_text_value(info["xpath"])
        if not xpath:
            continue

        if field_name == "menu":
            lines.append(
                "                Field('menu', DETAIL_XPATH[\"menu\"], [Text(), Join(separator='>')], type=\"xpath\"),"
            )
            continue

        if field_name == "content":
            lines.append("""                Field(
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
                        Join(separator='\\n')
                    ],
                    required=False,
                    type='xpath'
                ),""")
            continue

        # ✅ 附件字段：必须带 file_category='attachment'，否则无法触发下载
        if field_name in ("attachment", "attachment_name"):
            processors = field_processors_code(info)  # 通常是 []，但保留也没问题
            lines.append(
                f"                Field('{field_name}', DETAIL_XPATH[\"{field_name}\"], {processors}, required=False, type='xpath', file_category='attachment'),"
            )
            continue

        processors = field_processors_code(info)
        lines.append(
            f"                Field('{field_name}', DETAIL_XPATH[\"{field_name}\"], {processors}, required=False, type='xpath'),"
        )
    return "\n".join(lines)

def rewrite_spider_file(spider_file):
    class_name, spider_name, allowed_domain, start_urls = extract_spider_info(spider_file)

    list_xpath_dict = build_xpath_dict(list_widgets)
    detail_xpath_dict = build_xpath_dict(detail_widgets)
    regex_dict = build_regex_dict({**list_widgets, **detail_widgets})

    list_xpath_str = pretty_dict_ordered(list_xpath_dict, list(DEFAULT_LIST_FIELDS.keys()))

    detail_keys_order = list(DEFAULT_DETAIL_FIELDS.keys())
    if enable_gov_fields.get():
        for gov_k in GOV_DETAIL_FIELDS.keys():
            if gov_k in detail_xpath_dict:
                detail_keys_order.append(gov_k)

    detail_xpath_str = pretty_dict_ordered(detail_xpath_dict, detail_keys_order)

    if regex_dict:
        keys_order = list(DEFAULT_REGEX.keys())
        regex_dict_str = pretty_regex_dict(regex_dict, keys_order)
        regex_section = f"# ===================== Regex 常量 =====================\nREGEX = {regex_dict_str}"
    else:
        regex_section = ""

    list_fields_code = generate_list_fields_code(list_widgets)
    detail_fields_code = generate_detail_fields_code(detail_widgets)

    spider_code = SPIDER_TEMPLATE.format(
        class_name=class_name,
        spider_name=spider_name,
        allowed_domain=allowed_domain,
        start_urls=start_urls,
        list_xpath=list_xpath_str,
        detail_xpath=detail_xpath_str,
        regex_section=regex_section,
        list_fields=list_fields_code,
        detail_fields=detail_fields_code,
    )

    with open(spider_file, "w", encoding="utf-8") as f:
        f.write(spider_code)

# ===================== UI 辅助：状态/占位符/预览 =====================
def set_status(text: str, color=IDE_FG):
    if "status_var" not in globals():
        return
    status_var.set(text)
    if "status_label" in globals():
        status_label.configure(foreground=color)

def log(msg: str, level="info"):
    return  # ✅ 已取消日志

URL_PLACEHOLDER = "请输入 URL 或域名，例如：https://xxx.gov.cn/xx 或 xxx.gov.cn"

def set_url_placeholder_if_empty():
    if "url_entry" not in globals():
        return
    if not url_entry.get().strip():
        url_entry.insert(0, URL_PLACEHOLDER)
        url_entry.configure(fg=IDE_MUTED)

def clear_url_placeholder_on_focus():
    if url_entry.get().strip() == URL_PLACEHOLDER:
        url_entry.delete(0, "end")
        url_entry.configure(fg=IDE_FG)

def update_preview():
    if "url_entry" not in globals():
        return

    raw_url = url_entry.get().strip()
    if raw_url == URL_PLACEHOLDER:
        raw_url = ""

    cmd = ""
    if raw_url:
        u = raw_url
        if not u.startswith(("http://", "https://")):
            u = "http://" + u
        parsed = urlparse(u)
        domain = parsed.netloc.strip("/")
        spider_name = domain.replace(".", "_") if domain else "spider"
        python_exe = "python" if getattr(sys, "frozen", False) else sys.executable
        cmd = f'"{python_exe}" -m scrapy genspider {spider_name} {u}'

    if "cmd_text" in globals():
        cmd_text.configure(state="normal")
        cmd_text.delete("1.0", "end")
        cmd_text.insert("end", cmd)
        cmd_text.configure(state="disabled")

    if "preview_text" not in globals():
        return

    try:
        list_xpath_dict = build_xpath_dict(list_widgets)
        detail_xpath_dict = build_xpath_dict(detail_widgets)
        regex_dict = build_regex_dict({**list_widgets, **detail_widgets})

        list_xpath_str = pretty_dict_ordered(list_xpath_dict, list(DEFAULT_LIST_FIELDS.keys()))

        detail_keys_order = list(DEFAULT_DETAIL_FIELDS.keys())
        if enable_gov_fields.get():
            for gov_k in GOV_DETAIL_FIELDS.keys():
                if gov_k in detail_xpath_dict:
                    detail_keys_order.append(gov_k)
        detail_xpath_str = pretty_dict_ordered(detail_xpath_dict, detail_keys_order)

        if regex_dict:
            keys_order = list(DEFAULT_REGEX.keys())
            regex_dict_str = pretty_regex_dict(regex_dict, keys_order)
            regex_section = f"REGEX = {regex_dict_str}"
        else:
            regex_section = "REGEX = {}  # (未启用任何正则)"

        preview = []
        preview.append("# ========= 预览（将写入 spider 文件的关键配置）=========")
        preview.append("")
        preview.append("LIST_XPATH = " + list_xpath_str)
        preview.append("")
        preview.append("DETAIL_XPATH = " + detail_xpath_str)
        preview.append("")
        preview.append(regex_section)
        preview.append("")
        preview.append("# ========= 字段生成预览（list_items / items）=========")
        preview.append("")
        preview.append("## list_fields")
        preview.append(generate_list_fields_code(list_widgets) or "（无）")
        preview.append("")
        preview.append("## detail_fields")
        preview.append(generate_detail_fields_code(detail_widgets) or "（无）")

        preview_text.configure(state="normal")
        preview_text.delete("1.0", "end")
        preview_text.insert("end", "\n".join(preview))
        preview_text.configure(state="disabled")
    except Exception as e:
        preview_text.configure(state="normal")
        preview_text.delete("1.0", "end")
        preview_text.insert("end", f"预览生成失败：{e}")
        preview_text.configure(state="disabled")

def bind_live_update_to_text(t: tk.Text):
    t.bind("<KeyRelease>", lambda e: update_preview())
    t.bind("<FocusOut>", lambda e: update_preview())

def bind_live_update_to_entry(ent: tk.Entry):
    ent.bind("<KeyRelease>", lambda e: update_preview())
    ent.bind("<FocusOut>", lambda e: update_preview())

# ===================== 字段行（grid 两行布局，窄窗口不挤掉正则；启用仅打勾无文字）=====================
def build_field_row(parent, field_name, default_xpath, widget_dict, is_gov=False):
    card = ttk.Frame(parent, style="IDE.TFrame")
    card.pack(fill=tk.X, pady=5, padx=6)

    card.columnconfigure(0, weight=0)
    card.columnconfigure(1, weight=1)

    use_field_var = tk.BooleanVar(master=root, value=True)

    # Row 0
    if is_gov:
        name_widget = ttk.Checkbutton(
            card, text=field_name, variable=use_field_var, style="IDE.TCheckbutton",
            command=update_preview
        )
        name_widget.grid(row=0, column=0, sticky="w", padx=(2, 8), pady=(2, 2))
    else:
        ttk.Label(card, text=field_name, width=16, anchor="w", style="IDE.TLabel") \
            .grid(row=0, column=0, sticky="w", padx=(2, 8), pady=(2, 2))

    xpath_text = tk.Text(
        card, height=2, width=1,
        font=FONT_CODE, wrap="word",
        bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
        relief="flat", highlightthickness=1,
        highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
    )
    xpath_text.insert("1.0", default_xpath)
    xpath_text.grid(row=0, column=1, sticky="ew", padx=(0, 2), pady=(2, 2))
    bind_live_update_to_text(xpath_text)

    # Row 1
    ttk.Label(card, text="", width=16, style="IDE.TLabel") \
        .grid(row=1, column=0, sticky="w", padx=(2, 8), pady=(0, 2))

    bottom = ttk.Frame(card, style="IDE.TFrame")
    bottom.grid(row=1, column=1, sticky="ew", padx=(0, 2), pady=(0, 2))
    bottom.columnconfigure(3, weight=1)

    enable_regex_var = tk.BooleanVar(master=root, value=DEFAULT_ENABLE_REGEX.get(field_name, False))

    ttk.Label(bottom, text="Regex：", style="IDE.Muted.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 6))
    ttk.Checkbutton(
        bottom, variable=enable_regex_var, style="IDE.TCheckbutton",
        command=update_preview
    ).grid(row=0, column=1, sticky="w", padx=(0, 8))

    regex_key = field_name
    regex_entry = tk.Entry(
        bottom, width=28, font=FONT_CODE_SM,
        bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
        relief="flat", highlightthickness=1,
        highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
    )
    regex_entry.insert(0, DEFAULT_REGEX.get(regex_key, r"\d+"))
    regex_entry.grid(row=0, column=3, sticky="ew")
    bind_live_update_to_entry(regex_entry)

    widget_dict[field_name] = {
        "xpath": xpath_text,
        "enable_var": enable_regex_var,
        "regex_key": regex_key,
        "regex_entry": regex_entry,
        "use_field_var": use_field_var,
    }

# ===================== 按钮逻辑 =====================
def choose_path():
    global selected_path
    path = filedialog.askdirectory()
    if path:
        selected_path = path
        if "path_value" in globals():
            path_value.configure(text=path)
        set_status(f"已选择项目路径：{path}", IDE_OK)
        update_preview()

def clear_all():
    url_entry.delete(0, tk.END)
    set_url_placeholder_if_empty()
    if "cmd_text" in globals():
        cmd_text.configure(state="normal")
        cmd_text.delete("1.0", tk.END)
        cmd_text.configure(state="disabled")
    if "path_value" in globals():
        path_value.configure(text="未选择")
    set_status("就绪", IDE_FG)
    url_entry.focus()
    update_preview()

def quick_create_fixed_spider():
    try:
        if not selected_path:
            messagebox.showwarning("提示", "请先选择 Scrapy 项目路径")
            return
        raw_url = url_entry.get().strip()
        if raw_url == URL_PLACEHOLDER:
            raw_url = ""
        if not raw_url:
            messagebox.showwarning("提示", "请输入 URL 或域名")
            return
        if not raw_url.startswith(("http://", "https://")):
            raw_url = "http://" + raw_url
        parsed = urlparse(raw_url)
        domain = parsed.netloc.strip("/")
        spider_name = domain.replace(".", "_") + "_gk"

        spiders_dir = find_spiders_dir(selected_path)
        if not spiders_dir:
            messagebox.showerror("错误", "未找到 spiders 目录，请选择 Scrapy 项目根目录")
            return

        python_exe = "python" if getattr(sys, "frozen", False) else sys.executable
        cmd = f'"{python_exe}" -m scrapy genspider {spider_name} {raw_url}'

        if "cmd_text" in globals():
            cmd_text.configure(state="normal")
            cmd_text.delete("1.0", tk.END)
            cmd_text.insert(tk.END, cmd)
            cmd_text.configure(state="disabled")

        set_status("正在生成 Spider_gk...", IDE_WARN)

        completed = subprocess.run(cmd, cwd=selected_path, shell=True, capture_output=True, text=True)

        spider_file = os.path.join(spiders_dir, f"{spider_name}.py")
        if not os.path.exists(spider_file):
            set_status("生成失败：未找到 spider 文件", IDE_ERR)
            messagebox.showerror("错误", f"快捷创建失败，未找到 spider 文件：{spider_file}\n\n{completed.stderr}")
            return

        rewrite_spider_file(spider_file)
        set_status(f"成功：{spider_name}", IDE_OK)
        messagebox.showinfo("成功", f"GK Spider 创建成功！\n\n爬虫名称：{spider_name}\n文件路径：\n{spider_file}")
    except Exception as e:
        set_status("运行错误", IDE_ERR)
        messagebox.showerror("运行错误", str(e))

def run_and_generate():
    try:
        if not selected_path:
            messagebox.showwarning("提示", "请先选择 Scrapy 项目路径")
            return
        raw_url = url_entry.get().strip()
        if raw_url == URL_PLACEHOLDER:
            raw_url = ""
        if not raw_url:
            messagebox.showwarning("提示", "请输入 URL 或域名")
            return
        if not raw_url.startswith(("http://", "https://")):
            raw_url = "http://" + raw_url
        parsed = urlparse(raw_url)
        domain = parsed.netloc.strip("/")
        spider_name = domain.replace(".", "_")

        spiders_dir = find_spiders_dir(selected_path)
        if not spiders_dir:
            messagebox.showerror("错误", "未找到 spiders 目录，请选择 Scrapy 项目根目录")
            return

        python_exe = "python" if getattr(sys, "frozen", False) else sys.executable
        cmd = f'"{python_exe}" -m scrapy genspider {spider_name} {raw_url}'

        if "cmd_text" in globals():
            cmd_text.configure(state="normal")
            cmd_text.delete("1.0", tk.END)
            cmd_text.insert(tk.END, cmd)
            cmd_text.configure(state="disabled")

        set_status("正在生成 Spider...", IDE_WARN)

        completed = subprocess.run(cmd, cwd=selected_path, shell=True, capture_output=True, text=True)

        spider_file = os.path.join(spiders_dir, f"{spider_name}.py")
        if not os.path.exists(spider_file):
            set_status("生成失败：未找到 spider 文件", IDE_ERR)
            messagebox.showerror("错误", f"未找到生成的 spider 文件：{spider_file}\n\n{completed.stderr}")
            return

        rewrite_spider_file(spider_file)
        set_status(f"成功：{spider_name}", IDE_OK)
        messagebox.showinfo("成功", f"Spider 创建成功！\n\n文件路径：\n{spider_file}")
    except Exception as e:
        set_status("运行错误", IDE_ERR)
        messagebox.showerror("运行错误", str(e))

# ===================== GUI（IDE风：左配置 + 右预览/命令，无日志、无Notebook）=====================
root = tk.Tk()
root.title("Scrapy Portia Spider Generator (IDE)")
root.geometry("1400x900")
root.minsize(1100, 720)
root.configure(bg=IDE_BG)

enable_gov_fields = tk.BooleanVar(master=root, value=False)

# ttk 主题 + 样式
style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass

style.configure("IDE.TFrame", background=IDE_BG)
style.configure("IDE.Panel.TFrame", background=IDE_PANEL)
style.configure("IDE.TLabel", background=IDE_BG, foreground=IDE_FG, font=FONT_UI)
style.configure("IDE.Title.TLabel", background=IDE_BG, foreground=IDE_FG, font=(FONT_UI[0], 11, "bold"))
style.configure("IDE.Muted.TLabel", background=IDE_BG, foreground=IDE_MUTED, font=FONT_UI)
style.configure("IDE.TCheckbutton", background=IDE_BG, foreground=IDE_FG, font=FONT_UI)
style.map("IDE.TCheckbutton", background=[("active", IDE_BG)])

style.configure("IDE.TLabelframe", background=IDE_BG, foreground=IDE_FG)
style.configure("IDE.TLabelframe.Label", background=IDE_BG, foreground=IDE_FG, font=(FONT_UI[0], 10, "bold"))

style.configure("IDE.TButton", font=FONT_UI, padding=(10, 6))
style.configure("IDE.Primary.TButton", font=FONT_UI, padding=(12, 6), foreground="white", background=IDE_ACCENT)
style.map("IDE.Primary.TButton",
          background=[("active", "#5C9DE0"), ("pressed", "#3B74A8")],
          foreground=[("active", "white"), ("pressed", "white")])

# 顶部栏
top = ttk.Frame(root, style="IDE.TFrame")
top.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(10, 6))

title_row = ttk.Frame(top, style="IDE.TFrame")
title_row.pack(fill=tk.X)
ttk.Label(title_row, text="Scrapy Portia Spider Generator", style="IDE.Title.TLabel").pack(side=tk.LEFT)
ttk.Label(title_row, text="  （IDE风：左配置 / 右预览与命令，无日志）", style="IDE.Muted.TLabel").pack(side=tk.LEFT)

# URL 行
url_row = ttk.Frame(top, style="IDE.TFrame")
url_row.pack(fill=tk.X, pady=(8, 0))

ttk.Label(url_row, text="URL / 域名：", style="IDE.TLabel").pack(side=tk.LEFT, padx=(0, 8))

url_entry = tk.Entry(
    url_row, font=("Consolas", 12),
    bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
    relief="flat", highlightthickness=1,
    highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
)
url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
url_entry.bind("<FocusIn>", lambda e: clear_url_placeholder_on_focus())
url_entry.bind("<FocusOut>", lambda e: (set_url_placeholder_if_empty(), update_preview()))
url_entry.bind("<KeyRelease>", lambda e: update_preview())

# 路径行
path_row = ttk.Frame(top, style="IDE.TFrame")
path_row.pack(fill=tk.X, pady=(8, 0))

ttk.Button(path_row, text="选择 Scrapy 项目路径", style="IDE.TButton", command=choose_path).pack(side=tk.LEFT)
ttk.Label(path_row, text="当前路径：", style="IDE.TLabel").pack(side=tk.LEFT, padx=(12, 6))
path_value = ttk.Label(path_row, text="未选择", style="IDE.Muted.TLabel")
path_value.pack(side=tk.LEFT, fill=tk.X, expand=True)

# 主体分栏
main = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=8)

# ========== 左侧：字段配置（滚动）==========
left = ttk.Frame(main, style="IDE.TFrame")
main.add(left, weight=3)

left_header = ttk.Frame(left, style="IDE.TFrame")
left_header.pack(fill=tk.X, pady=(0, 6))
ttk.Label(left_header, text="字段配置", style="IDE.Title.TLabel").pack(side=tk.LEFT)

canvas_wrap = ttk.Frame(left, style="IDE.TFrame")
canvas_wrap.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(canvas_wrap, bg=IDE_BG, highlightthickness=0)
vbar = ttk.Scrollbar(canvas_wrap, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=vbar.set)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
vbar.pack(side=tk.RIGHT, fill=tk.Y)

scrollable_frame = ttk.Frame(canvas, style="IDE.TFrame")
frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

def on_frame_configure(_):
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_canvas_configure(event):
    canvas.itemconfig(frame_id, width=event.width)

scrollable_frame.bind("<Configure>", on_frame_configure)
canvas.bind("<Configure>", on_canvas_configure)

def _on_mousewheel(event):
    if platform.system() == "Windows":
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    elif platform.system() == "Darwin":
        canvas.yview_scroll(int(-1 * event.delta), "units")
    else:
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

def _bind_wheel(_):
    if platform.system() in ("Windows", "Darwin"):
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    else:
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

def _unbind_wheel(_):
    if platform.system() in ("Windows", "Darwin"):
        canvas.unbind_all("<MouseWheel>")
    else:
        canvas.unbind_all("<Button-4>")
        canvas.unbind_all("<Button-5>")

canvas.bind("<Enter>", _bind_wheel)
canvas.bind("<Leave>", _unbind_wheel)

# 左侧：列表页配置区
list_frame = ttk.LabelFrame(scrollable_frame, text="列表页字段（XPath + 正则）", style="IDE.TLabelframe")
list_frame.pack(padx=6, pady=(6, 8), fill=tk.X)
for k, v in DEFAULT_LIST_FIELDS.items():
    build_field_row(list_frame, k, v, list_widgets, is_gov=False)

# 左侧：详情页配置区
detail_frame = ttk.LabelFrame(scrollable_frame, text="详情页字段（XPath + 正则）", style="IDE.TLabelframe")
detail_frame.pack(padx=6, pady=(0, 10), fill=tk.X)
for k, v in DEFAULT_DETAIL_FIELDS.items():
    build_field_row(detail_frame, k, v, detail_widgets, is_gov=False)

gov_check_row = ttk.Frame(detail_frame, style="IDE.TFrame")
gov_check_row.pack(fill=tk.X, padx=6, pady=(8, 6))

gov_fields_container = ttk.Frame(detail_frame, style="IDE.TFrame")

def toggle_gov_fields_visibility():
    if enable_gov_fields.get():
        gov_fields_container.pack(fill=tk.X, padx=6, pady=(0, 8))
    else:
        gov_fields_container.pack_forget()
    scrollable_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_preview()

gov_cb = ttk.Checkbutton(
    gov_check_row,
    text="启用政府索引字段 (indexnumber / fileno / category / issuer / status / writtendate)",
    variable=enable_gov_fields,
    style="IDE.TCheckbutton",
    command=toggle_gov_fields_visibility
)
gov_cb.pack(anchor="w")

ttk.Label(gov_fields_container, text="政府字段区域（每行勾选启用字段）", style="IDE.Muted.TLabel").pack(anchor="w", pady=(0, 6))
for k, v in GOV_DETAIL_FIELDS.items():
    build_field_row(gov_fields_container, k, v, detail_widgets, is_gov=True)

toggle_gov_fields_visibility()

# ========== 右侧：预览 + 命令 ==========
right = ttk.Frame(main, style="IDE.TFrame")
main.add(right, weight=2)

right_header = ttk.Frame(right, style="IDE.TFrame")
right_header.pack(fill=tk.X, pady=(0, 6))
ttk.Label(right_header, text="预览", style="IDE.Title.TLabel").pack(side=tk.LEFT)

preview_box = ttk.LabelFrame(right, text="配置预览", style="IDE.TLabelframe")
preview_box.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

preview_text = tk.Text(
    preview_box, font=FONT_CODE_SM, wrap="none",
    bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
    relief="flat", highlightthickness=1,
    highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
)
preview_text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
preview_text.configure(state="disabled")

cmd_box = ttk.LabelFrame(right, text="Scrapy 命令预览", style="IDE.TLabelframe")
cmd_box.pack(fill=tk.X, padx=6, pady=(0, 6))

cmd_text = tk.Text(
    cmd_box, height=2, font=FONT_CODE,
    bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
    relief="flat", highlightthickness=1,
    highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
)
cmd_text.pack(fill=tk.X, padx=6, pady=6)
cmd_text.configure(state="disabled")

# 底部按钮栏
bottom = ttk.Frame(root, style="IDE.TFrame")
bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(6, 10))

btns = ttk.Frame(bottom, style="IDE.TFrame")
btns.pack(side=tk.LEFT)

ttk.Button(btns, text="生成并写入 Spider", style="IDE.Primary.TButton", command=run_and_generate)\
    .pack(side=tk.LEFT, padx=(0, 8))
ttk.Button(btns, text="生成并写入 Spider_gk", style="IDE.TButton", command=quick_create_fixed_spider)\
    .pack(side=tk.LEFT, padx=(0, 8))
ttk.Button(btns, text="清空", style="IDE.TButton", command=clear_all).pack(side=tk.LEFT)

status_var = tk.StringVar(value="就绪")
status_label = ttk.Label(bottom, textvariable=status_var, style="IDE.TLabel")
status_label.pack(side=tk.RIGHT)

# ✅ 不绑定回车
# root.bind("<Return>", lambda e: run_and_generate())

# 初始化
set_url_placeholder_if_empty()
set_status("就绪", IDE_FG)
update_preview()

root.mainloop()
