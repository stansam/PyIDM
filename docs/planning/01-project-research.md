# Comprehensive Project Research Report — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## Executive Summary

This report documents technical research conducted for **PyIDM**, an enterprise-grade desktop Internet Download Manager written in Python. It evaluates each mandatory technology, examines architectural trade-offs, defines standards compliance, and identifies critical limitations.

---

## 1. HTTP Networking & Client Architecture

### 1.1 HTTPX Synchronous vs. Asynchronous Model Evaluation

| Evaluation Criteria | `httpx.Client` (Synchronous) | `httpx.AsyncClient` (Asynchronous) |
|---|---|---|
| **Concurrency Model** | Dedicated OS threads (`ThreadPoolExecutor`) | Single event loop coroutines (`asyncio`) |
| **I/O Nature** | Blocking read per thread | Non-blocking cooperative polling |
| **Cancellation** | Clean via `threading.Event` checked per chunk | Task cancellation (`CancelledError`), requires careful cleanup |
| **GUI Integration** | Straightforward: Worker threads emit signals to Qt | Complex: requires running an `asyncio` loop in a secondary thread or using `qasync` |
| **Streaming Performance** | Direct socket read to disk in thread | Context switching in event loop for high chunk volume |
| **Connection Pooling** | Handled natively by HTTPX connection pool per thread | Handled natively in event loop |
| **Recommendation** | **PRIMARY SELECTION for Download Engine** | **Reserved exclusively for FastAPI Browser API** |

**Architectural Rationale:**
The synchronous `httpx.Client` combined with a bounded `ThreadPoolExecutor` is selected for PyIDM's download engine. A segmented download consists of 2–16 long-lived byte streams. Managing these streams across a pool of threads allows each worker to block independently on socket I/O and disk write without event loop starvation. Cooperative cancellation with `threading.Event` avoids the cancellation-during-yield complexities of `asyncio`.

### 1.2 HTTPX Version 0.28+ Specifics & Breaking Changes
- `httpx 0.28.x` dropped the plural `proxies=` argument in favor of singular `proxy=`.
- `WSGITransport` and `ASGITransport` require explicit instantiation (`app=` parameter was removed).
- SSL `verify=` parameter as string path is deprecated in favor of `ssl.SSLContext`.
- Connection pooling defaults: `max_connections=100`, `max_keepalive_connections=20`, `keepalive_expiry=5.0`.
- **Critical PyIDM Rule**: A single `httpx.Client` must be shared across all segment workers of a single download to enable HTTP/1.1 TCP connection reuse. Creating a new client per segment incurs TLS handshake overhead on every segment.

### 1.3 Streaming Response Handling
```python
# Canonical pattern for bounded memory streaming in PyIDM
with client.stream("GET", url, headers=range_header) as response:
    response.raise_for_status()
    # Use response.num_bytes_downloaded for wire-level tracking (bypasses gzip)
    for chunk in response.iter_bytes(chunk_size=65536):  # 64 KB buffer
        if cancel_event.is_set():
            break
        target_file.seek(write_offset)
        target_file.write(chunk)
        write_offset += len(chunk)
```

---

## 2. HTTP Range Requests & Protocol Semantics

### 2.1 RFC 9110 (superseding RFC 7233) Compliance
- **Range Syntax**: `Range: bytes=start-end` (inclusive offsets, 0-indexed). E.g., `bytes=0-10485759` represents exactly 10,485,760 bytes (10 MB).
- **206 Partial Content**:
  - `Content-Range: bytes 0-10485759/104857600` specifies the byte window and total entity length.
  - `Content-Length` in a 206 response indicates the length of the *partial payload*, not the total resource size.
- **416 Range Not Satisfiable**:
  - Returned if the requested range start is greater than or equal to the total resource length.
  - In PyIDM, if an interrupted download attempts to resume at an offset equal to the total length, HTTP 416 signals that the file is already complete.
- **Accept-Ranges Header**:
  - `Accept-Ranges: bytes` signals range capability.
  - If `Accept-Ranges` is omitted, the engine issues a probe range request (`Range: bytes=0-0`). If HTTP 206 is returned, segmentation is activated; if HTTP 200 is returned, fallback to single-stream is enforced.

### 2.2 Resume Validation: ETag and Last-Modified (RFC 9110 §13.1.5)
To prevent corrupting an assembled file when a remote resource has changed during pause/interruption:
- PyIDM captures `ETag` and `Last-Modified` during initial inspection.
- On resume, requests include `If-Range: <etag>` or `If-Range: <last-modified>`.
- **Server Behavior**:
  - If resource is unchanged: returns `206 Partial Content`.
  - If resource changed: returns `200 OK` with full content. The engine discards partial segments and restarts the download from byte 0.

### 2.3 Evaluation of Multipart Byte Ranges (`multipart/byteranges`)
Multi-range requests (`Range: bytes=0-1023, 2048-3071`) are intentionally **not supported**.
- RFC 9110 §14.1.2 defines multi-range responses as multipart MIME bodies requiring boundary delimiter parsing.
- Server support is notoriously inconsistent (many return 200 with full content).
- Multi-range over a single connection fails to achieve parallel throughput gains. Parallel single-range connections provide superior throughput and resilience.

---

## 3. Bandwidth Throttling & Speed Calculation

### 3.1 Token Bucket Throttling Algorithm
PyIDM implements an atomic token bucket to enforce user-configured speed limits:
- Capacity: `burst_limit = rate_bps * 2.0`
- Fill rate: `rate_bps` tokens per second.
- Consumption: Workers call `token_bucket.consume(len(chunk))` before writing.
- **Critical Threading Detail**: Sleep duration is computed under lock, but `time.sleep()` is executed outside the lock to prevent worker starvation.

### 3.2 Rolling Window Speed Calculation
To avoid unstable UI readings:
- PyIDM uses a `deque` of `(monotonic_timestamp, byte_count)` tuples over a 3.0 to 5.0 second rolling window.
- Speed is computed as `sum(bytes in window) / (latest_time - oldest_time)`.
- Using `time.monotonic()` prevents corrupted metrics caused by system NTP clock adjustments.

---

## 4. PySide6 & Qt 6 Desktop Architecture

### 4.1 Threading Model: Main Thread vs. Engine Isolation
Qt requires all GUI operations to occur exclusively on the primary thread.
- Background worker threads emit domain events via Qt Signals.
- Qt's signal-slot mechanism automatically routes cross-thread signals through `Qt.ConnectionType.QueuedConnection`, placing slot invocations into the main thread's event loop.
- The download engine contains zero PySide6 imports; an Application Layer adapter (`DownloadSignalEmitter`) acts as the bridge.

### 4.2 Qt Model/View Architecture
For managing hundreds of downloads without GUI latency:
- **Model**: Custom subclass of `QAbstractTableModel` maintaining an internal typed list of download records.
- **Update Frequency**: Throttled to 2–4 updates per second (250–500ms intervals) via `dataChanged` signals specifying only the affected columns (`ProgressColumn`, `SpeedColumn`, `ETAColumn`).
- **Delegate**: Custom `QStyledItemDelegate` for rendering native OS progress bars directly within the table view.

### 4.3 Modern UI Styling & Dark Mode
- Built using Qt Style Sheets (QSS) adhering to modern design tokens (spacing, typography, border radiuses).
- Automatic detection of OS light/dark mode preference via `QGuiApplication.styleHints().colorScheme()`, with manual override in settings.

---

## 5. Persistence Architecture: SQLite & SQLAlchemy 2.x

### 5.1 SQLite Configuration & WAL Mode
For high-concurrency desktop operations:
- **Write-Ahead Logging (WAL)**: `PRAGMA journal_mode = WAL;` allows concurrent readers during active writes.
- **Synchronous Mode**: `PRAGMA synchronous = NORMAL;` delivers high write performance while preserving durability in WAL mode.
- **Busy Timeout**: `PRAGMA busy_timeout = 5000;` prevents transient lock exceptions during concurrent segment state updates.
- **Foreign Keys**: `PRAGMA foreign_keys = ON;` explicitly enforced.
- **Memory Mapping**: `PRAGMA mmap_size = 268435456;` (256 MB) for rapid index and history scans.

### 5.2 SQLAlchemy 2.0 Modern Declarative Pattern
- Using `DeclarativeBase`, `Mapped[T]`, and `mapped_column()` with strict typing.
- Thread isolation: `NullPool` with `scoped_session` ensures each worker thread uses its own connection, avoiding SQLite multithreading corruption.
- In-flight segment counters are maintained in memory; database commits occur only on milestone transitions (start, pause, complete, fail).

### 5.3 Alembic Migration Framework
- SQLite limitations require table recreation for certain schema alterations. Alembic migrations must configure `render_as_batch=True`.
- Automated pre-flight backup (`pyidm.db.bak`) prior to applying migrations at application startup.

---

## 6. Browser Integration & Security Architecture

### 6.1 Native Messaging vs. Local HTTP API Evaluation

| Vector | Native Messaging Protocol | Local HTTP API (FastAPI) |
|---|---|---|
| **Installation** | Requires writing manifest to Windows Registry / Linux root paths | Standard loopback network communication |
| **Multi-Browser** | Separate registration per browser (Chrome, Firefox, Edge) | Single endpoint serves all compliant extensions |
| **Bi-directional** | Standard stdin/stdout JSON framing | Standard HTTP REST / WebSocket |
| **Privilege** | Runs with browser invocation permissions | Runs within PyIDM application sandbox |
| **Security Risk** | Malicious processes can hijack stdin if unmanaged | Localhost port exposure, DNS rebinding |
| **Recommendation** | Secondary / Packaging phase | **PRIMARY SELECTION for Browser Integration** |

### 6.2 Local API Security Constraints
To prevent Server-Side Request Forgery (SSRF) and malicious web page exploitation:
1. **Loopback Binding**: Bound strictly to `127.0.0.1`. Never bound to `0.0.0.0`.
2. **Shared Secret Token**: PyIDM generates a cryptographically secure API key at startup stored in user-restricted application data. Browser extensions must provide this key via the `X-PyIDM-Key` header.
3. **CORS & Host-Header Protection**: Explicitly validate `Host: 127.0.0.1:<port>` to reject DNS rebinding attacks. Reject requests containing unauthorized `Origin` headers.
4. **Target Scheme & Host Restrictions**: Refuse requests to download `file://`, `data:`, `gopher:`, or loopback/RFC 1918 private IP addresses.

---

## 7. Packaging & Distribution Strategy

### 7.1 PyInstaller vs. Alternatives

| Solution | PySide6 Compatibility | Build Reproducibility | Cross-Platform Support |
|---|---|---|---|
| **PyInstaller** | Excellent (mature `pyinstaller-hooks-contrib`) | High via `.spec` definition | Windows, Linux, macOS |
| **Nuitka** | Good (compiles to C++), but slower build times | Medium (sensitive to C compiler toolchain) | High |
| **cx_Freeze** | Moderate | Moderate | Moderate |

**Decision**: **PyInstaller** is selected for packaging PyIDM in directory mode (`onedir`) for production distributions, offering fast startup and reliable Qt plugin discovery.

### 7.2 Dependency Management with `uv`
- `uv` is evaluated as 10–100× faster than Poetry and pip.
- Strict lock file generation via `uv.lock`.
- Python 3.11 baseline compatibility guaranteed; forward compatible with Python 3.12+.

---

## 8. Summary of Final Architectural Recommendations

1. **Download Engine**: Multi-threaded synchronous HTTPX with thread-safe `TokenBucket` and `RollingSpeedMeter`.
2. **File Assembly**: Pre-allocated segmented temporary files (`.pyidm_temp/<uuid>/`) assembled via block streaming.
3. **GUI**: PySide6 Model/View with decoupled signal adapters and dark/light QSS theme engine.
4. **Persistence**: SQLite with WAL mode, SQLAlchemy 2.0 mapped models, Alembic batch migrations.
5. **Browser Integration**: Local FastAPI daemon thread guarded by shared secret authentication and host validation.
6. **Tooling**: `uv` for package management, `Ruff` for linting/formatting, `mypy --strict` for static type enforcement.
