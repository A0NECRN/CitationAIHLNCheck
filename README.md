# CitationCheck - 自动化引文查证工具

`CitationCheck` 是一个专为科研人员和开发者设计的 BibTeX 文献查证工具。它能够自动分析 `.bib` 文件，并通过 Crossref、arXiv 和 Semantic Scholar 等多个学术数据库交叉验证文献的真实性、准确性，有效识别 GPT 等大模型生成的“幻觉文献”（假文献）。

## 🚀 核心功能

- **多源交叉验证**: 整合 Crossref、arXiv 和 Semantic Scholar API，全方位检索文献元数据。
- **假文献识别**: 专门设计的年份校验与作者匹配算法，能精准拦截标题虚假、年份乱编的伪造文献。
- **模糊匹配引擎**: 采用 `RapidFuzz` 算法，兼容 BibTeX 中常见的标题格式差异和大括号干扰。
- **全自动批处理**: 支持自动扫描当前目录下所有 `.bib` 文件，一键生成详细的 Markdown 查证报告。
- **鲁棒性设计**: 内置指数退避重试机制，从容应对 API 频率限制（Rate Limiting）。

## 🛠️ 安装指南

本项目基于 Python 开发，建议在 Windows 11 环境下运行。

1. **克隆仓库**:
   ```bash
   git clone https://github.com/YourUsername/CitationCheck.git
   cd CitationCheck
   ```

2. **安装依赖**:
   使用清华大学镜像源以加快下载速度：
   ```bash
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   ```

## 📖 使用方法

### 快速查证
将您的 `.bib` 文件放入项目根目录，直接运行：
```bash
python main.py
```
程序会自动扫描所有 `.bib` 文件并为每个文件生成对应的 `_report.md` 报告。

### 指定文件查证
```bash
python main.py example.bib
```

## 📊 查证报告示例

生成的报告将以 Markdown 格式保存，包含以下状态：
- ✅ **[通过]**: 文献真实存在且元数据高度匹配。
- ⚠️ **[存疑]**: 找到相似文献但关键字段（如年份、作者）存在偏差。
- ❌ **[未找到]**: 库中无法匹配到该文献，极大概率为假文献。

## 📝 错误记录与维护
项目内置 [ERROR_LOG.md](ERROR_LOG.md)，详细记录了开发过程中的技术挑战（如编码问题、API 限流）及解决方案，确保系统长期稳定运行。

## 🛡️ 开源协议
MIT License
