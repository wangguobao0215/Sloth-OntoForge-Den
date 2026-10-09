#!/usr/bin/env python3
"""
树懒 · 本体锻炉 — YAML → Alembic Migration 脚本生成器

用法:
    python gen_alembic_migration.py <scenario.yaml>
    python gen_alembic_migration.py <scenario.yaml> --pk-type uuid
    python gen_alembic_migration.py <scenario.yaml> --down-revision 42efbdc1c8fc

生成:
    一个 Alembic migration 文件，包含：
    - upgrade():  CREATE TABLE (Kind/Relator) + CHECK 约束 + Phase 触发器 + Event 日志表
    - downgrade(): DROP TABLE + DROP FUNCTION（逆序）

设计:
    - 默认 BigInt PK（匹配 Sloth-HR-Agent 约定）
    - --pk-type uuid 切换为 UUID PK（匹配 OntoForge fixture 约定）
    - 表名 snake_case（ONT_Customer → customer, ONT_CNCMachine → cnc_machine）
    - Phase 状态机用 PostgreSQL CHECK 约束 + 触发器函数实现
"""

from __future__ import annotations

import argparse
import secrets
import re
from datetime import datetime
from pathlib import Path

import yaml

from common import snake, to_table, XSD_TO_SA, XSD_TO_PG, PI_VARCHAR_WIDTH


def gen_revision() -> str:
    """生成 12 位 hex revision ID（密码学安全随机，同毫秒不碰撞）。"""
    return secrets.token_hex(6)


def generate_migration(scenario: dict, pk_type: str = "bigint",
                       down_revision: str | None = None) -> str:
    """生成完整的 Alembic migration 文件内容。"""
    meta = scenario["meta"]
    upper = scenario.get("upper", {})
    domain = scenario.get("domain", {})
    app = scenario.get("application", {})

    revision = gen_revision()
    down_rev = repr(down_revision) if down_revision else "None"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # 收集所有 Kind/Relator/Phase 信息
    all_kinds = upper.get("kinds", []) + domain.get("kinds", [])
    all_relators = upper.get("relators", []) + domain.get("relators", [])
    all_qualities = domain.get("qualities", [])
    all_modes = domain.get("modes", [])
    phases = app.get("phases", [])
    kind_ids = {k["id"] for k in all_kinds}  # 用于区分 Kind vs Role 绑定

    # 构建 phase 查找表 (kind_id → phase_info)
    phase_map: dict[str, dict] = {}
    for ph in phases:
        phase_map[ph["of"]] = ph

    # 构建 quality 查找表 (kind_id → [qualities])
    quality_map: dict[str, list] = {}
    for q in all_qualities:
        targets = q["of"] if isinstance(q["of"], list) else [q["of"]]
        for t in targets:
            quality_map.setdefault(t, []).append(q)

    # 构建 mode 查找表 (kind_id → [modes])
    mode_map: dict[str, list] = {}
    for m in all_modes:
        targets = m["of"] if isinstance(m["of"], list) else [m["of"]]
        for t in targets:
            mode_map.setdefault(t, []).append(m)

    # ── PK 定义 ──
    if pk_type == "uuid":
        pk_col = "sa.Column('id', sa.String(36), primary_key=True, server_default=sa.text('gen_random_uuid()::text'))"
        pk_import = ""
        fk_type = "sa.String(36)"
    else:
        pk_col = "sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True)"
        pk_import = ""
        fk_type = "sa.BigInteger"

    # ── 生成 upgrade() ──
    upgrade_lines: list[str] = []
    downgrade_lines: list[str] = []
    created_tables: list[str] = []  # 用于 downgrade 逆序 drop

    # --- Kind 表 ---
    upgrade_lines.append("    # ── Kind 表 ──")
    for k in all_kinds:
        table = to_table(k["id"])
        created_tables.append(table)
        cols = [pk_col]
        cols.append("sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())")
        cols.append("sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())")

        # PI 字段
        pi = k.get("pi", "")
        if pi:
            for pi_field in pi.split("+"):
                pi_field = pi_field.strip()
                cols.append(f"sa.Column('{pi_field}', sa.String({PI_VARCHAR_WIDTH}), nullable=False)")

        # Phase 字段
        if k["id"] in phase_map:
            ph = phase_map[k["id"]]
            cols.append(f"sa.Column('phase', sa.String(32), nullable=False, server_default='{ph['initial']}')")

        # Quality 字段（内联到 Kind 表）
        for q in quality_map.get(k["id"], []):
            sa_type = XSD_TO_SA.get(q["xsd"], "sa.String(256)")
            q_name = snake(q["id"])
            cols.append(f"sa.Column('{q_name}', {sa_type})")

        # Mode 字段
        for m in mode_map.get(k["id"], []):
            sa_type = XSD_TO_SA.get(m["xsd"], "sa.String(256)")
            m_name = snake(m["id"])
            cols.append(f"sa.Column('{m_name}', {sa_type})")

        # CHECK 约束
        checks = []
        if k["id"] in phase_map:
            ph = phase_map[k["id"]]
            states_str = ", ".join(f"'{s}'" for s in ph["states"])
            check_name = f"ck_{table}_phase"
            checks.append(f'sa.CheckConstraint("phase IN ({states_str})", name="{check_name}")')

        # Mode enum CHECK
        for m in mode_map.get(k["id"], []):
            if "enum" in m:
                m_name = snake(m["id"])
                vals_str = ", ".join(f"'{v}'" for v in m["enum"])
                check_name = f"ck_{table}_{m_name}"
                checks.append(f'sa.CheckConstraint("{m_name} IN ({vals_str})", name="{check_name}")')

        # PI 唯一索引
        indexes = []
        if pi:
            for pi_field in pi.split("+"):
                pi_field = pi_field.strip()
                idx_name = f"ix_{table}_{pi_field}"
                indexes.append(f"sa.Index('{idx_name}', '{pi_field}', unique=True)")

        # 组合 table_args
        table_args_items = checks + indexes
        if table_args_items:
            args_str = ", ".join(table_args_items)
            cols.append(f"__table_args__ = ({args_str},)")

        cols_str = ",\n        ".join(cols)
        upgrade_lines.append(f"    op.create_table(")
        upgrade_lines.append(f"        '{table}',")
        upgrade_lines.append(f"        {cols_str},")
        upgrade_lines.append(f"    )")
        upgrade_lines.append("")

    # --- Relator 表 ---
    upgrade_lines.append("    # ── Relator 表 ──")
    for r in all_relators:
        table = to_table(r["id"])
        created_tables.append(table)
        cols = [pk_col]
        cols.append("sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())")

        # FK 字段（Kind 绑定加 FK，Role 绑定用普通列）
        for b in r.get("binds", []):
            fk_col_name = f"{snake(b)}_id"
            if b in kind_ids:
                target_table = to_table(b)
                cols.append(f"sa.Column('{fk_col_name}', {fk_type}, sa.ForeignKey('{target_table}.id'), nullable=False)")
            else:
                # Role 绑定：无独立表，存 ID 由应用层解析
                cols.append(f"sa.Column('{fk_col_name}', {fk_type}, nullable=False)")

        # Quality 字段（如果 Relator 有 quality）
        for q in quality_map.get(r["id"], []):
            sa_type = XSD_TO_SA.get(q["xsd"], "sa.String(256)")
            q_name = snake(q["id"])
            cols.append(f"sa.Column('{q_name}', {sa_type})")

        cols_str = ",\n        ".join(cols)
        upgrade_lines.append(f"    op.create_table(")
        upgrade_lines.append(f"        '{table}',")
        upgrade_lines.append(f"        {cols_str},")
        upgrade_lines.append(f"    )")

        # FK 索引（Relator 表的 JOIN 性能保障）
        for b in r.get("binds", []):
            fk_col_name = f"{snake(b)}_id"
            idx_name = f"ix_{table}_{fk_col_name}"
            upgrade_lines.append(f"    op.create_index('{idx_name}', '{table}', ['{fk_col_name}'])")
        upgrade_lines.append("")

    # --- Event 日志表 ---
    event_table = "ontology_events"
    created_tables.append(event_table)
    upgrade_lines.append("    # ── Event 日志表（所有状态转移的审计记录） ──")
    upgrade_lines.append(f"    op.create_table(")
    upgrade_lines.append(f"        '{event_table}',")
    upgrade_lines.append(f"        {pk_col},")
    upgrade_lines.append(f"        sa.Column('event_type', sa.String(64), nullable=False),")
    upgrade_lines.append(f"        sa.Column('target_table', sa.String(64), nullable=False),")
    upgrade_lines.append(f"        sa.Column('target_id', {fk_type}, nullable=False),")
    upgrade_lines.append(f"        sa.Column('old_phase', sa.String(32)),")
    upgrade_lines.append(f"        sa.Column('new_phase', sa.String(32)),")
    upgrade_lines.append(f"        sa.Column('actor_id', {fk_type}),")
    upgrade_lines.append(f"        sa.Column('payload', sa.JSON),")
    upgrade_lines.append(f"        sa.Column('occurred_at', sa.DateTime(timezone=True), server_default=sa.func.now()),")
    upgrade_lines.append(f"    )")
    upgrade_lines.append(f"    op.create_index('ix_{event_table}_target', '{event_table}', ['target_table', 'target_id'])")
    upgrade_lines.append(f"    op.create_index('ix_{event_table}_occurred_at', '{event_table}', ['occurred_at'])")
    upgrade_lines.append("")

    trigger_drops: list[str] = []  # 收集触发器 drop，最后逆序追加到 downgrade

    # --- Phase 转移触发器函数 ---
    if phases:
        upgrade_lines.append("    # ── Phase 表追加 actor_id 列（追踪状态变更者） ──")
        for ph in phases:
            table = to_table(ph["of"])
            upgrade_lines.append(f"    op.add_column('{table}', sa.Column('phase_actor_id', {fk_type}))")
        upgrade_lines.append("")

        upgrade_lines.append("    # ── Phase 转移触发器（非法转移自动拒绝 + 记录 actor） ──")
        for ph in phases:
            kind_id = ph["of"]
            table = to_table(kind_id)
            func_name = f"fn_{table}_phase_guard"
            event_table_ref = event_table

            # 构建合法转移映射
            transitions = ph.get("transitions", [])
            case_lines = []
            for t in transitions:
                case_lines.append(f"        WHEN OLD.phase = '{t['from']}' AND NEW.phase = '{t['to']}' THEN TRUE")

            case_str = "\n".join(case_lines)
            states_str = ", ".join(f"'{s}'" for s in ph["states"])

            trigger_sql = f"""\
CREATE OR REPLACE FUNCTION {func_name}()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.phase IS NOT DISTINCT FROM NEW.phase THEN
        RETURN NEW;
    END IF;
    IF NEW.phase NOT IN ({states_str}) THEN
        RAISE EXCEPTION 'Invalid phase: % for {table}', NEW.phase;
    END IF;
    CASE
{case_str}
        ELSE
            RAISE EXCEPTION 'Illegal phase transition on {table}: % -> %', OLD.phase, NEW.phase;
    END CASE;
    INSERT INTO {event_table_ref} (event_type, target_table, target_id, old_phase, new_phase, actor_id, occurred_at)
    VALUES (NEW.phase, '{table}', NEW.id, OLD.phase, NEW.phase, NEW.phase_actor_id, NOW());
    -- 更新 actor 追踪列
    NEW.phase_actor_id := NULL;  -- 重置，下次变更需重新设置
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;"""
            upgrade_lines.append(f"    op.execute(\"\"\"{trigger_sql}\"\"\")")
            upgrade_lines.append("")

            # 创建触发器
            trigger_name = f"trg_{table}_phase"
            trigger_sql = f"""\
CREATE TRIGGER {trigger_name}
    BEFORE UPDATE OF phase ON {table}
    FOR EACH ROW EXECUTE FUNCTION {func_name}();"""
            upgrade_lines.append(f"    op.execute(\"\"\"{trigger_sql}\"\"\")")
            upgrade_lines.append("")

            # downgrade 用（收集到 trigger_drops，最后逆序追加）
            # 注意：append 顺序是 FUNCTION 先、TRIGGER 后；
            # 经 reversed() 后输出顺序变为 TRIGGER 先、FUNCTION 后（正确依赖顺序）
            trigger_drops.append(f"    op.execute('DROP FUNCTION IF EXISTS {func_name}')")
            trigger_drops.append(f"    op.execute('DROP TRIGGER IF EXISTS {trigger_name} ON {table}')")

        # 乐观锁应用层模板（以注释形式写入 migration 文件）
        upgrade_lines.append("")
        upgrade_lines.append("    # ── 乐观锁模板（应用层必须遵循） ──")
        upgrade_lines.append("    # 任何 Phase 更新必须用 WHERE phase = :old_phase 防止并发篡改：")
        upgrade_lines.append("    #")
        upgrade_lines.append("    #   UPDATE quotations")
        upgrade_lines.append("    #      SET phase = :new_phase, phase_actor_id = :actor_id")
        upgrade_lines.append("    #    WHERE id = :id AND phase = :old_phase;")
        upgrade_lines.append("    #")
        upgrade_lines.append("    #   if result.rowcount != 1:")
        upgrade_lines.append("    #       raise ConflictError('状态已变更，请刷新后重试')")

    # --- downgrade() ---
    # 先 drop 触发器/函数（逆序），再 drop 索引，最后逆序 drop 表
    downgrade_lines.extend(reversed(trigger_drops))
    # Relator FK 索引 drop（表 drop 前执行，显式保障）
    for r in reversed(all_relators):
        table = to_table(r["id"])
        for b in reversed(r.get("binds", [])):
            fk_col_name = f"{snake(b)}_id"
            idx_name = f"ix_{table}_{fk_col_name}"
            downgrade_lines.append(f"    op.drop_index('{idx_name}', table_name='{table}')")
    for table in reversed(created_tables):
        downgrade_lines.append(f"    op.drop_table('{table}')")

    # ── 组装文件 ──
    lines = [
        f'"""ontology scenario: {meta["name_cn"]}',
        "",
        f"Revision ID: {revision}",
        f"Revises: {down_revision or ''}",
        f"Create Date: {now}",
        "",
        '"""',
        "from typing import Sequence, Union",
        "",
        "from alembic import op",
        "import sqlalchemy as sa",
        pk_import,
        "",
        "# revision identifiers, used by Alembic.",
        f"revision: str = '{revision}'",
        f"down_revision: Union[str, Sequence[str], None] = {down_rev}",
        "branch_labels: Union[str, Sequence[str], None] = None",
        "depends_on: Union[str, Sequence[str], None] = None",
        "",
        "",
        "def upgrade() -> None:",
        f'    """创建本体场景表: {meta["name_cn"]}"""',
        *upgrade_lines,
        "",
        "",
        "def downgrade() -> None:",
        f'    """回滚本体场景表: {meta["name_cn"]}"""',
        *downgrade_lines,
        "",
    ]

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(
        description="树懒 · 本体锻炉 — YAML → Alembic Migration 生成器"
    )
    p.add_argument("scenario", type=Path, help="scenario YAML 路径")
    p.add_argument("--out", type=Path, default=None,
                   help="输出文件路径 (默认 = scenario 同目录)")
    p.add_argument("--pk-type", choices=["bigint", "uuid"], default="bigint",
                   help="主键类型: bigint (默认, 匹配 Sloth-HR) 或 uuid")
    p.add_argument("--down-revision", type=str, default=None,
                   help="前置 migration revision ID")
    args = p.parse_args()

    scenario = yaml.safe_load(args.scenario.read_text())
    content = generate_migration(scenario, args.pk_type, args.down_revision)

    out_dir = args.out or args.scenario.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # 从 revision 生成文件名
    rev = content.split("Revision ID: ")[1].split("\n")[0]
    out_path = out_dir / f"{rev}_ontology_{scenario['meta']['id']}.py"
    out_path.write_text(content)

    print(f"✅ Alembic migration 已生成: {out_path}")
    print(f"   PK 类型: {args.pk_type}")
    print(f"   Revision: {rev}")
    if args.down_revision:
        print(f"   Down revision: {args.down_revision}")
    print()
    print("   使用方式:")
    print(f"   1. 复制到项目的 alembic/versions/ 目录")
    print(f"   2. alembic upgrade head")


if __name__ == "__main__":
    main()
