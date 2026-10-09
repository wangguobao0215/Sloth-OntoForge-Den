<p align="center">
  <img src="assets/sloth-avatar-round.png" width="120" />
</p>

<h1 align="center">Sloth-OntoForge-Den</h1>

<p align="center">
  <strong>树懒 · 本体锻炉</strong><br/>
  Compile business scenarios into AI-native product skeletons — ontology, data models, command routing, and LLM prompts
</p>

<p align="center">
  <img src="assets/qrcode.jpg" width="140" /><br/>
  <sub>Follow <strong>Sloth Old K</strong> · More AI Skills</sub><br/>
  <em>Slow down, go deeper</em>
</p>

---

## Overview

Sloth-OntoForge-Den is a seven-stage ontology compilation pipeline grounded in the Arp/Smith/Spear BFO methodology (*Building Ontologies with BFO*, MIT Press 2015). It takes a YAML scenario definition as input and produces six engineering artifacts ready for AI-native product development.

## Features

- **Seven-stage pipeline**: From scenario contract to executable artifacts, covering the full Arp/Smith/Spear BFO methodology
- **6 engineering artifacts**: OWL/TTL ontology, PostgreSQL DDL (with state machine triggers), OpenAPI schema, command routing JSON, LLM system prompt, FastAPI RBAC module
- **BFO + UFO combined**: BFO provides the relational backbone, UFO supplies stereotype labels (kind/role/relator/phase/mode)
- **Alembic migration generation**: upgrade/downgrade + optimistic locking + actor audit trail
- **TypeScript type generation**: interfaces + discriminated unions + API client stubs
- **Neo4j Cypher generation**: schema constraints + graph relationships + seed data
- **3-layer validation**: L1 OWL syntax, L2 structural baselines (11 test categories), L3 smoke test scaffold
- **Business-readable verbalization**: Auto-removes ontological jargon, generates business rules + few-shot routing examples

## Quick Start

```bash
# Clone the repository
git clone https://github.com/wangguobao0215/Sloth-OntoForge-Den.git
cd Sloth-OntoForge-Den/scripts

# Install dependencies
pip install -r requirements.txt

# Run the demo fixture (quote → order → scheduling)
make demo

# Full pipeline (including Neo4j + Alembic)
make demo && make neo4j && make migrate
```

Output artifacts are generated in `scripts/out/quote-order-schedule/`.

## Project Structure

```
Sloth-OntoForge-Den/
├── SKILL.md              # Skill definition (seven-stage pipeline)
├── scripts/              # Automation scripts
│   ├── compile.py        # YAML → 6 artifacts
│   ├── validate.py       # 3-layer validation
│   ├── gen_alembic_migration.py  # Alembic migration generator
│   ├── gen_react_types.py       # TypeScript type generator
│   ├── sync_to_neo4j.py         # Neo4j Cypher generator
│   ├── common.py                # Shared utility module
│   └── fixtures/                # Scenario YAML files
├── references/           # Reference papers and documents
├── assets/               # Brand assets
└── CHANGELOG.md          # Version history
```

## Version

Current: 2.0.0

## License

MIT License
