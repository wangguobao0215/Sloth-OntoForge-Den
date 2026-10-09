# 本体锻炉 · 自动化脚本 (Sloth-OntoForge-Den v2)

> 把 SKILL.md 里 7 阶段管线的「最机械的几步」交给脚本，让人专注在**业务判断**上。

## 三个脚本 + 一个 fixture

| 文件 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `wizard.py` | Phase 1-4 交互式引导，生成 scenario YAML | 人工回答 | `scenario.yaml` |
| `compile.py` | Phase 5 编译（YAML → 5 制品） | scenario YAML | OWL + DDL + OpenAPI + commands.json + prompt.md |
| `validate.py` | Phase 6 + 7 三层验证 | scenario YAML + 编译产物 | L1/L2 报告 + L3 pytest 骨架 |
| `gen_react_types.py` | YAML → TypeScript 类型定义 | scenario YAML | `types.ts`（interfaces + enums + API client 桩） |
| `sync_to_neo4j.py` | YAML → Neo4j Cypher 注入 | scenario YAML | `schema.cypher` + `graph.cypher` + `seed.cypher` |
| `gen_alembic_migration.py` | YAML → Alembic migration | scenario YAML | Alembic migration `.py`（DDL + CHECK + 触发器） |
| `fixtures/quote-order-schedule.yaml` | 智能报价 → 订单 → 排产全链路 fixture | — | 跑通脚本的默认示例 |

## 一键启动

```bash
cd scripts/
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
make demo        # 编译 + 验证 fixture
make types       # 生成 TypeScript 类型定义
make neo4j       # 生成 Neo4j Cypher 注入文件
make migrate     # 生成 Alembic migration 脚本
make wizard      # 交互式生成新 scenario
make run FIXTURE=fixtures/my-scenario.yaml
```

## 制品说明

| 制品 | 内容 | 体量 (按 fixture 估算) |
|---|---|---|
| `ontology.ttl` | OWL/Turtle 本体文件，导入 BFO.owl，所有 kind/role/relator/phase/event 都已声明 | ~300 三元组 |
| `schema.sql` | PostgreSQL DDL，含 UUID 主键、phase 状态机触发器（非法转移自动拒绝） | ~200 行 |
| `openapi.yaml` | OpenAPI 3.0.3 规范，每个 command 一个 path | ~100 行 |
| `commands.json` | /命令路由表（quick/direct/query）+ role 权限 + event 列表 | JSON |
| `prompt.md` | LLM System Prompt（verbalization 后的本体公理 + 路由规则 + 边界声明） | Markdown |
| `test_smoke.py` | pytest 冒烟测试骨架：happy-path + phase-guard + role-403 + LLM 反幻觉 | Python |
| `validation_report.md` | 三层验证结果报告 | Markdown |
| `types.ts` | TypeScript 类型定义：Kind/Relator 接口、Phase 联合类型、Event 判别联合、Command 常量表、API client 桩 | ~430 行 |
| `schema.cypher` | Neo4j 约束 + 索引：Kind/Relator/Event UNIQUE 约束、PI 索引、Phase 枚举文档 | ~160 行 |
| `graph.cypher` | Neo4j 关系模板：Relator 绑定、BFO 关系、Phase 转移、Event 记录 | ~220 行 |
| `seed.cypher` | Neo4j 种子数据模板：Kind/Relator 节点创建 | ~100 行 |
| `*_ontology_*.py` | Alembic migration：Kind/Relator 表 + CHECK 约束 + Phase 触发器 + Event 日志表 + downgrade | ~320 行 |

## 验证三层

- **L1**：rdflib 解析 TTL（语法一致性）；可选用 owlready2 跑推理
- **L2**：7 类结构基线测试（relator 绑定数 / role 依赖 / phase 完整性 / event 引用 / command endpoint / BFO 关系白名单 / 实在论声明三段）
- **L3**：pytest 冒烟骨架（人工填 TODO 即可运行）

## 关键设计

- **纯 Python 3.11 + pyyaml + rdflib**，不依赖重量级框架
- **YAML 是单一真相源**：人工维护的只有 scenario YAML，5 制品全从 YAML 派生
- **Phase 5 编译是确定性的**：同样的 YAML 输出同样的制品，便于 diff 和版本控制
- **Phase 6 验证是自动化的**：L1/L2 全自动，L3 生成骨架人工补断言
- **Phase 7 实在论复查**：脚本无法代替人做"这东西到底存不存在"的判断，留给 SKILL.md Phase 7

## 已知局限

- L1 推理需要 `owlready2`（未默认安装，`pip install owlready2` 即可启用）
- L2 仅做结构检查，不做公理深度验证（如需请用 Protégé + HermiT）
- L3 是骨架不是完整测试，需要人工补全 endpoint + body
- 编译不生成 React 组件代码（仅生成 TypeScript 类型定义，组件实现请走项目约定）
