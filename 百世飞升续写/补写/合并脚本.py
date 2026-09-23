# -*- coding: utf-8 -*-
"""
把 补写/ 目录下的补写章与重写章合并进 1-105.txt，并重新编号。

用法：
    cd F:/novel/百世飞升续写
    python 补写/合并脚本.py            # 预览（不写文件）
    python 补写/合并脚本.py --write    # 真正写入 1-105.merged.txt

规则：
  - 文件名含 "chNN后"  → 视为【补写】，插到第 NN 章之后
  - 文件名含 "chNN_" 且有 "重写" → 视为【重写】，替换第 NN 章正文
  - 只读取每个 md 里 "## 正文" 与下一个 "## " 之间的内容
  - 占位提示（以 "（在此写入正文" 开头）会被跳过

安全：
  - 默认只预览，必须加 --write 才写文件
  - 写入前自动备份 1-105.txt
"""
import os, re, sys, shutil, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC  = os.path.join(ROOT, '1-105.txt')
OUT  = os.path.join(ROOT, '1-105.merged.txt')

CH_RE = re.compile(r'^#\s*第(\d+)章\s*(.*)$')

def split_chapters(text):
    lines = text.split('\n')
    idx = [i for i, l in enumerate(lines) if CH_RE.match(l)]
    if not idx:
        raise SystemExit('没找到任何 "# 第N章" 标题，检查源文件格式')
    head = lines[:idx[0]]
    chapters = []
    for k, i in enumerate(idx):
        m = CH_RE.match(lines[i])
        end = idx[k+1] if k+1 < len(idx) else len(lines)
        chapters.append({'num': int(m.group(1)), 'title': m.group(2).strip(),
                         'body': lines[i+1:end]})
    return head, chapters

def extract_body(md_path):
    s = open(md_path, encoding='utf-8').read()
    m = re.search(r'^##\s*正文\s*$', s, re.M)
    if not m:
        return None, '没有 "## 正文" 一节'
    rest = s[m.end():]
    m2 = re.search(r'^##\s', rest, re.M)
    body = rest[:m2.start()] if m2 else rest
    body = body.strip('\n')
    if not body.strip() or body.lstrip().startswith('（在此写入正文'):
        return None, '正文还是空的'
    return body, None

def plan():
    ins, rep, warns = {}, {}, []
    for f in sorted(os.listdir(HERE)):
        if not f.endswith('.md') or f == 'README.md':
            continue
        p = os.path.join(HERE, f)
        body, err = extract_body(p)
        m_after = re.search(r'ch(\d+)后', f)
        m_id    = re.search(r'ch(\d+)_', f)
        if '重写' in f and m_id:
            n = int(m_id.group(1))
            if body is None: warns.append('跳过 %s（%s）' % (f, err)); continue
            rep[n] = body
        elif m_after:
            n = int(m_after.group(1))
            if body is None: warns.append('跳过 %s（%s）' % (f, err)); continue
            ins.setdefault(n, []).append((f, body))
        else:
            warns.append('跳过 %s（文件名看不出位置）' % f)
    return ins, rep, warns

def main():
    write = '--write' in sys.argv
    text = open(SRC, encoding='utf-8').read()
    head, chapters = split_chapters(text)
    orig_nums = [c['num'] for c in chapters]
    maxn = max(orig_nums)

    ins, rep, warns = plan()
    for w in warns: print('[警告]', w)
    if not ins and not rep:
        print('没有任何可合并的补写/重写文件。')
        return

    # 重写
    for c in chapters:
        if c['num'] in rep:
            c['body'] = [''] + rep[c['num']].split('\n') + ['']
            print('[重写] 第%d章 %s' % (c['num'], c['title']))
    # 补写
    for n in sorted(ins):
        for fname, body in ins[n]:
            title = re.sub(r'^\d+_ch\d+后?_?', '', os.path.splitext(fname)[0])
            newc = {'num': None, 'title': title, 'body': [''] + body.split('\n') + [''],
                    '_after': n}
            # 找到第 n 章的位置，插到它后面
            for k, c in enumerate(chapters):
                if c['num'] == n:
                    chapters.insert(k+1, newc)
                    break
            else:
                print('[警告] 找不到第%d章，%s 没插入' % (n, fname)); continue
            print('[补写] 插在第%d章之后 ← %s' % (n, fname))

    # 重新编号
    for i, c in enumerate(chapters, 1):
        c['num'] = i

    # 组装
    out = list(head)
    for c in chapters:
        out.append('# 第%d章 %s' % (c['num'], c['title']))
        out.extend(c['body'])
    result = '\n'.join(out)

    print('\n原 %d 章 → 新 %d 章，共 %d 字' %
          (len(orig_nums), len(chapters), len(re.findall(r'[\u4e00-\u9fff]', result))))

    if not write:
        print('\n预览模式，没有写文件。加 --write 才真正写入。')
        return
    bak = SRC + '.bak-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    shutil.copy2(SRC, bak)
    open(OUT, 'w', encoding='utf-8').write(result)
    print('已备份原文件 →', os.path.basename(bak))
    print('已写出 →', OUT)
    print('确认无误后手动覆盖：  mv 1-105.merged.txt 1-105.txt')

if __name__ == '__main__':
    main()