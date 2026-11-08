# UI Design and Presentation Specification — PyIDM

**Document version:** 1.0  
**Status:** Complete — Stage 1  
**Date:** 2026-11-08  
**Author:** Software Architecture Team

---

## 1. Visual Direction and UI Architecture

PyIDM is built with **PySide6** and follows modern desktop design conventions: clean visual hierarchy, low cognitive load, responsive layout scaling, and non-blocking interactions.

### 1.1 Key UI Architectural Rules
1. **Model/View Isolation**: `DownloadTableModel` (`QAbstractTableModel`) handles all data manipulation. Widgets do not hold application business state.
2. **Throttled Repaint**: Progress bar updates and speed metrics are pushed via `dataChanged` at a maximum frequency of 4 Hz (250ms).
3. **Thread Safety**: UI elements never run network calls, database queries, or file I/O. All communication to backend services is dispatched via Application Service commands; all progress and state updates are received via queued Qt signals.
4. **Zero Nonfunctional Controls**: Every action item, button, and menu choice triggers a real underlying handler.

---

## 2. Screen-by-Screen Specification

### 2.1 Main Application Window (`MainWindow`)

```
+----------------------------------------------------------------------------------------------------+
|  PyIDM - Python Internet Download Manager                                            [_] [O] [X]   |
+----------------------------------------------------------------------------------------------------+
|  [+ Add URL]  [▶ Resume]  [⏸ Pause]  [⏹ Stop]  [🗑 Delete]  |  [⚙ Settings]  [?] Help             |
+-------------------+--------------------------------------------------------------------------------+
| NAVIGATION        | DOWNLOAD DASHBOARD                                                             |
|                   | Filter: [ All Downloads ▼ ]   Search: [ 🔍 Filter by filename...             ] |
| 📥 All Downloads  +--------------------------------------------------------------------------------+
| ⬇ Downloading (2) | File Name        | Size      | Progress     | Speed    | ETA      | Status     |
| ⏳ Queued (3)      |------------------+-----------+--------------+----------+----------+------------|
| ⏸ Paused (1)     | ubuntu-24.04.iso | 5.8 GB    | [=====>  ]48%| 8.4 MB/s | 00:06:12 | Downloadi..|
| ✅ Completed (14) | python-setup.exe | 24.2 MB   | [==========] | --       | --       | Completed  |
| ❌ Failed (0)     | dataset-large.tar| 12.1 GB   | [===>    ]31%| --       | --       | Paused     |
|                   | blender-4.1.zip  | 340 MB    | [          ] | --       | --       | Queued     |
| CATEGORIES        |                  |           |              |          |          |            |
| 📁 Documents      |                  |           |              |          |          |            |
| 📦 Archives       |                  |           |              |          |          |            |
| 🎬 Video          |                  |           |              |          |          |            |
| 🎵 Audio          |                  |           |              |          |          |            |
|                   |                  |           |              |          |          |            |
| QUEUES            |                  |           |              |          |          |            |
| 🕒 Default Queue  |                  |           |              |          |          |            |
| 🌙 Nightly Queue  |                  |           |              |          |          |            |
+-------------------+--------------------------------------------------------------------------------+
| Ready. | Active: 2 | Total Speed: 8.4 MB/s | Limit: Unlimited | Disk Free: 184 GB                  |
+----------------------------------------------------------------------------------------------------+
```

#### Main Window Components
1. **Global Toolbar**: Quick action triggers (`Add Download`, `Resume All`, `Pause All`, `Clear Finished`, `Settings`).
2. **Left Navigation Sidebar**:
   - Status Filters (`All`, `Downloading`, `Queued`, `Paused`, `Completed`, `Failed`).
   - Category Filters (`Documents`, `Applications`, `Archives`, `Videos`, `Audio`, `Images`, `Other`).
   - Queue Management (`Default Queue`, custom user queues).
3. **Central Download Table**:
   - Sortable columns: `File Name`, `Size`, `Progress Bar`, `Speed`, `ETA`, `Category`, `Date Added`.
   - Native segmented progress rendering using a custom `QStyledItemDelegate`.
   - Right-click Context Menu:
     - `Open File` (for COMPLETED).
     - `Open Folder`.
     - `Resume` / `Pause` / `Cancel`.
     - `Force Recheck / Verify`.
     - `Copy Source URL`.
     - `Properties / Details`.
     - `Delete (Record only / With file)`.
4. **Bottom Status Bar**:
   - Overall network activity indicator.
   - Aggregate download throughput.
   - Global speed limit badge.
   - Destination disk available capacity.

---

### 2.2 Add Download Dialog (`AddDownloadDialog`)

```
+------------------------------------------------------------------+
| Add New Download                                           [X]   |
+------------------------------------------------------------------+
| URL:                                                             |
| [ https://releases.ubuntu.com/24.04/ubuntu-24.04-desktop-amd64.i ]|
|                                                                  |
| File Name:             [ ubuntu-24.04-desktop-amd64.iso        ] |
| Save Directory:        [ C:/Users/Downloads/ISOs       ] [Browse] |
| Category:              [ Archives / ISOs           ▼ ]           |
| Queue:                 [ Default Queue             ▼ ]           |
| Connections:           [ 8                         ▼ ] (1 - 32)  |
|                                                                  |
| [▶] Advanced Options (Headers, Authentication, Speed Limit)      |
|   User-Agent:    [ Default (PyIDM/1.0)                        ]  |
|   Referer:       [                                            ]  |
|   Authorization: [ Bearer token or User:Pass                  ]  |
|   Speed Cap:     [ Unlimited                                ▼ ]  |
|                                                                  |
| [ ] Start immediately                                            |
|                                                                  |
|                          [ Cancel ]  [ Download Later ]  [ Start ]|
+------------------------------------------------------------------+
```

#### Behavior & Validation
- **Auto-Paste**: When opened, automatically checks system clipboard for valid `http://` or `https://` URLs.
- **Async Inspection**: In the background, initiates a lightweight probe (`HEAD` or ranged `GET`) to prefill the true filename from `Content-Disposition`, file size, and range capability indicator.
- **Input Sanitization**: Disallows invalid path characters and strips path traversal characters (`..`, `/`, `\`).

---

### 2.3 Download Details Dialog (`DownloadDetailsDialog`)

Provides deep diagnostics for an active or completed download:
- **General Tab**: Original URL, resolved final URL (after redirects), local destination, file size, checksum, and creation/completion timestamps.
- **Segments Tab**: Visual graphical strip displaying each segment's byte window, downloaded percentage, assigned worker thread, and current download speed.
- **Log / Diagnostics Tab**: Recorded network events, HTTP status codes, redirect hops, and retry backoff logs.

---

### 2.4 Settings Interface (`SettingsDialog`)

Divided into clear functional categories:
1. **General**:
   - Default download directory.
   - System startup behavior (minimize to tray, auto-start).
   - Clipboard URL detection toggle.
2. **Engine & Connection**:
   - Default connections per download (default: 4, range: 1–32).
   - Maximum simultaneous active downloads (default: 3).
   - Buffer chunk size (64 KB, 128 KB, 256 KB).
   - Temporary directory path (defaults to `.pyidm_temp/`).
3. **Speed & Bandwidth**:
   - Global download speed limiter (Token Bucket).
   - Download speed display units (MB/s vs. Mbps).
4. **Browser Integration**:
   - Local API loopback port (default: 8743).
   - Security API token regeneration.
   - Extension installation helper button (opens Chrome Web Store / Firefox Addons).
5. **Appearance**:
   - Theme selection: `Light`, `Dark`, or `Follow OS`.

---

## 3. Custom Qt Delegates & Theming

### 3.1 Segmented Progress Bar Delegate
A custom `QStyledItemDelegate` subclass renders multi-connection progress directly in the table row:
- Paints individual sub-bars for each segment to give visual feedback on segment completion.
- Uses hardware-accelerated QPainter operations without generating child widget overhead.

### 3.2 Theme Management & Modern QSS
Styles are externalized into `light.qss` and `dark.qss`. The `ThemeManager` applies stylesheet changes on the fly using Qt's dynamic property system:
- High contrast borders (`#3b82f6` primary accent).
- Responsive hover and selection states.
- Clean system font stacks (Segoe UI on Windows, Inter/Roboto on Linux, SF Pro on macOS).

