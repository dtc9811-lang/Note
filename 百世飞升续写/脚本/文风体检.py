# -*- coding: utf-8 -*-
"""
文风体检 —— 按《千问写作包/07_禁区与自检清单.md》查硬指标。

用法（在 F:/novel/百世飞升续写 下运行）：
    python 脚本/文风体检.py                # 体检全部章（只报有问题的）
    python 脚本/文风体检.py 37             # 只体检第37章
    python 脚本/文风体检.py 全              # 全部章 + 跨章重复 + 读感统计 + 结构指标
    python 脚本/文风体检.py 读感            # 只出读感统计（章长/场数/对话/底线词密度）
    python 脚本/文风体检.py 合并            # 只出结构指标 + 逐章明细表（供「合并减字」用）
    python 脚本/文风体检.py 结构            # 只出结构指标汇总（不列明细）
    python 脚本/文风体检.py <文件路径>       # 体检任意一个稿件（草稿、重写稿都行）

判定分两档：
  [硬伤] 有明确阈值，超了就是超了
  [可疑] 只提出来给你看，要不要改由人判断

检查项（在原有硬指标之外新增）：
  * 跨章重复（tics）—— 同一套话/句式在多章反复出现，体检脚本原先抓不到。
    单章出现 ≥ TIC_CH_ALERT 次，或全书中 ≥ TIC_CHAPTERS_ALERT 章都出现，报警。
  * 自造人名 —— 台词里"XX说/问"的 XX，若不在《06 固定术语表》《09 人物速查卡》
    的登记表里，提示为疑似自造人名（07 G 节：没登记的名字一律不具名）。
  * 结构指标（2026-09 新增，为「合并减字」服务）—— 镜头数 / 镜头均长 /
    章末类型 / 模板句密度。拉稀的根因不是句子而是镜头碎片化：
    实测 630 镜头、均 334 字、62% 不足 300 字；36 章一拍一章；
    51/119 章末落在「看/望/站/走/合上账册」。方案见 规划/合并减字方案.md。

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

# ---------------------------------------------------------------- 结构指标（为「合并减字」服务）
# 实测口径（1—119 章）：211794 字 / 119 章 = 均 1779；镜头 630 个、均 334 字、中位 227；
# 34% 镜头 <150 字，62% <300 字；36 章无「——」分隔（一拍一章）；章末模板收尾 51/119。
# 结论：问题不在句子，在结构。合并目标 = 每章 3—5 镜、每镜 ≥450 字、章长 2600—2900。
SCENE_SEP_RE = re.compile(r'^[ \t]*——[ \t]*$', re.M)   # 独占一行的「——」才是镜头分隔
SCENE_TARGET_MIN = 450     # 合并口径：每镜目标 >=450 字
SCENE_FRAG = 300           # 低于此长度算碎片镜头
TEMPLATE_DENSITY_ALERT = 3.0   # 模板句密度上限（次/千字）
CH_MERGE_BAND = (2600, 2900)   # 合并后均章目标带（写作单章用 2500—3500）

# 模板句（非对话归属词）——这些是「写疲了」的口头禅，不是有意复现的意象
TEMPLATE_PHRASES = [
    '他在心里那本账上', '又添了一条', '赵升看着他', '皱了皱眉',
    '没有再问', '没有说话', '火苗很稳', '井底是黑的',
    '然后他开口了', '赵升没有笑', '看了很久', '笑了一声',
    '点了点头', '停了一下', '写下来', '看了他一眼', '停了一息',
]
# 对话归属词（对话体单一化指标，单独统计，不计入模板密度）
ATTR_PHRASES = [
    '赵升说', '赵素说', '赵九满说', '赵长庚说', '赵茂说', '赵敕说',
    '卫老修士说', '苗七说', '步纲君说', '窦让说', '谢青说', '祁广说',
]

# 章末类型判定（顺序即优先级）
END_RECORD = re.compile(r'(合上|写完|记下|记一笔|写下|搁笔|把账册|账册合上|收了笔|盖上)')
END_MOVE = re.compile(r'(站起来|走过去|走进|走出去|出门|上马|离开|坐下|坐下来|靠着|蹲下|往.{0,8}走|迈)')
END_LOOK = re.compile(r'(看|望|盯着|盯着看|朝.{0,8}看)')
END_PROP = re.compile(r'(灯|门|路|石板|雾|纸|账|印|碗|火|字|灰|缝|牌|杖|笔)')
END_BAN = ('视线', '记录')   # 章末模板收尾：这两类要压到 <=20/119
END_WEAK = ('空转',)         # 章末空转（短句抽象收尾，无具体物、无对白）

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


def split_scenes(body):
    """按独占一行的「——」切镜头。行内 —— 是破折号，不切。"""
    return [p.strip() for p in SCENE_SEP_RE.split(body) if p.strip()]


def scene_stats(body):
    """返回 (镜头数, 均长, 最短, 最长)。"""
    lens = [cjk(s) for s in split_scenes(body)]
    if not lens:
        return 0, 0, 0, 0
    return len(lens), sum(lens) // len(lens), min(lens), max(lens)


def template_density(body):
    """返回 (模板句密度/千字, [(短语, 次数)])。"""
    n = cjk(body) or 1
    hits = [(w, body.count(w)) for w in TEMPLATE_PHRASES]
    hits = [(w, c) for w, c in hits if c]
    return sum(c for _, c in hits) / n * 1000, sorted(hits, key=lambda x: -x[1])


def attr_count(body):
    return sum(body.count(w) for w in ATTR_PHRASES)


def body_paras(body):
    """正文段落，剔除空行与独占一行的「——」分隔符（末尾常残留一行）。"""
    out = []
    for p in body.strip().split('\n'):
        p = p.strip()
        if not p or SCENE_SEP_RE.match(p):
            continue
        out.append(p)
    return out


def end_type(body):
    """章末类型：对白 / 记录 / 位移 / 视线 / 画面 / 空转 / 其他 / 空。"""
    paras = body_paras(body)
    if not paras:
        return '空'
    last = paras[-1]
    if re.search(r'[「“]', last):
        return '对白'
    if END_RECORD.search(last):
        return '记录'
    if END_MOVE.search(last):
        return '位移'
    if END_LOOK.search(last):
        return '视线'
    if END_PROP.search(last):
        return '画面'
    if len(re.sub(r'\s', '', last)) < 20:
        return '空转'
    return '其他'


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


def check(name, body, verbose=True, struct=True):
    """struct=False 时不报结构项（镜头/章末/模板密度）——批量体检用，
    避免 116/119 章都报可疑；结构汇总走 struct_report()。"""
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

    paras = body_paras(body)
    if paras:
        last = paras[-1]
        sw = [w for w in SUMMARIZE if w in last]
        if sw and len(last) > 20:
            suspects.append('章末疑似抒情/总结（末段含 %s）' % '、'.join(sw))

    # ---- 结构指标（合并减字口径）
    if struct:
        ns, avg, mn, mx = scene_stats(body)
        if ns <= 1 and n >= 400:
            suspects.append('单场章（一拍一章，无「——」分隔；目标 3—5 镜）')
        elif ns and avg < SCENE_TARGET_MIN:
            suspects.append('镜头碎片化：%d 镜、均 %d 字、最短 %d（目标 ≥%d 字/镜）'
                            % (ns, avg, mn, SCENE_TARGET_MIN))
        elif ns > 5 and n >= CH_MERGE_BAND[0]:
            suspects.append('镜头过多：%d 镜（目标 3—5；长章里镜头多=该并场）' % ns)
        td, th = template_density(body)
        if td > TEMPLATE_DENSITY_ALERT:
            suspects.append('模板句密度 %.2f/千字（上限 %.1f）：%s'
                            % (td, TEMPLATE_DENSITY_ALERT,
                               '、'.join('%s×%d' % h for h in th[:5])))
        et = end_type(body)
        if et in END_BAN:
            suspects.append('章末模板收尾（%s类；脚本口径基线 24/119，目标 ≤20/119）' % et)
        elif et in END_WEAK:
            suspects.append('章末空转（短句抽象收尾，无具体物、无对白）')

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
        sc, avg, _, _ = scene_stats(body)
        rows.append({
            'no': int(re.match(r'^第0*(\d+)章', fn).group(1)),
            'n': cjk(body),
            'scenes': sc,
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
        print('单场章（无「——」分隔，共 %d 章）：%s'
              % (len(thin), '、'.join(str(g['no']) for g in thin)))


def struct_report(allch, detail=False):
    """结构指标：镜头数 / 镜头均长 / 章末类型 / 模板句密度。

    这是「合并减字」的量化验收尺（见 规划/合并减字方案.md）。
    只报不判：镜头碎片与章末模板是结构信号，改不改由人决定。
    """
    rows = []
    for fn, title, body in allch:
        ns, avg, mn, mx = scene_stats(body)
        td, th = template_density(body)
        rows.append({
            'no': int(re.match(r'^第0*(\d+)章', fn).group(1)),
            'title': title,
            'n': cjk(body),
            'sc': ns, 'avg': avg, 'min': mn,
            'end': end_type(body),
            'td': td, 'th': th,
            'attr': attr_count(body),
        })
    rows.sort(key=lambda r: r['no'])
    if not rows:
        return

    def med(xs):
        ys = sorted(xs)
        return ys[len(ys) // 2] if ys else 0

    tot_n = sum(r['n'] for r in rows)
    tot_sc = sum(r['sc'] for r in rows)
    print('-' * 88)
    print('结构指标（合并减字口径：3—5 镜/章、每镜 ≥%d 字、章长 %d—%d）'
          % (SCENE_TARGET_MIN, CH_MERGE_BAND[0], CH_MERGE_BAND[1]))
    print('%-9s %4s %7s %6s %6s %6s %7s %8s %9s'
          % ('段', '章数', '总字', '均字', '镜头', '镜均长', '碎片镜%', '模板密度', '章末模板%'))
    i = 0
    while i < len(rows):
        grp = rows[i:i + SEG]
        i += SEG
        gn = sum(g['n'] for g in grp) or 1
        gsc = sum(g['sc'] for g in grp)
        frag = sum(1 for g in grp if g['sc'] and g['avg'] < SCENE_FRAG)
        ban = sum(1 for g in grp if g['end'] in END_BAN)
        print('%-9s %4d %7d %6d %6d %6d %7.0f%% %8.2f %8.0f%%'
              % ('%d—%d' % (grp[0]['no'], grp[-1]['no']), len(grp), gn,
                 gn / len(grp), gsc,
                 sum(g['avg'] * g['sc'] for g in grp) // max(1, gsc),
                 frag * 100.0 / len(grp),
                 sum(g['td'] * g['n'] for g in grp) / gn,
                 ban * 100.0 / len(grp)))
    print('全体      %4d %7d %6d %6d %6d %7.0f%% %8.2f %8.0f%%'
          % (len(rows), tot_n, tot_n / len(rows), tot_sc,
             sum(r['avg'] * r['sc'] for r in rows) // max(1, tot_sc),
             sum(1 for r in rows if r['sc'] and r['avg'] < SCENE_FRAG) * 100.0 / len(rows),
             sum(r['td'] * r['n'] for r in rows) / tot_n,
             sum(1 for r in rows if r['end'] in END_BAN) * 100.0 / len(rows)))

    print('-' * 88)
    print('结构未达标清单（合并时要处理的对象）')
    one = [r for r in rows if r['sc'] <= 1 and r['n'] >= 400]
    frag = [r for r in rows if r['sc'] > 1 and r['avg'] < SCENE_TARGET_MIN]
    endb = [r for r in rows if r['end'] in END_BAN]
    endw = [r for r in rows if r['end'] in END_WEAK]
    dens = [r for r in rows if r['td'] > TEMPLATE_DENSITY_ALERT]
    short = [r for r in rows if r['n'] < CH_MERGE_BAND[0]]
    print('  一拍一章（无「——」）        %3d 章：%s'
          % (len(one), '、'.join(str(r['no']) for r in one)))
    print('  镜头碎片化（均长<%d）      %3d 章：%s'
          % (SCENE_TARGET_MIN, len(frag), '、'.join(str(r['no']) for r in frag)))
    print('  章末模板收尾（%s）      %3d 章：%s'
          % ('/'.join(END_BAN), len(endb), '、'.join(str(r['no']) for r in endb)))
    print('  章末空转收尾                %3d 章：%s'
          % (len(endw), '、'.join(str(r['no']) for r in endw)))
    print('  └ 弱收尾合计（模板+空转）    %3d 章（目标 ≤%d）'
          % (len(endb) + len(endw), int(len(rows) * 0.3)))
    print('  模板密度>%.1f/千字           %3d 章：%s'
          % (TEMPLATE_DENSITY_ALERT, len(dens), '、'.join(str(r['no']) for r in dens)))
    print('  章长<%d（合并目标下限）    %3d 章'
          % (CH_MERGE_BAND[0], len(short)))
    print('  对话归属词合计 %d 次（「赵升说」类；对话体单一化指标）'
          % sum(r['attr'] for r in rows))

    # 章末类型序列 + 连续同类型
    print('-' * 88)
    seq = [r['end'] for r in rows]
    print('章末类型分布：'
          + '、'.join('%s×%d' % (t, c) for t, c in Counter(seq).most_common()))
    runs = []
    j = 0
    while j < len(seq):
        k = j
        while k + 1 < len(seq) and seq[k + 1] == seq[j]:
            k += 1
        if k - j + 1 >= 3:
            runs.append('%s×%d（第%d—%d章）'
                        % (seq[j], k - j + 1, rows[j]['no'], rows[k]['no']))
        j = k + 1
    if runs:
        print('  连续同类型（>=3 连，读起来会撞车）：' + '；'.join(runs))
    else:
        print('  [OK] 无 >=3 连的章末同类型。')

    if detail:
        print('-' * 88)
        print('逐章明细（合并映射用）')
        print('%-5s %6s %4s %5s %5s %-4s %6s %5s  %s'
              % ('章', '字数', '镜头', '均长', '最短', '章末', '模板', '归属', '章名'))
        for r in rows:
            print('%-5d %6d %4d %5d %5d %-4s %6.2f %5d  %s'
                  % (r['no'], r['n'], r['sc'], r['avg'], r['min'],
                     r['end'], r['td'], r['attr'], r['title']))


def main():
    args = sys.argv[1:]
    if args and os.path.exists(args[0]):
        text = open(args[0], encoding='utf-8').read().replace('\r\n', '\n')
        check(os.path.basename(args[0]), text)
        return

    allch = load_all()
    mode = args[0] if args else ''
    want_cross = mode == '全'
    want_feel = mode == '读感'
    want_struct = mode in ('全', '合并', '结构')
    single = bool(args) and mode not in ('全', '读感', '合并', '结构')
    if single:
        key = args[0]
        if key.isdigit():
            allch = [c for c in allch if re.match(r'^第0*%d章_' % int(key), c[0])]
        else:
            allch = [c for c in allch if key in c[1]]

    bad = 0
    sus = 0
    only_struct = mode in ('合并', '结构')
    if not want_feel and not only_struct:
        for fn, title, body in allch:
            problems, suspects = check(
                '第%s章 %s' % (fn.split('章')[0].replace('第', '').lstrip('0') or '?', title),
                body, struct=single)
            if problems:
                bad += 1
            elif suspects:
                sus += 1
    total_n = sum(cjk(b) for _, _, b in allch)
    if not want_feel and not only_struct:
        print('-' * 60)
        print('体检 %d 章，%d 正文字；有硬伤 %d 章，有可疑 %d 章'
              % (len(allch), total_n, bad, sus))
        print('提示：[硬伤] 必改；[可疑] 只供参考，套话/术语替代命中老章属正常。')
        if not single:
            print('      结构项（镜头/章末/模板密度）不在此列表，'
                  '见 `python 脚本/文风体检.py 结构`。')
    if want_cross:
        cross_chapter_report(allch)
    if want_feel or want_cross:
        density_report(allch)
    if want_struct:
        struct_report(allch, detail=(mode == '合并'))


if __name__ == '__main__':
    main()