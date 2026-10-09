---
name: sloth-ontoforge-den
chinese_name: 树懒 · 本体锻炉
display_name: Sloth-OntoForge-Den
version: 2.0.0
family: Sloth-Role-Eido
description: >-
  Compiles business scenarios into AI-native product skeletons — ontology (BFO+UFO),
  data models, command routing, and LLM prompts via a seven-stage pipeline
  (Arp/Smith/Spear methodology). Use when the user wants to design an ontology
  for an AI product, convert business domains into knowledge graphs, build
  dialog-based ERP systems, or ground LLM outputs with ontological realism.
description_zh: >-
  把业务场景锻造成 AI 原生产品的本体骨架 + 数据模型 + 命令路由 + LLM prompt。
  七阶段管线（Arp/Smith/Spear《Building Ontologies with BFO》方法论合成）。
triggers:
  - 用本体设计一个 AI 产品
  - 把 XX 业务本体化
  - 知识图谱化
  - 对话式 ERP 怎么建
  - 领域模型 → 数据库 → Prompt → API 拉通
  - LLM 幻觉想用本体兜底
---

# Sloth-OntoForge-Den · 树懒 · 本体锻炉

> <p align="center"><img src="https://raw.githubusercontent.com/wangguobao0215/Sloth-OntoForge-Den/main/assets/qrcode.jpg" width="80" /><br/><sub>扫码关注 <b>树懒老K</b> · 获取更多 AI 技能</sub><br/><i>慢一点，深一度</i></p>
>
> **Ontology-Landing v2 · Arp 增强版**
> 把"本体论"从哲学概念锻造成 AI 原生产品（ERP/HR/MES/对话式系统）的可执行设计规则。

输入：一个业务场景（一句话描述）。
输出：本体驱动的产品设计包（本体骨架 + 数据模型 + 对话/命令路由 + 语义富化规则 + 验证清单）。

## 来源（v2 关键升级：Arp/Smith/Spear 书正文已通读）

**主源 · 整本通读**：
**Arp, Smith, Spear《Building Ontologies with Basic Formal Ontology》MIT Press 2015**（245 页，ISBN 978-0-262-52781-1）
—— 从 [hlaszny.eu 镜像](https://www.hlaszny.eu/NEBIH/ontology/BuildingOntologies_with_BasicFormalOntology.pdf) 下载到完整 PDF；抽取全文 9917 行；精读 Ch3（Domain Ontology Design 5 步法）+ Ch4（Terms/Definitions/Classification 25 条 best practice）+ Ch5（BFO Continuants）+ Ch7（Relations）+ Ch8（OWL + Protégé 实战）。

**辅助源（论文）**：
1. Guizzardi《Ontology-Driven Conceptual Modeling with Applications》SBSI 2008 —— UFO/OntoUML 12 个 stereotype
2. Amaral 等《Applying ODCM to the interpretation process》CEUR ONTOBRA 2025 —— 符号解释模型（Sign Triad + Metadata 分类）
3. Peixoto 等《Ontology-driven context engineering for semantically-aware chatbot responses》Semantic Web Journal 2025 —— 9 步 NeSy 语义富化框架
4. Amara 等《Ontological Modeling of ERP for Industry 4.0》CEUR 2022 —— ERP 本体建模样板

---

## 核心立场：本体实在论（Ontological Realism，本书立论根基）

> "描述现实里存在什么，而不是我们对它知道什么。"（Arp Ch4 §25: rule of objectivity）

每次开始建模前必须回答：**该场景里，独立于人脑和系统而存在的实体是什么？**
- ✅ 客户存在、机床存在、报价单存在（即使没人去看，它们还是在那里）
- ❌ "热门客户"不存在 —— 它是系统基于规则计算出的派生属性，不能当 kind
- ❌ "待审批报价"不存在 —— 它是 phase（报价单的一个状态），不是独立实体

**这一条是 v1 版本最大的升级：先问"什么存在"，再谈"怎么建模"。**

---

## 触发条件
以下任一出现即启用：
- "用本体/ontology 设计一个 AI 产品/ERP/HR/MES"
- "把 XX 业务本体化 / 知识图谱化"
- "对话式 ERP / 命令界面 / Path C 怎么建"
- "LLM 在业务系统里老幻觉，想用本体兜底"
- "领域模型 → 数据库 → Prompt → API 想一条线拉通"

---

## 核心流程：七阶段管线（v1 五阶段 + Arp 增强）

### Phase 1 — 场景锚定 + 实在论声明（20 分钟）

**必须回答 7 个硬问题**，缺一个就停下先问用户：

| # | 锚点 | 问题 | 典型答案 |
|---|---|---|---|
| 1 | 业务边界 | 场景的起止点？ | "销售接到询价 → 生成报价单" |
| 2 | 角色集合 | 谁在场景里说话/做事？ | 客户、销售、报价工程师、审批经理 |
| 3 | 关键实体 | 核心业务对象（名词）？ | 产品、工艺、材料、报价单 |
| 4 | 关键事件 | 改变状态的动作（动词）？ | 询价、核算、审批、下发 |
| 5 | 关键关系 | 实体之间的绑定？ | 报价单-包含-报价项；产品-需要-工艺 |
| 6 | 边界之外 | 明确不在范围里的？ | 生产排程、采购 |
| **7** | **实在论声明** | **该场景里，独立存在的是什么？派生出来的是什么？** | **见下** |

**实在论声明模板**（强制输出）：
```
【独立存在】客户、产品、员工、机床、材料、报价单（physical / social entity）
【派生属性】客户信用等级（依附于客户的 mode）、报价总额（计算属性）
【不存在】"热门客户"、"待审批报价"、"高毛利产品" —— 这些是查询结果或阶段状态，不入本体
```

### Phase 2 — 上层本体选型（5 分钟决策）

| 上层本体 | 适用 | 代价 |
|---|---|---|
| **BFO**（本书） | 强调物质/过程/时间切分（制造、设备、医疗、物理世界） | 哲学严谨，工具少 |
| **UFO / OntoUML** | 强调角色/关系/社会化概念（ERP/HR/CRM/对话系统） | 工具齐全，学习曲线陡 |
| **DOLCE** | 强调认知/语言/文化概念（多语言、多租户） | 表达力强，工程案例少 |

**新规则**：两者可以组合。BFO 提供**关系骨架**（part_of / depends_on / participates_in），UFO 提供**stereotype 标签**（kind/role/relator/phase/mode）。本 skill 默认走 **BFO 关系 + UFO 标签** 组合。

> **注意**：`<<relator>>` 是 UFO 独有概念，BFO 没有直接对应的上层类。编译到 OWL 时，relator 声明为 `owl:Class`（不挂 BFO 父类），通过 `BFO:specifically_depends_on` 关系标注其依赖的各方。

### Phase 3 — Arp 5 步建模（核心工艺，来自 Ch3）

**Step 1: Demarcate 划定范围**
用一句话写出"本体 X 是关于 Y 领域的本体"。
例："报价本体是关于 CNC 机加工企业从询价到报价单生成这一段业务流程的本体。"

**Step 2: Gather Terms 收集术语**
从以下 4 个来源收词（Ch3 §Gather）：
- 领域专家的口头词（开会时他们实际说的名词）
- 现有文档（SOP、合同、报价单模板）
- 已有数据（数据库表名、字段名）
- 相邻本体的术语（OBO Foundry 里的 OBI、IAO 等）

**Arp 术语规范**（Ch4 25 条节选，强制执行）：
- #5 用单数名词（`Customer` 不要 `Customers`）
- #7 避免缩写（`Customer_Relationship_Management` 不要 `CRM` 做本体类名）
- #8 每个术语配唯一 alphanumeric ID（`ONT_Customer`、`ONT_Quotation`）
- #9 确保单义性（一个词只能对应一个本体概念）
- #11 避免集体名词（`Material` 不要 `Materials`；`Inventory` 不是本体类）
- #12 区分 general vs particular（`Customer` 是 general；`Customer_ABC_Corp` 是 particular，只实例化）

**Step 3: Provisional Ordering 临时层级**
按"更一般 → 更具体"粗排，先不要管 is_a 是不是严格。

**Step 4: Regimentation 规整（最关键的一步）**
- 找到**最高层普遍者（highest-level universals）**，挂到 BFO 根节点
- 每个非根术语用**亚里士多德式定义（Aristotelian definition）**：`genus + differentia`
  - 模板：`X =def. a [genus] which [essential differentia]`
  - 例：`Quotation =def. a document (genus) which binds a seller, a buyer, and a set of priced line items with a validity period (differentia)`
- **asserted single inheritance**：每个类在 asserted 层级只有一个 is_a 父类（Ch4 §23）
  - 允许 inferred 多继承（推理器算出来的）
  - asserted 违反 → 重新拆类

**Step 5: Encoding 编码**
用 Protégé + BFO.owl 作为 import，把 Step 4 的定义翻译成 OWL。
- `<<kind>>` → `owl:Class` + `rdfs:subClassOf` BFO:Material Entity 或 BFO:Object
- `<<quality>>` → `owl:DatatypeProperty` + XSD range
- `<<relator>>` → `owl:Class` + reification + BFO:specifically_depends_on
- `<<event>>` → `owl:Class` + `rdfs:subClassOf` BFO:Process

### Phase 4 — 三层本体骨架（BFO + UFO 组合）

**Layer A — 上层（BFO 关系 + UFO stereotype 双标注）**

| 业务概念 | BFO 父类 | UFO Stereotype | 同一性原则 |
|---|---|---|---|
| Customer | BFO:Object | `<<kind>>` | customer_no |
| Product | BFO:Object | `<<kind>>` | sku |
| Quotation | BFO:Information Content Entity | `<<kind>>` | quote_no |
| DirectCustomer | Customer (单继承) | `<<subkind>>` | — |
| SalesRep | — | `<<role>>` | 依赖 QuotationRelator |
| QuotationRelator | UFO 扩展（BFO 无直接对应）| `<<relator>>` | 绑定 Customer + SalesRep |
| Draft/Pricing/PendingApproval/... | — | `<<phase>>` of Quotation | 互斥穷举 |
| CustomerCreditLevel | BFO:Quality | `<<mode>>` | 依附具体 Customer |
| UnitPrice | BFO:Quality | `<<quality>>` | XSD decimal |
| SubmitQuote | BFO:Process | `<<event>>` | — |

**Layer B — 领域（BFO 关系显式标注）**

每个关系必须显式标注 BFO 关系类型：
- `QuoteItem part_of Quotation`（BFO:continuant_part_of）
- `CustomerCreditLevel specifically_depends_on Customer`
- `SalesRep participates_in QuotationRelator`
- `SubmitQuote has_participant SalesRep`
- `Quotation located_in QuotationSystem`（可选）

**Layer C — 应用（全用 role 表达）**
- Quoter = Customer playing Inquirer role in Inquiry relator
- Approver = Employee playing Approver role in Approval relator

### Phase 5 — 编译到可执行制品

| 制品 | 编译规则 |
|---|---|
| **① OWL / TTL** | 导入 `http://purl.obolibrary.org/obo/bfo.owl`；每个 asserted 类只一个 `rdfs:subClassOf`；关系用 RO（Relations Ontology）标准（BFO:part_of = BFO:0000050 等） |
| **② DB schema** | `<<kind>>` → 表 + UUID；`<<relator>>` → 关联表；`<<phase>>` → 枚举 + 状态机 CHECK；`<<quality>>` → 数值列 + 单位列 |
| **③ API schema** | 每个 `<<event>>` 一个 POST 端点；每个 `<<relator>>` 一套"建立/解除/变更"端点 |
| **④ 对话/命令路由** | `<<event>>` → `/命令`（直连 API，不走 LLM）；`<<kind>>` 查询 → LLM；`<<role>>` 权限 → 命令可见性 |
| **⑤ LLM Prompt（verbalization）** | 把本体公理翻译成业务语言 + few-shot 路由示例 |
| **⑥ RBAC 权限模块** | `<<command>>` + `<<role>>` → FastAPI 依赖注入；命令-角色双向映射；角色解析函数 |

**Verbalization 模板**（compile_prompt 自动生成，不含本体论术语）：
```
你是 {domain} 领域的 AI 助理。

## 核心业务对象
- 客户（ONT_Customer）：用 customer_no 唯一识别
- 产品（ONT_Product）：用 sku 唯一识别
- ...

## 业务角色
- 销售：在报价关系、订单关系中承担职责的一方
- ...

## 状态流转规则
- 报价单状态流转：Draft → Pricing → PendingApproval → Approved → Sent → Accepted（只能按顺序推进，禁止跳跃）
- ...

## 业务规则
- 核心业务对象包括客户、产品、报价单等，每个对象都有唯一识别码
- 销售、报价人、审批人是业务角色，不是员工的行政职位
- 报价单、销售订单、排产任务都有严格的状态流转规则

## 路由规则
- 写操作（创建/修改/审批/提交） → 路由到 /命令
- 读操作（查询/统计/分析） → 用知识图谱上下文回答
- 超出范围 → 明确拒绝

## 可用命令
- /quote → POST /api/inquiry/submit（需要 SalesRep 角色）
- ...

## 路由示例
- 用户说：「查一下我本周提交的报价」 → 路由：LLM → SQL
- 用户说：「帮我提交一份报价」 → 路由：/submit-quote 命令
```

### Phase 6 — 验证（三层）

- **L1 HermiT/Pellet**：0 unsatisfiable class
- **L2 Themis 基线**（参考 Amara 2022）：`quote_item relator_of quotation`、`sales_rep role_in quotation_relator`、`approval phase_guard`
- **L3 端到端冒烟**：happy path + 4 negative cases + LLM 反幻觉测试（给本体外请求，必须拒绝）

### Phase 7 — 实在论复查（v2 新增）

完工后回头问自己 3 个问题：
1. 这个本体描述的实体，如果公司倒闭了、系统下线了，哪些还在？
   - 客户/员工/机床（物理/社会实体）→ 还在 → 是 kind
   - 报价单/工单（信息实体）→ 还在 → 是 kind
   - 报价项（关系绑定）→ 还在 → 是 relator
   - 草稿状态（phase）→ 不存在了 → 是 phase，不是 kind ✅ 正确
2. 哪些"类"其实是查询结果？删掉它们。
3. 哪些"类"其实是计算属性？降级为 quality 或 mode。

---

## 决策规则速查

- **造不造新 stereotype？** → 永远先用 UFO 现有 12 个 + BFO 现有关系（part_of / depends_on / participates_in / located_in / preceded_by）
- **概念是 kind 还是 role？** → 问"它能不能脱离关系独立存在？"能=kind，不能=role
- **概念是 kind 还是 phase？** → 问"实体消失后它还在不在？"不在=phase
- **概念是 kind 还是 quality？** → 问"它能不能脱离承载它的实体？"不能=quality
- **要不要建关联表？** → 关系是 relator 就建；如果只是属性型关联（"属于"），用外键
- **LLM 兜不住就退到命令？** → 任何写操作必须命令化，LLM 只负责解释与查询
- **本体粒度多细？** → 一个 `<<kind>>` 对应一个业务人员口头能独立说出的名词
- **asserted 单继承违反？** → 拆类或加 differentia，不要允许多 is_a 父类

## 反模式（禁止清单）

- ❌ 把"订单详情"做成 kind —— 它是 relator
- ❌ `<<role>>` 没有对应的 `<<relator>>`
- ❌ `<<phase>>` 之间允许跳跃（必须过 guard）
- ❌ 把 LLM 直接接到写操作
- ❌ 本体和数据库 schema 不一致
- ❌ prompt 写成"你是专家，请回答"——必须把公理 verbalize 进去
- ❌ 把"热门客户""高毛利产品"做成 kind —— 它们是查询结果或计算属性
- ❌ 用缩写做类名（CRM → Customer_Relationship_Management）
- ❌ asserted 层多继承
- ❌ 在定义里用被定义词本身（循环定义）

---

## 试跑示范：销售报价（完整版见 trial-sales-quotation-v2.md）

> **场景**：销售接到客户询价 → 核算工艺/材料 → 生成报价 → 走审批 → 发给客户 → 60 天未确认自动过期。

**Phase 1 实在论声明**：
- 独立存在：客户、产品、员工、CNC 机床、材料、报价单
- 派生属性：客户信用等级、报价总额、毛利率
- 不存在：热门客户、待审批报价、高毛利产品

**Phase 2**：BFO + UFO 组合（BFO 提供关系，UFO 提供标签）。

**Phase 3 Arp 5 步**：
1. 范围声明："报价本体是关于 CNC 机加工企业从询价到报价单归档这段业务流程的本体"
2. 术语收集：从 SOP、报价单模板、CRM 数据库、OBO Foundry 相关本体
3. 临时层级：Customer > DirectCustomer/ChannelCustomer；Product > Finished/Semi；...
4. 规整：每个术语给 Aristotelian 定义
   - `Quotation =def. an information content entity which binds a seller, a buyer, a set of priced line items, and a validity period`
   - 每个 asserted 单继承
5. 编码：Protégé + import bfo.owl

**Phase 4-7 见 trial 文件**。

---

## 交付清单
每个场景交付：
1. 场景契约（≤150 字）+ 实在论声明
2. 上层本体选型决策（1 行 + 理由）
3. Arp 5 步记录（范围/术语表/临时层级/规整后定义/OWL 编码）
4. 三层本体表（Upper/Domain/Application，含 BFO 关系标注）
5. 6 个工程制品对应表
6. 三层验证 + 实在论复查结果

## 自动化脚本（scripts/）

**Phase 5 编译 + Phase 6/7 验证 + TypeScript 类型生成全部脚本化**，YAML 是单一真相源：

| 脚本 | 作用 | 触发 |
|---|---|---|
| `scripts/wizard.py` | Phase 1-4 交互式引导 → scenario YAML | `python wizard.py` |
| `scripts/compile.py` | Phase 5: YAML → OWL + DDL + OpenAPI + commands + prompt | `python compile.py <scenario.yaml>` |
| `scripts/validate.py` | Phase 6+7: L1 OWL + L2 结构基线 + L3 pytest 骨架 | `python validate.py <scenario.yaml>` |
| `scripts/gen_react_types.py` | YAML → TypeScript 类型定义（interfaces + enums + API client 桩） | `python gen_react_types.py <scenario.yaml>` |
| `scripts/sync_to_neo4j.py` | YAML → Neo4j Cypher 注入（schema + graph + seed） | `python sync_to_neo4j.py <scenario.yaml>` |
| `scripts/gen_alembic_migration.py` | YAML → Alembic migration（DDL + CHECK 约束 + Phase 触发器） | `python gen_alembic_migration.py <scenario.yaml>` |

一键跑通：
```bash
cd scripts/
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
make demo       # 用 quote-order-schedule fixture 跑通
make wizard     # 交互生成新 scenario
```

详见 [`scripts/README.md`](scripts/README.md)。
