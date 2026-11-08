# Testing and Quality Assurance Strategy — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## 1. Quality Assurance Philosophy and Test Pyramid

PyIDM is a high-reliability desktop application handling critical user data and network I/O. Its test suite is organized into distinct layers to guarantee correctness, performance, and stability without relying on external internet connectivity.

```text
               / \
              /GUI\              (pytest-qt: Headless Model/View & Dialog tests)
             /-----\
            / Integ \            (Engine + DB + Local Mock HTTP Server)
           /---------\
          /   Unit    \          (Domain models, State transitions, Calculators)
         /-------------\
```

---

## 2. Test Suite Structure

```text
tests/
├── conftest.py                   # Global fixtures (temp dirs, session factories, mocks)
├── fixtures/
│   ├── mock_http_server.py       # Custom controllable HTTP server with Range/Error simulation
│   └── sample_payloads.py        # Known byte patterns and test binaries
├── unit/
│   ├── domain/
│   │   ├── test_download_entity.py
│   │   ├── test_state_machine.py # Exhaustive valid/invalid transition matrix
│   │   ├── test_segment_calc.py  # Range calculation edge cases (e.g., uneven splits)
│   │   ├── test_byte_range.py
│   │   ├── test_filename_resolver.py # Path traversal and sanitization tests
│   │   └── test_speed_meter.py   # Rolling window calculations with monotonic clocks
│   ├── engine/
│   │   ├── test_token_bucket.py  # Bandwidth throttling precision
│   │   ├── test_retry_policy.py  # Exponential backoff calculations
│   │   └── test_error_classifier.py
│   └── application/
│       └── test_command_handlers.py
├── integration/
│   ├── persistence/
│   │   ├── test_sql_repositories.py  # CRUD operations, cascading deletes, transactions
│   │   └── test_alembic_migrations.py# Upgrade/downgrade schema verification
│   ├── networking/
│   │   └── test_http_stream_client.py # HTTPX client integration with mock server
│   ├── engine/
│   │   ├── test_single_stream_download.py
│   │   ├── test_segmented_download.py # Full multi-threaded download + assembly
│   │   ├── test_pause_and_resume.py   # Interrupted downloads resuming at exact offsets
│   │   ├── test_recovery_manager.py   # Reconciling disk manifests after crash
│   │   └── test_file_assembler.py     # Large multi-segment stitching & hash verification
│   └── browser/
│       └── test_local_api.py          # FastAPI loopback endpoints, auth token validation
└── gui/
    ├── test_main_window.py       # PySide6 main window loading and menu actions
    ├── test_download_table.py    # Model updates, custom delegate painting
    └── test_add_dialog.py        # Add download dialog validation and prefill
```

---

## 3. Local Controllable HTTP Test Server

To guarantee that tests run reliably in offline CI/CD environments without external network dependencies, PyIDM provides a custom test fixture server built on Python's built-in `http.server` or `aiohttp` running in a dedicated test thread:

```python
# tests/fixtures/mock_http_server.py
class MockDownloadServer:
    """
    Controllable HTTP server simulating real-world server quirks:
    - 206 Partial Content with correct Content-Range
    - 200 OK fallback (ignoring Range header)
    - 416 Range Not Satisfiable
    - 429 Rate Limiting with Retry-After header
    - Abrupt connection resets / socket drop mid-stream
    - Artificial latency / slow chunk delivery
    - ETag mutation on resume (to test stale resource detection)
    """
    def set_content(self, data: bytes, etag: str = "initial-etag") -> None: ...
    def set_support_ranges(self, enabled: bool) -> None: ...
    def set_fail_after_bytes(self, byte_count: int) -> None: ...
    def set_rate_limit(self, retry_after_sec: int) -> None: ...
    def mutate_etag(self, new_etag: str) -> None: ...
```

---

## 4. Concurrency and Race Condition Testing

### 4.1 Multi-Threaded Stress Test Matrix
- **Rapid Pause/Resume Cycles**: A test will fire 50 rapid pause and resume events in quick succession during an active download to ensure `threading.Event` synchronization and file locks never deadlock or corrupt offsets.
- **Simultaneous Worker Completion**: Ensure that multiple segments finishing at the exact same millisecond safely aggregate progress without race conditions in `ProgressAggregator`.
- **Worker Cancellation under Load**: Confirm that cancelling an active download cleanly terminates all worker threads within 1 second and deterministically closes all open file descriptors.

---

## 5. Headless GUI Testing with `pytest-qt`

PySide6 GUI components are tested without requiring a physical display by running Qt in offscreen platform mode (`QT_QPA_PLATFORM=offscreen`).

```python
# tests/gui/test_main_window.py
def test_add_download_flow(qtbot, container):
    window = MainWindow(container)
    qtbot.addWidget(window)
    window.show()

    # Trigger Add Download action
    window.action_add_download.trigger()
    
    # Assert model reflects changes
    assert window.table_model.rowCount() == 1
    assert window.table_model.data(window.table_model.index(0, 0)) == "expected_file.zip"
```

---

## 6. Static Analysis and Tooling Pipeline

| Tool | Purpose | Configuration / Threshold |
|---|---|---|
| **Ruff** | Linting & Formatting | PEP 8, flake8 rules, docstring presence, zero warnings |
| **mypy** | Static Typing | `--strict` mode: zero `Any`, explicit generic annotations, no untyped defs |
| **pytest** | Test Runner | Parallel execution via `pytest-xdist`, fail on warnings |
| **pytest-cov** | Code Coverage | Target: **≥ 80% coverage on `app/engine` and `app/domain`** |
| **pytest-qt** | GUI Harness | Offscreen rendering, signal spy verification |

