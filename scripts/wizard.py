#!/usr/bin/env python3
"""
wizard.py — Sloth-OntoForge-Den · 树懒 · 本体锻炉
七阶段交互式引导，从零生成 scenario YAML。

用法：
  python wizard.py                                  # 输出到 ./new-scenario.yaml
  python wizard.py --out fixtures/my-scenario.yaml  # 指定输出路径

依赖：pyyaml
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


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  › {prompt}{suffix}: ").strip()
    return val or default


def ask_list(prompt: str) -> list[str]:
    print(f"  › {prompt} (每行一条，空行结束):")
    items = []
    while True:
        line = input("    ").strip()
        if not line:
            break
        items.append(line)
    return items


def header(stage: int, title: str):
    print(f"\n{'─' * 60}")
    print(f"  Phase {stage} · {title}")
    print(f"{'─' * 60}")


# ──────────────────────────────────────────────────────────────
# Phase 1 — 场景锚定 + 实在论声明
# ──────────────────────────────────────────────────────────────
def phase1() -> dict[str, Any]:
    header(1, "场景锚定 + 实在论声明")
    print("回答 7 个硬问题，缺一个就停下先想清楚。\n")
    meta = {
        "id": ask("场景 ID (snake_case, 例: quote-order-schedule)", "my-scenario"),
        "name_cn": ask("场景中文名", "我的场景"),
        "version": "1.0.0",
        "scope": ask("业务边界 (起止点)", "起点 → 终点"),
        "domain_experts": ask_list("领域专家 (每行一个)"),
        "realism_statement": {},
    }
    print("\n  实在论声明 (强制):")
    meta["realism_statement"]["independent"] = ask_list(
        "独立存在的实体 (physical / social entity)"
    )
    meta["realism_statement"]["derived"] = ask_list(
        "派生属性 (mode / 计算属性)"
    )
    meta["realism_statement"]["nonexistent"] = ask_list(
        "不存在的概念 (查询结果/派生, 不入本体)"
    )
    return meta


# ──────────────────────────────────────────────────────────────
# Phase 2 — 上层本体选型
# ──────────────────────────────────────────────────────────────
def phase2() -> str:
    header(2, "上层本体选型")
    print("  BFO  → 物质/过程/时间切分 (制造/设备/医疗)")
    print("  UFO  → 角色/关系/社会化概念 (ERP/HR/CRM)")
    print("  DOLCE → 认知/语言/文化 (多语言多租户)")
    print("  BFO+UFO → 推荐组合 (BFO 关系骨架 + UFO stereotype 标签)\n")
    return ask("选择", "BFO+UFO")


# ──────────────────────────────────────────────────────────────
# Phase 3 — Arp 5 步建模
# ──────────────────────────────────────────────────────────────
def phase3() -> dict[str, Any]:
    header(3, "Arp 5 步建模")
    print("  Step 1: Demarcate (划定范围)")
    demarcate = ask("一句话说明「本体 X 是关于 Y 领域的本体」", "")

    print("\n  Step 2: Gather Terms (收集术语)")
    print("  提示: 4 个词源 → 口头/文档/数据/OBO Foundry")
    terms = ask_list("列出核心业务名词 (每行一个)")

    print("\n  Step 3: Provisional Ordering (临时层级)")
    print("  (wizard 会自动帮你归到 kind/role/relator)")

    print("\n  Step 4: Regimentation (规整 + 亚里士多德定义)")
    print("  每个 kind 必须回答「X =def. a [genus] which [differentia]」")

    print("\n  Step 5: Encoding (wizard 后续阶段编译)")

    return {"demarcate": demarcate, "gathered_terms": terms}


# ──────────────────────────────────────────────────────────────
# Phase 4 — 三层本体骨架
# ──────────────────────────────────────────────────────────────
def phase4(terms: list[str]) -> dict[str, Any]:
    header(4, "三层本体骨架 (BFO + UFO)")
    print(f"  你收集的术语: {terms[:10]}{'...' if len(terms) > 10 else ''}\n")

    upper = {"kinds": [], "roles": [], "relators": []}
    domain = {"kinds": [], "qualities": [], "modes": [], "bfo_relations": []}
    app = {"phases": [], "events": [], "commands": [], "queries": []}

    print("  分类每个术语 (输入 k=kind / r=role / rl=relator / q=quality / m=mode / p=phase / e=event / s=skip):")
    for t in terms:
        cat = ask(f"  {t}", "s").lower()
        if cat == "k":
            pi = ask(f"    {t} 的同一性原则 (PI)", "id")
            bfo = ask(f"    {t} 的 BFO 父类 (Object / InformationContentEntity / ...)", "Object")
            upper["kinds"].append({"id": f"ONT_{t}", "label": t, "bfo_parent": bfo, "pi": pi})
        elif cat == "r":
            deps = ask_list(f"    {t} 依赖哪些 relator (每行一个 ID)")
            upper["roles"].append({"id": f"ONT_{t}", "label": t, "depends_on": deps})
        elif cat == "rl":
            binds = ask_list(f"    {t} 绑定哪些实体 (每行一个 ID)")
            upper["relators"].append({"id": f"ONT_{t}", "label": t, "binds": binds})
        elif cat == "q":
            of = ask(f"    {t} 依附于哪个实体", "ONT_Entity")
            xsd = ask(f"    {t} 数据类型 (string/integer/decimal/date/dateTime)", "string")
            domain["qualities"].append({"id": f"ONT_{t}", "label": t, "xsd": xsd, "of": of})
        elif cat == "m":
            of = ask(f"    {t} 依附于哪个实体", "ONT_Entity")
            xsd = ask(f"    {t} 数据类型", "string")
            domain["modes"].append({"id": f"ONT_{t}", "label": t, "xsd": xsd, "of": of})
        elif cat == "p":
            print(f"    Phase of {t}:")
            states = ask_list("    状态集 (每行一个)")
            initial = ask("    初始状态", states[0] if states else "")
            app["phases"].append({"of": f"ONT_{t}", "states": states, "initial": initial, "transitions": []})
        elif cat == "e":
            triggers = ask(f"    {t} 触发的状态转移 (例: ONT_X.A→B)", "")
            app["events"].append({"id": f"ONT_{t}", "label": t, "triggers": triggers})

    return {"upper": upper, "domain": domain, "application": app}


# ──────────────────────────────────────────────────────────────
# Phase 5/6/7 委托给 compile.py / validate.py
# ──────────────────────────────────────────────────────────────
def phase567_instructions(out_path: Path):
    header(5, "编译 → 验证 (自动化)")
    print(f"  你的 scenario YAML 已经生成到:")
    print(f"    📄 {out_path.resolve()}\n")
    print("  下一步执行:")
    print(f"    python compile.py  {out_path}           # Phase 5: 编译 5 制品")
    print(f"    python validate.py {out_path}           # Phase 6 + 7: 验证")
    print()
    print("  或者用 Makefile 一键:")
    print(f"    make run FIXTURE={out_path}")


# ──────────────────────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(description="树懒 · 本体锻炉 — 7 阶段交互式向导")
    p.add_argument("--out", type=Path, default=Path("new-scenario.yaml"), help="输出 YAML 路径")
    args = p.parse_args()

    print("╔══════════════════════════════════════════════════════╗")
    print("║  🔨 树懒 · 本体锻炉 · Sloth-OntoForge-Den v2        ║")
    print("║  7 阶段交互式建模向导                                 ║")
    print("╚══════════════════════════════════════════════════════╝")

    meta = phase1()
    meta["upper_ontology"] = phase2()
    arp = phase3()
    layers = phase4(arp["gathered_terms"])

    scenario = {
        "meta": meta,
        "upper": layers["upper"],
        "domain": layers["domain"],
        "application": layers["application"],
        "verbalization": {
            "domain_name": meta["name_cn"],
            "axioms": [
                "{<<kind>>} 是独立存在的业务对象，用 {PI} 识别",
                "{<<role>>} 是 {<<relator>>} 关系中扮演某方，不是员工的职位字段",
                "{<<phase>>} 的合法状态是 {phase_list}，状态转移仅当 {guard}",
                "{<<quality>>} 依附于具体 {<<kind>>}，不可跨实体共享",
            ],
            "llm_rules": [
                "命中 event/role 操作 → 路由到 /命令",
                "命中 kind/quality 查询 → 用 KG 上下文回答",
                "命中本体外请求 → 拒绝",
            ],
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        yaml.dump(scenario, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"\n✅ scenario YAML 已生成: {args.out.resolve()}")

    phase567_instructions(args.out)


if __name__ == "__main__":
    main()
