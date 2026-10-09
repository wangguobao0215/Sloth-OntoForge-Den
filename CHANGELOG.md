# Changelog

## [2.0.0] - 2026-10-09

### Added
- Seven-stage ontology compilation pipeline (BFO + UFO combined methodology)
- 6 engineering artifacts: OWL/TTL, PostgreSQL DDL, OpenAPI, command routing, LLM prompt, RBAC module
- Alembic migration generator with phase state machines + optimistic locking
- TypeScript type generator (interfaces + discriminated unions + API client stubs)
- Neo4j Cypher generator (schema/graph/seed)
- 3-layer validation (L1 OWL syntax, L2 structural baselines ×11 tests, L3 smoke scaffold)
- Business-readable verbalization with few-shot routing examples
- CNC machining fixture: 11 kinds, 6 roles, 7 relators, 3 phase state machines, 13 commands
- Common module (shared naming conversions + XSD type mappings)

### Changed
- Refactored all scripts to share common.py as single source of truth
- Unified DDL output between compile_ddl and gen_alembic_migration
- Phase triggers now record actor_id for audit trail
- Verbalization template rewritten from ontological jargon to business rules

### Fixed
- RO IRI mapping for continuant_part_of (was incorrectly RO:0000052)
- Relator FK NOT NULL constraint in DDL
- Mode map crash when "of" field is a list
- Revision ID collision (sha256 → secrets.token_hex)
- API client generation for commands without path params
- Table pluralization edge cases (consonant+y, f/fe endings)
