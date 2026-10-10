# 来源、方法与修改记录

## 真实材料来源

2026-10-10 收集实验服务器 `/data/llmxcpg-repro` 下的真实工作副本、冻结原代码、提示词、LICENSE、模型配置、FormAI 原输入、逐条预测、run.log、指标 TSV 和阈值复算 JSON。导出时间 2026-10-10 03:56:17 UTC。收集过程不加载模型、不重跑 GPU；原评测日志记录为 10:43:51–10:48:46，服务器时间所属时区未独立核对。

每个导出文件的 SHA256 已在本地校验，见 [材料清单](../configs/evidence_manifest.json)。真实检测工作副本 SHA256：`4bee84d5be2b79a218e4ab2c8a77099596d1939b7b452973efad38d973c10026`；冻结检测原源码：`bb8908cb68deb1e9cc3a5fabe23698a828652b68a7629f5783bcde3ca09c0c6f`；原数据：`43ae6acc6e16ae294d77438a621bd110cd27b4888fb05570ee495a9b36e6732b`。

原源码归档：[Zenodo](https://zenodo.org/records/15614095)，交接记录中的短标识 d49afdd。冻结目录没有可读取的 Git HEAD，因此不猜写完整提交 SHA；该待补项不改变对本次原文件哈希的记录。

## 本次核对

383 条预测中概率和标签全部保留在公开 scores.jsonl，代码正文替换为 SHA256。独立标准库工具按 >=0.5 和 >0.547 复算，与服务器保存的两组混淆矩阵和指标一致。原 FormAI 输入与 JSONL 中代码/标签的多重集合一致，包含重复输入；顺序因打乱及按长度分组而改变。多重集合校验只证明当前文件对应，不证明与论文各阶段完全相同。

DataProcessor、InferenceEngine、MetricsCalculator、ResultsHandler 四个类与冻结原源码的 AST 对比完全一致。真实脚本、提示词和 LICENSE 逐字节收录。run.sanitized.log 仅将实验根路径替换为 `<experiment-root>`；服务器阈值 JSON 仅将 prediction_file 改为来源说明，指标对象未修改；原始文件哈希保留在材料清单。

原预测、完整 FormAI 输入和未脱敏日志保存在服务器原结果目录与私下导出，不在 GitHub 再分发。可用公开代码哈希自行比对持有的上游输入，并用公开数值复算指标。

## 已验证的推理适配

原模型加载改为 AutoModelForCausalLM + PeftModel，本地文件加载，BF16、device_map={"":0}、SDPA、batch_size=1、use_cache=False。基础模型 tokenizer 的 No=2753、Yes=9454，分类头为 [2,5120]。适配器真实配置为 r=64、alpha=32、use_rslora=True；静态 Config.LORA_CONFIG 中保留的旧 alpha=128 字典未被本地 PeftModel 加载过程使用，不能将它作为实际适配器参数。

正式格式为 system prompt + Instruction/Input/Response 纯文本；短文本生成验证的 chat template 未用于正式分类。原代码 replace 针对 Single word，而输入使用 One word，本次保持作者原行为。[Issue #20](https://github.com/qcri/llmxcpg/issues/20) 中作者确认此匹配限制，不能据此断定它导致论文差异。

## 工作边界与来源

[官方论文](https://www.usenix.org/system/files/usenixsecurity25-lekssays.pdf) Table 3 和第 4.2 节用于参考指标与阈值；[原仓库](https://github.com/qcri/llmxcpg)为代码来源；[检测模型](https://huggingface.co/QCRI/LLMxCPG-D)为公开适配器来源。权重完整性校验和模型 revision 来自此前已验证下载记录，本次发布没有重新扫描约 20 GB 权重。

2026-10-10 发布整理新增中文文档、标准库阈值复算和材料导出工具、匿名概率、结果汇总、证据审计、依赖及忽略规则。没有重训、重新量化、修改实际推理代码、运行 Q 模型或独立重建 CPG 切片。四样本结果只是流程检查，置信度不等于准确率。
