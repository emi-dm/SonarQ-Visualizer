<!--
Sync Impact Report
Version change: none → 1.0.0
Modified principles:
- Added: I. Test-First & Property-Based Testing (NON-NEGOTIABLE)
- Added: II. Documentation & Traceability (Changelog + Docs)
- Added: III. Maintainability & Code Health
- Added: IV. Reproducible Releases & Semantic Versioning
- Added: V. Observability, Simplicity & Error Signals
Added sections:
- Additional Constraints (technology-agnostic requirements)
- Development Workflow (review, CI, gating)
Removed sections: none
Templates requiring review (⚠ pending):
- .specify/templates/plan-template.md ⚠ pending (Constitution Check: ensure PBT + changelog gates reflected)
- .specify/templates/spec-template.md ⚠ pending (User Scenarios & Testing: add PBT as mandatory test type)
- .specify/templates/tasks-template.md ⚠ pending (Tasks: ensure test tasks include property-based tests and changelog tasks)
- .specify/templates/checklist-template.md ⚠ pending
Follow-up TODOs:
- RATIFICATION_DATE: TODO(RATIFICATION_DATE): original ratification date unknown; maintainers must set this value when ratifying.
-->

# SonarQ-Visualizer Constitution

## Core Principles

### I. Test-First & Property-Based Testing (NON-NEGOTIABLE)

Todas las funcionalidades y librerías deben diseñarse con pruebas primero. Las pruebas deben incluir Property-Based Tests (PBT) para las invariantes y comportamientos clave, además de tests unitarios y de integración.

- MUST: Escribir tests que fallen antes de implementar (Red-Green-Refactor).
- MUST: Incluir PBT para los invariantes del dominio y entradas/límites relevantes; PBT debe ejecutarse en CI y en la matriz de pruebas locales.
- SHOULD: Mantener suites rápidas (unit) y suites más exhaustivas (PBT, integración) separadas para tiempos de ejecución manejables.

Rationale: PBT encuentra clases de fallos que los tests unitarios basados en ejemplos no detectan; imponer PBT mejora la robustez y mantiene la calidad en cambios refactor.

### II. Documentation & Traceability (Changelog + Docs)

El proyecto debe estar completamente documentado y cada cambio debe ser trazable.

- MUST: Toda PR que cambia comportamiento público debe incluir o actualizar el changelog (CHANGELOG.md) con una entrada clara que siga el formato Keep a Changelog.
- MUST: Mantener documentación mínima: README.md (quickstart), docs/ (arquitectura, contributing, releases), y especificaciones por característica en specs/.
- MUST: Cada especificación y tarea asociada debe referenciar el issue/PR correspondiente para trazabilidad completa.

Rationale: La trazabilidad y documentación reducen la fricción para nuevos contribuyentes, facilitan auditorías y permiten releases reproducibles.

### III. Maintainability & Code Health

El código debe ser modular, legible y sujeto a gates automáticos de calidad.

- MUST: Aplicar linters, formateadores y reglas de estilo en CI; fallas en linting deben bloquear merges.
- SHOULD: Preferir diseño modular, interfaces pequeñas y documentación inline; usar tipos (annotations) cuando el lenguaje lo soporte.
- MUST: Todas las dependencias externas deben estar justificadas en la documentación y listadas en el manifiesto de dependencias.

Rationale: Mantener la deuda técnica baja y facilitar refactors seguros mejora la velocidad de entrega a largo plazo.

### IV. Reproducible Releases & Semantic Versioning

Las publicaciones deben ser reproducibles y semánticamente versionadas.

- MUST: Usar Semantic Versioning (MAJOR.MINOR.PATCH). Las reglas de bump:
  - MAJOR: Cambios incompatibles o reescrituras de gobernanza/principales principios.
  - MINOR: Nuevas secciones o principios añadidos, o extensiones materiales.
  - PATCH: Correcciones menores, clarificaciones o typo fixes.
- MUST: Cada release debe incluir una entrada en CHANGELOG.md y un conjunto de artefactos/commit tags que permitan reconstrucción reproducible.

Rationale: Versionado claro y changelog garantizan confianza para usuarios y para integraciones automatizadas.

### V. Observability, Simplicity & Error Signals

Simplicidad primero; el proyecto debe instrumentar señales básicas de salud y errores.

- MUST: Emitir logs estructurados y métricas básicas para procesos críticos; usar stderr para errores en herramientas CLI.
- SHOULD: Preferir soluciones simples y comprobadas (KISS); evitar optimizaciones prematuras.

Rationale: Observability permite depuración efectiva y operaciones seguras en producción o en ejecuciones locales complejas.

## Additional Constraints

- Technology-agnostic requirements:
  - The project MUST maintain a quickstart in README.md that reproduces a working example in ≤ 5 steps.
  - Tests MUST run on CI with an explicit matrix (unit, pbt, integration).
  - Security-sensitive changes MUST include a documented threat assessment in the related spec.

## Development Workflow

- All work MUST go through issues → branch → PR; PRs require at least one approving maintainer review and passing CI (lint, tests, PBT).
- CI MUST run: linters, unit tests, property-based tests (sample/limited seeds for PRs; full runs on main), and changelog validation.
- Complex or breaking changes MUST include a migration plan in the PR description.

## Governance

- The constitution is the top-level guidance for project practices. Amendments process:
  1.  Propose amendment as a PR against `.specify/memory/constitution.md` with rationale and migration plan.

2.  Label PR with `governance/amendment` and include maintainers as reviewers.
3.  Non-breaking clarifications (PATCH) require one approving maintainer. Material additions (MINOR) require two maintainers. Breaking governance or principle removals (MAJOR) require consensus from majority of maintainers and an explicit migration plan. 4. On merge, update `Last Amended` date and bump `CONSTITUTION_VERSION` per semantic rules.

- Compliance review expectations: Every PR that affects code quality, testing, or release process MUST reference the relevant principle and demonstrate passing CI gates. Audits may be requested quarterly.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): original ratification date unknown | **Last Amended**: 2026-02-06
