# Implementation Roadmap and Phase Specifications — PyIDM

**Document version:** 2.0  
**Status:** Complete — Stage 1 Discovery & Audit Aligned  
**Date:** 2026-11-08  
**Author:** Software Architecture Team  
**Audit Baseline:** 72 source files, 1,833 statements, 24 passing tests, 79% coverage.

---

## 1. Roadmap Overview and Phase Dependencies

The implementation plan is structured into 11 strictly sequenced phases. Every task is explicitly classified based on the findings from the comprehensive codebase audit:
- **`[Reuse]`**: Existing implementation is verified and preserved without structural changes.
- **`[Modify]`**: Existing file requires targeted updates (e.g., removing `Any`, fixing Ruff lints).
- **`[Refactor]`**: Existing component requires structural improvement or event wiring.
- **`[Replace]`**: Existing component is superseded by an improved architectural design.
- **`[New]`**: Entirely new functionality to be constructed.

```mermaid
graph TD
    P0[Phase 0: Foundations & Quality Baselines] --> P1[Phase 1: Domain & Persistence]
    P1 --> P2[Phase 2: Networking Foundation]
    P2 --> P3[Phase 3: Segmented Download Engine]
    P3 --> P4[Phase 4: Lifecycle, Pause/Resume & Recovery]
    P4 --> P5[Phase 5: Queue Management & Scheduling]
    P1 --> P6[Phase 6: Desktop GUI Foundation]
    P5 --> P7[Phase 7: Full GUI Functional Integration]
    P6 --> P7
    P7 --> P8[Phase 8: Advanced Features & Browser Extension]
    P8 --> P9[Phase 9: Quality Assurance & Hardening]
    P9 --> P10[Phase 10: Packaging & Distribution]
```

---

## 2. Detailed Phase Specifications

### Phase 0: Architecture and Foundations Baseline
- **Prerequisites**: Approved Stage 1 audit and implementation plan.
- **Objectives**: Resolve existing linting violations, clean up type suppressions, and establish strict typing across all interfaces.
- **Tasks**:
  1. `[Modify]` Fix 5 Ruff linting violations in `app/application/signals/download_signals.py` (`I001`, `F401`) and `app/engine/downloader/orchestrator.py` (`UP017` `datetime.UTC`).
  2. `[Modify]` Replace `typing.Any` in `app/presentation/models/download_table_model.py` (`headerData` and `data` methods) with `object` / `str | None`.
  3. `[Modify]` Replace `dict[str, Any]` in `app/infrastructure/browser/server.py` (`enqueue_download` return type) with `dict[str, str]`.
  4. `[Modify]` Annotate `qtbot: QtBot` in `tests/gui/test_main_window.py` and eliminate `# type: ignore[no-untyped-def]`.
  5. `[Reuse]` Preserve existing `pyproject.toml`, `uv.lock`, and tool configurations.
- **Exit Criteria**: `uv run ruff check .` and `uv run mypy --explicit-package-bases app tests` pass with 0 errors, 0 warnings, and 0 `Any` usage.

---

### Phase 1: Domain Models and Persistence Layer
- **Prerequisites**: Phase 0.
- **Objectives**: Validate and maintain pure domain business logic and SQLite/SQLAlchemy 2.0 repository persistence.
- **Tasks**:
  1. `[Reuse]` Preserve domain entities `Download` (`app/domain/downloads/entities/download.py`) and `DownloadSegment`.
  2. `[Reuse]` Preserve all domain value objects (`ByteRange`, `DownloadUrl`, `DownloadSpeed`, `FileSize`, `HttpHeaders`, `RetryPolicy`).
  3. `[Reuse]` Preserve domain services (`SegmentCalculator`, `DownloadStateValidator`, `FilenameResolver`, `CategoryClassifier`).
  4. `[Reuse]` Preserve SQLAlchemy 2.0 declarative models (`DownloadModel`, `SegmentModel`) and bidirectional mappers in `app/infrastructure/persistence/`.
  5. `[Reuse]` Preserve `SqlDownloadRepository` and `SqlSegmentRepository` with WAL mode SQLite engine.
  6. `[New]` Introduce formal Alembic migration script baseline (`render_as_batch=True`).
  7. `[Reuse]` Execute and preserve existing unit and integration tests (`test_domain_models.py`, `test_persistence.py`).
- **Exit Criteria**: 100% test pass rate on all domain state transitions and persistence CRUD operations.

---

### Phase 2: Networking Foundation
- **Prerequisites**: Phase 1.
- **Objectives**: Maintain HTTP client abstractions, resource inspection, and single-stream streaming downloader.
- **Tasks**:
  1. `[Reuse]` Preserve `HttpStreamClient` (`app/infrastructure/networking/http_stream_client.py`) wrapping `httpx.Client` with connection pooling, redirects, and 64 KB chunk streaming.
  2. `[Reuse]` Preserve `inspect()` method for HEAD requests and ranged GET fallback (`Range: bytes=0-0`).
  3. `[Reuse]` Preserve `FilenameResolver` for RFC 6266 `Content-Disposition` extraction and path traversal sanitization.
  4. `[Reuse]` Preserve `ResponseMetadata` dataclass and headers normalization.
  5. `[Reuse]` Preserve local controllable mock HTTP server fixture (`tests/fixtures/mock_http_server.py`).
  6. `[Reuse]` Execute existing networking integration tests (`test_networking.py`).
- **Exit Criteria**: Single-stream downloads execute successfully; byte-range support detection works reliably across standard and non-standard servers.

---

### Phase 3: Segmented Download Engine
- **Prerequisites**: Phase 2.
- **Objectives**: Maintain multi-connection segmented engine, worker pool concurrency, and atomic file assembly.
- **Tasks**:
  1. `[Reuse]` Preserve `SegmentCalculator` contiguous byte-range partitioning logic.
  2. `[Reuse]` Preserve `SegmentWorker` (`app/engine/workers/segment_worker.py`) streaming byte ranges into isolated `.part` files.
  3. `[Reuse]` Preserve `WorkerPool` managing bounded concurrency via `ThreadPoolExecutor`.
  4. `[Reuse]` Preserve `FileAssembler` (`app/engine/assembly/file_assembler.py`) performing sequential block copying and file size validation.
  5. `[Modify]` Wire `TokenBucket` rate limiter into `SegmentWorker` chunk read loop to ensure strict per-worker and aggregate bandwidth compliance.
  6. `[Reuse]` Execute segmented engine integration tests (`test_segmented_engine.py`).
- **Exit Criteria**: Multi-segment downloads produce bit-perfect files matching expected byte lengths and checksums.

---

### Phase 4: Download Lifecycle, Pause/Resume & Crash Recovery
- **Prerequisites**: Phase 3.
- **Objectives**: Validate cooperative pause, resume from partial bytes, exponential backoff retries, and disk manifest recovery.
- **Tasks**:
  1. `[Reuse]` Preserve `DownloadOrchestrator` (`app/engine/downloader/orchestrator.py`) managing inspection, planning, downloading, verification, and assembly.
  2. `[Reuse]` Preserve cooperative pause via `threading.Event` and segment state flushing.
  3. `[Reuse]` Preserve `JsonManifestStorage` creating and deleting `.pyidm_temp/<id>/manifest.json`.
  4. `[Reuse]` Preserve `RecoveryManager` (`app/engine/recovery/recovery_manager.py`) startup reconciliation of interrupted downloads.
  5. `[Modify]` Integrate `RetryCoordinator` into `SegmentWorker` to handle transient network dropped connections with exponential backoff and `Retry-After` adherence.
  6. `[Reuse]` Execute lifecycle integration tests (`test_lifecycle_and_queues.py`).
- **Exit Criteria**: Paused downloads resume from partially written byte offsets without redownloading; startup recovery restores interrupted tasks to `PAUSED`.

---

### Phase 5: Queue Management & Scheduling
- **Prerequisites**: Phase 4.
- **Objectives**: Implement automated queue progression, priority scheduling, and background timer coordination.
- **Tasks**:
  1. `[Reuse]` Preserve `DownloadManager` (`app/engine/manager/download_manager.py`) tracking active orchestrators and threads.
  2. `[Reuse]` Preserve `QueueManager` and `DownloadQueue` entity with priority sorting and slot limiting.
  3. `[New]` Implement background scheduler timer in `QueueManager` or `Container` that automatically calls `tick()` upon task completion signals.
  4. `[New]` Implement time-based scheduling (start queue at specified wall-clock time, stop queue at specified time).
  5. `[Reuse]` Execute queue integration tests in `test_lifecycle_and_queues.py`.
- **Exit Criteria**: Queued downloads automatically progress into open concurrency slots as active downloads finish.

---

### Phase 6: Desktop GUI Foundation & Dual-Mode Shell
- **Prerequisites**: Phase 1.
- **Objectives**: Construct the modern PySide6 desktop interface supporting seamless toggling between Expanded Mode (`page.jfif` / `page-1.jfif`) and Compact Mode (`compact.jfif`).
- **Tasks**:
  1. `[Refactor]` Restructure `MainWindow` (`app/presentation/windows/main_window.py`) to support a dynamic view switcher (Expanded Mode vs. Compact Mode).
  2. `[New]` Implement Left Navigation Sidebar for Expanded Mode (Downloads filters with count badges, Settings shortcuts, and Category tree).
  3. `[New]` Implement Slim Vertical Icon Sidebar for Compact Mode (Downloads, Queues, Completed, Add, Settings gear).
  4. `[New]` Implement Header Bar with Profile picker, Action buttons, Mode toggle switch, and live Search bar.
  5. `[New]` Implement `SegmentedProgressBarDelegate` (`QStyledItemDelegate`) painting multi-segment progress bars with color-coded states (Blue active, Green completed, Orange paused/error).
  6. `[Modify]` Update `app/presentation/themes/dark.qss` with styled switches, navigation trees, and status badges.
  7. `[Modify]` Expand headless GUI test suite in `tests/gui/test_main_window.py` to verify mode switching and sidebar interactions.
- **Exit Criteria**: GUI launches cleanly in both Expanded and Compact modes; toggling modes switches views without losing table selection or state.

---

### Phase 7: Full GUI Functional Integration & Dialogs
- **Prerequisites**: Phase 5, Phase 6.
- **Objectives**: Wire all toolbar actions, context menus, and interactive dialogs to application services.
- **Tasks**:
  1. `[Reuse]` Wire `DownloadSignalEmitter` to `DownloadTableModel` for real-time progress, speed, and status updates.
  2. `[Modify]` Enhance `AddDownloadDialog` (`app/presentation/dialogs/add_download_dialog.py`) with clipboard auto-paste, background inspection probe, and advanced options (headers, speed limit).
  3. `[New]` Implement `DownloadDetailsDialog` with tabs for General info, visual Segment stripes, and diagnostic logs.
  4. `[New]` Implement `SettingsDialog` managing download directories, default connections, speed limits, theme, and API keys.
  5. `[Modify]` Complete all context menu actions in `MainWindow`: Resume, Pause, Cancel, Delete, Display Order, Select Failed, Select Completed, Select All, Copy Link, Open Containing Folder, Open File.
  6. `[New]` Implement system tray icon (`QSystemTrayIcon`) with minimize-to-tray and notification bubbles.
- **Exit Criteria**: All buttons, menus, and dialogs are fully backed by real engine operations; zero nonfunctional or placeholder controls.

---

### Phase 8: Advanced Features & Browser Integration
- **Prerequisites**: Phase 7.
- **Objectives**: Finalize browser extension integration, clipboard monitoring, and automatic categorization.
- **Tasks**:
  1. `[Reuse]` Maintain `LocalApiServer` (`app/infrastructure/browser/server.py`) running FastAPI/uvicorn loopback on `127.0.0.1:8743`.
  2. `[Reuse]` Maintain token authentication (`X-PyIDM-Key`), Host header verification, and CORS regex matching.
  3. `[Modify]` Wire `ClipboardMonitor` (`app/infrastructure/system/clipboard_monitor.py`) into `MainWindow` with user prompt notification.
  4. `[Reuse]` Preserve Chrome Manifest V3 extension in `browser_extensions/chrome/`.
  5. `[New]` Create Firefox WebExtension manifest and packaging script.
  6. `[Reuse]` Preserve `CategoryClassifier` heuristics for automatic download categorization.
- **Exit Criteria**: Browser extension captures downloaded links and enqueues them into PyIDM via authenticated loopback API; clipboard watcher prompts user on copied URLs.

---

### Phase 9: Quality Assurance & Hardening
- **Prerequisites**: Phase 8.
- **Objectives**: Concurrency stress testing, memory profiling, full test suite execution, and security review.
- **Tasks**:
  1. `[New]` Write concurrency stress tests simulating 20 simultaneous downloads and rapid pause/resume cycles.
  2. `[New]` Verify bounded memory utilization during multi-gigabyte file streaming (constant chunk buffer verification).
  3. `[New]` Write comprehensive GUI interaction tests for `AddDownloadDialog`, `DownloadDetailsDialog`, and `SettingsDialog`.
  4. `[Modify]` Run static analysis: achieve 0 `mypy --strict` errors, 0 Ruff violations, and 0 `Any` occurrences.
  5. `[Modify]` Verify test coverage reaches ≥ 85% across all modules.
- **Exit Criteria**: Complete test suite passes cleanly; zero unhandled exceptions; verified memory and CPU efficiency.

---

### Phase 10: Packaging and Distribution
- **Prerequisites**: Phase 9.
- **Objectives**: Build standalone desktop executables and installers for Windows and Linux.
- **Tasks**:
  1. `[Reuse]` Preserve `packaging/pyinstaller/pyidm.spec`.
  2. `[Modify]` Update PyInstaller spec with theme resources, icon assets, and hidden imports.
  3. `[New]` Test standalone directory (`onedir`) build on Windows 10/11.
  4. `[New]` Create Inno Setup script for Windows installer generation (`PyIDM-Setup.exe`).
  5. `[New]` Provide Linux build instructions (`pyinstaller` / AppImage).
  6. `[New]` Finalize User Manual and Developer Guide in `docs/`.
- **Exit Criteria**: Standalone executable launches without Python installed; clean uninstaller provided; documentation complete.
