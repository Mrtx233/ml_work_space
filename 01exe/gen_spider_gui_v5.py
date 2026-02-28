import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from urllib.parse import urlparse
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

from ...items import ListItems, HbeaItem
from ...utils.spiders import BasePortiaSpider
from ...utils.starturls import FeedGenerator, FragmentGenerator
from ...utils.processors import Item, Field, Text, Number, Price, Date, Url, Image, Regex


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
    "total_page": '//script/text()'
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

# ✅ 快捷正则下拉（可扩展）
QUICK_REGEX_PRESETS = {
    "日期": r"\d{4}-\d{1,2}-\d{1,2}",
    "来源：xxx": r"来源：\s*(.*?)\s*",
    "时间：YYYY-MM-DD": r"时间：\s*(\d{4}-\d{1,2}-\d{1,2})",
    "页码createPage(...)": r"createPage(?:HTML)?\(\s*(\d+)\s*,",
    "链接URL": r"https?://[^\s\"']+",
}

# ===================== IDE风格配色 =====================
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

def snake_to_camel(s: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", s)
    parts = [p for p in parts if p]
    if not parts:
        return "MySpider"
    return "".join(p[:1].upper() + p[1:] for p in parts)

def domain_to_filename(domain: str) -> str:
    """
    kjt.zj.gov.cn -> kjt_zj_gov_cn
    """
    d = (domain or "").strip().lower().strip(".")
    d = re.sub(r"\s+", "", d)
    d = d.replace(".", "_")
    d = re.sub(r"[^a-z0-9_]+", "_", d)
    d = re.sub(r"_+", "_", d).strip("_")
    return d or "spider"

def normalize_user_url(raw_url: str) -> str:
    u = (raw_url or "").strip()
    if not u:
        return ""
    if u == URL_PLACEHOLDER:
        return ""
    if not u.startswith(("http://", "https://")):
        u = "http://" + u
    return u

def normalize_cn_name(raw: str) -> str:
    t = (raw or "").strip()
    if not t or t == CN_NAME_PLACEHOLDER:
        return ""
    return t

def set_status(text: str, color=IDE_FG):
    status_var.set(text)
    status_label.configure(foreground=color)

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

def field_processors_code(info):
    if not info["enable_var"].get():
        return "[]"
    return f'[Regex(REGEX["{info["regex_key"]}"])]'

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

        if field_name in ("attachment", "attachment_name"):
            processors = field_processors_code(info)
            lines.append(
                f"                Field('{field_name}', DETAIL_XPATH[\"{field_name}\"], {processors}, required=False, type='xpath', file_category='attachment'),"
            )
            continue

        processors = field_processors_code(info)
        lines.append(
            f"                Field('{field_name}', DETAIL_XPATH[\"{field_name}\"], {processors}, required=False, type='xpath'),"
        )
    return "\n".join(lines)

def write_spider_to_cn_folder(spiders_dir: str, cn_name: str, raw_url: str, suffix: str = "", overwrite: bool = True):
    """
    ✅ 目录：<spiders_dir>/<中文名称>/
    ✅ 文件：<domain_to_filename(domain)><suffix>.py
         例：kjt_zj_gov_cn.py / kjt_zj_gov_cn_gk.py
    """
    spiders_dir = (spiders_dir or "").strip().strip('"').strip()
    if not spiders_dir:
        raise ValueError("spiders 路径不能为空")
    if not os.path.isdir(spiders_dir):
        raise ValueError(f"spiders 路径不存在或不是目录：{spiders_dir}")

    cn_name = normalize_cn_name(cn_name)
    if not cn_name:
        raise ValueError("目录名不能为空（中文名称）")

    u = normalize_user_url(raw_url)
    if not u:
        raise ValueError("请输入 URL 或域名")

    parsed = urlparse(u)
    domain = parsed.netloc.strip("/")
    if not domain:
        raise ValueError("URL 无法解析域名（请检查输入）")

    allowed_domain = domain
    start_urls = repr([u])

    base = domain_to_filename(domain)
    spider_name = base + suffix
    class_name = snake_to_camel(spider_name)

    # GUI 配置 -> 字典/正则
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

    out_dir = os.path.join(spiders_dir, cn_name)
    os.makedirs(out_dir, exist_ok=True)

    # ✅ 创建 __init__.py 确保包识别
    init_file = os.path.join(out_dir, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("# coding: utf-8\n")

    filename = f"{base}{suffix}.py"
    out_file = os.path.join(out_dir, filename)

    if os.path.exists(out_file) and not overwrite:
        raise ValueError(f"文件已存在：{out_file}")

    with open(out_file, "w", encoding="utf-8") as f:
        f.write(spider_code)

    return spider_name, class_name, out_file

# ===================== Entry 撤销/重做（Ctrl+Z / Ctrl+Y）=====================
def enable_entry_undo(entry: tk.Entry):
    history = []
    redo_stack = []
    last = entry.get()

    def snapshot(_=None):
        nonlocal last
        cur = entry.get()
        if cur != last:
            history.append(last)
            last = cur
            redo_stack.clear()

    def undo(_=None):
        nonlocal last
        if history:
            redo_stack.append(entry.get())
            prev = history.pop()
            entry.delete(0, "end")
            entry.insert(0, prev)
            last = prev
            update_preview()
        return "break"

    def redo(_=None):
        nonlocal last
        if redo_stack:
            history.append(entry.get())
            nxt = redo_stack.pop()
            entry.delete(0, "end")
            entry.insert(0, nxt)
            last = nxt
            update_preview()
        return "break"

    entry.bind("<KeyRelease>", snapshot, add=True)
    entry.bind("<<Paste>>", snapshot, add=True)
    entry.bind("<<Cut>>", snapshot, add=True)
    entry.bind("<FocusOut>", snapshot, add=True)

    entry.bind("<Control-z>", undo, add=True)
    entry.bind("<Control-y>", redo, add=True)

# ===================== UI 辅助：占位符/预览 =====================
URL_PLACEHOLDER = "请输入 URL 或域名"
CN_NAME_PLACEHOLDER = "请输入中文目录名"
SPIDERS_PLACEHOLDER = "请粘贴 spiders 路径"

def set_placeholder_if_empty(entry: tk.Entry, placeholder: str):
    if not entry.get().strip():
        entry.insert(0, placeholder)
        entry.configure(fg=IDE_MUTED)

def clear_placeholder_on_focus(entry: tk.Entry, placeholder: str):
    if entry.get().strip() == placeholder:
        entry.delete(0, "end")
        entry.configure(fg=IDE_FG)

def bind_live_update_to_text(t: tk.Text):
    """
    之前用于实时更新右侧预览，现在预览功能已删除，留空实现以兼容旧代码调用。
    """
    return

def bind_live_update_to_entry(ent: tk.Entry):
    """
    之前用于实时更新右侧预览，现在预览功能已删除，留空实现以兼容旧代码调用。
    """
    return

def update_preview():
    """
    预览功能已移除，该函数保留为空实现，避免其他地方调用时报错。
    """
    return

def open_multiline_editor(parent, title: str, initial_text: str, on_save):
    """
    打开一个可放大的多行编辑器弹窗，用于查看/编辑较长内容（如 XPath）。
    on_save: function(new_text: str) -> None
    """
    win = tk.Toplevel(parent)
    win.title(title)
    win.geometry("900x500")
    win.minsize(700, 360)
    win.configure(bg=IDE_BG)
    win.transient(parent)

    box = ttk.Frame(win, style="IDE.TFrame")
    box.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
    box.columnconfigure(0, weight=1)
    box.rowconfigure(0, weight=1)

    txt = tk.Text(
        box,
        font=FONT_CODE,
        wrap="word",
        bg=IDE_BG2,
        fg=IDE_FG,
        insertbackground=IDE_FG,
        relief="flat",
        highlightthickness=1,
        highlightbackground=IDE_PANEL,
        highlightcolor=IDE_ACCENT,
        undo=True,
        autoseparators=True,
        maxundo=-1,
    )
    txt.insert("1.0", initial_text or "")
    txt.grid(row=0, column=0, sticky="nsew")

    ybar = ttk.Scrollbar(box, orient="vertical", command=txt.yview)
    txt.configure(yscrollcommand=ybar.set)
    ybar.grid(row=0, column=1, sticky="ns", padx=(8, 0))

    btn_row = ttk.Frame(win, style="IDE.TFrame")
    btn_row.pack(fill=tk.X, padx=12, pady=(0, 12))

    def _save_and_close(_=None):
        on_save(txt.get("1.0", "end-1c"))
        win.destroy()
        return "break"

    def _cancel(_=None):
        win.destroy()
        return "break"

    ttk.Button(btn_row, text="保存", style="IDE.Primary.TButton", command=_save_and_close).pack(side=tk.LEFT)
    ttk.Button(btn_row, text="取消", style="IDE.TButton", command=_cancel).pack(side=tk.LEFT, padx=(8, 0))

    win.bind("<Control-Return>", _save_and_close, add=True)
    win.bind("<Escape>", _cancel, add=True)
    win.grab_set()
    txt.focus_set()
    return win

# ===================== 字段行（XPath + Regex + 下拉）=====================
def build_field_row(parent, field_name, default_xpath, widget_dict, is_gov=False):
    card = ttk.Frame(parent, style="IDE.TFrame")
    card.pack(fill=tk.X, pady=5, padx=6)

    # 单行布局：name | xpath | Regex | [✓] | preset | regex_entry
    card.columnconfigure(0, weight=0)  # name
    card.columnconfigure(1, weight=1)  # xpath
    card.columnconfigure(2, weight=0)  # "Regex"
    card.columnconfigure(3, weight=0)  # checkbox
    card.columnconfigure(4, weight=0)  # preset combobox
    card.columnconfigure(5, weight=1)  # regex entry

    use_field_var = tk.BooleanVar(master=root, value=True)

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
        card, height=1, width=1,
        font=FONT_CODE, wrap="word",
        bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
        relief="flat", highlightthickness=1,
        highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT,
        undo=True, autoseparators=True, maxundo=-1
    )
    xpath_text.insert("1.0", default_xpath)
    xpath_text.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=(2, 2))
    bind_live_update_to_text(xpath_text)

    # 双击 XPath 打开多行编辑器，便于查看/编辑换行后的完整内容
    def _open_xpath_editor(_=None):
        def _apply(new_text: str):
            xpath_text.configure(state="normal")
            xpath_text.delete("1.0", "end")
            xpath_text.insert("1.0", new_text)
            xpath_text.configure(state="normal")
            update_preview()

        open_multiline_editor(
            parent=root,
            title=f"{field_name} - XPath 编辑器（Ctrl+Enter 保存）",
            initial_text=xpath_text.get("1.0", "end-1c"),
            on_save=_apply,
        )
        return "break"

    xpath_text.bind("<Double-Button-1>", _open_xpath_editor, add=True)

    # 右键菜单：编辑/全选
    menu = tk.Menu(card, tearoff=0)
    menu.add_command(label="打开大编辑器", command=lambda: _open_xpath_editor())
    menu.add_separator()
    menu.add_command(label="全选", command=lambda: (xpath_text.tag_add("sel", "1.0", "end"), "break"))

    def _popup_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    xpath_text.bind("<Button-3>", _popup_menu, add=True)

    enable_regex_var = tk.BooleanVar(master=root, value=DEFAULT_ENABLE_REGEX.get(field_name, False))

    ttk.Label(card, text="Regex：", style="IDE.Muted.TLabel") \
        .grid(row=0, column=2, sticky="w", padx=(0, 6), pady=(2, 2))
    ttk.Checkbutton(
        card, variable=enable_regex_var, style="IDE.TCheckbutton",
        command=update_preview
    ).grid(row=0, column=3, sticky="w", padx=(0, 10), pady=(2, 2))

    regex_key = field_name

    preset_values = ["（选择快捷正则）"] + list(QUICK_REGEX_PRESETS.keys())
    preset_combo = ttk.Combobox(card, values=preset_values, state="readonly", width=18)
    preset_combo.current(0)
    preset_combo.grid(row=0, column=4, sticky="w", padx=(0, 10), pady=(2, 2))

    # 禁止在下拉列表上通过鼠标滚轮误触切换选项
    preset_combo.bind("<MouseWheel>", lambda e: "break")
    preset_combo.bind("<Button-4>", lambda e: "break")
    preset_combo.bind("<Button-5>", lambda e: "break")

    regex_entry = tk.Entry(
        card, width=28, font=FONT_CODE_SM,
        bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
        relief="flat", highlightthickness=1,
        highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
    )
    regex_entry.insert(0, DEFAULT_REGEX.get(regex_key, r"\d+"))
    regex_entry.grid(row=0, column=5, sticky="ew", pady=(2, 2))
    bind_live_update_to_entry(regex_entry)
    enable_entry_undo(regex_entry)

    def on_preset_selected(_=None):
        label = preset_combo.get()
        if label in QUICK_REGEX_PRESETS:
            regex_entry.delete(0, "end")
            regex_entry.insert(0, QUICK_REGEX_PRESETS[label])
            enable_regex_var.set(True)
            update_preview()
        return "break"

    preset_combo.bind("<<ComboboxSelected>>", on_preset_selected, add=True)

    widget_dict[field_name] = {
        "xpath": xpath_text,
        "enable_var": enable_regex_var,
        "regex_key": regex_key,
        "regex_entry": regex_entry,
        "use_field_var": use_field_var,
        "preset_combo": preset_combo,
        "default_xpath": default_xpath,
    }

# ===================== GOV 显示隐藏 =====================
def toggle_gov_fields_visibility():
    if enable_gov_fields.get():
        gov_fields_container.pack(fill=tk.X, padx=6, pady=(0, 8))
    else:
        gov_fields_container.pack_forget()
    scrollable_frame.update_idletasks()
    canvas.configure(scrollregion=canvas.bbox("all"))
    update_preview()

# ===================== 写入 / 重置按钮逻辑 =====================
def write_normal():
    try:
        spiders_dir = spiders_entry.get().strip()
        if spiders_dir == SPIDERS_PLACEHOLDER:
            spiders_dir = ""
        set_status("正在写入 Spider 文件...", IDE_WARN)
        spider_name, class_name, out_file = write_spider_to_cn_folder(
            spiders_dir=spiders_dir,
            cn_name=cn_entry.get(),
            raw_url=url_entry.get(),
            suffix="",
            overwrite=True
        )
        set_status("写入成功", IDE_OK)
        messagebox.showinfo("成功", f"已写入：\n{out_file}\n\nspider.name={spider_name}\nclass={class_name}")
    except Exception as e:
        set_status("运行错误", IDE_ERR)
        messagebox.showerror("运行错误", str(e))

def write_gk():
    try:
        spiders_dir = spiders_entry.get().strip()
        if spiders_dir == SPIDERS_PLACEHOLDER:
            spiders_dir = ""
        set_status("正在写入 Spider_gk 文件...", IDE_WARN)
        spider_name, class_name, out_file = write_spider_to_cn_folder(
            spiders_dir=spiders_dir,
            cn_name=cn_entry.get(),
            raw_url=url_entry.get(),
            suffix="_gk",
            overwrite=True
        )
        set_status("写入成功", IDE_OK)
        messagebox.showinfo("成功", f"已写入：\n{out_file}\n\nspider.name={spider_name}\nclass={class_name}")
    except Exception as e:
        set_status("运行错误", IDE_ERR)
        messagebox.showerror("运行错误", str(e))

def reset_all():
    # 1) 清空 URL/目录名
    url_entry.delete(0, "end")
    cn_entry.delete(0, "end")
    set_placeholder_if_empty(url_entry, URL_PLACEHOLDER)
    set_placeholder_if_empty(cn_entry, CN_NAME_PLACEHOLDER)

    # 2) 关闭政府字段并隐藏
    enable_gov_fields.set(False)
    toggle_gov_fields_visibility()

    # 3) 恢复 list 字段默认 XPath/Regex
    for field, info in list_widgets.items():
        # XPath 默认
        default_xpath = DEFAULT_LIST_FIELDS.get(field, "")
        info["xpath"].configure(state="normal")
        info["xpath"].delete("1.0", "end")
        info["xpath"].insert("1.0", default_xpath)
        # 启用字段默认（列表字段默认都启用）
        info["use_field_var"].set(True)
        # Regex 勾选默认
        info["enable_var"].set(DEFAULT_ENABLE_REGEX.get(field, False))
        # Regex 内容默认
        info["regex_entry"].delete(0, "end")
        info["regex_entry"].insert(0, DEFAULT_REGEX.get(field, r"\d+"))
        # 下拉默认
        if info.get("preset_combo"):
            info["preset_combo"].current(0)

    # 4) 恢复 detail 字段默认 XPath/Regex + use_field
    for field, info in detail_widgets.items():
        default_xpath = DEFAULT_DETAIL_FIELDS.get(field, GOV_DETAIL_FIELDS.get(field, ""))
        info["xpath"].configure(state="normal")
        info["xpath"].delete("1.0", "end")
        info["xpath"].insert("1.0", default_xpath)

        # 详情字段默认启用（包括 gov 的 use_field_var，也恢复为 True）
        info["use_field_var"].set(True)

        info["enable_var"].set(DEFAULT_ENABLE_REGEX.get(field, False))
        info["regex_entry"].delete(0, "end")
        info["regex_entry"].insert(0, DEFAULT_REGEX.get(field, r"\d+"))
        if info.get("preset_combo"):
            info["preset_combo"].current(0)

    set_status("已重置为默认值", IDE_OK)
    update_preview()

def choose_spiders_dir():
    path = filedialog.askdirectory()
    if path:
        spiders_entry.delete(0, "end")
        spiders_entry.insert(0, path)
        spiders_entry.configure(fg=IDE_FG)
        update_preview()

# ===================== GUI =====================
root = tk.Tk()
root.title("Scrapy Portia Spider Generator")
root.geometry("1400x900")
root.minsize(1100, 720)
root.configure(bg=IDE_BG)

enable_gov_fields = tk.BooleanVar(master=root, value=False)

style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass

style.configure("IDE.TFrame", background=IDE_BG)
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

# spiders 路径输入行（✅可直接粘贴）
spiders_row = ttk.Frame(top, style="IDE.TFrame")
spiders_row.pack(fill=tk.X, pady=(10, 0))
ttk.Label(spiders_row, text="spiders 路径：", style="IDE.TLabel").pack(side=tk.LEFT, padx=(0, 8))

spiders_entry = tk.Entry(
    spiders_row, font=("Consolas", 12),
    bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
    relief="flat", highlightthickness=1,
    highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
)
spiders_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
spiders_entry.bind("<FocusIn>", lambda e: clear_placeholder_on_focus(spiders_entry, SPIDERS_PLACEHOLDER), add=True)
spiders_entry.bind("<FocusOut>", lambda e: (set_placeholder_if_empty(spiders_entry, SPIDERS_PLACEHOLDER), update_preview()), add=True)
spiders_entry.bind("<KeyRelease>", lambda e: update_preview(), add=True)
enable_entry_undo(spiders_entry)

ttk.Button(spiders_row, text="浏览...", style="IDE.TButton", command=choose_spiders_dir).pack(side=tk.LEFT, padx=(8, 0))

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
url_entry.bind("<FocusIn>", lambda e: clear_placeholder_on_focus(url_entry, URL_PLACEHOLDER), add=True)
url_entry.bind("<FocusOut>", lambda e: (set_placeholder_if_empty(url_entry, URL_PLACEHOLDER), update_preview()), add=True)
url_entry.bind("<KeyRelease>", lambda e: update_preview(), add=True)
enable_entry_undo(url_entry)

# 中文目录名行
cn_row = ttk.Frame(top, style="IDE.TFrame")
cn_row.pack(fill=tk.X, pady=(8, 0))
ttk.Label(cn_row, text="目录名（中文）：", style="IDE.TLabel").pack(side=tk.LEFT, padx=(0, 8))

cn_entry = tk.Entry(
    cn_row, font=("Microsoft YaHei UI", 12),
    bg=IDE_BG2, fg=IDE_FG, insertbackground=IDE_FG,
    relief="flat", highlightthickness=1,
    highlightbackground=IDE_PANEL, highlightcolor=IDE_ACCENT
)
cn_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
cn_entry.bind("<FocusIn>", lambda e: clear_placeholder_on_focus(cn_entry, CN_NAME_PLACEHOLDER), add=True)
cn_entry.bind("<FocusOut>", lambda e: (set_placeholder_if_empty(cn_entry, CN_NAME_PLACEHOLDER), update_preview()), add=True)
cn_entry.bind("<KeyRelease>", lambda e: update_preview(), add=True)
enable_entry_undo(cn_entry)

# 主体区域（仅字段配置，无预览）
main = ttk.Frame(root, style="IDE.TFrame")
main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=12, pady=8)

# 字段配置（滚动）
left = ttk.Frame(main, style="IDE.TFrame")
left.pack(fill=tk.BOTH, expand=True)

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

scrollable_frame.bind("<Configure>", on_frame_configure, add=True)
canvas.bind("<Configure>", on_canvas_configure, add=True)

def _on_mousewheel(event):
    """
    仅在字段配置区域内滚动 canvas，不再使用 bind_all，避免影响其他控件。
    """
    sys_name = platform.system()
    if sys_name == "Windows":
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    elif sys_name == "Darwin":
        canvas.yview_scroll(int(-1 * event.delta), "units")
    else:
        if event.num == 4:
            canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            canvas.yview_scroll(1, "units")

# 直接在 canvas 和可滚动区域上绑定鼠标滚轮，不使用 bind_all / Enter / Leave
if platform.system() in ("Windows", "Darwin"):
    canvas.bind("<MouseWheel>", _on_mousewheel, add=True)
    scrollable_frame.bind("<MouseWheel>", _on_mousewheel, add=True)
else:
    canvas.bind("<Button-4>", _on_mousewheel, add=True)
    canvas.bind("<Button-5>", _on_mousewheel, add=True)
    scrollable_frame.bind("<Button-4>", _on_mousewheel, add=True)
    scrollable_frame.bind("<Button-5>", _on_mousewheel, add=True)

# 列表页配置区
list_frame = ttk.LabelFrame(scrollable_frame, text="列表页字段", style="IDE.TLabelframe")
list_frame.pack(padx=6, pady=(6, 8), fill=tk.X)
for k, v in DEFAULT_LIST_FIELDS.items():
    build_field_row(list_frame, k, v, list_widgets, is_gov=False)

# 详情页配置区
detail_frame = ttk.LabelFrame(scrollable_frame, text="详情页字段", style="IDE.TLabelframe")
detail_frame.pack(padx=6, pady=(0, 10), fill=tk.X)
for k, v in DEFAULT_DETAIL_FIELDS.items():
    build_field_row(detail_frame, k, v, detail_widgets, is_gov=False)

gov_check_row = ttk.Frame(detail_frame, style="IDE.TFrame")
gov_check_row.pack(fill=tk.X, padx=6, pady=(8, 6))

gov_fields_container = ttk.Frame(detail_frame, style="IDE.TFrame")

gov_cb = ttk.Checkbutton(
    gov_check_row,
    text="启用政府索引字段",
    variable=enable_gov_fields,
    style="IDE.TCheckbutton",
    command=toggle_gov_fields_visibility
)
gov_cb.pack(anchor="w")

for k, v in GOV_DETAIL_FIELDS.items():
    build_field_row(gov_fields_container, k, v, detail_widgets, is_gov=True)

toggle_gov_fields_visibility()

# 底部按钮栏（✅按你指定顺序）
bottom = ttk.Frame(root, style="IDE.TFrame")
bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=12, pady=(6, 10))

btns = ttk.Frame(bottom, style="IDE.TFrame")
btns.pack(side=tk.LEFT)

ttk.Button(btns, text="写入 Spider", style="IDE.Primary.TButton", command=write_normal).pack(side=tk.LEFT, padx=(0, 8))
ttk.Button(btns, text="写入 Spider_gk", style="IDE.TButton", command=write_gk).pack(side=tk.LEFT, padx=(0, 8))
ttk.Button(btns, text="重置", style="IDE.TButton", command=reset_all).pack(side=tk.LEFT)

status_var = tk.StringVar(value="就绪")
status_label = ttk.Label(bottom, textvariable=status_var, style="IDE.TLabel")
status_label.pack(side=tk.RIGHT)

# 初始化占位符 + 预览
set_placeholder_if_empty(spiders_entry, SPIDERS_PLACEHOLDER)
set_placeholder_if_empty(url_entry, URL_PLACEHOLDER)
set_placeholder_if_empty(cn_entry, CN_NAME_PLACEHOLDER)
set_status("就绪", IDE_FG)
update_preview()

root.mainloop()
