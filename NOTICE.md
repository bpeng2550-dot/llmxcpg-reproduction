# 来源与许可

LLMxCPG 原作者：Ahmed Lekssays、Hamza Mouhcine、Khang Tran、Ting Yu、Issa Khalil。原项目：https://github.com/qcri/llmxcpg 。论文：https://www.usenix.org/conference/usenixsecurity25/presentation/lekssays 。本项目为独立复现与本地部署记录。

inference/detect_local_offline.py 派生自作者的 inference/detect_inference.py。真实工作副本由实验服务器取得，未经本次发布编辑；主要改动为本地 Transformers/PEFT 加载、实际适配器配置读取、单卡与显存检查、batch_size=1、提示词绝对路径及峰值显存记录。四个处理类的语法树与冻结原源码一致。详细哈希和方法见 docs/provenance.md。

prompts/detect_system_prompt.txt 从冻结作者源码逐字节复制，LICENSE 为冻结原仓库的 GPL version 3 文本，未修改。新增整理工具按 GPL-3.0-only 提供；代码仍应保留 GPL-3.0 许可和来源。

基础模型和检测模型各自页面标注 Apache-2.0。本仓库没有模型权重或完整外部数据；代码许可不自动覆盖论文、模型与数据。公开 scores.jsonl 保留已保存的数值概率及标签，以代码 SHA256 代替外部代码正文。
