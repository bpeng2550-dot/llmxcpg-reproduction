# 基于 LLMxCPG-D 的代码漏洞检测复现与本地部署

基于 PyTorch、Transformers 和 PEFT，部署公开 QwQ-32B 4-bit 基础模型与 LLMxCPG-D LoRA 适配器，适配离线二分类推理，并在作者提供的 FormAI 检测输入上完成 **383 条样本评测**。采用论文阈值 `p > 0.547` 时，Accuracy 为 **95.30%**，F1 为 **95.24%**，峰值分配显存约 **20.62 GiB**。

本仓库收录服务器上实际运行的检测工作副本、原始系统提示词、保存概率的匿名版本、汇总指标和脱敏日志。真实源码与结果已由服务器导出取得，指标可在 CPU 上独立复算。

## 已完成的工程工作

- 部署公开预量化 NF4 4-bit 基础模型，加载作者已经训练好的 LoRA 适配器。
- 将原作者的模型加载适配为 Transformers/PEFT 本地离线加载，指定单张 RTX 6000 Ada，保留 No/Yes 二分类方式。
- 提取 `No` / `Yes` 两个 Token 的语言模型头权重，以最后位置 logits 的 softmax 概率完成分类。
- 保留作者的数据处理、推理、指标计算和结果保存类；与冻结源码的语法树对比确认这四个类未改变。
- 完成分词器、短生成、四样本流程验证及 FormAI 383 条完整评测。
- 对保存概率按原阈值和论文固定阈值复算，并记录模型版本、源文件哈希、环境和资源开销。

`4-bit` 指使用作者公开的已量化模型，`LoRA` 指加载公开的已训练适配器。本项目尚未重新训练模型；LLMxCPG-Q、Joern CPG 查询、独立切片与端到端复现见[后续计划](docs/roadmap.md)。

## FormAI 结果

数据集共 383 条，BENIGN 198 条，VULNERABLE 185 条。结果已与服务器的逐条概率、阈值复算 JSON、TSV 和运行日志核对。

| 判定规则 | Accuracy | Precision | Recall | F1 | TP | FP | FN | TN |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **p > 0.547（论文阈值）** | **95.30%** | **93.26%** | **97.30%** | **95.24%** | 180 | 13 | 5 | 185 |
| p >= 0.5（原运行） | 96.34% | 93.40% | 99.46% | 96.34% | 184 | 13 | 1 | 185 |

`p` 是漏洞概率。4 条概率恰好为 0.5 的样本均为真实漏洞，没有概率恰好为 0.547 的样本。`argmax` 与 `>= 0.5` 的边界规则不能混用。推理约 4 分 43 秒，GPU 为 NVIDIA RTX 6000 Ada Generation；20.62 GiB 来自 `torch.cuda.max_memory_allocated()`，不是显卡所有进程的总显存。

结果文件：

- [JSON 指标](results/formai_full383_20261010_104348/metrics.json)、[CSV 指标](results/formai_full383_20261010_104348/metrics.csv)。
- [匿名逐条概率](results/formai_full383_20261010_104348/scores.jsonl)：每条保留真实概率与标签，以 SHA256 代替代码正文；未虚构预测。
- [服务器阈值复算](results/formai_full383_20261010_104348/threshold_recheck_050_0547.json)、[原指标 TSV](results/formai_full383_20261010_104348/metrics.server.tsv)、[脱敏日志](results/formai_full383_20261010_104348/run.sanitized.log)。
- [核对记录](results/formai_full383_20261010_104348/audit.json)：原输入与保存预测的代码/标签多重集合一致，包含重复样本计数；逐条概率与完整代码保留在原服务器，不在此公开再分发。

## 运行与复算

在仓库根目录使用任意兼容 Python，仅需标准库即可复算已发布结果：

```bash
python scripts/recompute_metrics.py \
  --predictions results/formai_full383_20261010_104348/scores.jsonl \
  --expected-samples 383 \
  --output /tmp/llmxcpg_formai_recomputed.json \
  --csv /tmp/llmxcpg_formai_recomputed.csv
```

工具拒绝覆盖已有输出。GPU 推理工作副本位于 [inference/detect_local_offline.py](inference/detect_local_offline.py)，提示词位于 [prompts/detect_system_prompt.txt](prompts/detect_system_prompt.txt)。完整历史环境运行命令及路径准备见[复现说明](docs/reproduction.md)。本次发布保留脚本原样：提示词使用固定 `/data/llmxcpg-repro/src-frozen/llmxcpg-main/prompts/detect_system_prompt.txt`，要求单张 RTX 6000 Ada 且至少 28 GiB 空闲显存；跨机器路径和硬件参数化将在后续补充。

## 环境与模型

已核对服务器环境：Python 3.11.17、torch 2.5.1+cu124、transformers 4.47.1、peft 0.14.0、bitsandbytes 0.45.0、accelerate 1.2.1、huggingface-hub 0.27.0。完整版本见 [requirements.txt](requirements.txt) 和[环境记录](docs/environment.md)。

- [基础模型](https://huggingface.co/unsloth/QwQ-32B-Preview-bnb-4bit)，revision `8827dd400f326edcaabd655a8559f9da89f2a6e4`。
- [检测适配器](https://huggingface.co/QCRI/LLMxCPG-D)，revision `91e6c0d0e8ea645047c237166b1403262d116a92`。
- [模型版本与权重校验记录](configs/model_manifest.json)、[服务器材料哈希清单](configs/evidence_manifest.json)。

模型权重、缓存、虚拟环境及完整外部数据不随仓库发布；发布时未升级现有环境或重跑 GPU 评测。

## 与论文的条件差异

[论文](https://www.usenix.org/system/files/usenixsecurity25-lekssays.pdf) Table 3 的 FormAI 参考结果为 Accuracy 81.46%、Precision 80.97%、Recall 80.54%、F1 80.75%。论文描述 LoRA rank=8、alpha=4；实际公开适配器配置和日志为 r=64、alpha=32、use_rslora=True。本地使用 Transformers/PEFT，论文分类推理使用 Unsloth；本次使用作者准备好的检测输入，尚未独立重建查询和切片。原提示词替换不匹配现象保持不变，见[来源与方法记录](docs/provenance.md)。

当前结果如实保留，不在此测试集上搜索最佳阈值。样本数量和原仓库输入对应，不自动证明与论文逐条切片或所有实验条件完全一致；本项目不声称同条件优于论文方法。

## 许可与引用

原代码为 GPL-3.0，本仓库保留原 [LICENSE](LICENSE) 与[原作者归属及修改说明](NOTICE.md)。模型页面标注 Apache-2.0；代码、模型、外部数据和论文分别适用各自许可。本仓库不再分发权重或完整数据。

来源：[原代码仓库](https://github.com/qcri/llmxcpg)、[论文官方页](https://www.usenix.org/conference/usenixsecurity25/presentation/lekssays)。

```bibtex
@inproceedings{lekssays2025llmxcpg,
  title={LLMxCPG: Context-Aware Vulnerability Detection Through Code Property Graph-Guided Large Language Models},
  author={Lekssays, Ahmed and Mouhcine, Hamza and Tran, Khang and Yu, Ting and Khalil, Issa},
  booktitle={34th USENIX Security Symposium (USENIX Security 25)},
  pages={489--507},
  year={2025}
}
```
