# 百世飞升 · 第十世续写

正文工作区：`F:\novel`。

## 目录

```text
F:\novel\
├─ AGENTS.md                     AI 开工入口
├─ README.md                     本页
├─ _backup_before_slim_20260925.zip  瘦身前完整备份
└─ 百世飞升续写\
   ├─ 分章\                      ★ 正文唯一真源
   ├─ 全本.txt                   由脚本生成，不手改
   ├─ 脚本\                      正文管理 / 文风体检
   ├─ 写作资料\                  只保留 4 份长期资料
   └─ 待处理\                    尚未并入正文的候选稿
```

## 核心原则

- **正文事实**：看 `分章/`。
- **现在正在做什么**：看 DevTrace。
- **固定设定**：看 `写作资料/02_设定总表.md`。
- **宏观方向**：看 `写作资料/03_长期总纲.md`。
- 不再用“每章一个交接卡 / 多套章卡 / 多份进度台账”维持活状态。

## 标准模型协作

```text
DeepSeek Flash：规划下一章
→ DevTrace note
→ Qwen 3.8 Max：写正文
→ DevTrace change
→ 脚本检查
→ DeepSeek Flash：验收
→ DevTrace test + 更新当前状态
```

## 常用命令

```bash
cd F:/novel/百世飞升续写
python 脚本/正文管理.py 状态
python 脚本/正文管理.py 全本
python 脚本/正文管理.py 检查
python 脚本/文风体检.py <章号>
python 脚本/文风体检.py 全
python 脚本/文风体检.py 读感
```

增删章一律走 `正文管理.py` 的插入/替换/删除，不手工重编号。
