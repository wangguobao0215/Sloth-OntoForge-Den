#!/usr/bin/env python3
"""
gen_react_types.py — Sloth-OntoForge-Den · 树懒 · 本体锻炉
YAML scenario → TypeScript 类型定义 (types.ts)

生成内容：
  - 所有 Kind 的 interface（含 subkind extends）
  - 所有 Relator 的 interface
  - 所有 Quality / Mode 的 interface
  - 所有 Phase 的 string literal union + const tuple (as const)
  - 所有 Event 的判别联合 (discriminated union)
  - 所有 Command 的常量表 (含 role 守卫)
  - API 客户端桩 (Axios 风格)

依赖：pyyaml 仅此而已。无 TS 编译期依赖。

用法：
  python gen_react_types.py fixtures/quote-order-schedule.yaml
  python gen_react_types.py fixtures/quote-order-schedule.yaml --out types.ts
"""

from __future__ import annotations
import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.exit("需要 pyyaml：pip install pyyaml")

from common import pascal, camel, screaming_snake, XSD_TO_TS


# ──────────────────────────────────────────────────────────────
# 主生成
# ──────────────────────────────────────────────────────────────
def generate(sc: dict[str, Any]) -> str:
    meta = sc["meta"]
    upper = sc.get("upper", {})
    domain = sc.get("domain", {})
    app = sc.get("application", {})

    lines: list[str] = []

    # ── 文件头 ──────────────────────────────────────────
    lines.append(f"/**")
    lines.append(f" * 自动生成，请勿手改。")
    lines.append(f" * Scenario : {meta['name_cn']}")
    lines.append(f" * ID       : {meta['id']}")
    lines.append(f" * Version  : {meta.get('version', '1.0.0')}")
    lines.append(f" * Generator: Sloth-OntoForge-Den · 树懒 · 本体锻炉 v2")
    lines.append(f" * Date     : {dt.date.today().isoformat()}")
    lines.append(f" */")
    lines.append("")
    lines.append("/* eslint-disable @typescript-eslint/no-explicit-any */")
    lines.append("")

    # ── Base interfaces ─────────────────────────────────
    lines.append("// =============================================================")
    lines.append("// Base (本体论根类型，所有实体都继承)")
    lines.append("// =============================================================")
    lines.append("export interface BaseEntity {")
    lines.append("  id: string;           // UUID")
    lines.append("  created_at: string;   // ISO datetime")
    lines.append("  updated_at: string;   // ISO datetime")
    lines.append("}")
    lines.append("")

    # ── Kinds ───────────────────────────────────────────
    lines.append("// =============================================================")
    lines.append("// Kinds (独立存在的业务对象)")
    lines.append("// =============================================================")
    for k in upper.get("kinds", []) + domain.get("kinds", []):
        cls = pascal(k["id"])
        pi = k.get("pi", "id")
        pi_fields: list[str] = []
        for p in pi.replace(" ", "").split("+"):
            p = p.strip()
            if p and p != "id":
                pi_fields.append(f"  {p}: string;")
        lines.append(f"/** <<kind>> {k['label']} (PI: {pi}) */")
        lines.append(f"export interface {cls} extends BaseEntity {{")
        for f in pi_fields:
            lines.append(f)
        lines.append("}")
        lines.append("")

        # subkinds (extends)
        for sub in k.get("subkinds", []):
            lines.append(f"export interface {sub} extends {cls} {{}}")
            lines.append("")

    # ── Relators ────────────────────────────────────────
    lines.append("// =============================================================")
    lines.append("// Relators (关系实体 · 绑定两端)")
    lines.append("// =============================================================")
    for rel in upper.get("relators", []):
        cls = pascal(rel["id"])
        lines.append(f"/** <<relator>> {rel['label']} — 绑定 {', '.join(pascal(b) for b in rel['binds'])} */")
        lines.append(f"export interface {cls} extends BaseEntity {{")
        for b in rel["binds"]:
            b_cls = pascal(b)
            field = camel(b) + "_id"
            lines.append(f"  {field}: string;  // FK → {b_cls}")
        lines.append("}")
        lines.append("")

    # ── Qualities (可量化属性) ─────────────────────────
    lines.append("// =============================================================")
    lines.append("// Qualities (可量化属性 · 依附具体 Kind)")
    lines.append("// =============================================================")
    for q in domain.get("qualities", []):
        cls = pascal(q["id"])
        ts_type = XSD_TO_TS.get(q["xsd"], "string")
        of_list = q["of"] if isinstance(q["of"], list) else [q["of"]]
        doc_of = ", ".join(pascal(o) for o in of_list)
        lines.append(f"/** <<quality>> {q['label']} · 依附 {doc_of} */")
        lines.append(f"export interface {cls}Quality {{")
        lines.append(f"  value: {ts_type};")
        if q["xsd"] == "decimal":
            lines.append(f"  unit?: string;   // 单位 (元/公斤/...)")
        lines.append("}")
        lines.append("")

    # ── Modes (不可分的内在属性) ─────────────────────────
    lines.append("// =============================================================")
    lines.append("// Modes (依附于具体 Kind，不可跨实体共享)")
    lines.append("// =============================================================")
    for m in domain.get("modes", []):
        cls = pascal(m["id"])
        ts_type = XSD_TO_TS.get(m["xsd"], "string")
        of_list = m["of"] if isinstance(m["of"], list) else [m["of"]]
        doc_of = ", ".join(pascal(o) for o in of_list)
        lines.append(f"/** <<mode>> {m['label']} · 依附 {doc_of} */")
        if "enum" in m:
            enum_items = " | ".join(f'"{v}"' for v in m["enum"])
            lines.append(f"export type {cls}Mode = {enum_items};")
        else:
            lines.append(f"export type {cls}Mode = {ts_type};")
        lines.append("")

    # ── Phases (状态枚举) ──────────────────────────────
    lines.append("// =============================================================")
    lines.append("// Phases (状态机 · string literal union + as const 元组)")
    lines.append("// =============================================================")
    for ph in app.get("phases", []):
        target = pascal(ph["of"])
        states = ph["states"]
        # string literal union
        union = " | ".join(f'"{s}"' for s in states)
        lines.append(f"export type {target}Phase = {union};")
        # as const 元组 (方便 Object.values 遍历 + 下拉选项)
        tuple_items = ", ".join(f'"{s}"' for s in states)
        lines.append(f"export const {target}Phases = [{tuple_items}] as const;")
        # 初始状态常量
        lines.append(f"export const {target}InitialPhase: {target}Phase = \"{ph['initial']}\";")
        lines.append("")

    # ── Events (事件 · discriminated union) ─────────────
    lines.append("// =============================================================")
    lines.append("// Events (事件 · 判别联合 · 每个事件对应一个 phase 转移)")
    lines.append("// =============================================================")
    events = app.get("events", [])
    if events:
        # 每个 event 一个 interface
        for e in events:
            cls = pascal(e["id"])
            lines.append(f"export interface {cls}Event {{")
            lines.append(f'  type: "{e["id"]}";')
            lines.append(f"  /** {e['label']} · triggers: {e['triggers']} */")
            lines.append(f"  payload?: Record<string, unknown>;")
            lines.append("}")
            lines.append("")
        # 总联合
        union = " | ".join(pascal(e["id"]) + "Event" for e in events)
        lines.append(f"export type ScenarioEvent = {union};")
        lines.append("")
        # 事件 ID 常量
        lines.append("export const EventTypes = {")
        for e in events:
            const_name = screaming_snake(e["id"])
            lines.append(f'  {const_name}: "{e["id"]}" as const,')
        lines.append("} as const;")
        lines.append("")

    # ── Commands (命令路由 · 含 role 守卫) ──────────────
    lines.append("// =============================================================")
    lines.append("// Commands (/命令路由表 · quick/direct/query)")
    lines.append("// =============================================================")
    commands = app.get("commands", [])
    if commands:
        lines.append("export interface Command {")
        lines.append("  name: string;")
        lines.append("  type: 'quick' | 'direct' | 'fill' | 'prompt';")
        lines.append("  endpoint: string;")
        lines.append("  method: 'GET' | 'POST' | 'PUT' | 'DELETE';")
        lines.append("  role?: string;  // 缺省 = 任何登录用户")
        lines.append("}")
        lines.append("")
        lines.append("export const Commands: readonly Command[] = [")
        for c in commands:
            method, path = c["endpoint"].split(" ", 1)
            role_arg = f', role: "{c["role"]}"' if "role" in c else ""
            lines.append(f'  {{ name: "{c["name"]}", type: "{c["type"]}", endpoint: "{path}", method: "{method}"{role_arg} }},')
        lines.append("] as const;")
        lines.append("")

        # role 索引表 (便于权限检查)
        role_cmds = [c for c in commands if "role" in c]
        if role_cmds:
            lines.append("/** role → 可见命令清单 (用于菜单可见性判断) */")
            lines.append("export const CommandsByRole: Record<string, readonly string[]> = {")
            role_groups: dict[str, list[str]] = {}
            for c in role_cmds:
                role_groups.setdefault(c["role"], []).append(c["name"])
            for role, names in role_groups.items():
                items = ", ".join(f'"{n}"' for n in names)
                lines.append(f'  {role}: [{items}],')
            lines.append("};")
            lines.append("")

    # ── Queries (自然语言查询 · 用于 LLM 路由示例) ────
    queries = app.get("queries", [])
    if queries:
        lines.append("// =============================================================")
        lines.append("// Query examples (自然语言 → 路由 · LLM few-shot 用)")
        lines.append("// =============================================================")
        lines.append("export const QueryExamples = [")
        for q in queries:
            lines.append(f'  {{ natural: "{q["natural"]}", route: "{q["route"]}" }},')
        lines.append("] as const;")
        lines.append("")

    # ── Realism 边界声明 (LLM 拒绝清单) ────────────────
    nonexistent = meta.get("realism_statement", {}).get("nonexistent", [])
    if nonexistent:
        lines.append("// =============================================================")
        lines.append("// Realism 边界 · 用户提及这些概念时 LLM 必须拒绝")
        lines.append("// =============================================================")
        lines.append("export const OutOfOntologyConcepts: readonly string[] = [")
        for x in nonexistent:
            lines.append(f'  "{x}",')
        lines.append("] as const;")
        lines.append("")

    # ── API Client 桩 (axios 风格) ─────────────────────
    if commands:
        lines.append("// =============================================================")
        lines.append("// API Client 桩 (axios 风格 · 替换 axiosInstance 即可接入)")
        lines.append("// =============================================================")
        lines.append("export interface ApiClient {")
        lines.append("  request<T = unknown>(method: string, path: string, body?: unknown): Promise<T>;")
        lines.append("}")
        lines.append("")
        lines.append("/**")
        lines.append(" * 为每个 command 生成类型安全的调用函数。")
        lines.append(" * 用法:")
        lines.append(" *   const api = createApi(client);")
        lines.append(" *   await api.approve({ id: '...' });")
        lines.append(" */")
        lines.append("export const createApi = (client: ApiClient) => ({")
        seen_names: set[str] = set()
        for c in commands:
            method, path = c["endpoint"].split(" ", 1)
            fn_name = camel(c["name"].lstrip("/").replace("-", "_"))
            if fn_name in seen_names:
                continue
            seen_names.add(fn_name)
            # 提取 path 参数
            import re
            params = re.findall(r"\{(\w+)\}", path)
            param_sig = ", ".join(f"{p}: string" for p in params)
            path_interp = path
            for p in params:
                path_interp = path_interp.replace(f"{{{p}}}", f"${{{p}}}")
            # 无路径参数时签名只有 body；有路径参数时 id 在前 body 在后
            if params:
                sig = f"{param_sig}, body?: unknown"
            else:
                sig = "body?: unknown"
            lines.append(f"  {fn_name}: ({sig}) =>")
            lines.append(f'    client.request("{method}", `{path_interp}`, body),')
        lines.append("});")
        lines.append("")

    # ── 文件尾 ──────────────────────────────────────────
    lines.append("// =============================================================")
    lines.append("// End of auto-generated types")
    lines.append("// =============================================================")
    lines.append("")

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser(
        description="树懒 · 本体锻炉 — YAML → TypeScript 类型定义"
    )
    p.add_argument("scenario", type=Path, help="scenario YAML 路径")
    p.add_argument("--out", type=Path, default=None,
                   help="输出 .ts 路径 (默认 = scenario 同目录 types.ts)")
    args = p.parse_args()

    with args.scenario.open("r", encoding="utf-8") as f:
        sc = yaml.safe_load(f)

    ts = generate(sc)

    out_path = args.out or (args.scenario.parent / "types.ts")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(ts, encoding="utf-8")
    print(f"✅ TypeScript 类型定义已生成: {out_path}")


if __name__ == "__main__":
    main()
