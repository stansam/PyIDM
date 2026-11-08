# Project Structure Specification — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## 1. Directory Tree & Module Boundaries

The project structure enforces strict domain boundaries, explicit typing, and complete separation between GUI, engine, persistence, and external networking.

```text
PyIDM/
│
├── .gitignore
├── .python-version               # Fixed to 3.11 for immediate compatibility, targets 3.12+
├── pyproject.toml                # Managed via uv (PEP 517/518 + [tool.uv])
├── uv.lock                       # Deterministic dependency lock file
├── README.md
├── CONTRIBUTING.md
├── LICENSE
│
├── app/                          # Core Application Source Root
│   ├── __init__.py
│   ├── main.py                   # Application Entry Point & PySide6 exec loop
│   ├── bootstrap.py              # Environment initialization, migrations, container setup
│   │
│   ├── shared/                   # Cross-cutting primitives & strict contracts
│   │   ├── __init__.py
│   │   ├── constants.py          # Application-wide defaults & configuration keys
│   │   ├── types.py              # Generic type aliases & Result[T, E] containers
│   │   └── protocols.py          # Core lifecycle protocols (Startable, Stoppable)
│   │
│   ├── domain/                   # Pure Business Logic (No external framework imports)
│   │   ├── __init__.py
│   │   ├── exceptions/           # Domain error hierarchy (PyIDMDomainError)
│   │   │   ├── __init__.py
│   │   │   └── domain_errors.py
│   │   ├── downloads/            # Downloads bounded context
│   │   │   ├── __init__.py
│   │   │   ├── entities/         # Download, DownloadSegment, DownloadCategory
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download.py
│   │   │   │   ├── segment.py
│   │   │   │   └── category.py
│   │   │   ├── value_objects/    # Immutable typed objects
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ids.py        # DownloadId, SegmentId, QueueId
│   │   │   │   ├── byte_range.py
│   │   │   │   ├── url.py
│   │   │   │   ├── speed.py
│   │   │   │   ├── file_size.py
│   │   │   │   ├── headers.py
│   │   │   │   ├── retry_policy.py
│   │   │   │   └── progress.py
│   │   │   ├── enums/            # Typed enumerations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download_status.py
│   │   │   │   ├── segment_status.py
│   │   │   │   ├── strategy.py
│   │   │   │   ├── failure_category.py
│   │   │   │   └── priority.py
│   │   │   ├── interfaces/       # Abstract Protocols
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download_repository.py
│   │   │   │   ├── segment_repository.py
│   │   │   │   ├── manifest_storage.py
│   │   │   │   ├── resource_inspector.py
│   │   │   │   └── progress_reporter.py
│   │   │   └── services/         # Domain calculations & validation rules
│   │   │       ├── __init__.py
│   │   │       ├── segment_calculator.py
│   │   │       ├── state_validator.py
│   │   │       ├── filename_resolver.py
│   │   │       ├── category_classifier.py
│   │   │       └── speed_calculator.py
│   │   ├── queues/               # Queues bounded context
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── download_queue.py
│   │   │   │   └── queue_schedule.py
│   │   │   ├── interfaces/
│   │   │   │   ├── __init__.py
│   │   │   │   └── queue_repository.py
│   │   │   └── enums/
│   │   │       └── queue_status.py
│   │   └── scheduling/           # Time calculation models
│   │       ├── __init__.py
│   │       └── schedule_evaluator.py
│   │
│   ├── engine/                   # Specialized Download Engine (Zero GUI code)
│   │   ├── __init__.py
│   │   ├── manager/              # High-level download coordination
│   │   │   ├── __init__.py
│   │   │   ├── download_manager.py
│   │   │   └── queue_manager.py
│   │   ├── downloader/           # Per-download lifecycle execution
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py
│   │   │   └── resource_inspector_impl.py
│   │   ├── segmentation/         # Byte-range chunking & pre-allocation
│   │   │   ├── __init__.py
│   │   │   └── segment_allocator.py
│   │   ├── workers/              # Thread-pool execution units
│   │   │   ├── __init__.py
│   │   │   ├── segment_worker.py
│   │   │   └── worker_pool.py
│   │   ├── retry/                # Network backoff & resilience
│   │   │   ├── __init__.py
│   │   │   ├── retry_coordinator.py
│   │   │   └── error_classifier.py
│   │   ├── recovery/             # Crash detection & manifest reconciliation
│   │   │   ├── __init__.py
│   │   │   └── recovery_manager.py
│   │   ├── assembly/             # Atomic file stitching
│   │   │   ├── __init__.py
│   │   │   └── file_assembler.py
│   │   └── monitoring/           # Speed & bandwidth limiters
│   │       ├── __init__.py
│   │       ├── progress_aggregator.py
│   │       ├── rolling_speed_meter.py
│   │       └── token_bucket.py
│   │
│   ├── application/              # Use Cases & Cross-Layer Coordination
│   │   ├── __init__.py
│   │   ├── container.py          # Dependency injection container
│   │   ├── application_service.py# Primary facade for UI & Browser API
│   │   ├── commands/             # Action request DTOs
│   │   │   ├── __init__.py
│   │   │   ├── add_download_command.py
│   │   │   ├── control_commands.py  # Pause, Resume, Cancel, Retry
│   │   │   └── queue_commands.py
│   │   ├── queries/              # Data retrieval DTOs
│   │   │   ├── __init__.py
│   │   │   └── download_queries.py
│   │   ├── handlers/             # Command execution logic
│   │   │   ├── __init__.py
│   │   │   ├── command_handler.py
│   │   │   └── query_handler.py
│   │   └── signals/              # Qt Signal Emitter Adapter
│   │       ├── __init__.py
│   │       └── download_signals.py
│   │
│   ├── infrastructure/           # Technical Implementations & Third-party integrations
│   │   ├── __init__.py
│   │   ├── networking/           # HTTPX implementation
│   │   │   ├── __init__.py
│   │   │   ├── http_stream_client.py
│   │   │   └── response_adapter.py
│   │   ├── persistence/          # SQLAlchemy 2.0 & SQLite
│   │   │   ├── __init__.py
│   │   │   ├── database.py       # Engine, scoped_session, WAL pragma setup
│   │   │   ├── models/           # Declarative mapped tables
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── download_model.py
│   │   │   │   ├── segment_model.py
│   │   │   │   └── queue_model.py
│   │   │   ├── repositories/     # Concrete repository classes
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sql_download_repository.py
│   │   │   │   ├── sql_segment_repository.py
│   │   │   │   └── sql_queue_repository.py
│   │   │   └── migrations/       # Alembic migration environment
│   │   │       ├── env.py
│   │   │       ├── script.py.mako
│   │   │       └── versions/
│   │   ├── filesystem/           # Safe OS filesystem operations
│   │   │   ├── __init__.py
│   │   │   ├── file_manager.py
│   │   │   └── temp_storage.py
│   │   ├── configuration/        # Pydantic Settings
│   │   │   ├── __init__.py
│   │   │   └── app_settings.py
│   │   ├── logging/              # Structured logging & redaction
│   │   │   ├── __init__.py
│   │   │   └── logging_config.py
│   │   ├── browser/              # Local Loopback FastAPI API
│   │   │   ├── __init__.py
│   │   │   ├── server.py
│   │   │   ├── routes.py
│   │   │   └── security.py
│   │   └── system/               # Desktop OS integration
│   │       ├── __init__.py
│   │       ├── tray_icon.py
│   │       ├── clipboard_monitor.py
│   │       └── notifications.py
│   │
│   └── presentation/             # PySide6 GUI (Model/View & Widgets)
│       ├── __init__.py
│       ├── app.py                # QApplication lifecycle
│       ├── windows/              # Top-level windows
│       │   ├── __init__.py
│       │   └── main_window.py
│       ├── pages/                # Content views
│       │   ├── __init__.py
│       │   ├── dashboard_page.py
│       │   ├── queue_page.py
│       │   └── settings_page.py
│       ├── dialogs/              # User input modals
│       │   ├── __init__.py
│       │   ├── add_download_dialog.py
│       │   ├── download_details_dialog.py
│       │   └── confirm_dialog.py
│       ├── widgets/              # Reusable custom UI components
│       │   ├── __init__.py
│       │   ├── speed_graph.py
│       │   ├── status_badge.py
│       │   └── segmented_progress_bar.py
│       ├── models/               # Qt View Models
│       │   ├── __init__.py
│       │   └── download_table_model.py
│       ├── delegates/            # Table View Custom Renderers
│       │   ├── __init__.py
│       │   ├── progress_delegate.py
│       │   └── actions_delegate.py
│       ├── controllers/          # UI-to-Application action routers
│       │   ├── __init__.py
│       │   └── main_controller.py
│       ├── themes/               # QSS Stylings
│       │   ├── __init__.py
│       │   ├── theme_manager.py
│       │   ├── light.qss
│       │   └── dark.qss
│       └── resources/            # Icons, svgs, fonts
│           ├── icons/
│           └── resources.qrc
│
├── browser_extensions/           # Standalone Extension Packages
│   ├── shared/
│   │   ├── background.js
│   │   ├── content.js
│   │   └── popup/
│   ├── chrome/                   # Manifest V3
│   │   └── manifest.json
│   └── firefox/                  # Firefox WebExtension
│       └── manifest.json
│
├── tests/                        # Comprehensive Test Suites
│   ├── conftest.py               # Root fixtures (mock servers, tmp paths)
│   ├── unit/                     # Domain & unit testing
│   │   ├── domain/
│   │   ├── engine/
│   │   └── application/
│   ├── integration/              # DB, HTTP client, Assembly
│   │   ├── persistence/
│   │   ├── networking/
│   │   └── engine/
│   ├── gui/                      # pytest-qt headless UI tests
│   │   ├── test_main_window.py
│   │   └── test_download_table.py
│   ├── fixtures/                 # Test files, mock HTTP responses
│   │   └── http_server.py
│   └── mocks/
│
├── docs/                         # Architecture, Specs, User Documentation
│   ├── planning/                 # Stage 1 Planning Artifacts
│   ├── architecture/
│   └── development/
│
├── packaging/                    # Distribution & Build Scripts
│   ├── pyinstaller/
│   │   ├── pyidm.spec
│   │   └── hooks/
│   └── windows/
│       └── installer.iss         # Inno Setup script
│
├── data/                         # Local database & logs directory
└── downloads/                    # Default target destination
    └── .pyidm_temp/              # Hidden segment staging area
```

---

## 2. Package Boundaries and Import Discipline

To enforce the layered architecture and prevent spaghetti code or circular dependencies, the following linting and structural boundaries are guaranteed:

| Package | May Import From | Must NEVER Import From |
|---|---|---|
| `app.domain` | `app.shared` | `app.presentation`, `app.engine`, `app.infrastructure`, `PySide6`, `sqlalchemy`, `httpx`, `fastapi` |
| `app.engine` | `app.domain`, `app.shared`, `app.infrastructure.networking`, `app.infrastructure.filesystem` | `app.presentation`, `app.application`, `PySide6`, `fastapi` |
| `app.infrastructure` | `app.domain`, `app.shared` | `app.presentation`, `app.application` |
| `app.application` | `app.domain`, `app.engine`, `app.infrastructure`, `app.shared` | `app.presentation` |
| `app.presentation` | `app.application`, `app.domain.enums`, `app.shared` | `app.engine`, `app.infrastructure.persistence`, `app.infrastructure.networking` |

Enforcement will be configured via custom Ruff import boundary rules (`flake8-tidy-imports` / `banned-api`).

