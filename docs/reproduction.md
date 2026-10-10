# 操作说明

当前仓库收录真实 GPU 检测工作副本；本次发布仅验证语法、来源哈希及结果文件，没有重跑 GPU。下述导出和复算工具不加载模型。

## 1. 导出服务器真实材料

把当前项目包放到服务器 `/data/llmxcpg-repro/github/llmxcpg-reproduction` 后执行完整命令：

```bash
/data/llmxcpg-repro/envs/llmxcpg/bin/python \
  /data/llmxcpg-repro/github/llmxcpg-reproduction/scripts/export_server_artifacts.py \
  --root /data/llmxcpg-repro \
  --run-dir results/formai_full383_20261010_104348 \
  --output /data/llmxcpg-repro/github/server-artifacts-20261010.zip
```

该工具只读既有文件，向明确的输出路径写一个小 ZIP，已有同名输出会停止。只收集白名单脚本、提示词、LICENSE、配置、日志、预测、FormAI 输入及指标 TSV；不收集权重、缓存、环境目录、SSH 凭据。ZIP 含代码及原日志，属于私下核对材料，不直接上传 GitHub。清单记录存在/缺失文件、SHA256、文件大小、Python 与已安装依赖版本。发现必需材料缺失时仍提供清单，但以非零退出状态提示检查。

## 2. 对保存概率复算

在原服务器执行：

```bash
/data/llmxcpg-repro/envs/llmxcpg/bin/python \
  /data/llmxcpg-repro/github/llmxcpg-reproduction/scripts/recompute_metrics.py \
  --predictions /data/llmxcpg-repro/results/formai_full383_20261010_104348/QwQ-32B-Preview-bnb-4bit_formai_avengers_test_instruction_predictions.jsonl \
  --expected-samples 383 \
  --output /data/llmxcpg-repro/github/recomputed_formai_metrics.json \
  --csv /data/llmxcpg-repro/github/recomputed_formai_metrics.csv
```

输入字段为 `label` 和 `probability_vulnerable`，工具不会使用可能采用其他判定规则的 `prediction` 字段。0.5 使用 `>=`，0.547 使用 `>`，明确保留边界统计。输出文件已有同名时停止。该命令是本次新增的复算工具使用说明，尚未在真实服务器概率上执行。

## 3. 历史 GPU 评测命令结构

以下结构与已成功运行的命令相同；真实工作副本已收录，实验服务器原路径仍可直接使用。示例通过交互输入选卡 UUID，每次创建新结果目录。本次发布未执行 GPU 命令。将仓库脚本部署到新机器时，必须先准备相同提示词路径，保持作者原输入格式。

```bash
(
set -euo pipefail
read -r -p "请填写 RTX 6000 Ada 的 GPU UUID：" LLMXCPG_GPU_UUID
test -n "$LLMXCPG_GPU_UUID"
LLMXCPG_RUN_DIR="/data/llmxcpg-repro/results/formai_full383_$(date +%Y%m%d_%H%M%S)"
mkdir "$LLMXCPG_RUN_DIR"
cd "$LLMXCPG_RUN_DIR"
CUDA_VISIBLE_DEVICES="$LLMXCPG_GPU_UUID" \
HF_HOME=/data/llmxcpg-repro/cache/huggingface \
XDG_CACHE_HOME=/data/llmxcpg-repro/cache \
TORCH_HOME=/data/llmxcpg-repro/cache/torch \
TRITON_CACHE_DIR=/data/llmxcpg-repro/cache/triton \
CUDA_CACHE_PATH=/data/llmxcpg-repro/cache/cuda \
HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
/data/llmxcpg-repro/envs/llmxcpg/bin/python -u \
  /data/llmxcpg-repro/work/detect_local_offline.py \
  --base-model /data/llmxcpg-repro/models/QwQ-32B-Preview-bnb-4bit \
  --model-path /data/llmxcpg-repro/models/LLMxCPG-D \
  --dataset-path /data/llmxcpg-repro/src-frozen/llmxcpg-main/data/formai_avengers_test_instruction.json \
  --threshold 0.5 \
  --output-dir "$LLMXCPG_RUN_DIR" \
  2>&1 | tee "$LLMXCPG_RUN_DIR/run.log"
)
```

正式输入使用作者纯文本 `Instruction / Input / Response` 格式；不能换为短文本生成检查用的 chat template 再称为同一实验。No=0 / Yes=1 的分类头与最后位置 softmax 是分类步骤，非自由文本生成。
