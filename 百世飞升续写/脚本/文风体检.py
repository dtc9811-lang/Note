# -*- coding: utf-8 -*-
"""
文风体检 —— 按《千问写作包/07_禁区与自检清单.md》查硬指标。

用法（在 F:/novel/百世飞升续写 下运行）：
    python 脚本/文风体检.py                # 体检全部章（只报有问题的）
    python 脚本/文风体检.py 37             # 只体检第37章
    python 脚本/文风体检.py 全              # 全部章的汇总
    python 脚本/文风体检.py <文件路径>       # 体检任意一个稿件（草稿、重写稿都行）

判定分两档：
  [硬伤] 有明确阈值，超了就是超了
  [可疑] 只提出来给你看，要不要改由人判断

阈值来源：07_禁区与自检清单.md C 节、文风样本 05、固定术语表 06。
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
CH_RE = re.compile(r'^#\s*第\s*(\d+)\s*章\s*(.*)$')

# 硬指标阈值
MAX_DE_DOU = 4.0      # 「的，」密度 /千字
MAX_COMMA = 6         # 单句最多逗号
MIN_CJK = 1200        # 正文字数下限（新章目标 1500—2500，老章偏短，只提示）

# 套话（07_禁区 C 节）
BAN = ['嘴角勾起', '嘴角微扬', '眸光一凝', '气息暴涨', '恐怖如斯', '心中一凛',
       '倒吸一口凉气', '与此同时', '不由得', '不禁', '眼中闪过一丝',
       '淡淡道', '冷笑道', '沉声道', '意味深长', '若有所思', '眉头一皱',
       '不置可否', '话里有话']

# 术语替代（06 固定术语表 右列，只取歧义小的）
FORBIDDEN = ['觉醒', '解封', '仙气', '灵气', '元气', '真元', '精神力', '灵魂力',
             '无名渡', '归墟', '幽灵', '亡魂', '鬼魂', '归人', '潮汐',
             '时间表', '轮值表', '执照', '渡主', '渡长', '官方名录',
             '长照渡', '长昭', '常照', '生门', '绝路', '死路',
             '合路', '并道', '汇流', '登记簿', '客人册', '拐杖', '铁棍',
             '生死笔', '轮回笔', '混元体', '混沌体', '丹田世界', '内天地',
             '小世界', '五面镜', '五行镜', '雷令', '雷钺']

# 模糊数量（要求具体数字）
VAGUE = ['许多', '无数', '很多', '不计其数', '数不清', '大量', '一大群']

# 堆砌动作
FILLER = ['看了一眼', '没有说话', '停了一下', '顿了顿', '沉默', '点了点头']

# 章末抒情/总结的迹象
SUMMARIZE = ['原来', '其实', '终究', '也许', '这一切', '某种意义', '他明白了',
             '他终于', '从此', '就这样', '说到底', '本质上']


def cjk(s):
    return len(re.findall(r'[\u4e00-\u9fff]', s))


def max_comma(s):
    return max((x.count('，') for x in re.split(r'[。！？；\n]', s)), default=0)


def load_all():
    out = []
    for fn in sorted(os.listdir(CH_DIR)):
        if not fn.endswith('.md'):
            continue
        p = os.path.join(CH_DIR, fn)
        text = open(p, encoding='utf-8').read().replace('\r\n', '\n')
        lines = text.split('\n')
        title = fn
        if lines and CH_RE.match(lines[0]):
            title = CH_RE.match(lines[0]).group(2).strip()
            lines = lines[1:]
        out.append((fn, title, '\n'.join(lines)))
    return out


def check(name, body, verbose=True):
    n = cjk(body)
    problems = []
    suspects = []

    de = body.count('的，') / max(1, n) * 1000
    if de > MAX_DE_DOU:
        problems.append('「的，」密度 %.2f/千字（上限 %.0f）' % (de, MAX_DE_DOU))

    mc = max_comma(body)
    if mc > MAX_COMMA:
        problems.append('单句最多逗号 %d 个（上限 %d）' % (mc, MAX_COMMA))

    if n < MIN_CJK:
        suspects.append('正文只 %d 字（新章目标 1500—2500）' % n)

    hit = [(w, body.count(w)) for w in BAN if w in body]
    if hit:
        suspects.append('套话：' + '、'.join('%s×%d' % h for h in hit))

    fh = [(w, body.count(w)) for w in FORBIDDEN if w in body]
    if fh:
        suspects.append('疑似术语替代：' + '、'.join('%s×%d' % h for h in fh))

    vg = [(w, body.count(w)) for w in VAGUE if w in body]
    if vg:
        suspects.append('模糊数量（要求具体数字）：' + '、'.join('%s×%d' % h for h in vg))

    fl = [(w, body.count(w)) for w in FILLER if body.count(w) >= 3]
    if fl:
        suspects.append('动作堆砌：' + '、'.join('%s×%d' % h for h in fl))

    paras = [p.strip() for p in body.strip().split('\n') if p.strip()]
    if paras:
        last = paras[-1]
        sw = [w for w in SUMMARIZE if w in last]
        if sw and len(last) > 20:
            suspects.append('章末疑似抒情/总结（末段含 %s）' % '、'.join(sw))
        if '“' not in last and '。' in last and len(last) > 60:
            pass

    quotes = body.count('“') + body.count('"') + body.count('「')

    half = body.count('"')
    if half:
        problems.append('半角引号 %d 处（全书统一用全角 “”）' % half)
    if body.count('“') != body.count('”'):
        problems.append('全角引号不成对：“×%d  ”×%d' % (body.count('“'), body.count('”')))
    if verbose:
        flag = '[硬伤]' if problems else ('[可疑]' if suspects else '[OK]  ')
        print('%s %s  （%d 字，的，%.2f，逗号≤%d，对话%d 处）'
              % (flag, name, n, de, mc, quotes))
        for p in problems:
            print('        × ' + p)
        for s in suspects:
            print('        ? ' + s)
    return problems, suspects


def main():
    args = sys.argv[1:]
    if args and os.path.exists(args[0]):
        text = open(args[0], encoding='utf-8').read().replace('\r\n', '\n')
        check(os.path.basename(args[0]), text)
        return

    allch = load_all()
    if args and args[0] != '全':
        key = args[0]
        if key.isdigit():
            allch = [c for c in allch if re.match(r'^第0*%d章_' % int(key), c[0])]
        else:
            allch = [c for c in allch if key in c[1]]

    bad = 0
    sus = 0
    for fn, title, body in allch:
        problems, suspects = check('第%s章 %s' % (fn.split('章')[0].replace('第', '').lstrip('0') or '?', title), body)
        if problems:
            bad += 1
        elif suspects:
            sus += 1
    total_n = sum(cjk(b) for _, _, b in allch)
    print('-' * 60)
    print('体检 %d 章，%d 正文字；有硬伤 %d 章，有可疑 %d 章'
          % (len(allch), total_n, bad, sus))
    print('提示：[硬伤] 必改；[可疑] 只供参考，套话/术语替代命中老章属正常。')


if __name__ == '__main__':
    main()