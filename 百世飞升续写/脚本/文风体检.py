# -*- coding: utf-8 -*-
"""
文风体检 —— 按《千问写作包/07_禁区与自检清单.md》查硬指标。

用法（在 F:/novel/百世飞升续写 下运行）：
    python 脚本/文风体检.py                # 体检全部章（只报有问题的）
    python 脚本/文风体检.py 37             # 只体检第37章
    python 脚本/文风体检.py 全              # 全部章 + 跨章重复汇总 + 读感统计
    python 脚本/文风体检.py 读感            # 只出读感统计（章长/场数/对话/底线词密度）
    python 脚本/文风体检.py <文件路径>       # 体检任意一个稿件（草稿、重写稿都行）

判定分两档：
  [硬伤] 有明确阈值，超了就是超了
  [可疑] 只提出来给你看，要不要改由人判断

检查项（在原有硬指标之外新增）：
  * 跨章重复（tics）—— 同一套话/句式在多章反复出现，体检脚本原先抓不到。
    单章出现 ≥ TIC_CH_ALERT 次，或全书中 ≥ TIC_CHAPTERS_ALERT 章都出现，报警。
  * 自造人名 —— 台词里"XX说/问"的 XX，若不在《06 固定术语表》《09 人物速查卡》
    的登记表里，提示为疑似自造人名（07 G 节：没登记的名字一律不具名）。

阈值来源：07_禁区与自检清单.md C 节、文风样本 05、固定术语表 06。
"""
import os
import re
import sys
from collections import Counter

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH_DIR = os.path.join(ROOT, '分章')
PKG_DIR = os.path.join(ROOT, '千问写作包')
CH_RE = re.compile(r'^#\s*第\s*(\d+)\s*章\s*(.*)$')

# 硬指标阈值
MAX_DE_DOU = 4.0          # 「的，」密度 /千字
MAX_COMMA = 6             # 单句最多逗号
MIN_CJK = 1200            # 正文字数下限（新章目标 1500—2500，老章偏短，只提示）

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

# ---------------------------------------------------------------- 读感统计（2026-09 新增）
# 硬指标全绿不等于好读。下列是 27 号文实测出问题的那些：
#   章长分布 / 场数与对话段 / 世界专名密度 / 底线词密度
# “大世界”只算原著专名＋已登记的上层地名（不算“路网/渡口”这类本地气泡词）
BIGWORLD = ['天柱界', '大椿界', '净光界', '离辰界', '红海界', '沧海界',
            '太乙灵界', '太素灵界', '太乙关', '太乙', '太素', '先天神州',
            '鸿荒', '无回天', '虚界九天', '诸天', '大道长河', '灵界',
            '客安城', '四会渡', '坊市城']
CULT_WORDS = ['修炼', '闭关', '仙炁', '醒成', '洞天', '神识', '法力', '经脉',
              '本源', '丹田', '炼']
FIGHT_WORDS = ['出手', '动手', '劈', '斩', '挡', '撞', '围攻', '硬扛', '夺',
               '抡', '踢', '掀', '压住', '接住', '跌', '血']
SEG = 10          # 每 10 章汇总一段
SHORT_CH = 1100   # 低于此字数进入“过短”清单（新章下限 1200；老章只报不判）

# ---------------------------------------------------------------- 跨章重复
# 这些是机器原先抓不到的"作者口头禅/模板"。qs 写 15 章后最常堆这类。
TIC_PHRASES = [
    '看了很久', '笑了一声', '你这个人，很有意思', '灰得比昨天更浅',
    '灯还亮着。火苗很稳', '灯还亮着', '没有说话', '点了点头',
    '赵升没有笑', '他不知道', '看了他一眼', '停了一下',
    '我不是炼气后期', '为什么要问', '他又回来了',
]
TIC_CH_ALERT = 4           # 单章出现 >=4 次 → 该章报警
TIC_CHAPTERS_ALERT = 6     # 全书 >=6 章都出现 → 汇总时报警（这类大多是有意复现的意象，靠人判断）

# ---------------------------------------------------------------- 自造人名
# 台词动词前的人名：XX说 / XX问 / XX答（前面不能再接汉字，避免把"先医后问"当人名）
NAME_SPEAK_RE = re.compile(
    r'(?<![\u4e00-\u9fff])([\u4e00-\u9fff]{2,4})(?:说|问|答|道)(?=[：，。！？\n“])')
# 介绍句式：姓名/籍贯 记录格式（“叫XX”“姓XX”歧义太大，不用）
NAME_INTRO_RE = re.compile(r'(?:姓名|籍贯|名字)\s*[：:]\s*([\u4e00-\u9fff]{1,6})')

# 含这些字的候选基本不是人名（虚词/动词/代词）
BAD_CHARS = set('的了是不我你他她它们没也就都很太在有会能要想知看听手主')

# 明显不是人名的词（动词/代词/身份/群体），避免误报
NOT_NAME = set('''
那人 有人 众人 老头 老修士 那个人 这个人 一个人 两个人 三个人 四个人 一个人
没人 没有人 谁也没 不知谁 对方 双方 各自 他自己 他们 我们 你们 人家 旁人
先医后 先医 三条 一条 一条条 这枚 那枚 一枚 一句 一声 一把 一半 一面 一起 两件 三件
探子 年轻人 引首 一支 两支 进去 医完了再 你怎么知 那就先不 但赵升知 看着老人 是正册
也不知道 也没有 一支队 一队人 半个人 没有人说
明天 后天 哪天 半天 今日 昨日 明年 平时 平日
堂主 老祖宗 管事 掌柜 伙计 护卫 随从 散修 客人 归客 渡客 伤者 死者 家属
化神 元婴 金丹 筑基 炼气 返虚 真仙 长老 弟子 族人 商号 车队 队伍
一个 两个 三个 四个 五个 一群 一人 二人 三人 四人 两人 几位 各位
白袍 青袍 灰袍 赤袍 黄袍 袍子 甲片 身影 声音 脚步 手掌 手指 眼睛
赵氏 坳里 家里 族里 坊市 渡口 路网 正册 仙籍 棺船 废渡 断堤 井底
禁地 死区 深处 外围 上头 底下 东边 西边 南边 北边 那边 这边
说着 说着话 商量 回答 回声 追问 反问 问道 说道 笑着说 低声 小声
'''.split())

PERSON_SUFFIX = ('说', '问', '答', '道', '君', '子', '老', '公', '祖')


def load_registry():
    """从 06 固定术语表 / 09 人物速查卡 抽登记过的人名、地名。"""
    names = set()
    for fn in ('06_固定术语表.md', '09_人物速查卡.md'):
        p = os.path.join(PKG_DIR, fn)
        if not os.path.exists(p):
            continue
        for line in open(p, encoding='utf-8'):
            # 09 的 **赵升**（970）
            for m in re.finditer(r'\*\*([^*（）()]{1,8})\*\*', line):
                names.add(m.group(1).strip())
            # 表格式 | 赵素 / 赵茂 / ... |
            if line.lstrip().startswith('|'):
                cell = line.split('|')[1].strip()
                cell = re.sub(r'（.*?）|\(.*?\)', '', cell)
                for part in re.split(r'[/、,，]', cell):
                    part = part.strip()
                    if 1 <= len(part) <= 6 and not part.startswith('-'):
                        names.add(part)
    # 手工兜底（早期正文里的人，表格里不一定成条）
    names.update(['赵升', '赵素', '赵九满', '赵长庚', '赵茂', '赵敕', '赵慎',
                  '步纲君', '岑固', '窦让', '苗七', '祁广', '谢青', '卫老修士',
                  '赵玄靖', '鸿运子', '天运子', '石灵', '赵宏运',
                  '无归渡', '合利渡', '葬仙墟', '长照', '古驿', '客安城'])
    return names


REGISTRY = load_registry()


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


# 常见姓氏。候选名字必须以姓氏开头，否则不当人名列（防住"然后说""墟渡说"这类）
SURNAMES = set('赵钱孙李周吴郑王冯陈卫蒋沈韩杨朱秦许何吕施张孔曹严华金魏陶姜谢邹柏窦章苏潘葛范彭郎鲁韦马苗方任袁柳史唐费廉岑薛雷贺倪汤罗郝安常傅卞齐康伍余顾孟黄和穆萧尹姚汪祁毛狄米贝明戴谈宋庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄高夏蔡田樊胡凌霍虞万柯卢莫')


def _starts_with_registry(name):
    return any(name.startswith(r) and len(r) < len(name) for r in REGISTRY)


def name_suspects(body):
    """返回疑似自造人名 [(名字, 出现次数)]。"""
    cands = set()
    for m in NAME_SPEAK_RE.finditer(body):
        cands.add(m.group(1))
    for m in NAME_INTRO_RE.finditer(body):
        cands.add(m.group(1))
    hits = []
    for name in cands:
        if name in NOT_NAME or name in REGISTRY:
            continue
        if any(ch in BAD_CHARS for ch in name):
            continue
        if name[0] not in SURNAMES:       # 不是姓氏开头，基本不是人名
            continue
        if _starts_with_registry(name):   # 是已登记名字 + 尾巴（如"赵敕那边"）
            continue
        total = body.count(name)
        if total >= 2:
            hits.append((name, total))
    return sorted(hits, key=lambda x: -x[1])


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

    tic = [(w, body.count(w)) for w in TIC_PHRASES if body.count(w) >= TIC_CH_ALERT]
    if tic:
        suspects.append('单章高频重复：' + '、'.join('%s×%d' % h for h in tic))

    nm = name_suspects(body)
    if nm:
        suspects.append('疑似自造人名（查 06/09 登记表）：'
                        + '、'.join('%s×%d' % h for h in nm))

    paras = [p.strip() for p in body.strip().split('\n') if p.strip()]
    if paras:
        last = paras[-1]
        sw = [w for w in SUMMARIZE if w in last]
        if sw and len(last) > 20:
            suspects.append('章末疑似抒情/总结（末段含 %s）' % '、'.join(sw))

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


def cross_chapter_report(allch):
    """跨章重复汇总：同一短语在多少章出现。只报超阈值的。"""
    print('-' * 60)
    print('跨章重复汇总（同一短语在多章反复出现；多为模板/口头禅）')
    any_hit = False
    for w in TIC_PHRASES:
        chs = [(t, b.count(w)) for _, t, b in allch if w in b]
        total = sum(c for _, c in chs)
        if len(chs) >= TIC_CHAPTERS_ALERT:
            any_hit = True
            worst = '、'.join('%s×%d' % (t, c) for t, c in
                              sorted(chs, key=lambda x: -x[1])[:6])
            print('  ! 「%s」 出现在 %d 章、共 %d 次；最密：%s'
                  % (w, len(chs), total, worst))
    if not any_hit:
        print('  [OK] 无短语达到 %d 章的复现阈值。' % TIC_CHAPTERS_ALERT)
    print('  提示：意象句（“井底是黑的”等）反复出现是有意设计；'
          '口头禅（“看了很久”“笑了一声”）反复出现是模型写疲了。靠人判断。')


def density_report(allch):
    """读感统计：章长分布、场数与对话段、世界专名与底线词密度。只报不判。"""
    rows = []
    for fn, title, body in allch:
        n = cjk(body) or 1
        rows.append({
            'no': int(re.match(r'^第0*(\d+)章', fn).group(1)),
            'n': cjk(body),
            'scenes': body.count('——'),
            'dlog': body.count('“') // 2,
            'bw': sum(body.count(w) for w in BIGWORLD) / n * 1000,
            'cu': sum(body.count(w) for w in CULT_WORDS) / n * 1000,
            'fi': sum(body.count(w) for w in FIGHT_WORDS) / n * 1000,
        })
    rows.sort(key=lambda r: r['no'])

    def med(xs):
        ys = sorted(xs)
        return ys[len(ys) // 2] if ys else 0

    print('-' * 72)
    print('读感统计（只报不判；对应 27_全书总览与优化方案.md）')
    print('%-10s %5s %7s %7s %7s %8s %8s' % ('段', '章数', '总字', '均字', '中位', '场(中位)', '对话(中位)'))
    i = 0
    while i < len(rows):
        grp = rows[i:i + SEG]
        i += SEG
        ss = [g['n'] for g in grp]
        print('%-10s %5d %7d %7d %7d %8.0f %8.0f'
              % ('%d—%d' % (grp[0]['no'], grp[-1]['no']), len(grp), sum(ss),
                 sum(ss) / len(ss), med(ss),
                 med([g['scenes'] for g in grp]), med([g['dlog'] for g in grp])))
    print('全体     %5d %7d %7d %7d'
          % (len(rows), sum(g['n'] for g in rows),
             sum(g['n'] for g in rows) / len(rows), med([g['n'] for g in rows])))

    print('-' * 72)
    print('底线词密度（每千字；“大世界”只算原著专名＋已登记的上层地名）')
    print('%-10s %9s %9s %9s' % ('段', '大世界', '修炼', '战斗'))
    i = 0
    while i < len(rows):
        grp = rows[i:i + SEG]
        i += SEG
        tot = sum(g['n'] for g in grp) or 1
        print('%-10s %9.2f %9.2f %9.2f'
              % ('%d—%d' % (grp[0]['no'], grp[-1]['no']),
                 sum(g['bw'] * g['n'] for g in grp) / tot,
                 sum(g['cu'] * g['n'] for g in grp) / tot,
                 sum(g['fi'] * g['n'] for g in grp) / tot))

    short = [g for g in rows if g['n'] < SHORT_CH]
    print('-' * 72)
    if short:
        print('过短章（<%d 字，共 %d 章，占 %.0f%%）：'
              % (SHORT_CH, len(short), len(short) * 100.0 / len(rows)))
        print('  ' + '、'.join('%d(%d)' % (g['no'], g['n']) for g in short))
    else:
        print('[OK] 无过短章。')
    thin = [g for g in rows if g['scenes'] < 2]
    if thin:
        print('单场章（无"——"分隔，共 %d 章）：%s'
              % (len(thin), '、'.join(str(g['no']) for g in thin)))


def main():
    args = sys.argv[1:]
    if args and os.path.exists(args[0]):
        text = open(args[0], encoding='utf-8').read().replace('\r\n', '\n')
        check(os.path.basename(args[0]), text)
        return

    allch = load_all()
    want_cross = bool(args and args[0] == '全')
    want_feel = bool(args and args[0] == '读感')
    if args and args[0] not in ('全', '读感'):
        key = args[0]
        if key.isdigit():
            allch = [c for c in allch if re.match(r'^第0*%d章_' % int(key), c[0])]
        else:
            allch = [c for c in allch if key in c[1]]

    bad = 0
    sus = 0
    if not want_feel:
        for fn, title, body in allch:
            problems, suspects = check(
                '第%s章 %s' % (fn.split('章')[0].replace('第', '').lstrip('0') or '?', title), body)
            if problems:
                bad += 1
            elif suspects:
                sus += 1
    total_n = sum(cjk(b) for _, _, b in allch)
    if not want_feel:
        print('-' * 60)
        print('体检 %d 章，%d 正文字；有硬伤 %d 章，有可疑 %d 章'
              % (len(allch), total_n, bad, sus))
        print('提示：[硬伤] 必改；[可疑] 只供参考，套话/术语替代命中老章属正常。')
    if want_cross:
        cross_chapter_report(allch)
    if want_feel or want_cross:
        density_report(allch)


if __name__ == '__main__':
    main()