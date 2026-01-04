# 开发过程中的问题与解决方案记录 (ERROR_LOG)

为了保证代码质量并避免重复犯错，本文档记录了开发过程中遇到的关键问题及其解决方案。

## 1. Unicode 编码错误 (Windows Console)
**问题描述**: 
在 Windows 环境下，当控制台尝试输出特殊字符（如 ✅ Emoji）时，抛出 `UnicodeEncodeError: 'gbk' codec can't encode character...`。
**解决方案**: 
不再将详细报告直接打印到控制台。改为将报告写入 UTF-8 编码的 Markdown 文件 (`*_report.md`)，控制台仅显示进度条和最终统计信息。

## 2. Semantic Scholar API Rate Limit
**问题描述**: 
在批量查证时，Semantic Scholar API 频繁返回 429 Too Many Requests，导致查证失败。
**解决方案**: 
在 `verify_by_semantic_scholar` 函数中实现了指数退避 (Exponential Backoff) 重试机制。当收到 429 响应时，程序会等待 2秒、4秒、8秒... 后重试，最大重试次数为 3 次。

## 3. 假文献误判 (False Positives)
**问题描述**: 
对于 `reffa.bib` 中的伪造文献（如 GPT 生成的），工具曾将其误判为“通过”。原因是 API 搜索到了标题相似但年份或作者完全不同的真实论文，且模糊匹配分数过高。
**解决方案**: 
在 `src/verifier.py` 中引入了年份验证逻辑 (`check_year_match`) 和惩罚机制：
- 提取 BibTeX 和 API 结果中的年份。
- 如果年份差异超过 2 年，相似度分数扣除 30 分。
- 只有最终分数超过 80 分才视为有效匹配。

## 4. arXiv 搜索标题清洗过度
**问题描述**: 
`clean_title` 函数曾将所有非字母数字字符移除，导致 "Ckt-GNN" 变成了 "CktGNN"，这在 arXiv API 的精确搜索中可能导致失败。
**解决方案**: 
修改了标题清洗逻辑，将非字母数字字符替换为空格，保留了词的边界，提高了搜索命中率。

## 5. 缺少依赖导致运行失败
**问题描述**: 
在报告生成代码中使用了 `time` 模块但未导入，导致 `NameError`。
**解决方案**: 
在 `main.py` 头部添加了 `import time`。

## 6. 幻觉拦截能力增强 (Strict Verification Logic)
**问题描述**: 
基础的相似度匹配仍然可能被高级的 AI 伪造文献（如：真实的标题 + 假的作者/年份）欺骗。
**解决方案**: 
在 `src/verifier.py` 中实施了“一票否决制”：
- **作者强制匹配**: 如果 BibTeX 提供了作者，但 API 返回的作者姓氏不匹配，最终得分直接归零。
- **年份强制匹配**: 如果 BibTeX 年份与 API 返回年份误差超过 2 年，最终得分直接归零。
- **DOI 穿透验证**: 即使 DOI 正确，也会进行年份比对，不一致则标记为 `DOUBTFUL`。

---
*最后更新: 2026-01-04*
