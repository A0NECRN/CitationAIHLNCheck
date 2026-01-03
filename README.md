# CitationCheck - AI 引文真实性自动化查证工具

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**CitationCheck** 是一款专为科研人员和开发者设计的 BibTeX 引文自动化查证工具。它能够有效识别由大语言模型（如 ChatGPT）生成的“幻觉文献”，并通过多源 API 交叉验证确保引文的真实性与准确性。

## 🌟 核心功能

- **自动化全扫描**: 自动识别并处理当前目录下的所有 `.bib` 文件。
- **多源交叉验证**: 集成 Crossref, Semantic Scholar, 以及 arXiv 三大权威学术数据库。
- **抗幻觉算法**: 深度结合标题相似度、作者匹配以及**严格年份校验**，精准拦截伪造文献。
- **智能重试机制**: 内置指数退避算法，优雅处理 API 频率限制（Rate Limiting）。
- **可视化报告**: 自动生成美观的 Markdown 查证报告，包含 DOI 链接、匹配得分及失败原因。

## 🛠️ 工作原理

系统采用“漏斗式”校验逻辑：
1. **精确匹配**: 优先通过 DOI 进行金标准验证。
2. **模糊检索**: 利用 `RapidFuzz` 算法对标题进行单词级排序比对，兼容各种排版差异。
3. **加权评分**:
   - **标题相似度**: 基础分。
   - **作者加分**: 命中第一作者姓氏额外加分。
   - **年份惩罚**: 年份不匹配（误差 > 2年）将面临重度扣分，这是识别假文献的关键。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 运行查证
将您的 `.bib` 文件放入项目根目录，直接运行：
```bash
python main.py
```
或者指定特定文件：
```bash
python main.py example.bib
```

### 3. 查看结果
查证完成后，项目目录下将生成对应的 `*_report.md` 文件。

## 📂 项目结构
- `main.py`: 程序入口，负责调度与报告生成。
- `src/`: 核心逻辑模块（解析器、验证器）。
- `ERROR_LOG.md`: 记录开发过程中的技术挑战与解决方案。
- `example.bib`: 包含真实文献与测试用伪造文献的示例文件。

## 📝 开发者记录
本项目在开发过程中严格遵循自动化验证与代码整洁规范，详细的错误处理经验记录在 [ERROR_LOG.md](./ERROR_LOG.md) 中。

---
**由 A0NECRN 开发并维护**
