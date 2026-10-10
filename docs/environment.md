# 实验环境

2026-10-10 从服务器通过标准库 importlib.metadata 只读查询并导出。未为了发布改变依赖。

| 组件 | 版本 |
| --- | --- |
| Python | 3.11.17 |
| torch | 2.5.1+cu124 |
| transformers | 4.47.1 |
| peft | 0.14.0 |
| bitsandbytes | 0.45.0 |
| accelerate | 1.2.1 |
| huggingface-hub | 0.27.0 |
| numpy | 1.26.4 |
| tqdm | 4.67.1 |
| jsonlines | 4.0.0 |
| scikit-learn | 1.5.2 |
| NVIDIA 驱动 | 570.86.15 |
| 内核 | Linux 5.15.0-134-generic |
| 实際评测 GPU | NVIDIA RTX 6000 Ada Generation，49140 MiB |
| 峰值分配显存 | 20.62 GiB |

正式分类为 BF16、本地预量化 NF4 4-bit + double quantization、PEFT LoRA、SDPA、batch_size=1、use_cache=False。脚本固定 random 和 torch 种子 42；数据先打乱再按 Token 长度分组，共 128 组，实际样本数是 383。

只让一张 GPU 可见后，模型使用 cuda:0 和 device_map={"": 0}。数字选卡曾出现设备不一致，正式成功运行采用 UUID 选择 RTX 6000 Ada；请查询自己的设备 UUID，原标识不公开。

requirements.txt 记录已验证的 Linux GPU 环境，不是 Windows 安装教程；CPU 复算工具仅需 Python 标准库。操作系统发行版和 CUDA toolkit 完整信息尚待补充。PyTorch 的 +cu124 是运行构建信息，不代表已经验证系统 toolkit 版本。
