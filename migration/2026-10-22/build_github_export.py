#!/usr/bin/env python3
"""Prepare the GitHub source/data snapshot in a separate directory."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
SELF = Path(__file__).resolve()
ARCHIVE_BUILDER = SELF.with_name("build_server_archive.py")
MANIFEST = SELF.with_name("GITHUB_TRANSFER_MANIFEST.json")
EXCLUDE_PREFIXES = (
    "tgppo/setup/scip-6.0.1/",
    "tgppo/setup/soplex-4.0.1/",
    "docs/stage1/sources/",
)
README = """# TGPPO 复现与搜索信息 Critic

本仓库包含当前研究源码、阶段文档、25 个训练/开发和 66 个测试 MILP MPS 实例，以及六个服务器训练作业的配置。旧模型权重、轨迹、编译产物、原始论文 PDF 和体积较大的第三方 SCIP/SoPlex 源码未提交；对应版本与构建线索见 tgppo/setup/source_versions.json 和 migration/2026-10-22/environment/。

今晚的实验协议：B0、R0、Rjoint × 种子 11/22，六个独立 V100 作业，各 500 个完整 episode，每 100 保存，开发集逐种子选权重。目标 V100 和 Slurm 未在源机验证，正式训练尚未启动。B0 是本轮 120 秒/Adam/四任务批更新的原架构参照，不是论文 3600 秒/AdamW 全规模复现。

从 [服务器交接](migration/2026-10-22/HANDOFF_SERVER_2026-10-22.md)、[Codex 接续 prompt](migration/2026-10-22/PROMPT_服务器Codex.md) 和 [六作业说明](migration/2026-10-22/server-run/README.md) 开始。研究代码在 tgppo/experiments/server-20261022，定制绑定源码在 tgppo/experiments/stage4/metrics_binding。GitHub 文件范围见 migration/2026-10-22/GITHUB_TRANSFER_MANIFEST.json。已生成的直传包是另一个独立交付，包含 SCIP/SoPlex 源码；本 Git 快照不包含该 tar.gz。
"""
GITIGNORE = """# Generated training and local environments
*.pt
*.pkl
*.pyc
*.pyo
*.so
*.o
*.a
**/__pycache__/
**/build/
**/dist/
**/.pytest_cache/
**/.venv/
.env
.env.*
/tgppo/solver/
/tgppo/downloads/
/tgppo/setup/scip-6.0.1/
/tgppo/setup/soplex-4.0.1/
/docs/stage1/sources/
/migration/2026-10-22/*.tar.gz*
/tgppo/runs/server6-20261022/
"""


def load_archive_builder():
    spec = importlib.util.spec_from_file_location("handoff_pack", ARCHIVE_BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    target = args.output.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit("Output directory must be empty")
    target.mkdir(parents=True, exist_ok=True)
    m = load_archive_builder()
    selected = []
    for src in m.selected():
        rel = src.relative_to(ROOT).as_posix()
        if rel.startswith(EXCLUDE_PREFIXES):
            continue
        if src == MANIFEST or rel == "README.md":
            continue
        selected.append(src)
    for src in selected:
        rel = src.relative_to(ROOT)
        dst = target / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            dst.symlink_to(src.readlink())
        else:
            shutil.copy2(src, dst)
    (target / "README.md").write_text(README)
    (target / ".gitignore").write_text(GITIGNORE)
    files = [p for p in target.rglob("*") if p.is_file() and not p.is_symlink()]
    counts = {
        "train_mps": sum("tgppo/datasets/train_instances/" in p.as_posix() and p.name.endswith(".mps.gz") for p in files),
        "test_mps": sum("tgppo/datasets/test_instances/" in p.as_posix() and p.name.endswith(".mps.gz") for p in files),
    }
    if counts != {"train_mps": 25, "test_mps": 66}:
        raise SystemExit("MPS count mismatch: {}".format(counts))
    total_bytes = sum(p.stat().st_size for p in files)
    largest = max(files, key=lambda p: p.stat().st_size)
    if largest.stat().st_size >= 100_000_000:
        raise SystemExit("File too large for standard GitHub blob: {}".format(largest))
    data = {
        "schema": "tgppo-github-transfer-v1",
        "date": "2026-10-22",
        "target": "DaisyLandForu/tgppo_alter",
        "file_count_excluding_manifest": len(files),
        "total_bytes_excluding_manifest": total_bytes,
        "train_mps_count": counts["train_mps"],
        "test_mps_count": counts["test_mps"],
        "largest_file": {"path": largest.relative_to(target).as_posix(), "bytes": largest.stat().st_size},
        "excluded": [
            "old checkpoints (.pt), trajectories (.pkl), compiled objects/shared libraries, build directories",
            "source machine Conda environment and account/session credentials",
            "download tarball and the handoff .tar.gz archive",
            "paper PDFs under docs/stage1/sources",
            "upstream SCIP/SoPlex source trees: acquire fixed commits from tgppo/setup/source_versions.json or use direct-transfer archive",
        ],
        "files_sha256": {
            p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)
        },
    }
    MANIFEST.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    shutil.copy2(MANIFEST, target / MANIFEST.relative_to(ROOT))
    print(json.dumps({"output": str(target), "files": len(files) + 1, "bytes": total_bytes, "train_mps": 25, "test_mps": 66, "largest_bytes": largest.stat().st_size}, ensure_ascii=False))


if __name__ == "__main__":
    main()
