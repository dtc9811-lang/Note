# -*- coding: utf-8 -*-
"""
改稿体检：对比 分段/原文 与 修改/改稿，查出"改坏了"的地方。

用法：
    cd F:/novel/百世飞升续写
    python 分段/体检脚本.py              # 体检所有已改的份
    python 分段/体检脚本.py 06           # 只体检分段06
"""
import os, re, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOD  = os.path.join(ROOT, '修改')

CH_RE = re.compile(r'^#\s*第(\d+)章\s*(.*)$')

# 固定专有名词（不得被改掉/替换）
TERMS = ['无归渡','合利渡','葬仙墟','长照','古驿','正册','坊市','路网','归客','归潮',
         '时刻表','账本','牌照','渡正','验渡人','生死断笔','混元仙体','不朽仙魂','洞天',
         '本源仙炁','赵升','赵素','赵九满','赵长庚','赵茂','赵慎','赵敕','赵玄靖',
         '鸿运子','赵宏运','天运子','石灵','岑固','步纲君','苗七','祁广','谢青','窦让',
         '卫老修士','劫户点名印','铁尺杖','三条规矩','并线','死门','过客册','残图','归处']
TERMS = [t for t in TERMS if t.strip() and not t.isascii()]

BAN = ['嘴角勾起','眸光一凝','气息暴涨','恐怖如斯','心中一凛','倒吸一口凉气',
       '与此同时','不由得','不禁','眼中闪过一丝','淡淡道','冷笑道','沉声道']

def blocks(text):
    lines = text.split('\n')
    idx = [i for i,l in enumerate(lines) if CH_RE.match(l)]
    res = []
    for k,i in enumerate(idx):
        m = CH_RE.match(lines[i])
        end = idx[k+1] if k+1 < len(idx) else len(lines)
        res.append((m.group(2).strip(), '\n'.join(lines[i+1:end])))
    return res

def cjk(s): return len(re.findall(r'[\u4e00-\u9fff]', s))
def quotes(s): return s.count('“') + s.count('”')

def nums(s):
    """抽取数字（中文数字 + 阿拉伯）"""
    cn = re.findall(r'[零一二三四五六七八九十百千万两]+', s)
    ar = re.findall(r'\d+', s)
    return set(cn) | set(ar)

def maxcomma(s):
    return max((x.count('，') for x in re.split(r'[。！？\n]', s)), default=0)

def check(seg_path):
    base = os.path.basename(seg_path)
    mod_path = os.path.join(MOD, base)
    if not os.path.exists(mod_path):
        return None
    orig = blocks(open(seg_path, encoding='utf-8').read())
    mod  = blocks(open(mod_path, encoding='utf-8').read())

    print('\n' + '='*56)
    print('体检：%s' % base)
    print('='*56)

    if len(orig) != len(mod):
        print('  [章节数] 原文 %d 章 → 改稿 %d 章   <<< 不一致，检查是不是漏章/多章'
              % (len(orig), len(mod)))
    else:
        print('  [章节数] %d 章  一致' % len(orig))

    o_all = '\n'.join(b for _, b in orig)
    m_all = '\n'.join(b for _, b in mod)

    # 逐章字数
    print('  [字数]  原文 %d → 改稿 %d  (%+.0f%%)'
          % (cjk(o_all), cjk(m_all), (cjk(m_all)-cjk(o_all))/max(1,cjk(o_all))*100))
    shrink = []
    for i in range(min(len(orig), len(mod))):
        a, b = cjk(orig[i][1]), cjk(mod[i][1])
        if a > 300 and b < a*0.85:
            shrink.append((orig[i][0], a, b))
    if shrink:
        print('  [缩水]  这些章改稿比原文少了 15% 以上，检查是不是删了事：')
        for t, a, b in shrink: print('          %s: %d → %d' % (t, a, b))

    # 专有名词
    miss = [t for t in TERMS if t in o_all and t not in m_all]
    if miss:
        print('  [术语]  原文有、改稿里没了的词：%s   <<< 可能被替换或删掉' % '、'.join(miss))

    # 数字
    on, mn = nums(o_all), nums(m_all)
    lost = sorted(on - mn, key=len, reverse=True)[:15]
    if lost:
        print('  [数字]  原文有、改稿缺的数字：%s' % '、'.join(lost))

    # 禁用词
    hit = [(w, m_all.count(w)) for w in BAN if w in m_all]
    if hit:
        print('  [禁用]  %s' % '、'.join('%s×%d' % h for h in hit))

    # 文风指标
    d = m_all.count('的，') / max(1, cjk(m_all)) * 1000
    mc = maxcomma(m_all)
    print('  [文风]  「的，」%.2f/千字（上限4）　单句最多逗号 %d（上限6）' % (d, mc))
    print('  [对话]  引号 %d 处，平均每章 %.1f' % (quotes(m_all), quotes(m_all)/max(1,len(mod))))
    if d > 4: print('         <<< 「的，」超标')
    if mc > 6: print('         <<< 有长逗号串句')

    return True

def main():
    segs = sorted(glob.glob(os.path.join(HERE, '[0-9][0-9]_ch*.md')))
    if len(sys.argv) > 1:
        key = sys.argv[1]
        segs = [s for s in segs if os.path.basename(s).startswith(key)]
    done = 0
    for s in segs:
        if check(s): done += 1
    print('\n共体检 %d 份已改稿（共 %d 份分段）' % (done, len(glob.glob(os.path.join(HERE,'[0-9][0-9]_ch*.md')))))
    if done == 0:
        print('修改/ 里还没有稿子。改完一份再跑。')

if __name__ == '__main__':
    main()