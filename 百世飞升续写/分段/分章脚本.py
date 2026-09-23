# -*- coding: utf-8 -*-
"""把 1-105.txt（实为 1—111 章）拆成一章一个文件，输出到 ../分章/。

用法：
    cd F:/novel/百世飞升续写
    python 分段/分章脚本.py            # 预览
    python 分段/分章脚本.py --write    # 实际写出
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, '1-105.txt')
DST = os.path.join(ROOT, '分章')

HEAD = re.compile(r'^#\s*第(\d+)章\s*(.*)$')


def parse(text):
    lines = text.split('\n')
    marks = [(i, HEAD.match(l)) for i, l in enumerate(lines) if HEAD.match(l)]
    out = []
    for k, (i, m) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        num = int(m.group(1))
        name = m.group(2).strip()
        body = '\n'.join(lines[i:end]).strip() + '\n'
        out.append((num, name, body))
    return out


def main():
    write = '--write' in sys.argv
    text = open(SRC, encoding='utf-8').read()
    chaps = parse(text)

    if not chaps:
        print('没解析到章节，检查 %s' % SRC)
        return

    nums = [c[0] for c in chaps]
    gaps = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
    print('共 %d 章，第 %d—%d 章' % (len(chaps), nums[0], nums[-1]))
    if gaps:
        print('[!] 缺章号：%s' % gaps)
    else:
        print('[OK] 章号连续，无缺口')

    total_src = len(re.findall(r'[\u4e00-\u9fff]', text))
    total_out = sum(len(re.findall(r'[\u4e00-\u9fff]', c[2])) for c in chaps)
    print('汉字：原文 %d / 拆分合计 %d %s' % (
        total_src, total_out, '[OK]' if total_src == total_out else '[!!] 不一致！'))

    if not write:
        print('\n（预览模式，加 --write 才会写出文件）')
        for num, name, body in chaps[:3]:
            print('  %s' % fname(num, name))
        print('  ...')
        for num, name, body in chaps[-2:]:
            print('  %s' % fname(num, name))
        return

    os.makedirs(DST, exist_ok=True)
    for num, name, body in chaps:
        path = os.path.join(DST, fname(num, name))
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
    print('\n[OK] 已写出 %d 个文件到 %s' % (len(chaps), DST))


def fname(num, name):
    return '第%03d章_%s.md' % (num, name)


if __name__ == '__main__':
    main()