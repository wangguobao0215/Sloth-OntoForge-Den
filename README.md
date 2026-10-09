<p align="center">
  <img src="assets/sloth-avatar-round.png" width="120" />
</p>

<h1 align="center">树懒 · 本体锻炉</h1>

<p align="center">
  <strong>Sloth-OntoForge-Den</strong><br/>
  把业务场景锻造成 AI 原生产品的本体骨架 + 数据模型 + 命令路由 + LLM prompt
</p>

<p align="center">
  <img src="assets/qrcode.jpg" width="140" /><br/>
  <sub>扫码关注 <strong>树懒老K</strong> · 获取更多 AI 技能</sub><br/>
  <em>慢一点，深一度</em>
</p>

---

## 品名释义

**「树懒」** 取自品牌 IP「树懒老K」—— 慢一点，深一度。本体论建模是一项需要深度思考的工作，树懒的「慢」恰好对应了 Arp/Smith/Spear 五步法的严谨与耐心。

**「本体锻炉」** 将本体论建模比喻为锻造工艺：YAML 场景定义是原材料，七阶段管线是锻炉，六种工程制品是锻造成品。

## 功能概览

- **七阶段管线**：从场景契约到可执行制品，完整覆盖 Arp/Smith/Spear BFO 方法论
- **6 种工程制品**：OWL/TTL 本体、PostgreSQL DDL（含状态机触发器）、OpenAPI、命令路由、LLM 系统 Prompt、FastAPI RBAC 模块
- **BFO + UFO 组合**：BFO 提供关系骨架，UFO 提供 stereotype 标签（kind/role/relator/phase/mode）
- **Alembic Migration 生成**：upgrade/downgrade + 乐观锁 + actor 审计
- **TypeScript 类型生成**：接口 + 可辨识联合 + API Client 桩
- **Neo4j Cypher 生成**：schema 约束 + graph 关系 + seed 数据
- **三层验证**：L1 OWL 语法、L2 结构基线（11 类测试）、L3 冒烟测试骨架
- **业务化 Verbalization**：自动去本体论术语，生成 LLM 可读的业务规则 + few-shot 路由示例

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/wangguobao0215/Sloth-OntoForge-Den.git
cd Sloth-OntoForge-Den/scripts

# 安装依赖
pip install -r requirements.txt

# 跑通 fixture（报价→订单→排产全链路）
make demo

# 完整管线（含 Neo4j + Alembic）
make demo && make neo4j && make migrate
```

输出在 `scripts/out/quote-order-schedule/` 目录。

## 目录结构

```
Sloth-OntoForge-Den/
├── SKILL.md              # 技能定义（七阶段管线指令）
├── scripts/              # 自动化编译脚本
│   ├── compile.py        # YAML → 6 制品
│   ├── validate.py       # 三层验证
│   ├── gen_alembic_migration.py  # Alembic 迁移生成
│   ├── gen_react_types.py       # TypeScript 类型生成
│   ├── sync_to_neo4j.py         # Neo4j Cypher 生成
│   ├── common.py                # 共享工具模块
│   └── fixtures/                # 场景 YAML
├── references/           # 参考论文与文档
├── assets/               # 品牌资源
└── CHANGELOG.md          # 变更记录
```

## 版本

当前版本：2.0.0

## 许可证

MIT License
