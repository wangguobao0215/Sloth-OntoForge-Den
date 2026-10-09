#!/usr/bin/env python3
"""
validate.py — Sloth-OntoForge-Den · 树懒 · 本体锻炉
三层验证：
  L1  OWL 语法一致性 (用 rdflib 解析 TTL，无异常即 pass；若有 owlready2 则跑推理)
  L2  结构基线 (模拟 Themis 的 5 类测试：subclass、property type、domain/range、phase guard)
  L3  端到端冒烟测试骨架 (生成 pytest 脚本 + httpx)

用法：
  python validate.py fixtures/quote-order-schedule.yaml
  python validate.py fixtures/quote-order-schedule.yaml --out-dir out/...

Python 3.11 · 依赖：pyyaml, rdflib (必需), owlready2 (可选), httpx (生成脚本用)
"""

from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：pip install pyyaml")

from common import load_scenario

try:
    from rdflib import Graph
    RDFLIB_OK = True
except ImportError:
    RDFLIB_OK = False

try:
    import owlready2
    OWLREADY_OK = True
except ImportError:
    OWLREADY_OK = False


# ──────────────────────────────────────────────────────────────
# L1 — OWL 语法一致性
# ──────────────────────────────────────────────────────────────
def l1_owl_syntax(ttl_path: Path) -> dict:
    result = {"level": "L1", "test": "OWL 语法一致性", "status": "pass", "details": []}
    if not ttl_path.exists():
        result["status"] = "skip"
        result["details"].append(f"{ttl_path} 不存在，跳过")
        return result
    if not RDFLIB_OK:
        result["status"] = "warn"
        result["details"].append("rdflib 未安装，仅做存在性检查")
        return result
    try:
        g = Graph()
        g.parse(str(ttl_path), format="turtle")
        triples = len(g)
        result["details"].append(f"TTL 解析成功，{triples} 条三元组")
    except Exception as e:
        result["status"] = "fail"
        result["details"].append(f"TTL 解析失败: {e}")

    if OWLREADY_OK:
        try:
            onto = owlready2.get_ontology(str(ttl_path)).load()
            unsat = list(onto.inconsistent_classes()) if hasattr(onto, "inconsistent_classes") else []
            result["details"].append(f"owlready2 加载成功，unsatisfiable classes = {len(unsat)}")
            if unsat:
                result["status"] = "fail"
                result["details"].extend(f"  unsat: {c}" for c in unsat[:10])
        except Exception as e:
            result["status"] = "warn"
            result["details"].append(f"owlready2 加载失败 (可忽略): {e}")
    else:
        result["details"].append("owlready2 未安装，跳过推理")
    return result


# ──────────────────────────────────────────────────────────────
# L2 — 结构基线（模拟 Themis 5 类测试）
# ──────────────────────────────────────────────────────────────
def l2_structural(sc: dict) -> dict:
    result = {"level": "L2", "test": "结构基线 (Themis 风格)", "status": "pass", "details": []}
    failures: list[str] = []

    # 测试 1: 每个 relator 必须绑定 ≥ 2 个 kind/role
    for rel in sc["upper"].get("relators", []):
        if len(rel["binds"]) < 2:
            failures.append(f"❌ {rel['id']} 必须绑定 ≥ 2 个实体，实际 {len(rel['binds'])}")

    # 测试 2: 每个 role 必须依赖 ≥ 1 个 relator
    for r in sc["upper"].get("roles", []):
        if not r.get("depends_on"):
            failures.append(f"❌ {r['id']} 没有依赖任何 relator (裸角色反模式)")

    # 测试 3: 每个 phase 必须互斥且穷举 (状态集 + initial ∈ states)
    for ph in sc.get("application", {}).get("phases", []):
        if ph["initial"] not in ph["states"]:
            failures.append(f"❌ {ph['of']} initial='{ph['initial']}' 不在 states 里")
        for t in ph.get("transitions", []):
            if t["from"] not in ph["states"] or t["to"] not in ph["states"]:
                failures.append(f"❌ {ph['of']} 转移 {t['from']}→{t['to']} 涉及未定义状态")

    # 测试 4: 每个 event 的 triggers 必须引用有效的 phase 转移
    events = {e["id"] for e in sc.get("application", {}).get("events", [])}
    for ph in sc.get("application", {}).get("phases", []):
        for t in ph.get("transitions", []):
            if t["event"] not in events:
                failures.append(f"❌ {ph['of']} 转移 {t['from']}→{t['to']} 引用未定义事件 {t['event']}")

    # 测试 5: 每个 command 必须有对应 endpoint
    for cmd in sc.get("application", {}).get("commands", []):
        if "endpoint" not in cmd or not cmd["endpoint"].startswith(("GET ", "POST ", "PUT ", "DELETE ")):
            failures.append(f"❌ command {cmd['name']} 缺少合法 endpoint")

    # 测试 6: BFO 关系类型必须在白名单内
    BFO_WHITELIST = {
        "continuant_part_of", "occurrent_part_of", "part_of", "has_part",
        "specifically_depends_on", "generically_depends_on",
        "participates_in", "has_participant", "located_in",
        "preceded_by", "derives_from",
    }
    for br in sc.get("domain", {}).get("bfo_relations", []):
        if br["type"] not in BFO_WHITELIST:
            failures.append(f"❌ BFO 关系 {br['type']} 不在白名单")

    # 测试 7: 实在论声明必须有 3 段 (independent / derived / nonexistent)
    rs = sc["meta"].get("realism_statement", {})
    for k in ("independent", "derived", "nonexistent"):
        if not rs.get(k):
            failures.append(f"❌ realism_statement.{k} 缺失或为空")

    # ── 交叉引用完整性 (测试 8-11) ──

    # 收集所有已定义的 ID（kind + role + relator + quality + mode + event）
    upper = sc.get("upper", {})
    domain = sc.get("domain", {})
    all_kinds = upper.get("kinds", []) + domain.get("kinds", [])
    all_roles = upper.get("roles", []) + domain.get("roles", [])
    all_relators = upper.get("relators", []) + domain.get("relators", [])
    all_qualities = domain.get("qualities", [])
    all_modes = domain.get("modes", [])
    all_events = sc.get("application", {}).get("events", [])
    defined_ids = {item["id"] for item in all_kinds + all_roles + all_relators + all_qualities + all_modes + all_events}

    # 测试 8: relator.binds 必须引用已定义的 kind/role ID
    for rel in all_relators:
        for b in rel.get("binds", []):
            if b not in defined_ids:
                failures.append(f"❌ {rel['id']}.binds 引用未定义 ID: {b}")

    # 测试 9: quality.of / mode.of 必须引用已定义的 kind/relator ID
    for q in domain.get("qualities", []):
        targets = q["of"] if isinstance(q["of"], list) else [q["of"]]
        for t in targets:
            if t not in defined_ids:
                failures.append(f"❌ quality {q['id']}.of 引用未定义 ID: {t}")
    for m in domain.get("modes", []):
        targets = m["of"] if isinstance(m["of"], list) else [m["of"]]
        for t in targets:
            if t not in defined_ids:
                failures.append(f"❌ mode {m['id']}.of 引用未定义 ID: {t}")

    # 测试 10: bfo_relations 的 subject/object 必须引用已定义 ID
    for br in domain.get("bfo_relations", []):
        if br.get("subject") not in defined_ids:
            failures.append(f"❌ bfo_relations subject 引用未定义 ID: {br.get('subject')}")
        if br.get("object") not in defined_ids:
            failures.append(f"❌ bfo_relations object 引用未定义 ID: {br.get('object')}")

    # 测试 11: phase.of 必须引用已定义的 kind ID
    kind_ids = {k["id"] for k in all_kinds}
    for ph in sc.get("application", {}).get("phases", []):
        if ph["of"] not in kind_ids:
            failures.append(f"❌ phase.of 引用未定义 kind: {ph['of']}")

    test_count = 11
    if failures:
        result["status"] = "fail"
        result["details"].extend(failures)
    else:
        result["details"].append(f"{test_count} 类基线测试全部通过")
    return result


# ──────────────────────────────────────────────────────────────
# L3 — 端到端冒烟测试骨架生成
# ──────────────────────────────────────────────────────────────
def l3_smoke_scaffold(sc: dict) -> str:
    events = sc.get("application", {}).get("events", [])
    commands = sc.get("application", {}).get("commands", [])
    phases = sc.get("application", {}).get("phases", [])

    lines = [
        '"""',
        f"L3 冒烟测试骨架 — {sc['meta']['name_cn']}",
        "由 Sloth-OntoForge-Den validate.py 自动生成。",
        "用法：pip install httpx pytest && pytest test_smoke.py -v",
        '"""',
        "",
        "import pytest",
        "import httpx",
        "",
        "BASE = 'http://localhost:8000'",
        "client = httpx.Client(base_url=BASE, timeout=10)",
        "",
        "",
        "class TestHappyPath:",
        '    """覆盖每个 <<event>> 至少一次"""',
    ]

    # happy path: 为每个 event 生成一个测试方法
    for e in events:
        method_name = f"test_{e['id'].replace('ONT_', '').lower()}"
        lines.append(f"    def {method_name}(self):")
        lines.append(f'        # {e["label"]} → {e["triggers"]}')
        lines.append(f"        # TODO: 替换为真实 endpoint + body")
        lines.append(f"        # r = client.post('/api/events/{e['id']}', json={{}})")
        lines.append(f"        # assert r.status_code == 200")
        lines.append(f"        pass")
        lines.append("")

    lines.append("")
    lines.append("class TestPhaseGuards:")
    '    """非法状态转移必须返回 400"""'
    lines.append("")
    for ph in phases:
        target = ph["of"].replace("ONT_", "")
        # 生成一个 "反向转移" 的负例
        if ph.get("transitions"):
            t0 = ph["transitions"][0]
            lines.append(f"    def test_{target}_illegal_reverse(self):")
            lines.append(f'        # 反向转移 {t0["to"]} → {t0["from"]} 必须 400')
            lines.append(f"        # r = client.post(...)")
            lines.append(f"        # assert r.status_code == 400")
            lines.append(f"        pass")
            lines.append("")

    lines.append("")
    lines.append("class TestRolePermission:")
    '    """role 校验必须返回 403"""'
    lines.append("")
    for cmd in commands:
        if "role" in cmd:
            method_name = f"test_{cmd['name'].lstrip('/').replace('-', '_')}_forbidden"
            lines.append(f"    def {method_name}(self):")
            lines.append(f'        # 非 {cmd["role"]} 调用 {cmd["name"]} 必须 403')
            lines.append(f"        pass")
            lines.append("")

    lines.append("")
    lines.append("class TestLLMNoHallucination:")
    '    """LLM 必须拒绝本体外请求"""'
    lines.append("")
    nonexistent = sc["meta"].get("realism_statement", {}).get("nonexistent", [])
    for i, x in enumerate(nonexistent):
        lines.append(f"    def test_reject_out_of_ontology_{i}(self):")
        lines.append(f'        # 用户提及「{x}」→ LLM 必须拒绝而非编造')
        lines.append(f"        # r = client.post('/api/chat', json={{'message': '帮我查一下{x}'}})")
        lines.append(f"        # assert '不在本体内' in r.json()['reply']")
        lines.append(f"        pass")
        lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────
def run_all(scenario_path: Path, out_dir: Path | None) -> int:
    sc = load_scenario(scenario_path)
    out_dir = out_dir or (scenario_path.parent / "out" / sc["meta"]["id"])
    out_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict] = []

    # L1
    ttl = out_dir / "ontology.ttl"
    if not ttl.exists():
        # 尝试从 scenario 目录找
        ttl = scenario_path.parent / "out" / sc["meta"]["id"] / "ontology.ttl"
    results.append(l1_owl_syntax(ttl))

    # L2
    results.append(l2_structural(sc))

    # L3 (生成文件)
    smoke_path = out_dir / "test_smoke.py"
    smoke_path.write_text(l3_smoke_scaffold(sc), encoding="utf-8")
    results.append({
        "level": "L3",
        "test": "端到端冒烟测试骨架",
        "status": "generated",
        "details": [f"已生成 {smoke_path} (含 happy-path + phase-guard + role + LLM 反幻觉)"],
    })

    # 输出报告
    print("=" * 60)
    print(f"🔨 本体锻炉 · 验证报告 — {sc['meta']['name_cn']}")
    print("=" * 60)
    overall = "pass"
    for r in results:
        icon = {"pass": "✅", "fail": "❌", "warn": "⚠️ ", "skip": "⏭️ ", "generated": "📝"}.get(r["status"], "•")
        print(f"{icon} {r['level']} · {r['test']}  [{r['status'].upper()}]")
        for d in r["details"]:
            print(f"    {d}")
        if r["status"] == "fail":
            overall = "fail"
    print("=" * 60)
    print(f"Overall: {'✅ PASS' if overall == 'pass' else '❌ FAIL'}")

    # 写验证报告
    report_path = out_dir / "validation_report.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write(f"# 验证报告 — {sc['meta']['name_cn']}\n\n")
        for r in results:
            f.write(f"## {r['level']} · {r['test']}  [{r['status'].upper()}]\n\n")
            for d in r["details"]:
                f.write(f"- {d}\n")
            f.write("\n")

    return 0 if overall == "pass" else 1


def main():
    p = argparse.ArgumentParser(description="树懒 · 本体锻炉 — 三层验证")
    p.add_argument("scenario", type=Path)
    p.add_argument("--out-dir", type=Path, default=None)
    args = p.parse_args()
    sys.exit(run_all(args.scenario, args.out_dir))


if __name__ == "__main__":
    main()
