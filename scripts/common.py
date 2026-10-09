"""
树懒 · 本体锻炉 — 共享工具模块

所有脚本的命名转换、XSD 类型映射、场景加载统一收口于此。
任何修改请同步更新此文件，不要在脚本里各写一份。
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml


# ──────────────────────────────────────────────────────────────
# 命名转换（ONT_XXX → 各种目标格式）
# ──────────────────────────────────────────────────────────────

def pascal(ont_id: str) -> str:
    """ONT_Customer → Customer, ONT_CNCMachine → CNCMachine"""
    return ont_id.replace("ONT_", "")


def camel(ont_id: str) -> str:
    """ONT_Customer → customer, ONT_CNCMachine → cncMachine"""
    name = pascal(ont_id)
    if not name:
        return ""
    return name[0].lower() + name[1:]


def snake(ont_id: str) -> str:
    """ONT_Customer → customer, ONT_CNCMachine → cnc_machine"""
    name = ont_id.replace("ONT_", "")
    s1 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s2 = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s1)
    return s2.lower()


def screaming_snake(ont_id: str) -> str:
    """ONT_Customer → CUSTOMER, ONT_CNCMachine → CNC_MACHINE"""
    return snake(ont_id).upper()


def to_table(ont_id: str) -> str:
    """ONT_Customer → customers, ONT_CNCProcess → cnc_processes, ONT_Company → companies"""
    name = snake(ont_id)
    if name.endswith(("s", "x", "z", "ch", "sh")):
        return name + "es"
    if name.endswith("y") and len(name) > 1 and name[-2] not in "aeiou":
        return name[:-1] + "ies"
    if name.endswith(("f", "fe")):
        return name[: -2 if name.endswith("fe") else -1] + "ves"
    return name + "s"


# ──────────────────────────────────────────────────────────────
# XSD → 目标类型映射
# ──────────────────────────────────────────────────────────────

# PostgreSQL DDL 原始类型（compile.py 使用）
XSD_TO_PG = {
    "string": "VARCHAR(256)",
    "integer": "INTEGER",
    "long": "BIGINT",
    "float": "REAL",
    "double": "DOUBLE PRECISION",
    "decimal": "NUMERIC(18,4)",
    "date": "DATE",
    "dateTime": "TIMESTAMPTZ",
    "time": "TIME",
    "boolean": "BOOLEAN",
    "anyURI": "VARCHAR(2048)",
    "base64Binary": "BYTEA",
    "duration": "INTERVAL",
    "gYear": "INTEGER",
}

# SQLAlchemy 类型（gen_alembic_migration.py 使用）
XSD_TO_SA = {
    "string": "sa.String(256)",
    "integer": "sa.Integer",
    "long": "sa.BigInteger",
    "float": "sa.Float",
    "double": "sa.Float",
    "decimal": "sa.Numeric(18, 4)",
    "date": "sa.Date",
    "dateTime": "sa.DateTime(timezone=True)",
    "time": "sa.Time",
    "boolean": "sa.Boolean",
    "anyURI": "sa.String(2048)",
    "base64Binary": "sa.LargeBinary",
    "duration": "sa.Interval",
    "gYear": "sa.Integer",
}

# TypeScript 类型（gen_react_types.py 使用）
XSD_TO_TS = {
    "string": "string",
    "integer": "number",
    "long": "number",
    "float": "number",
    "double": "number",
    "decimal": "number",
    "date": "string",
    "dateTime": "string",
    "time": "string",
    "boolean": "boolean",
    "anyURI": "string",
    "base64Binary": "string",
    "duration": "string",
    "gYear": "number",
}

# Neo4j Cypher 类型（sync_to_neo4j.py 使用）
XSD_TO_CYPHER = {
    "string": "STRING",
    "integer": "INTEGER",
    "long": "INTEGER",
    "float": "FLOAT",
    "double": "FLOAT",
    "decimal": "FLOAT",
    "date": "STRING",
    "dateTime": "STRING",
    "time": "STRING",
    "boolean": "BOOLEAN",
    "anyURI": "STRING",
    "base64Binary": "STRING",
    "duration": "STRING",
    "gYear": "INTEGER",
}

# ──────────────────────────────────────────────────────────────
# 常量
# ──────────────────────────────────────────────────────────────

# Phase 状态列统一名称
PHASE_COLUMN = "phase"

# PI（身份标识）字段统一宽度
PI_VARCHAR_WIDTH = 256


# ──────────────────────────────────────────────────────────────
# 场景加载
# ──────────────────────────────────────────────────────────────

def load_scenario(path: Path) -> dict:
    """加载并返回 scenario YAML dict。"""
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)
