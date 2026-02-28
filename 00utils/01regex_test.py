import re

def test_regex(pattern, text):
    print("="*60)
    print(f"🔍 正则表达式: {pattern}")
    print(f"📄 测试文本: {text}")
    print("="*60)

    try:
        regex = re.compile(pattern)
    except re.error as e:
        print("❌ 正则表达式有语法错误：", e)
        return

    # ------- 全部匹配 findall -------
    findall_res = regex.findall(text)
    print("\n📌 findall 匹配结果：")
    if findall_res:
        for idx, item in enumerate(findall_res, 1):
            print(f"  {idx}. {item}")
    else:
        print("  ❌ 无匹配结果")

    # ------- finditer 输出位置 -------
    print("\n📌 finditer 详细匹配信息：")
    found = False
    for m in regex.finditer(text):
        found = True
        print(f"  ✔ 匹配到：{m.group()}")
        print(f"    位置: {m.span()}")
        if m.groups():
            print(f"    分组: {m.groups()}")
        print("  ---")
    if not found:
        print("  ❌ 无匹配信息")

    # ------- search 搜索 -------
    print("\n📌 search 搜索结果：")
    m = regex.search(text)
    if m:
        print(f"  ✔ 第一次出现：{m.group()}  位置: {m.span()}")
    else:
        print("  ❌ 文本中未找到匹配")

    # ------- match 从头匹配 -------
    print("\n📌 match 从头匹配结果：")
    m = regex.match(text)
    if m:
        print(f"  ✔ 开头匹配成功：{m.group()}  位置: {m.span()}")
    else:
        print("  ❌ 文本开头未匹配")

    print("="*60)


# ===========================
# 示例使用（你可以自由修改）
# ===========================

if __name__ == "__main__":
    pattern = r"index_(\d+)\.html"
    text = "https://tyj.gd.gov.cn/tyxw_zyxw/index_20.html"

    test_regex(pattern, text)
