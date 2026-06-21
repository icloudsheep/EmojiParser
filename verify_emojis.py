#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立验证 emojis.csv 与 emojis-mask.csv 的正确性。

刻意不复用 extract_emojis.py 的解析函数：改用一套独立实现从 res/
重新推导“期望集合”，再与 CSV 实际内容双向比对。这样解析逻辑里的
潜在 bug 不会被复制到验证侧。
"""

import re
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent
RES = ROOT / 'res'


def expected_from_sources():
    """独立地从三个源文件抽取期望的 emoji 集合。

    规则：取每行分号前的字段，按空白拆成十六进制码点；遇到 A..B
    形式按范围展开（单码点）。其余多码点组合直接拼成一个序列。
    """
    expected = set()
    for fname in ('emoji-test.txt', 'emoji-sequences.txt',
                  'emoji-zwj-sequences.txt'):
        for raw in (RES / fname).read_text(encoding='utf-8').splitlines():
            line = raw.strip()
            if not line or line.startswith('#'):
                continue
            if ';' not in line:
                continue
            field = line.split(';', 1)[0].strip()
            # 范围形式：单个 token 形如 231A..231B
            if '..' in field:
                lo, hi = field.split('..')
                for cp in range(int(lo, 16), int(hi, 16) + 1):
                    expected.add(chr(cp))
                continue
            tokens = field.split()
            if not tokens:
                continue
            if not all(re.fullmatch(r'[0-9A-Fa-f]+', t) for t in tokens):
                continue
            expected.add(''.join(chr(int(t, 16)) for t in tokens))
    return expected


def read_csv_emojis(path):
    """读取 CSV，返回 (emoji 列表, 问题列表)。同时检查格式。"""
    problems = []
    raw = path.read_bytes()
    if raw[:3] == b'\xef\xbb\xbf':
        problems.append('文件带 UTF-8 BOM（Java 读取首行会混入 BOM）')
    rows = list(csv.reader(path.open(encoding='utf-8')))
    if not rows or rows[0] != ['emoji']:
        problems.append(f'首行标题不是 [emoji]，而是 {rows[0] if rows else "空"}')
    emojis = [r[0] for r in rows[1:]]
    # 多列行检查
    for i, r in enumerate(rows[1:], start=2):
        if len(r) != 1:
            problems.append(f'第{i}行列数={len(r)}（非单列）: {r}')
    return emojis, problems


def has_surrogate(e):
    return any(ord(c) > 0xFFFF for c in e)


def check_file(path, expected, mask):
    print(f'\n===== 验证 {path.name} =====')
    if not path.exists():
        print(f'  ✗ 文件不存在')
        return False
    emojis, problems = read_csv_emojis(path)
    ok = True

    # 1. 格式问题
    for p in problems:
        print(f'  ✗ 格式: {p}')
        ok = False

    # 2. 重复检查
    dups = len(emojis) - len(set(emojis))
    if dups:
        print(f'  ✗ 存在 {dups} 个重复行')
        ok = False

    # 3. 空行检查
    empties = sum(1 for e in emojis if e == '')
    if empties:
        print(f'  ✗ 存在 {empties} 个空 emoji 行')
        ok = False

    actual = set(emojis)
    target = {e for e in expected if not has_surrogate(e)} if mask else expected

    # 4. 双向比对
    missing = target - actual       # 源里有、CSV 缺
    extra = actual - target         # CSV 有、源里没有（解析杂质）
    if missing:
        print(f'  ✗ 缺失 {len(missing)} 个（源文件有但 CSV 没有），示例: {list(missing)[:5]}')
        ok = False
    if extra:
        print(f'  ✗ 多余 {len(extra)} 个（CSV 有但源文件无，疑似解析杂质），示例: {list(extra)[:5]}')
        ok = False

    # 5. mask 专项：不得含代理项，且必须是全量集的子集
    if mask:
        bad = [e for e in actual if has_surrogate(e)]
        if bad:
            print(f'  ✗ mask 文件仍含 {len(bad)} 个代理项 emoji，示例: {bad[:5]}')
            ok = False

    if ok:
        print(f'  ✓ 通过：{len(actual)} 个 emoji，与独立推导的期望集合完全一致')
    return ok


def main():
    expected = expected_from_sources()
    print(f'独立从 res/ 推导出期望集合：{len(expected)} 个唯一 emoji')

    full_ok = check_file(ROOT / 'emojis.csv', expected, mask=False)
    mask_ok = check_file(ROOT / 'emojis-mask.csv', expected, mask=True)

    # 交叉检查：mask 必须是 full 的真子集
    print('\n===== 交叉检查 =====')
    full = set([r[0] for r in csv.reader((ROOT / 'emojis.csv').open(encoding='utf-8'))][1:])
    maskset = set([r[0] for r in csv.reader((ROOT / 'emojis-mask.csv').open(encoding='utf-8'))][1:])
    if maskset <= full:
        print(f'  ✓ emojis-mask.csv 是 emojis.csv 的子集')
    else:
        print(f'  ✗ mask 中有 {len(maskset - full)} 项不在全量文件中')
        mask_ok = False
    if maskset == {e for e in full if not has_surrogate(e)}:
        print(f'  ✓ emojis-mask.csv 恰好等于「全量去代理项」的结果')
    else:
        print(f'  ✗ mask 与「全量去代理项」不一致')
        mask_ok = False

    print('\n' + ('✅ 全部验证通过' if full_ok and mask_ok else '❌ 验证未通过'))
    sys.exit(0 if full_ok and mask_ok else 1)


if __name__ == '__main__':
    main()
