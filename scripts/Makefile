.PHONY: help install run compile validate types neo4j migrate clean demo

FIXTURE ?= fixtures/quote-order-schedule.yaml
OUT_DIR ?= out/$(shell basename $(FIXTURE) .yaml)

help:
	@echo "╔════════════════════════════════════════════════╗"
	@echo "║ 🔨 树懒 · 本体锻炉 · Sloth-OntoForge-Den v2   ║"
	@echo "╚════════════════════════════════════════════════╝"
	@echo ""
	@echo "  make install       安装依赖 (pyyaml, rdflib, owlready2)"
	@echo "  make demo          跑通 fixture (quote-order-schedule)"
	@echo "  make wizard        交互式 7 阶段向导 (生成新 scenario)"
	@echo "  make run           编译 + 验证当前 FIXTURE"
	@echo "  make compile       仅编译 (YAML → 5 制品)"
	@echo "  make validate      仅验证 (L1 OWL + L2 结构 + L3 冒烟骨架)"
	@echo "  make types         生成 TypeScript 类型定义 (YAML → types.ts)"
	@echo "  make neo4j         生成 Neo4j Cypher 注入文件 (schema/graph/seed)"
	@echo "  make migrate       生成 Alembic migration 脚本 (YAML → DDL + 触发器)"
	@echo "  make clean         清理 out/"
	@echo ""
	@echo "  FIXTURE=<path>     指定 scenario YAML (默认 fixtures/quote-order-schedule.yaml)"
	@echo "  OUT_DIR=<path>     指定输出目录"

install:
	@echo "🔧 安装依赖..."
	python3 -m pip install --quiet -r requirements.txt

demo: FIXTURE=fixtures/quote-order-schedule.yaml
demo: run

run: compile validate types

compile:
	@echo "🔨 编译 $(FIXTURE) → $(OUT_DIR)/ ..."
	python3 compile.py $(FIXTURE) --out-dir $(OUT_DIR)

validate:
	@echo "✅ 验证 $(FIXTURE) ..."
	python3 validate.py $(FIXTURE) --out-dir $(OUT_DIR) || true

types:
	@echo "📘 生成 TypeScript 类型定义..."
	python3 gen_react_types.py $(FIXTURE) --out $(OUT_DIR)/types.ts

neo4j:
	@echo "🔗 生成 Neo4j Cypher 注入文件..."
	python3 sync_to_neo4j.py $(FIXTURE) --out $(OUT_DIR)

migrate:
	@echo "📦 生成 Alembic migration 脚本..."
	python3 gen_alembic_migration.py $(FIXTURE) --out $(OUT_DIR)

wizard:
	python3 wizard.py --out $(FIXTURE)

clean:
	rm -rf out/
	@echo "🧹 已清理 out/"
