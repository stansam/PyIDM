# System Requirements Specification — PyIDM

**Document version:** 1.0  
**Status:** Draft — Stage 1  
**Date:** 2026-11-08

---

## 1. Introduction

This document defines the functional and non-functional requirements for PyIDM, a production-grade Python Internet Download Manager.

Requirements are assigned unique identifiers. Each requirement includes acceptance criteria.

---

## 2. Functional Requirements

### 2.1 Core Download Functionality

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-001 | The application must download files over HTTP. | A file can be downloaded from an HTTP URL to a specified local path. The file content must match the server content. |
| FR-002 | The application must download files over HTTPS. | A file can be downloaded from an HTTPS URL. TLS certificates must be validated. |
| FR-003 | The application must support single-connection downloads. | A download can proceed using a single TCP connection when the user or server dictates. |
| FR-004 | The application must support multi-connection segmented downloads. | A file is divided into N byte-range segments and downloaded concurrently via N parallel connections. The assembled file must be byte-identical to the source. |
| FR-005 | The application must detect whether a server supports HTTP Range requests. | A HEAD or ranged GET request is issued before segmented download. The result determines the download strategy. |
| FR-006 | The application must fall back to single-stream download when range requests are not supported. | When a server returns 200 (not 206) or omits the Accept-Ranges header, a single-stream download is initiated automatically. |
| FR-007 | The application must support pausing downloads. | A running download can be paused. All active segment workers stop cooperatively. Progress is persisted. The file is not corrupted. |
| FR-008 | The application must support resuming paused downloads. | A paused download can be resumed. Already-downloaded segments are not re-downloaded. The final assembled file is correct. |
| FR-009 | The application must support cancelling downloads. | A download can be cancelled at any time. Network resources are released. Temporary files are cleaned up according to the configured policy. |
| FR-010 | The application must resume interrupted downloads after application restart. | On startup, unfinished downloads are detected. The user is offered the option to resume. Resuming reuses existing segment data. |
| FR-011 | The application must validate file integrity after assembly. | If a checksum or ETag is available, the assembled file is verified. Verification failure is reported to the user. |
| FR-012 | The application must support configurable connection counts per download. | The user can set 1–32 connections per download. The engine respects the configured value. |
| FR-013 | The application must extract filenames from Content-Disposition headers. | When a server provides a Content-Disposition header with a filename, that name is used as the default download filename. |
| FR-014 | The application must detect MIME types. | The Content-Type header is captured and used for automatic categorization. |
| FR-015 | The application must handle HTTP redirects. | 301, 302, 303, 307, and 308 redirects are followed. The final URL is recorded. Redirect chains are limited to prevent loops. |
| FR-016 | The application must support custom request headers. | The user can specify additional HTTP headers for a download (e.g., Referer, Authorization). |
| FR-017 | The application must support cookie-based downloads. | The user can supply cookie values for authenticated downloads. |

### 2.2 Download Lifecycle and State Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-020 | The application must implement a formal download state machine. | Downloads transition through defined states. Invalid transitions are rejected. The state is persisted. |
| FR-021 | The application must support the following states: PENDING, QUEUED, INSPECTING, DOWNLOADING, PAUSING, PAUSED, RESUMING, VERIFYING, ASSEMBLING, COMPLETED, FAILED, CANCELLED. | Each state is represented in the codebase as a typed enum. Only valid transitions are allowed. |
| FR-022 | The application must persist download state to SQLite. | After restart, the last known state of each download is restored. |
| FR-023 | The application must detect and handle download state corruption. | If a download's persisted state is inconsistent with its temporary files, it is flagged for user review, not silently marked complete. |

### 2.3 Retry and Resilience

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-030 | The application must automatically retry failed segment downloads. | On transient failure, the segment is retried with exponential backoff. The attempt count and delay are configurable. |
| FR-031 | The application must respect Retry-After response headers. | When a server returns HTTP 429 or 503 with a Retry-After header, the application waits the specified duration before retrying. |
| FR-032 | The application must distinguish permanent from transient failures. | HTTP 404, 410, and similar permanent errors are not retried. HTTP 500, 503, and network errors are retried. |
| FR-033 | The application must limit retry attempts to a configurable maximum. | After exhausting retries, the download transitions to FAILED with a descriptive message. |
| FR-034 | The application must detect and report insufficient disk space. | Before writing, available disk space is checked. If insufficient, the download is paused and the user is notified. |
| FR-035 | The application must revalidate the remote resource identity on resume. | On resume, the ETag or Last-Modified value is compared to the value recorded at download start. If changed, the user is notified. |

### 2.4 Queue Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-040 | The application must support multiple download queues. | At least one default queue exists. The user can create, rename, and delete additional queues. |
| FR-041 | The application must enforce a configurable maximum simultaneous downloads limit. | No more than N downloads run concurrently, where N is user-configurable. |
| FR-042 | The application must support per-queue concurrent download limits. | Each queue has its own configurable concurrency limit that the system enforces. |
| FR-043 | The application must support priority levels for downloads. | Downloads with higher priority are started before lower-priority downloads. |
| FR-044 | The application must support reordering pending downloads. | The user can drag or move a pending download to change its position in the queue. |
| FR-045 | The application must automatically advance the queue. | When a download completes or fails, the next pending download in the queue starts automatically, subject to concurrency limits. |
| FR-046 | The application must support pausing and resuming entire queues. | All active downloads in a queue can be paused together. All paused downloads in a queue can be resumed together. |

### 2.5 Scheduling

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-050 | The application must support scheduled download start. | The user can specify a date and time for a download to begin automatically. |
| FR-051 | The application must support scheduled download stop. | The user can specify a time at which active downloads are paused. |
| FR-052 | The application must support daily recurring schedules. | Queues can be scheduled to run on specific days and times each week. |
| FR-053 | The application must persist scheduled configurations. | Schedules survive application restart. |

### 2.6 Speed Monitoring and Bandwidth Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-060 | The application must display current download speed per download. | Speed is displayed in the download list and updated at most every 500ms. |
| FR-061 | The application must display estimated time remaining per download. | ETA is calculated from current speed and remaining bytes. It is displayed in the download list. |
| FR-062 | The application must support a global bandwidth speed limit. | When configured, total download speed does not exceed the configured value. |
| FR-063 | The application must support per-download speed limits. | The user can assign a speed limit to individual downloads. |
| FR-064 | The application must implement bandwidth limiting using a token bucket algorithm. | Speed limiting is smooth, not bursty. The token bucket refill rate is set from the configured limit. |
| FR-065 | The application must display overall application download speed in the status bar. | The aggregate speed of all active downloads is displayed and updated periodically. |

### 2.7 Download Categorization

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-070 | The application must automatically categorize downloads. | Downloads are categorized as Documents, Applications, Archives, Videos, Audio, Images, or Other based on MIME type and file extension. |
| FR-071 | The application must support custom categories. | The user can create custom category names. |
| FR-072 | The application must support category-based download destinations. | Each category can be assigned a default download directory. |
| FR-073 | The application must handle duplicate filenames. | If a file with the target name exists, the application appends a numeric suffix rather than silently overwriting. |
| FR-074 | The application must normalize filenames. | Unsafe characters are removed or replaced. Path traversal sequences are rejected. |

### 2.8 Browser Integration

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-080 | The application must provide a browser extension for Chrome. | The extension can capture a download URL from the browser and send it to PyIDM. |
| FR-081 | The application must provide a browser extension for Firefox. | The extension can capture a download URL from Firefox and send it to PyIDM. |
| FR-082 | The application must provide a local HTTP API for browser communication. | The API listens on 127.0.0.1 only. It accepts download requests from authenticated extensions. |
| FR-083 | The browser extension must support context-menu integration. | Right-clicking a link in the browser shows a "Download with PyIDM" context menu item. |
| FR-084 | The application must handle requests when the application is not running. | The extension detects the application is unavailable and informs the user. |

### 2.9 Clipboard Monitoring

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-090 | The application must optionally monitor the clipboard for URLs. | When enabled, clipboard changes are detected. |
| FR-091 | The application must present a non-intrusive prompt when a downloadable URL is detected. | A small prompt appears allowing the user to add the download. The prompt disappears automatically if ignored. |
| FR-092 | Clipboard monitoring must be disabled by default. | The feature is opt-in and controlled in Settings. |

### 2.10 File Management

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-100 | The application must allow opening a completed download file. | The file is opened with the system default application. |
| FR-101 | The application must allow opening the containing folder of a download. | The file manager opens at the directory containing the downloaded file. |
| FR-102 | The application must allow deleting a download record. | The download record is removed from history. The user is prompted before deleting the actual file. |
| FR-103 | The application must allow clearing download history. | The user can clear completed and failed download records. |

### 2.11 Notifications

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-110 | The application must notify the user when a download completes. | A system notification is shown with the filename. |
| FR-111 | The application must notify the user when a download fails. | A system notification is shown with the error reason. |
| FR-112 | Notifications must be configurable. | The user can disable notifications in Settings. |

### 2.12 Settings and Configuration

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| FR-120 | The application must provide a Settings interface. | A settings page or dialog exposes all configurable options. |
| FR-121 | The application must persist settings to disk. | Settings survive application restart. |
| FR-122 | The application must support a default download directory setting. | All downloads default to the configured directory unless overridden. |
| FR-123 | The application must support a maximum simultaneous downloads setting. | The queue manager respects the configured limit. |
| FR-124 | The application must support a maximum connections per download setting. | New downloads default to the configured connection count. |
| FR-125 | The application must support light and dark themes. | The user can switch themes in Settings. The preference persists. |
| FR-126 | The application must support configurable log levels. | The user can select DEBUG, INFO, WARNING, or ERROR. The change takes effect without restart. |

---

## 3. Non-Functional Requirements

### 3.1 Architecture and Design

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-001 | The GUI thread must never be blocked by network operations. | No HTTP request is initiated on the main Qt thread. No file I/O runs on the main Qt thread. |
| NFR-002 | The download engine must be independently testable without a GUI. | All engine tests run without instantiating any Qt widget. |
| NFR-003 | The domain layer must not depend on PySide6, HTTPX, or SQLAlchemy. | No PySide6, HTTPX, or SQLAlchemy imports exist in `app/domain/`. |
| NFR-004 | The application must use dependency injection throughout. | Major services receive their dependencies through constructors. No global service locators in production code. |
| NFR-005 | The codebase must be strictly typed. | `mypy --strict` or Pyright strict mode produces zero unexplained errors. The word `Any` does not appear in production code. |
| NFR-006 | The application must use object-oriented design throughout. | All major behaviors are expressed through classes with clear responsibilities. SOLID principles are demonstrably applied. |

### 3.2 Performance

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-010 | The application must stream file content in bounded chunks. | No download loads the entire file into memory. Chunk size is configurable (default 64KB–256KB). |
| NFR-011 | The GUI must remain interactive during active downloads. | The main thread's event loop executes without stalling during downloads. |
| NFR-012 | GUI progress updates must be throttled. | Progress signals are emitted at most every 250–500ms per download. |
| NFR-013 | The application must limit the total number of active threads. | The thread pool has an upper bound. The application does not create unbounded threads. |
| NFR-014 | The application must reuse HTTP connections where possible. | HTTPX connection pooling is enabled. Multiple segments from the same host share connections where available. |
| NFR-015 | The application must handle files of at least 50GB without memory exhaustion. | A large file download completes without memory growth beyond the chunk buffer size. |

### 3.3 Reliability

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-020 | The application must recover from network disconnection. | A download that is interrupted by network loss retries automatically. On reconnect, it continues from where it stopped. |
| NFR-021 | The application must not expose incomplete files as completed. | Assembled files are written to the final path only after full assembly and optional integrity verification. |
| NFR-022 | Temporary files must be isolated from completed downloads. | Temporary segment files reside in a designated temp directory. They are not visible in the download destination during download. |
| NFR-023 | The application must handle disk full conditions gracefully. | A download pauses with an informative error rather than crashing or corrupting data. |
| NFR-024 | The application must not corrupt the SQLite database on crash. | SQLite WAL mode is enabled. Database transactions are used appropriately. |

### 3.4 Security

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-030 | The application must validate all URLs before use. | Only HTTP and HTTPS schemes are accepted. file://, ftp://, and javascript: are rejected. |
| NFR-031 | The application must prevent path traversal in filenames. | Filenames are sanitized before constructing file paths. `../` and absolute paths are rejected. |
| NFR-032 | The local API must bind exclusively to 127.0.0.1. | The API does not listen on 0.0.0.0 or any external interface. |
| NFR-033 | The local API must authenticate browser extension requests. | A shared secret token is required in all API requests from the extension. |
| NFR-034 | The application must not log sensitive headers or cookies. | Authorization and Cookie headers are redacted in all log output. |
| NFR-035 | Redirect chains must be limited. | At most 10 redirects are followed. Redirect cycles are detected and rejected. |
| NFR-036 | The application must reject private network URLs from browser extension input. | Requests to 192.168.x.x, 10.x.x.x, 172.16-31.x.x, and similar ranges are blocked when relayed via the extension API. |

### 3.5 Maintainability

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-040 | The codebase must pass Ruff checks with zero violations. | `ruff check .` passes without errors on all production code. |
| NFR-041 | All public classes and methods must have docstrings. | Public API has docstring coverage. `pydocstyle` or Ruff D-rule checks pass. |
| NFR-042 | The codebase must have no circular imports. | The module graph is acyclic. Import order follows the layered architecture. |
| NFR-043 | Dependencies must be pinned reproducibly. | `uv.lock` is committed. The environment is exactly reproducible from the lock file. |

### 3.6 Compatibility

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-050 | The application must support Windows 10 and later. | Installation and all core features work on Windows 10 (64-bit) and Windows 11. |
| NFR-051 | The application must support mainstream Linux distributions. | Installation and all core features work on Ubuntu 22.04 LTS and later. |
| NFR-052 | The application must not require the user to install Python. | The packaged distribution bundles a Python interpreter. |
| NFR-053 | The application must use Python 3.11 as the minimum supported version. | The codebase uses no features beyond Python 3.11. (Note: 3.12 is preferred but 3.11 is the installed baseline.) |

### 3.7 Testability

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| NFR-060 | The test suite must not depend on external internet resources. | All network tests use a local mock HTTP server. |
| NFR-061 | The test suite must achieve meaningful coverage of the download engine. | Coverage for `app/engine/` is at least 80%. |
| NFR-062 | The test suite must include concurrency and race condition tests. | Tests exercise simultaneous downloads, pause/resume under load, and cancellation. |
| NFR-063 | GUI tests must run headlessly in CI environments. | pytest-qt tests run with QT_QPA_PLATFORM=offscreen. |

---

## 4. Assumptions

| ID | Assumption |
|----|------------|
| ASM-001 | The application does not support FTP, Magnet links, or BitTorrent in the initial release. |
| ASM-002 | Authentication is limited to HTTP Basic Auth and bearer tokens supplied by the user. OAuth flows are out of scope. |
| ASM-003 | Browser integration targets Chrome 120+ and Firefox 120+. |
| ASM-004 | The initial release does not include video streaming or media player integration. |
| ASM-005 | The application stores credentials only in memory during a session. No credential keychain integration is included in the initial release. |
| ASM-006 | Python 3.11 is the minimum target. The `.python-version` file will specify 3.12 for future development; the codebase avoids 3.12-only syntax in the initial phases. |

