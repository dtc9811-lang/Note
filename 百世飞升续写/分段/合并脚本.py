# -*- coding: utf-8 -*-
"""
把 修改/ 目录下改好的 19 份重新合成一本，并做体检。

用法：
    cd F:/novel/百世飞升续写
    python 分段/合并脚本.py            # 预览体检
    python 分段/合并脚本.py --write    # 写出 1-105.改后.txt

规则：
  - 按文件名顺序读 修改/01_*.md ... 19_*.md
  - 提取所有 "# 第N章 标题" 块，按出现顺序重新编号（因为可能插了补写章）
  - 没改的份（修改/ 里不存在）自动用 分段/ 里的原文补上
"""
import os, re, sys, glob, datetime, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SEG  = HERE
MOD  = os.path.join(ROOT, '修改')
OUT  = os.path.join(ROOT, '1-105.改后.txt')

CH_RE = re.compile(r'^#\s*第(\d+)章\s*(.*)$')

def blocks_from(text):
    """返回 [(title, [lines])]"""
    lines = text.split('\n')
    idx = [i for i, l in enumerate(lines) if CH_RE.match(l)]
    res = []
    for k, i in enumerate(idx):
        m = CH_RE.match(lines[i])
        end = idx[k+1] if k+1 < len(idx) else len(lines)
        res.append((m.group(2).strip(), lines[i+1:end]))
    return res

def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))

def main():
    write = '--write' in sys.argv
    segs = sorted(glob.glob(os.path.join(SEG, '[0-9][0-9]_ch*.md')))
    if not segs:
        raise SystemExit('分段/ 里没找到分段文件')

    allblocks = []
    report = []
    for sp in segs:
        base = os.path.basename(sp)
        mp = os.path.join(MOD, base)
        src = mp if os.path.exists(mp) else sp
        tag = '改' if os.path.exists(mp) else '原'
        text = open(src, encoding='utf-8').read()
        bs = blocks_from(text)
        if not bs:
            report.append('  !! %s 没有解析到章节' % base); continue
        tot = sum(cjk('\n'.join(b[1])) for b in bs)
        allblocks.extend(bs)
        report.append('  [%s] %s  %d章  %d字' % (tag, base, len(bs), tot))

    # 重新编号
    out = []
    for i, (title, body) in enumerate(allblocks, 1):
        out.append('# 第%d章 %s' % (i, title))
        out.extend(body)
    result = '\n'.join(out)

    print('=== 分段体检 ===')
    for r in report: print(r)
    print('\n合计 %d 章，%d 汉字' % (len(allblocks), cjk(result)))

    # 逐章长度
    lens = [cjk('\n'.join(b[1])) for b in allblocks]
    if lens:
        short = [(i+1, l) for i, l in enumerate(lens) if l < 500]
        print('最短 %d，中位 %d，最长 %d' % (min(lens), sorted(lens)[len(lens)//2], max(lens)))
        if short:
            print('过短的章（<500字，建议合并或写足）：', short[:20])

    if not write:
        print('\n预览模式，没有写文件。加 --write 才写出。')
        return
    open(OUT, 'w', encoding='utf-8').write(result)
    print('\n已写出 →', OUT)
    print('确认无误后手动覆盖：  mv 1-105.改后.txt 1-105.txt')
    print('（覆盖前先备份 1-105.txt）')

if __name__ == '__main__':
    main()