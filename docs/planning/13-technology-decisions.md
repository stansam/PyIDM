# Technology Decisions and Trade-off Analysis — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## 1. Summary of Architectural Decisions (ADR)

| Decision ID | Area | Selected Technology | Alternative Evaluated | Decision Driver |
|---|---|---|---|---|
| **ADR-01** | Networking Client | **HTTPX (Sync Client)** | aiohttp / requests / urllib | Modern HTTP/1.1 streaming, native connection pooling, cleaner cancellation via threads than asyncio |
| **ADR-02** | Concurrency Engine | **ThreadPoolExecutor** | asyncio / Multiprocessing | Thread per segment is ideal for I/O streaming; simpler state synchronization than cross-process IPC |
| **ADR-03** | Desktop GUI | **PySide6 (Qt 6)** | PyQt6 / Tkinter / wxPython | Official Qt binding, superior Model/View architecture, native cross-platform theming, active support |
| **ADR-04** | Database & ORM | **SQLite + SQLAlchemy 2.0** | Peewee / Raw sqlite3 / DuckDB | Strict type annotations (`Mapped[T]`), battle-tested migration ecosystem with Alembic, WAL mode performance |
| **ADR-05** | Configuration | **Pydantic Settings** | Dynaconf / JSON files / ConfigParser | Strict validation, environment variable override, automatic type casting, seamless schema generation |
| **ADR-06** | Browser API | **FastAPI (Embedded)** | Native Messaging / Flask / Tornado | Asynchronous event loop in background thread, automatic OpenAPI docs, lightweight dependencies, fast routing |
| **ADR-07** | Dependency Tooling| **uv** | Poetry / pip-tools | 10–100× faster lock and sync resolution, standard PEP 517/621 compatibility, built-in virtual environment handling |
| **ADR-08** | Packaging | **PyInstaller (onedir)** | Nuitka / cx_Freeze / Briefcase | Proven PySide6 hook ecosystem, stable Qt resource bundling, faster build times during development iterations |

---

## 2. In-Depth Trade-Off Analysis

### 2.1 Networking: HTTPX vs. Requests vs. Aiohttp

- **Requests**: Long-standing industry standard, but lacks first-class HTTP/2 support, lacks modern timeout primitives (connect vs. read timeouts are cumbersome), and is essentially in maintenance mode.
- **Aiohttp**: Excellent for high-volume asynchronous network services. However, running a download engine on an asyncio loop inside a desktop GUI creates event loop contention with Qt's event loop, requiring complex integration bridges (such as `qasync`). Furthermore, cancellation of asynchronous tasks during file stream writes frequently introduces race conditions or partial file flushes.
- **HTTPX (Selected)**: Provides clean, modern synchronous and asynchronous APIs, fine-grained `Timeout` configuration (connect, read, write, pool), robust connection pooling (`Limits`), and transparent redirect handling. Using synchronous `httpx.Client` with worker threads maps naturally to the operating system's file I/O capabilities.

### 2.2 GUI: PySide6 vs. PyQt6 vs. Web-Based (Electron / PyWebView)

- **Web-Based Frameworks (Electron/PyWebView)**: Very high RAM footprint (150MB+ idle for Chromium runtime), sluggish startup, non-native look and feel.
- **PyQt6**: Mature, but governed by GPL/commercial licensing which restricts proprietary or commercial distribution without royalties.
- **PySide6 (Selected)**: Official Qt company project under LGPLv3, modern Pythonic API, seamless type stubs, comprehensive Model/View subsystem, and official PyInstaller integration hooks.

### 2.3 Dependency Management: `uv` vs. `Poetry`

- **Poetry**: Feature-rich, but dependency resolution on complex wheels (especially Qt packages) is noticeably slow.
- **uv (Selected)**: Written in Rust, executes lock resolution and package downloads in seconds. Works with standard `pyproject.toml` tables (`[project]` and `[tool.uv]`), perfectly suited for rapid CI/CD runs and deterministic local setups.

