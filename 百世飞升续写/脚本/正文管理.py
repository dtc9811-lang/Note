# -*- coding: utf-8 -*-
"""
正文管理 —— 增删改章唯一入口。

设计：**分章/ 是唯一真源，全本.txt 是生成物。**
任何插入/删除/替换都走本脚本，它自动重编号 + 重生成全本，不用手工改两边。

用法（在 F:/novel/百世飞升续写 下运行）：
    python 脚本/正文管理.py 状态                # 列出所有章：章号、标题、字数
    python 脚本/正文管理.py 检查                # 校验：章号连续？全本与分章一致？
    python 脚本/正文管理.py 全本                # 由 分章/ 生成 全本.txt
    python 脚本/正文管理.py 重编号              # 按文件名顺序重写各章首行
    python 脚本/正文管理.py 插入 <N> <文件>      # 在第 N 章之后插入
    python 脚本/正文管理.py 追加 <文件>          # 加到最后
    python 脚本/正文管理.py 删除 <N>            # 删除第 N 章
    python 脚本/正文管理.py 替换 <N> <文件>      # 用文件内容替换第 N 章

参数：
    全本 支持 --干净   （不加生成提示头，输出纯正文）

约定：
    文件名  第001章_章名.md        ← 前缀数字决定顺序（权威）
    首行    # 第1章 章名          ← 章名（权威）；重编号时数字会被改写
"""
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH_DIR = os.path.join(ROOT, '分章')
FULL = os.path.join(ROOT, '全本.txt')

CH_RE = re.compile(r'^#\s*第\s*(\d+)\s*章\s*(.*)$')
FN_RE = re.compile(r'^第\s*(\d+)\s*章[_\s]*(.*)\.md$')

BAD_FN = re.compile(r'[\\/:*?"<>|\r\n]')


# ---------------------------------------------------------------- 基础

def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))


def safe_name(name):
    return BAD_FN.sub('', name).strip() or '无题'


def read_chapter(path):
    """返回 (标题, 正文行列表)。首行若是 '# 第N章 标题' 就吃掉。"""
    text = open(path, encoding='utf-8').read()
    lines = text.replace('\r\n', '\n').split('\n')
    title = None
    if lines and CH_RE.match(lines[0]):
        title = CH_RE.match(lines[0]).group(2).strip()
        lines = lines[1:]
    if title is None:
        m = FN_RE.match(os.path.basename(path))
        title = m.group(2).strip() if m else '无题'
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return title, lines


def load():
    """按文件名数字排序，返回 [(num, title, path, lines)]"""
    if not os.path.isdir(CH_DIR):
        die('找不到 %s' % CH_DIR)
    items = []
    for fn in os.listdir(CH_DIR):
        if not fn.endswith('.md'):
            continue
        m = FN_RE.match(fn)
        if not m:
            warn('文件名不合规，跳过：%s' % fn)
            continue
        path = os.path.join(CH_DIR, fn)
        title, lines = read_chapter(path)
        items.append([int(m.group(1)), title, path, lines])
    items.sort(key=lambda x: x[0])
    return items


def die(msg):
    print('[错误] ' + msg)
    sys.exit(1)


def warn(msg):
    print('[警告] ' + msg)


# ---------------------------------------------------------------- 命令

def cmd_status():
    items = load()
    if not items:
        print('分章/ 下没有章节文件。')
        return
    print('共 %d 章' % len(items))
    print('%-6s %-24s %8s  %s' % ('章号', '章名', '正文字', '文件'))
    total = 0
    for num, title, path, lines in items:
        n = cjk('\n'.join(lines))
        total += n
        print('%-6d %-24s %8d  %s' % (num, title, n, os.path.basename(path)))
    print('-' * 56)
    print('合计 %d 正文字（不含章名），中位 %d，最短 %d，最长 %d'
          % (total, sorted(cjk('\n'.join(x[3])) for x in items)[len(items)//2],
             min(cjk('\n'.join(x[3])) for x in items),
             max(cjk('\n'.join(x[3])) for x in items)))


def parse_full(text):
    """把全本解析成 [(标题, 正文)]，忽略开头的 > 提示行。"""
    lines = text.replace('\r\n', '\n').split('\n')
    idx = [i for i, l in enumerate(lines) if CH_RE.match(l)]
    res = []
    for k, i in enumerate(idx):
        m = CH_RE.match(lines[i])
        end = idx[k + 1] if k + 1 < len(idx) else len(lines)
        res.append((m.group(2).strip(), '\n'.join(lines[i + 1:end]).strip()))
    return res


def cmd_check():
    items = load()
    ok = True
    nums = [x[0] for x in items]
    if nums != list(range(1, len(items) + 1)):
        warn('章号不连续（或不是从 1 开始）：%s' % nums[:20])
        ok = False
    else:
        print('[OK] 章号连续：1—%d，共 %d 章' % (len(items), len(items)))

    for num, title, path, lines in items:
        want = '第%03d章_%s.md' % (num, safe_name(title))
        if os.path.basename(path) != want:
            warn('文件名与章号/章名不一致：%s  → 应为 %s' % (os.path.basename(path), want))
            ok = False

    mine = [(t, '\n'.join(ls).strip()) for (_, t, _, ls) in items]
    if not os.path.exists(FULL):
        warn('全本.txt 不存在，跑一下：python 脚本/正文管理.py 全本')
        ok = False
    else:
        full_ch = parse_full(open(FULL, encoding='utf-8').read())
        if len(full_ch) != len(mine):
            warn('全本章数(%d) 与分章(%d) 不一致，跑一下：python 脚本/正文管理.py 全本'
                 % (len(full_ch), len(mine)))
            ok = False
        else:
            diff = [i + 1 for i in range(len(mine))
                    if full_ch[i][0] != mine[i][0] or full_ch[i][1] != mine[i][1]]
            if diff:
                warn('这些章全本与分章不一致：%s  跑一下：python 脚本/正文管理.py 全本'
                     % diff[:20])
                ok = False
            else:
                print('[OK] 全本.txt 与分章逐章一致（%d 章）' % len(mine))

    print('[%s] 检查结束' % ('OK' if ok else '!!'))
    return ok


def render(items, clean=False):
    out = []
    if not clean:
        out.append('> 《百世飞升》第十世 · 全本（第1—%d章，%d 正文字）'
                   % (len(items), sum(cjk('\n'.join(x[3])) for x in items)))
        out.append('> 本文件由 脚本/正文管理.py 自动生成，请勿直接修改；改正文请改 分章/ 下的单章文件。')
        out.append('')
    for i, (num, title, path, lines) in enumerate(items, 1):
        out.append('# 第%d章 %s' % (i, title))
        out.append('')
        out.extend(lines)
        out.append('')
    return '\n'.join(out).rstrip() + '\n'


def cmd_full(clean=False):
    items = load()
    text = render(items, clean)
    with open(FULL, 'w', encoding='utf-8') as f:
        f.write(text)
    print('[OK] 已生成 %s（%d 章，%d 正文字）' % (os.path.basename(FULL), len(items),
                                             sum(cjk('\n'.join(x[3])) for x in items)))


def cmd_renumber():
    items = load()
    if not items:
        return
    changed = 0
    for i, (num, title, path, lines) in enumerate(items, 1):
        body = '# 第%d章 %s\n\n%s\n' % (i, title, '\n'.join(lines).strip())
        newname = '第%03d章_%s.md' % (i, safe_name(title))
        newpath = os.path.join(CH_DIR, newname)
        with open(newpath, 'w', encoding='utf-8') as f:
            f.write(body)
        if os.path.abspath(newpath) != os.path.abspath(path):
            os.remove(path)
        if i != num:
            changed += 1
    print('[OK] 已重编号 %d 章（其中 %d 章章号有变动）' % (len(items), changed))


def _title_from_file(path):
    m = CH_RE.match(open(path, encoding='utf-8').read().replace('\r\n', '\n').split('\n')[0] or '')
    if m:
        return m.group(2).strip()
    b = os.path.splitext(os.path.basename(path))[0]
    b = re.sub(r'^第\s*\d+\s*章[_\s]*', '', b)
    return b.strip() or '无题'


def cmd_insert(after, path):
    if not os.path.exists(path):
        die('找不到要插入的文件：%s' % path)
    items = load()
    n = int(after)
    if not (0 <= n <= len(items)):
        die('插入位置 %d 超出范围（0—%d）' % (n, len(items)))
    title, lines = read_chapter(path)
    items.insert(n, [n + 1, title, path, lines])
    for i, it in enumerate(items, 1):
        it[0] = i
        it[3] = it[3]
    # 直接按新顺序重写全部
    tmp = []
    for i, (num, t, p, ls) in enumerate(items, 1):
        tmp.append([i, t, p, ls])
    _rewrite_all(tmp)
    print('[OK] 已在第 %d 章后插入「%s」，现在共 %d 章' % (n, title, len(tmp)))
    cmd_full()


def cmd_append(path):
    cmd_insert(len(load()), path)


def cmd_delete(num):
    items = load()
    n = int(num)
    if not (1 <= n <= len(items)):
        die('章号 %d 不在 1—%d 范围内' % (n, len(items)))
    title = items[n - 1][1]
    path = items[n - 1][2]
    if os.path.exists(path):
        os.remove(path)
    items.pop(n - 1)
    tmp = [[i, t, p, ls] for i, (_, t, p, ls) in enumerate(items, 1)]
    _rewrite_all(tmp)
    print('[OK] 已删除第 %d 章「%s」，现在共 %d 章' % (n, title, len(tmp)))
    cmd_full()


def cmd_replace(num, path):
    if not os.path.exists(path):
        die('找不到替换文件：%s' % path)
    items = load()
    n = int(num)
    if not (1 <= n <= len(items)):
        die('章号 %d 不在 1—%d 范围内' % (n, len(items)))
    title, lines = read_chapter(path)
    items[n - 1][1] = title
    items[n - 1][3] = lines
    tmp = [[i, t, p, ls] for i, (_, t, p, ls) in enumerate(items, 1)]
    _rewrite_all(tmp)
    print('[OK] 已替换第 %d 章 → 「%s」' % (n, title))
    cmd_full()


def _rewrite_all(items):
    """按给定顺序写回 分章/，删除多余旧文件。"""
    keep = set()
    for i, (num, title, path, lines) in enumerate(items, 1):
        newname = '第%03d章_%s.md' % (i, safe_name(title))
        newpath = os.path.join(CH_DIR, newname)
        with open(newpath, 'w', encoding='utf-8') as f:
            f.write('# 第%d章 %s\n\n%s\n' % (i, title, '\n'.join(lines).strip()))
        keep.add(os.path.abspath(newpath))
    for fn in os.listdir(CH_DIR):
        if not fn.endswith('.md'):
            continue
        p = os.path.abspath(os.path.join(CH_DIR, fn))
        if p not in keep:
            os.remove(p)


# ---------------------------------------------------------------- 入口

def main():
    args = [a for a in sys.argv[1:]]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    rest = args[1:]

    if cmd in ('状态', 'status'):
        cmd_status()
    elif cmd in ('检查', 'check'):
        cmd_check()
    elif cmd in ('全本', 'build'):
        cmd_full(clean='--干净' in rest)
    elif cmd in ('重编号', 'renumber'):
        cmd_renumber()
    elif cmd in ('插入', 'insert'):
        if len(rest) < 2:
            die('用法：python 脚本/正文管理.py 插入 <N> <文件>')
        cmd_insert(rest[0], rest[1])
    elif cmd in ('追加', 'append'):
        if not rest:
            die('用法：python 脚本/正文管理.py 追加 <文件>')
        cmd_append(rest[0])
    elif cmd in ('删除', 'delete'):
        if not rest:
            die('用法：python 脚本/正文管理.py 删除 <N>')
        cmd_delete(rest[0])
    elif cmd in ('替换', 'replace'):
        if len(rest) < 2:
            die('用法：python 脚本/正文管理.py 替换 <N> <文件>')
        cmd_replace(rest[0], rest[1])
    else:
        print(__doc__)


if __name__ == '__main__':
    main()