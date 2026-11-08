# Implementation Plan Summary — PyIDM (Stage 1 Master Plan)

**Document version:** 2.0  
**Status:** Complete & Awaiting User Approval — Stage 1 Discovery Gate  
**Date:** 2026-11-08  
**Author:** Software Architecture Team  
**Audit Baseline:** 72 source files, 1,833 statements, 24 passing tests, 79% test coverage.

---

## 1. Executive Summary

This document presents the finalized implementation plan for **PyIDM**, an enterprise-grade, fully featured, multi-connection Internet Download Manager written in Python.

PyIDM is architected to rival established tools like Internet Download Manager (IDM), Motrix, and Free Download Manager. Following a comprehensive audit of the existing repository, the software strictly adheres to:
- **Object-Oriented Design**: Full application of SOLID principles, explicit domain boundaries, and constructor dependency injection.
- **Strict Static Typing**: Zero use of `Any`, fully generic annotations, and 100% compliance with `mypy --strict`.
- **Decoupled Architecture**: Complete separation of PySide6 GUI, domain business models, SQLite persistence, and multi-threaded HTTPX network streaming.
- **Dual-Mode Desktop Interface**: Native PySide6 interface supporting instant toggling between **Expanded Mode** (`pics/page.jfif` & `pics/page-1.jfif`) and **Compact Mode** (`pics/compact.jfif`), sharing the identical state and table model.
- **Reliability & Resilience**: Automatic HTTP range detection, single-stream fallback, cooperative pause/resume, startup crash recovery, exponential backoff, and bandwidth limiting.

---

## 2. Planning Deliverables Index

All Stage 1 architectural, audit, and planning deliverables have been authored and placed under `docs/planning/`:

0. [`00-existing-codebase-audit.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/00-existing-codebase-audit.md): Comprehensive 16-section audit of existing code, test results, code quality, and gap analysis against UI references.
1. [`01-project-research.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/01-project-research.md): Technical evaluation of HTTPX, RFC 9110 range semantics, PySide6 threading, SQLAlchemy 2.0 WAL mode, and packaging.
2. [`02-system-requirements.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/02-system-requirements.md): 40+ functional and non-functional requirements with testable acceptance criteria.
3. [`03-architecture-design.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/03-architecture-design.md): Layered architecture, system startup sequence, download execution sequence, and dependency injection container design.
4. [`04-project-structure.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/04-project-structure.md): Complete directory layout, module definitions, and package import discipline rules.
5. [`05-domain-model.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/05-domain-model.md): Pure business entities (`Download`, `DownloadSegment`, `DownloadQueue`), value objects, domain services, and typed protocols.
6. [`06-download-engine-design.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/06-download-engine-design.md): Deep-dive into chunk streaming, byte-range partitioning, worker lifecycle, and atomic file assembly.
7. [`07-concurrency-and-state-management.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/07-concurrency-and-state-management.md): ThreadPoolExecutor budget, Qt signal cross-thread adapters, download state machine, and cancellation mechanics.
8. [`08-database-design.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/08-database-design.md): Normalized SQLite schema, SQLAlchemy 2.0 mapped models, WAL mode tuning, and Alembic migrations.
9. [`09-ui-design.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/09-ui-design.md): PySide6 Model/View specification for Dual-Mode UI (Expanded Mode `page.jfif`/`page-1.jfif` and Compact Mode `compact.jfif`), custom delegates, and theming.
10. [`10-security-design.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/10-security-design.md): Threat modeling, anti-DNS rebinding, host validation, API token authentication, and path traversal prevention.
11. [`11-testing-strategy.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/11-testing-strategy.md): Unit, integration, concurrency, and headless GUI (`pytest-qt`) test harness with custom mock HTTP test server.
12. [`12-implementation-roadmap.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/12-implementation-roadmap.md): 11-phase implementation roadmap with explicit task classifications (`[Reuse]`, `[Modify]`, `[Refactor]`, `[New]`).
13. [`13-technology-decisions.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/13-technology-decisions.md): Architecture Decision Records (ADRs) explaining technology choices and trade-offs.
14. [`14-risk-register.md`](file:///c:/Users/Windows%2010%20Pro/OneDrive/Documents/workspace/PyIDM/docs/planning/14-risk-register.md): 10 identified project risks, impact ratings, mitigations, and fallback strategies.

---

## 3. Recommended Implementation Roadmap Sequence

| Phase | Phase Name | Primary Focus | Task Nature |
|---|---|---|---|
| **Phase 0** | **Foundations & Quality Baselines** | Fix 5 Ruff lints, remove `Any` from model & server, type `qtbot` | `[Modify]`, `[Reuse]` |
| **Phase 1** | **Domain & Persistence** | Domain entities, value objects, SQLite/SQLAlchemy 2.0 models, Alembic baseline | `[Reuse]`, `[New]` |
| **Phase 2** | **Networking Foundation** | `HttpStreamClient` (HTTPX), resource inspection, single-stream download worker | `[Reuse]` |
| **Phase 3** | **Segmented Download Engine** | Byte-range calculator, multi-connection worker pool, rate limiting, file assembly | `[Reuse]`, `[Modify]` |
| **Phase 4** | **Lifecycle & Crash Recovery** | Pause, resume, retry with exponential backoff, JSON manifests, startup recovery | `[Reuse]`, `[Modify]` |
| **Phase 5** | **Queue Management & Scheduling** | Background queue scheduler timer, slot limits, priority dispatching | `[Reuse]`, `[New]` |
| **Phase 6** | **Desktop GUI Dual-Mode Shell** | Expanded Mode (`page.jfif`), Compact Mode (`compact.jfif`), Mode switcher, `SegmentedProgressBarDelegate` | `[Refactor]`, `[New]` |
| **Phase 7** | **Full GUI Integration & Dialogs** | Enhanced `AddDownloadDialog`, `DownloadDetailsDialog`, `SettingsDialog`, context menus, system tray | `[Modify]`, `[New]` |
| **Phase 8** | **Advanced Features** | Local FastAPI browser API, Chrome/Firefox extensions, clipboard watcher, categories | `[Reuse]`, `[Modify]` |
| **Phase 9** | **Quality Assurance & Hardening** | Concurrency stress testing, memory profiling, mock server integration tests, 85%+ coverage | `[New]`, `[Modify]` |
| **Phase 10** | **Packaging & Distribution** | PyInstaller standalone packaging (`onedir`), Inno Setup Windows installer, documentation | `[Reuse]`, `[New]` |

---

## 4. Key Assumptions & Decision Confirmation Points

Before Stage 2 implementation begins, the following assumptions are flagged for explicit confirmation:
1. **Python Target Version**: Python 3.11 is installed on the host system. The project targets Python 3.11+ compatibility, while keeping all syntax forward-compatible with Python 3.12+.
2. **Dual-Mode Desktop Interface**: PyIDM will feature both the Expanded Mode (matching `page.jfif` and `page-1.jfif`) and the Compact Mode (matching `compact.jfif`), seamlessly switchable via a header toggle switch and persisting in settings.
3. **Browser Extension Architecture**: The embedded FastAPI loopback server on `127.0.0.1:8743` guarded by token authentication and host-header verification will serve both Chrome MV3 and Firefox extensions.
4. **Bandwidth Throttling**: The token bucket algorithm will operate per download and globally across all active connections.

---

## 5. Absolute Stop Condition

**STAGE 1 DISCOVERY AND PLANNING IS COMPLETE.**

In strict adherence to the project instructions:
- No application source code has been altered or created during this discovery phase.
- No project dependencies have been installed or modified.
- No placeholder code has been written.
- All research, codebase audit, and planning deliverables are finalized under `docs/planning/`.

**Implementation (Stage 2) will ONLY begin after you have reviewed this audit and plan and provided your explicit approval.**
