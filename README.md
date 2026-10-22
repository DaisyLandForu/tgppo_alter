# TGPPO 复现与搜索信息 Critic

本仓库包含当前研究源码、阶段文档、25 个训练/开发和 66 个测试 MILP MPS 实例，以及六个服务器训练作业的配置。旧模型权重、轨迹、编译产物、原始论文 PDF 和体积较大的第三方 SCIP/SoPlex 源码未提交；对应版本与构建线索见 tgppo/setup/source_versions.json 和 migration/2026-10-22/environment/。

今晚的实验协议：B0、R0、Rjoint × 种子 11/22，六个独立 V100 作业，各 500 个完整 episode，每 100 保存，开发集逐种子选权重。目标 V100 和 Slurm 未在源机验证，正式训练尚未启动。B0 是本轮 120 秒/Adam/四任务批更新的原架构参照，不是论文 3600 秒/AdamW 全规模复现。

从 [服务器交接](migration/2026-10-22/HANDOFF_SERVER_2026-10-22.md)、[Codex 接续 prompt](migration/2026-10-22/PROMPT_服务器Codex.md) 和 [六作业说明](migration/2026-10-22/server-run/README.md) 开始。研究代码在 tgppo/experiments/server-20261022，定制绑定源码在 tgppo/experiments/stage4/metrics_binding。GitHub 文件范围见 migration/2026-10-22/GITHUB_TRANSFER_MANIFEST.json。已生成的直传包是另一个独立交付，包含 SCIP/SoPlex 源码；本 Git 快照不包含该 tar.gz。
