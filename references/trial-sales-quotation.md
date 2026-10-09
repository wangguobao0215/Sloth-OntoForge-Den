# Ontology-Landing 试跑记录：销售报价场景

> 执行日期：2026-10-09
> 执行方式：严格按 skill 五阶段推进，每步给出决策与产物

---

## Phase 1 — 场景锚定

**场景契约（138 字）**：
销售接到客户询价（邮件/IM/电话任一来源），录入询价 → 拉工艺与材料数据 → 核算单价 → 生成报价单草稿 → 走审批 → 批准 → 发给客户 → 60 天未确认自动过期 → 客户确认则转销售订单（转单不在本场景）。

- **角色集合**：客户、销售、报价工程师、定价经理、审批经理
- **关键实体**：客户、产品、工艺路线、材料、报价单、报价项、折扣、有效期
- **关键事件**：询价、核算、生成报价、审批、发送、过期
- **边界之外**：合同签署、订单转生产、开票收款

## Phase 2 — 上层本体选型

**决策：UFO**
理由：销售报价 80% 的概念是"社会性角色"（客户、销售、审批人）+ 关系（询价关系、报价关系、审批关系）。UFO 对 role/relator 的显式区分正是这个场景的核心语义痛点——同一个员工在 A 报价里是报价人、在 B 报价里是审批人，身份不该写到员工表里。

## Phase 3 — 三层本体

### Layer A — Upper（UFO stereotype 映射）

| 业务概念 | Stereotype | 同一性原则 / 依赖 |
|---|---|---|
| Customer | `<<kind>>` | customer_no（客户编号） |
| Product | `<<kind>>` | sku |
| Quotation | `<<kind>>` | quote_no（报价单号） |
| DirectCustomer | `<<subkind>>` of Customer | — |
| ChannelCustomer | `<<subkind>>` of Customer | — |
| FinishedProduct | `<<subkind>>` of Product | — |
| SemiProduct | `<<subkind>>` of Product | — |
| SalesRep | `<<role>>` | 依赖 QuotationRelator |
| Approver | `<<role>>` | 依赖 ApprovalRelator |
| Quoter | `<<role>>` | 依赖 QuotationRelator |
| QuoteEngineer | `<<role>>` | 依赖 CostEstimationRelator |
| PricingManager | `<<role>>` | 依赖 DiscountApprovalRelator |
| InquiryRelator | `<<relator>>` | 绑定 Customer + SalesRep |
| CostEstimationRelator | `<<relator>>` | 绑定 Inquiry + QuoteEngineer + CostRecord |
| QuotationRelator | `<<relator>>` | 绑定 Customer + SalesRep + Quotation |
| ApprovalRelator | `<<relator>>` | 绑定 Quotation + Approver |
| QuoteItem | `<<relator>>` | 绑定 Quotation + Product（**不是 kind！**） |
| Draft / Pricing / PendingApproval / Approved / Rejected / Sent / Expired / Accepted | `<<phase>>` of Quotation | 互斥且穷举 |
| CustomerCreditLevel | `<<mode>>` | 依附于具体 Customer |
| CustomerDiscountAuthority | `<<mode>>` | 依附于具体 Customer |
| UnitPrice / Quantity / DiscountRate / ValidityDays / TotalAmount | `<<quality>>` | XSD range |
| SubmitQuote / Approve / Reject / Send / Expire / Accept | `<<event>>` | 各自对应 phase 转移 |

### Layer B — Domain（CNC 机加工报价领域）

| 业务概念 | Stereotype | 说明 |
|---|---|---|
| CNCProcess | `<<kind>>` | PI: process_id |
| MachiningCenter | `<<kind>>` | PI: machine_id |
| Material | `<<kind>>` | PI: material_code |
| Cutter / Fixture | `<<role>>` | 在 ProcessStepRelator 中扮演 |
| ProcessRoute | `<<kind>>` | PI: route_id + version |
| ProcessStepRelator | `<<relator>>` | 绑定 ProcessRoute + CNCProcess + seq_no |
| MaterialRequirementRelator | `<<relator>>` | 绑定 CNCProcess + Material + qty |
| MachineHourRate | `<<quality>>` | MachiningCenter 的机时费 |
| MaterialUnitPrice | `<<quality>>` | Material 的公斤价 |
| CycleTime | `<<quality>>` | CNCProcess 的单件节拍（秒） |

### Layer C — Application（报价应用层）

全部用 role 表达，因为都是"某物在某次报价会话中扮演的角色"：
- Inquiry 在 InquirerRelator 中由 Customer 扮演
- CostRecord 在 EstimationRelator 中由 QuoteEngineer 产出
- QuoteItem 的 unit_price 是 quality，由 MaterialUnitPrice + MachineHourRate × CycleTime 推算（**公式写在本体公理里**，不是代码里硬编码）

## Phase 4 — 编译到可执行制品

### ① OWL（节选）
```turtle
:Quotation rdf:type owl:Class ;
    rdfs:subClassOf [ rdf:type owl:Restriction ;
        owl:onProperty :hasPhase ;
        owl:oneOf (:Draft :Pricing :PendingApproval :Approved :Rejected :Sent :Expired :Accepted) ] .

:QuoteItem rdf:type owl:Class ;
    rdfs:subClassOf :Relator ;   # 显式声明为 relator
    rdfs:comment "QuoteItem is NOT a Kind; it mediates Quotation and Product."@en .

:SalesRep rdf:type owl:Class ;
    rdfs:subClassOf :Role ;
    rdfs:subClassOf [ rdf:type owl:Restriction ;
        owl:onProperty :playsIn ;
        owl:someValuesFrom :QuotationRelator ] .
```

### ② DDL（节选）
```sql
CREATE TABLE customer (
    id UUID PRIMARY KEY,
    customer_no VARCHAR(32) UNIQUE NOT NULL,  -- PI 物理化
    name TEXT NOT NULL,
    credit_level SMALLINT CHECK (credit_level BETWEEN 1 AND 10)  -- <<mode>>
);

CREATE TABLE quotation (
    id UUID PRIMARY KEY,
    quote_no VARCHAR(32) UNIQUE NOT NULL,     -- PI
    customer_id UUID REFERENCES customer(id),
    sales_rep_id UUID REFERENCES employee(id),
    status VARCHAR(20) NOT NULL CHECK (status IN
        ('Draft','Pricing','PendingApproval','Approved','Rejected','Sent','Expired','Accepted')),
    valid_days INT DEFAULT 60,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE quote_item (                -- relator 表
    id UUID PRIMARY KEY,
    quotation_id UUID REFERENCES quotation(id),
    product_id UUID REFERENCES product(id),
    qty NUMERIC NOT NULL CHECK (qty > 0),
    unit_price NUMERIC NOT NULL,
    discount_rate NUMERIC DEFAULT 1.0 CHECK (discount_rate BETWEEN 0 AND 1),
    UNIQUE (quotation_id, product_id)
);

CREATE TABLE approval_log (              -- approval relator 表
    id UUID PRIMARY KEY,
    quotation_id UUID REFERENCES quotation(id),
    approver_id UUID REFERENCES employee(id),
    decision VARCHAR(10) CHECK (decision IN ('Approve','Reject')),
    decided_at TIMESTAMPTZ
);
```

### ③ API（节选）
- `POST /api/inquiry/submit` → 生成 InquiryRelator，自动创建 Draft Quotation
- `POST /api/quotation/{id}/price` → 调用工艺/材料/机时费 KG 算价，phase Draft→Pricing
- `POST /api/quotation/{id}/submit` → Pricing→PendingApproval（**仅当所有 item 已定价**）
- `POST /api/quotation/{id}/approve` → PendingApproval→Approved（**仅 approver_role 可见**）
- `POST /api/quotation/{id}/reject` → PendingApproval→Rejected
- `POST /api/quotation/{id}/send` → Approved→Sent
- 定时任务：每天扫 `valid_days` 超期且 status=Sent 的报价 → Sent→Expired

### ④ 命令路由
| 命令 | 类型 | 路由 |
|---|---|---|
| `/quote` | quick | `/api/inquiry/submit` 直连，不经 LLM |
| `/price {quote_id}` | direct | `/api/quotation/{id}/price` |
| `/approve {quote_id}` | direct | `/api/quotation/{id}/approve`（role 校验） |
| `/reject {quote_id} {reason}` | direct | `/api/quotation/{id}/reject` |
| `/send {quote_id}` | direct | `/api/quotation/{id}/send` |
| "查一下我本周提交的报价" | query | LLM 转 SQL（用本体 verbalization） |
| "为什么报价 X 被驳回" | query | LLM 查 approval_log + reason |
| "把 8 折给客户 Y 行不行" | prompt | LLM 基于 CustomerCreditLevel mode 回答 |

### ⑤ LLM Prompt（verbalization 节选）
```
你是 CNC 机加工报价领域的 AI 助理。本体公理如下：
1. Quotation 是有独立身份的业务对象（kind），用 quote_no 识别；
2. QuoteItem 是 relator（不是 kind），它把 Quotation 与 Product 绑定在一起；
3. SalesRep、Approver、QuoteEngineer 都是 role，必须通过具体关系实例出现，
   不要把它当作员工的"职位字段"来查询；
4. Quotation 的 phase 严格限定为 Draft/Pricing/PendingApproval/Approved/Rejected/Sent/Expired/Accepted；
5. /approve 命令仅在 phase=PendingApproval 时允许调用；调用方必须是当前 ApprovalRelator 中绑定的 approver；
6. 任何写操作必须走 /命令；你只能解释、查询、推荐，禁止代客审批。
当用户请求命中事件清单（SubmitQuote/Approve/Reject/Send/Expire）→ 路由到 /命令；
当用户请求命中 kind 或 quality 查询 → 用 KG 上下文回答；
当用户请求命中本体外事件 → 拒绝并说明"不在报价本体事件范围内"。
```

## Phase 5 — 验证

**L1 本体一致性**（HermiT 推理）：
- 期望 0 个 unsatisfiable class
- 重点检查：`QuoteItem` 被声明为 relator 又同时出现在 quotation.items 集合里 → 必须显式区分 "quote_item 本身" 和 "报价单-包含-报价项" 这一关系，否则会触发循环依赖

**L2 结构基线**（5 条，参考 Amara 2022 ERP 本体）：
| 测试 | 预期 |
|---|---|
| `quote_item relator_of quotation` | pass |
| `direct_customer subclassOf customer` | pass |
| `sales_rep role_in quotation_relator` | pass |
| `approval phase_transition_guard` | pass |
| `unit_price quality_of quote_item` | pass |

**L3 业务冒烟脚本**（伪代码）：
```python
# happy path
customer = create_customer()
inquiry = submit_inquiry(customer, products=[P1, P2])
quote = create_draft(inquiry)
price(quote.id)                       # Draft → Pricing
submit(quote.id)                      # Pricing → PendingApproval
approve(quote.id, approver=AMGR)      # PendingApproval → Approved
send(quote.id)                        # Approved → Sent
advance_days(61)                      # Sent → Expired (cron)

# negative cases
assert reject(quote.id, approver=SALES)   # 403: 非绑定的 approver
assert approve(quote2.id)                 # 400: phase=Draft 不允许
assert llm("把机床升级一下")             # 拒绝：不在本体外编 API
assert llm("查我本周的报价")            # 走 KG 查询，正确返回
```

---

## 试跑结论

| 阶段 | 是否走得通 | 发现的问题 |
|---|---|---|
| Phase 1 锚定 | ✅ | 6 个锚点足以收敛，无需更多提问 |
| Phase 2 选型 | ✅ | 决策表 3 行即够用 |
| Phase 3 三层建模 | ✅ | **关键发现：`QuoteItem` 容易被误建为 kind**，stereotype 表里必须显式列出 relator 类型并加"反模式"提示 |
| Phase 4 编译 | ✅ | 5 个制品全部能从本体表机械生成， verbalization 模板直接套用 |
| Phase 5 验证 | ✅ | L3 冒烟脚本覆盖 happy path + 4 条负面用例，规则清晰 |

**结论**：skill 可执行，且在销售报价这一未预先设计的场景下能给出一致、可落地的产物。
建议把"QuoteItem 是 relator 不是 kind"这类**反模式判断**沉淀为 skill 的硬规则（已写入决策规则速查）。
