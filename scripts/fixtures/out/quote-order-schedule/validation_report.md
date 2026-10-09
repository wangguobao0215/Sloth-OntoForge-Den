# 验证报告 — 智能报价 → 订单 → 排产全链路

## L1 · OWL 语法一致性  [PASS]

- TTL 解析成功，297 条三元组
- owlready2 未安装，跳过推理

## L2 · 结构基线 (Themis 风格)  [PASS]

- 7 类基线测试全部通过

## L3 · 端到端冒烟测试骨架  [GENERATED]

- 已生成 fixtures/out/quote-order-schedule/test_smoke.py (含 happy-path + phase-guard + role + LLM 反幻觉)

