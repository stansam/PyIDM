# Risk Register and Mitigation Strategy — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## 1. Risk Matrix Overview

This register identifies technical, operational, and architectural risks associated with building PyIDM, evaluating their probability, severity, and providing concrete mitigation strategies and fallback plans.

```
High Severity   | [RSK-02] [RSK-04]           [RSK-01]
Medium Severity | [RSK-08] [RSK-05]           [RSK-03]
Low Severity    |          [RSK-07]           [RSK-06]
                +---------------------------------------
                           Probability (Low -> High)
```

---

## 2. Risk Evaluation Table

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Fallback / Recovery Plan |
|---|---|---|---|---|---|
| **RSK-01** | **Servers Rejecting HTTP Range Requests** | High | High | Issue a lightweight range probe (`Range: bytes=0-0`). Detect HTTP 200 vs 206 responses. | Automatically downgrade download strategy to `SINGLE_STREAM`. Inform the user that acceleration is unavailable for this host. |
| **RSK-02** | **Remote File Mutation During Pause/Interruption** | Medium | High | Capture `ETag` and `Last-Modified` headers during initial inspection. Send `If-Range` on resume. | If server returns HTTP 200 instead of 206, detect that the file has changed. Alert the user and offer a clean re-download from byte 0. |
| **RSK-03** | **Network Timeout / Connection Drops Mid-Stream** | High | Medium | Implement chunk-level exception catching for socket/read errors. Apply `RetryCoordinator` with exponential backoff and jitter. | Pause the worker temporarily. If retries exhaust after 5 attempts, transition download to `FAILED` with retry button. |
| **RSK-04** | **Database & Temp File Inconsistency After Crash** | Medium | High | Maintain an atomic manifest file (`.pyidm_temp/<id>/manifest.json`) alongside segment files. | Run `RecoveryManager` on startup. Cross-check SQLite segment records against actual file sizes on disk before allowing resume. |
| **RSK-05** | **Disk Full During Active Write (ENOSPC)** | Low | High | Check available destination disk space before starting and periodically during downloads. | Catch `OSError: [Errno 28] No space left on device`. Transition download to `PAUSED`, display an urgent UI warning, and release worker threads. |
| **RSK-06** | **Qt Event Loop Saturation from Progress Signals** | High | Low | Throttle progress signal emissions inside `ProgressAggregator` to a maximum frequency of 4 Hz (250–400ms). | If the main thread falls behind, drop intermediate progress events; always emit the final completion event. |
| **RSK-07** | **DNS Rebinding Attacks on Browser Local API** | Low | High | Strictly validate the HTTP `Host` header (`127.0.0.1:<port>`). Require an `X-PyIDM-Key` token on every request. | Drop any unauthorized request with `400 Bad Request` or `401 Unauthorized` before processing any parameters. |
| **RSK-08** | **PySide6 Plugin & Library Bundling Failures in PyInstaller** | Medium | Medium | Use proven PySide6 hooks (`pyinstaller-hooks-contrib`). Maintain an explicit `.spec` file testing Qt platform plugins. | Test standalone `onedir` builds on clean virtual machines (Windows and Linux) in Phase 10 before generating installers. |
| **RSK-09** | **CDN Per-IP Connection Throttling** | Medium | Medium | Allow the user to configure connection count per download (1–32, defaulting to 4). | If HTTP 429 is encountered, respect `Retry-After` header and dynamically scale down active connection count. |
| **RSK-10** | **File Path Traversal in Server Content-Disposition** | Low | High | Clean all filenames through `FilenameResolver`, stripping `/`, `\`, and `..` components and restricting characters to safe OS sets. | Fallback to a sanitized URL basename or a generated UUID filename if Content-Disposition contains malicious paths. |

