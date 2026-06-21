#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取Unicode官方emoji数据文件中的所有emoji字符
输出为标准CSV格式，方便Java读取到HashSet
"""

import re
import csv
import argparse
from pathlib import Path


def has_surrogate(emoji):
    """判断emoji在Java(UTF-16)中是否包含代理项char。

    Java字符串以UTF-16存储，码点 >= U+10000 的补充字符会被表示为
    一对代理项(surrogate pair)，此时 Character.isSurrogate(ch) 为true。
    因此只要emoji中存在任一码点 >= U+10000，就含代理项。
    """
    return any(ord(c) > 0xFFFF for c in emoji)


def parse_emoji_test(file_path):
    """解析emoji-test.txt文件"""
    emojis = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 格式: 1F600 ; fully-qualified # 😀 E1.0 grinning face
            match = re.match(r'^([0-9A-F\s]+)\s*;', line)
            if match:
                code_points = match.group(1).strip().split()
                # 将十六进制码点转换为实际emoji字符
                emoji = ''.join(chr(int(cp, 16)) for cp in code_points)
                emojis.add(emoji)

    return emojis


def parse_emoji_sequences(file_path):
    """解析emoji-sequences.txt文件"""
    emojis = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 格式: 231A..231B ; Basic_Emoji ; watch..hourglass done
            # 或: 23F0 ; Basic_Emoji ; alarm clock
            match = re.match(r'^([0-9A-F]+)(?:\.\.([0-9A-F]+))?\s*;', line)
            if match:
                start_cp = match.group(1)
                end_cp = match.group(2)

                if end_cp:
                    # 范围形式
                    for cp in range(int(start_cp, 16), int(end_cp, 16) + 1):
                        emojis.add(chr(cp))
                else:
                    # 单个码点
                    emojis.add(chr(int(start_cp, 16)))
            else:
                # 尝试匹配多个码点的序列
                match = re.match(r'^([0-9A-F\s]+)\s*;', line)
                if match:
                    code_points = match.group(1).strip().split()
                    emoji = ''.join(chr(int(cp, 16)) for cp in code_points)
                    emojis.add(emoji)

    return emojis


def parse_emoji_zwj_sequences(file_path):
    """解析emoji-zwj-sequences.txt文件"""
    emojis = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue

            # 格式: 1F468 200D 2764 FE0F 200D 1F468 ; RGI_Emoji_ZWJ_Sequence ; couple with heart
            match = re.match(r'^([0-9A-F\s]+)\s*;', line)
            if match:
                code_points = match.group(1).strip().split()
                # 将十六进制码点转换为实际emoji字符
                emoji = ''.join(chr(int(cp, 16)) for cp in code_points)
                emojis.add(emoji)

    return emojis


def main():
    parser = argparse.ArgumentParser(
        description="提取Unicode官方emoji数据文件中的所有emoji并输出为CSV")
    parser.add_argument(
        '--mask-surrogate', action='store_true',
        help="筛除在Java(UTF-16)中含代理项char的emoji(即任一码点>=U+10000)，"
             "只保留全部码点都在BMP内的emoji，输出到 emojis-mask.csv")
    args = parser.parse_args()

    # 设置文件路径
    res_dir = Path(__file__).parent / 'res'
    if args.mask_surrogate:
        output_file = Path(__file__).parent / 'emojis-mask.csv'
    else:
        output_file = Path(__file__).parent / 'emojis.csv'

    # 提取所有emoji
    print("正在提取emoji-test.txt...")
    emojis_test = parse_emoji_test(res_dir / 'emoji-test.txt')
    print(f"  提取到 {len(emojis_test)} 个emoji")

    print("正在提取emoji-sequences.txt...")
    emojis_seq = parse_emoji_sequences(res_dir / 'emoji-sequences.txt')
    print(f"  提取到 {len(emojis_seq)} 个emoji")

    print("正在提取emoji-zwj-sequences.txt...")
    emojis_zwj = parse_emoji_zwj_sequences(res_dir / 'emoji-zwj-sequences.txt')
    print(f"  提取到 {len(emojis_zwj)} 个emoji")

    # 合并所有emoji（自动去重）
    all_emojis = emojis_test | emojis_seq | emojis_zwj
    print(f"\n总计提取到 {len(all_emojis)} 个唯一emoji")

    # 按需筛除含代理项(补充字符)的emoji
    if args.mask_surrogate:
        before = len(all_emojis)
        all_emojis = {e for e in all_emojis if not has_surrogate(e)}
        print(f"已筛除含代理项的emoji {before - len(all_emojis)} 个，"
              f"剩余 {len(all_emojis)} 个全BMP码点的emoji")

    # 排序（按照码点）
    sorted_emojis = sorted(all_emojis, key=lambda e: [ord(c) for c in e])

    # 写入CSV文件
    # 格式：每行一个emoji，使用单列 "emoji" 作为标题
    print(f"\n正在写入到 {output_file}...")
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        # lineterminator='\n' 强制使用 LF 行尾；csv 模块默认写 CRLF(\r\n)
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
        writer.writerow(['emoji'])  # CSV标题行
        for emoji in sorted_emojis:
            writer.writerow([emoji])

    print(f"✅ 完成！已保存到 {output_file}")
    print(f"\nCSV格式：")
    print("  - 第一行为标题：emoji")
    print("  - 每行一个emoji字符")
    print("  - 使用UTF-8编码")
    print("  - 标准CSV格式，可直接被Java读取")


if __name__ == '__main__':
    main()
