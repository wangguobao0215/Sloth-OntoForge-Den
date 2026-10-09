#!/usr/bin/env python3
"""
树懒 · 本体锻炉 — YAML → Neo4j Cypher 注入脚本

用法:
    python sync_to_neo4j.py <scenario.yaml>                  # dry-run，输出 .cypher
    python sync_to_neo4j.py <scenario.yaml> --neo4j-uri bolt://localhost:7687 \\
                                             --neo4j-user neo4j --neo4j-password xxx
                                              # 实际执行

生成:
    schema.cypher   — 约束 + 索引 + Phase 枚举属性约束
    graph.cypher    — Relator/BFO 关系 + 事件模板
    seed.cypher     — 种子数据模板（人工补字段后导入）
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

import yaml

from common import pascal, camel, XSD_TO_CYPHER


def collect_defined_ids(scenario: dict) -> set[str]:
    """收集 YAML 中所有已定义的实体 ID，用于过滤悬挂引用。"""
    ids: set[str] = set()
    upper = scenario.get("upper", {})
    domain = scenario.get("domain", {})
    app = scenario.get("application", {})

    for section in (upper, domain):
        for cat in ("kinds", "roles", "relators"):
            for item in section.get(cat, []):
                ids.add(item["id"])
        for item in section.get("qualities", []):
            ids.add(item["id"])
        for item in section.get("modes", []):
            ids.add(item["id"])

    for ev in app.get("events", []):
        ids.add(ev["id"])

    return ids


def generate_schema(scenario: dict, defined_ids: set[str]) -> str:
    """生成 schema.cypher：约束 + 索引。"""
    lines: list[str] = []
    upper = scenario.get("upper", {})
    domain = scenario.get("domain", {})
    app = scenario.get("application", {})

    lines.append("// ═══════════════════════════════════════════════════")
    lines.append(f"// Schema — {scenario['meta']['name_cn']}")
    lines.append(f"// Generated: {datetime.now().isoformat()}")
    lines.append(f"// Generator: Sloth-OntoForge-Den · 树懒 · 本体锻炉 v2")
    lines.append("// ═══════════════════════════════════════════════════")
    lines.append("")

    # ── Kind 约束 + PI 索引 ──
    lines.append("// ── Kind 节点：唯一约束 + PI 索引 ──")
    for section in (upper, domain):
        for k in section.get("kinds", []):
            label = pascal(k["id"])
            lines.append(f"CREATE CONSTRAINT {label}_id_unique IF NOT EXISTS")
            lines.append(f"  FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
            lines.append("")
            # PI 索引
            pi = k.get("pi", "")
            if pi:
                pi_field = pi.split("+")[0].split(" ")[0].strip()
                idx_name = f"{label}_{pi_field}_idx"
                lines.append(f"CREATE INDEX {idx_name} IF NOT EXISTS")
                lines.append(f"  FOR (n:{label}) ON (n.{pi_field});")
                lines.append("")

    # ── Relator 约束 ──
    lines.append("// ── Relator 节点：唯一约束 ──")
    for section in (upper, domain):
        for r in section.get("relators", []):
            label = pascal(r["id"])
            lines.append(f"CREATE CONSTRAINT {label}_id_unique IF NOT EXISTS")
            lines.append(f"  FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
            lines.append("")

    # ── Event 约束 ──
    events = app.get("events", [])
    if events:
        lines.append("// ── Event 节点：唯一约束 ──")
        for ev in events:
            label = pascal(ev["id"])
            lines.append(f"CREATE CONSTRAINT {label}_id_unique IF NOT EXISTS")
            lines.append(f"  FOR (n:{label}) REQUIRE n.id IS UNIQUE;")
            lines.append("")
        # 共享 Event 标签索引
        lines.append("// ── 共享 Event 标签索引（按时间线查询） ──")
        lines.append("CREATE INDEX event_occurred_at_idx IF NOT EXISTS")
        lines.append("  FOR (e:Event) ON (e.occurred_at);")
        lines.append("")

    # ── Phase 枚举约束（属性存在性 + 值域文档化）──
    lines.append("// ── Phase 枚举约束 ──")
    lines.append("// Neo4j 原生不支持 CHECK 约束，用以下方式兜底：")
    lines.append("// 1. 应用层校验（推荐）")
    lines.append("// 2. APOC trigger 拦截非法写入")
    lines.append("// 3. Cypher 查询时 WHERE phase IN [...] 过滤")
    lines.append("")
    for ph in app.get("phases", []):
        label = pascal(ph["of"])
        states = ph["states"]
        states_str = ", ".join(f'"{s}"' for s in states)
        lines.append(f"// {label}.phase ∈ [{states_str}]")
        lines.append(f"// initial: {ph['initial']}")
        lines.append("")

    # ── Mode 枚举约束 ──
    for section in (upper, domain):
        for m in section.get("modes", []):
            if "enum" in m:
                label = pascal(m["of"])
                prop = camel(m["id"])
                vals = ", ".join(f'"{v}"' for v in m["enum"])
                lines.append(f"// {label}.{prop} ∈ [{vals}]")
                lines.append("")

    return "\n".join(lines)


def generate_graph(scenario: dict, defined_ids: set[str]) -> str:
    """生成 graph.cypher：关系模板 + BFO 关系 + Phase 初始值。"""
    lines: list[str] = []
    upper = scenario.get("upper", {})
    domain = scenario.get("domain", {})
    app = scenario.get("application", {})

    lines.append("// ═══════════════════════════════════════════════════")
    lines.append(f"// Graph — {scenario['meta']['name_cn']}")
    lines.append(f"// Generated: {datetime.now().isoformat()}")
    lines.append("// ═══════════════════════════════════════════════════")
    lines.append("")

    # ── Relator 关系（UFO relator 在 Neo4j 中用中间节点 + 两条边表示）──
    lines.append("// ── Relator 中间节点（UFO 模式） ──")
    lines.append("// 每个 Relator 是一个独立节点，通过关系绑定两端")
    lines.append("")
    for section in (upper, domain):
        for r in section.get("relators", []):
            label = pascal(r["id"])
            binds = r.get("binds", [])
            lines.append(f"// {r['label']} ({label}) — 绑定 {len(binds)} 端")
            for b in binds:
                if b in defined_ids:
                    target = pascal(b)
                    rel_type = f"BINDS_{target.upper()}"
                    lines.append(f"// MATCH (r:{label}), (t:{target})")
                    lines.append(f"//   WHERE r.{camel(b)}_id = t.id")
                    lines.append(f"//   CREATE (r)-[:{rel_type}]->(t);")
            lines.append("")

    # ── BFO 关系 ──
    bfo_rels = domain.get("bfo_relations", [])
    if bfo_rels:
        lines.append("// ── BFO 关系（过滤悬挂引用） ──")
        for rel in bfo_rels:
            subj = rel["subject"]
            obj = rel["object"]
            if subj not in defined_ids or obj not in defined_ids:
                lines.append(f"// SKIP: {subj} → {obj}（一端未定义）")
                continue
            rel_type = rel["type"].upper()
            s_label = pascal(subj)
            o_label = pascal(obj)
            lines.append(f"// MATCH (a:{s_label}), (b:{o_label})")
            lines.append(f"//   CREATE (a)-[:{rel_type}]->(b);")
        lines.append("")

    # ── Phase 初始值 MERGE 模板 ──
    lines.append("// ── Phase 初始值（创建节点时设置） ──")
    for ph in app.get("phases", []):
        label = pascal(ph["of"])
        initial = ph["initial"]
        lines.append(f"// MERGE (n:{label} {{id: $id}})")
        lines.append(f"//   ON CREATE SET n.phase = '{initial}', n.created_at = datetime()")
        lines.append(f"//   ON MATCH SET n.updated_at = datetime();")
        lines.append("")

    # ── Event 记录模板 ──
    lines.append("// ── Event 记录模板（每次状态转移创建一个事件节点） ──")
    lines.append("// CREATE (e:Event {")
    lines.append("//   id: randomUUID(),")
    lines.append("//   type: $event_type,")
    lines.append("//   occurred_at: datetime(),")
    lines.append("//   actor_id: $actor_id,")
    lines.append("//   payload: $payload")
    lines.append("// })")
    lines.append("// WITH e MATCH (target {id: $target_id})")
    lines.append("// CREATE (e)-[:TRIGGERED_BY]->(target);")
    lines.append("")

    # ── Phase 转移查询模板 ──
    lines.append("// ── Phase 转移（带 guard 校验） ──")
    for ph in app.get("phases", []):
        label = pascal(ph["of"])
        for t in ph.get("transitions", []):
            guard_comment = f"  // guard: {t['guard']}" if "guard" in t else ""
            lines.append(f"// {label}: {t['from']} → {t['to']} (event: {t['event']}){guard_comment}")
            lines.append(f"// MATCH (n:{label} {{id: $id}})")
            lines.append(f"//   WHERE n.phase = '{t['from']}'")
            lines.append(f"//   SET n.phase = '{t['to']}', n.updated_at = datetime()")
            lines.append(f"//   CREATE (e:{pascal(t['event'])} {{")
            lines.append(f"//     id: randomUUID(), occurred_at: datetime(), actor_id: $actor_id")
            lines.append(f"//   }})-[:TRIGGERED]->(n);")
            lines.append("")

    return "\n".join(lines)


def generate_seed(scenario: dict, defined_ids: set[str]) -> str:
    """生成 seed.cypher：种子数据模板。"""
    lines: list[str] = []
    upper = scenario.get("upper", {})
    domain = scenario.get("domain", {})
    app = scenario.get("application", {})

    lines.append("// ═══════════════════════════════════════════════════")
    lines.append(f"// Seed — {scenario['meta']['name_cn']}")
    lines.append(f"// Generated: {datetime.now().isoformat()}")
    lines.append("// ═══════════════════════════════════════════════════")
    lines.append("// 用法: 取消注释 → 填充 $变量 → 在 Neo4j Browser 执行")
    lines.append("")

    # ── Kind 种子 ──
    lines.append("// ── Kind 节点种子 ──")
    for section in (upper, domain):
        for k in section.get("kinds", []):
            label = pascal(k["id"])
            pi = k.get("pi", "")
            pi_field = pi.split("+")[0].split(" ")[0].strip() if pi else "code"
            phase_prop = ""
            # 检查是否有 phase
            for ph in app.get("phases", []):
                if ph["of"] == k["id"]:
                    phase_prop = f", phase: '{ph['initial']}'"
                    break
            lines.append(f"// CREATE (n:{label} {{")
            lines.append(f"//   id: randomUUID(),")
            lines.append(f"//   {pi_field}: ${pi_field},")
            lines.append(f"//   created_at: datetime(), updated_at: datetime(){phase_prop}")
            lines.append(f"// }});")
        lines.append("")

    # ── Relator 种子 ──
    lines.append("// ── Relator 节点种子（绑定两端 ID） ──")
    for section in (upper, domain):
        for r in section.get("relators", []):
            label = pascal(r["id"])
            binds = r.get("binds", [])
            fk_fields = ",\n".join(
                f"//   {camel(b)}_id: ${camel(b)}_id" for b in binds if b in defined_ids
            )
            lines.append(f"// CREATE (n:{label} {{")
            lines.append(f"//   id: randomUUID(),")
            lines.append(fk_fields + ",")
            lines.append(f"//   created_at: datetime()")
            lines.append(f"// }});")
        lines.append("")

    return "\n".join(lines)


def sync_to_neo4j(uri: str, user: str, password: str, cypher_files: list[Path]) -> None:
    """连接 Neo4j 执行 Cypher。"""
    try:
        from neo4j import GraphDatabase
    except ImportError:
        print("❌ 需要 neo4j 驱动: pip install neo4j")
        sys.exit(1)

    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        for f in cypher_files:
            if not f.exists():
                continue
            content = f.read_text()
            # 过滤注释行和空行
            stmts = [
                s.strip()
                for s in content.split(";")
                if s.strip() and not s.strip().startswith("//")
            ]
            print(f"📡 执行 {f.name}: {len(stmts)} 条语句")
            for i, stmt in enumerate(stmts, 1):
                try:
                    session.run(stmt)
                except Exception as e:
                    print(f"  ⚠️  语句 {i} 失败: {e}")
    driver.close()
    print("✅ Neo4j 同步完成")


def main():
    p = argparse.ArgumentParser(
        description="树懒 · 本体锻炉 — YAML → Neo4j Cypher 注入"
    )
    p.add_argument("scenario", type=Path, help="scenario YAML 路径")
    p.add_argument("--out", type=Path, default=None,
                   help="输出目录 (默认 = scenario 同目录)")
    p.add_argument("--neo4j-uri", type=str, default=None,
                   help="Neo4j URI (bolt://localhost:7687)")
    p.add_argument("--neo4j-user", type=str, default="neo4j")
    p.add_argument("--neo4j-password", type=str, default=None)
    args = p.parse_args()

    scenario = yaml.safe_load(args.scenario.read_text())
    out_dir = args.out or args.scenario.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    defined_ids = collect_defined_ids(scenario)

    # 生成三个 .cypher 文件
    schema = generate_schema(scenario, defined_ids)
    graph = generate_graph(scenario, defined_ids)
    seed = generate_seed(scenario, defined_ids)

    schema_path = out_dir / "schema.cypher"
    graph_path = out_dir / "graph.cypher"
    seed_path = out_dir / "seed.cypher"

    schema_path.write_text(schema)
    graph_path.write_text(graph)
    seed_path.write_text(seed)

    print(f"✅ schema.cypher → {schema_path}")
    print(f"✅ graph.cypher  → {graph_path}")
    print(f"✅ seed.cypher   → {seed_path}")

    # 连接模式
    if args.neo4j_uri and args.neo4j_password:
        sync_to_neo4j(
            args.neo4j_uri, args.neo4j_user, args.neo4j_password,
            [schema_path, graph_path, seed_path],
        )
    else:
        print()
        print("💡 Dry-run 模式，3 个 .cypher 文件已生成。")
        print("   实际注入请指定 Neo4j 连接参数：")
        print(f"   python sync_to_neo4j.py {args.scenario} \\")
        print("     --neo4j-uri bolt://localhost:7687 \\")
        print("     --neo4j-user neo4j --neo4j-password <pwd>")
        print()
        print("   或手动在 Neo4j Browser 里粘贴执行 schema.cypher → graph.cypher → seed.cypher")


if __name__ == "__main__":
    main()
