import os
import json
import re
import hashlib
from collections import defaultdict


# ======================================================
# 通用工具函数
# ======================================================

def normalize_string(s):
    if not s:
        return ""
    return re.sub(r'\s+', '', s).lower()


def normalize_content(s):
    if not s:
        return ""
    return re.sub(r'\s+', ' ', s).strip()


def content_hash(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def _norm_key(k: str) -> str:
    return re.sub(r'[^a-z0-9]', '', (k or '').lower())


def _to_text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (int, float, bool)):
        return str(v).strip()
    if isinstance(v, str):
        return v.strip()
    try:
        return json.dumps(v, ensure_ascii=False).strip()
    except Exception:
        return ""


def extract_field(json_data, field_name: str):
    target = _norm_key(field_name)

    if isinstance(json_data, dict):
        for k, v in json_data.items():
            if _norm_key(k) == target:
                return _to_text(v)
        for v in json_data.values():
            res = extract_field(v, field_name)
            if res is not None:
                return res

    elif isinstance(json_data, list):
        for item in json_data:
            res = extract_field(item, field_name)
            if res is not None:
                return res

    return None


def extract_title(data):
    return extract_field(data, "title") or ""


def extract_content(data):
    res = extract_field(data, "content")
    return res if res is not None else ""


def extract_src_url(data):
    return extract_field(data, "src_url") or "【无src_url】"


def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        with open(path, 'r', encoding='gbk') as f:
            return json.load(f)


# ======================================================
# 功能 1：查找指定 Title
# ======================================================

def find_folders_by_title(root_path, target_title):
    norm_target = normalize_string(target_title)
    folder_map = defaultdict(set)
    checked = 0

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        title = extract_title(data)
                        if normalize_string(title) == norm_target:
                            folder = os.path.dirname(dirpath)
                            src_url = extract_src_url(data)
                            folder_map[folder].add(src_url)
                            print(f"✅ 匹配：{path}")
                            print(f"   📁 {folder}")
                            print(f"   🔗 src_url：{src_url}")
                    except Exception as e:
                        print(f"❌ 失败：{path} - {e}")

    print(f"\n📊 共检查 {checked} 个 JSON 文件")

    if not folder_map:
        print(f"❓ 未找到 Title：{target_title}")
        return

    print(f"🎉 找到 {len(folder_map)} 个文件夹：")
    for i, (folder, urls) in enumerate(sorted(folder_map.items()), 1):
        print(f"   {i}. {folder}")
        print(f"      🔗 src_url：{' | '.join(sorted(urls))}")


# ======================================================
# 功能 2：检查指定 Title 的 content 是否为空
# ======================================================

def check_title_content_empty(root_path, target_title):
    norm_target = normalize_string(target_title)
    checked = 0
    found = False

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        title = extract_title(data)
                        if normalize_string(title) == norm_target:
                            found = True
                            content = extract_content(data)
                            src_url = extract_src_url(data)
                            folder = os.path.dirname(dirpath)
                            print(f"\n📄 {path}")
                            print(f"📁 {folder}")
                            print(f"🔗 src_url：{src_url}")
                            print(f"📝 content：{'❌ 为空' if not content else '✅ 非空'}")
                    except Exception as e:
                        print(f"❌ 失败：{path} - {e}")

    print(f"\n📊 共检查 {checked} 个 JSON 文件")
    if not found:
        print(f"❓ 未找到 Title：{target_title}")


# ======================================================
# 功能 3：查找重复 Title
# ======================================================

def find_duplicate_titles(root_path):
    title_map = defaultdict(list)
    checked = 0

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        title = extract_title(data)
                        src_url = extract_src_url(data)
                        folder = os.path.dirname(dirpath)
                        norm = normalize_string(title)
                        if norm:
                            title_map[norm].append((path, folder, title, src_url))
                    except Exception:
                        pass

    duplicates = {k: v for k, v in title_map.items() if len(v) > 1}

    print(f"\n📊 共检查 {checked} 个 JSON 文件")

    if not duplicates:
        print("✅ 未发现重复 Title")
        return

    for idx, items in enumerate(duplicates.values(), 1):
        print(f"\n⚠️ 重复 Title 组 {idx}")
        for i, (path, folder, title, src_url) in enumerate(items, 1):
            print(f"   {i}. {path}")
            print(f"      📁 {folder}")
            print(f"      🏷️ {title}")
            print(f"      🔗 src_url：{src_url}")


# ======================================================
# 功能 4：查找所有 content 为空的文件
# ======================================================

def find_all_empty_content_files(root_path):
    checked = 0
    empty_list = []

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        if not extract_content(data):
                            title = extract_title(data)
                            src_url = extract_src_url(data)
                            folder = os.path.dirname(dirpath)
                            empty_list.append(path)
                            print(f"❌ 空 content：{path}")
                            print(f"   📁 {folder}")
                            print(f"   🏷️ {title}")
                            print(f"   🔗 src_url：{src_url}")
                    except Exception:
                        pass

    print(f"\n📊 共检查 {checked} 个 JSON 文件")
    if not empty_list:
        print("✅ 未发现 content 为空的文件")


# ======================================================
# 功能 5：查找指定 src_url
# ======================================================

def find_by_src_url(root_path, target_url):
    norm_target = normalize_string(target_url)
    checked = 0
    found = False

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        src_url = extract_src_url(data)
                        if normalize_string(src_url) == norm_target:
                            found = True
                            title = extract_title(data)
                            folder = os.path.dirname(dirpath)
                            print(f"✅ 命中：{path}")
                            print(f"   📁 {folder}")
                            print(f"   🏷️ {title}")
                            print(f"   🔗 src_url：{src_url}")
                    except Exception:
                        pass

    print(f"\n📊 共检查 {checked} 个 JSON 文件")
    if not found:
        print("❓ 未找到指定 src_url")


# ======================================================
# 功能 6：查找重复 src_url
# ======================================================

def find_duplicate_src_url(root_path):
    url_map = defaultdict(list)
    checked = 0

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        src_url = extract_src_url(data)
                        if src_url != "【无src_url】":
                            title = extract_title(data)
                            folder = os.path.dirname(dirpath)
                            url_map[normalize_string(src_url)].append(
                                (path, folder, title, src_url)
                            )
                    except Exception:
                        pass

    duplicates = {k: v for k, v in url_map.items() if len(v) > 1}

    print(f"\n📊 共检查 {checked} 个 JSON 文件")

    if not duplicates:
        print("✅ 未发现重复 src_url")
        return

    for idx, items in enumerate(duplicates.values(), 1):
        print(f"\n⚠️ 重复 src_url 组 {idx}：{items[0][3]}")
        for i, (path, folder, title, src_url) in enumerate(items, 1):
            print(f"   {i}. {path}")
            print(f"      📁 {folder}")
            print(f"      🏷️ {title}")


# ======================================================
# 功能 7：查找重复 content（真正的）
# ======================================================

def find_duplicate_content(root_path):
    content_map = defaultdict(list)
    checked = 0

    for dirpath, _, filenames in os.walk(root_path):
        if os.path.basename(dirpath).lower() == 'meta':
            for fn in filenames:
                if fn.lower().endswith('.json'):
                    checked += 1
                    path = os.path.join(dirpath, fn)
                    try:
                        data = load_json(path)
                        raw = extract_content(data)
                        if not raw:
                            continue
                        norm = normalize_content(raw)
                        h = content_hash(norm)
                        title = extract_title(data)
                        src_url = extract_src_url(data)
                        folder = os.path.dirname(dirpath)
                        content_map[h].append((path, folder, title, src_url, norm[:120]))
                    except Exception:
                        pass

    duplicates = {k: v for k, v in content_map.items() if len(v) > 1}

    print(f"\n📊 共检查 {checked} 个 JSON 文件")

    if not duplicates:
        print("✅ 未发现重复 content")
        return

    for idx, items in enumerate(duplicates.values(), 1):
        print(f"\n⚠️ 重复 content 组 {idx}")
        print(f"📄 内容预览：{items[0][4]}...")
        for i, (path, folder, title, src_url, _) in enumerate(items, 1):
            print(f"   {i}. {path}")
            print(f"      📁 {folder}")
            print(f"      🏷️ {title}")
            print(f"      🔗 src_url：{src_url}")


# ======================================================
# 主程序
# ======================================================

def get_valid_path():
    while True:
        path = input("\n请输入文件夹路径：").strip()
        if os.path.exists(path):
            return path
        print("❌ 路径不存在")


def main():
    last_path = None

    while True:
        if not last_path:
            last_path = get_valid_path()

        print(f"\n📂 当前路径：{last_path}")
        print("1 - 查找指定 Title")
        print("2 - 检查指定 Title 的 content 是否为空")
        print("3 - 查找重复 Title")
        print("4 - 查找重复 content")
        print("5 - 查找所有 content 为空的文件")
        print("6 - 查找指定 src_url")
        print("7 - 查找重复 src_url")
        print("c - 切换路径")
        print("q - 退出")

        choice = input("请选择功能（1-7/c/q）：").strip().lower()

        if choice == 'q':
            print("👋 程序退出")
            break
        elif choice == 'c':
            last_path = get_valid_path()
        elif choice == '1':
            find_folders_by_title(last_path, input("请输入 Title："))
        elif choice == '2':
            check_title_content_empty(last_path, input("请输入 Title："))
        elif choice == '3':
            find_duplicate_titles(last_path)
        elif choice == '4':
            find_duplicate_content(last_path)
        elif choice == '5':
            find_all_empty_content_files(last_path)
        elif choice == '6':
            find_by_src_url(last_path, input("请输入 src_url："))
        elif choice == '7':
            find_duplicate_src_url(last_path)
        else:
            print("❌ 无效选择")



if __name__ == "__main__":
    main()
