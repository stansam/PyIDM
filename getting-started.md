# PyIDM — Getting Started & User Guide

Welcome to **PyIDM** (Python Internet Download Manager), a modern, high-performance desktop download manager written in Python. PyIDM features multi-connection segmented downloading, cooperative pause/resume, startup crash recovery, bandwidth throttling, and a responsive native Qt interface with dual interface modes (Expanded and Compact).

---

## 1. System Requirements

- **Operating System:** Windows 10/11, Linux (Ubuntu, Debian, Fedora, Arch), macOS 12+
- **Python:** Version 3.11 or higher (Python 3.12+ fully supported)
- **Key Libraries:** PySide6 (Qt 6.7+), QtAwesome, HTTPX 0.28+, SQLAlchemy 2.0, FastAPI, Pydantic 2.x

---

## 2. Installation & Environment Setup

### 2.1 Using `uv` (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/pyidm/pyidm.git
   cd pyidm
   ```

2. **Sync dependencies and virtual environment:**
   ```bash
   uv sync --active --group dev
   ```

### 2.2 Using Standard `venv` & `pip`

1. **Create and activate a virtual environment:**
   ```powershell
   # Windows PowerShell
   python -m venv venv
   .\venv\Scripts\activate
   ```
   ```bash
   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install PyIDM with development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

---

## 3. Launching the Desktop Application

Once dependencies are installed, launch PyIDM from the project root:

```bash
# With uv:
uv run python app/main.py

# Or with activated virtual environment:
python -m app.main
```

---

## 4. How to Use PyIDM

### 4.1 Adding a Download
1. Click the **➕ New** action in the top toolbar (or double-click the empty table).
2. Enter or paste a valid `http://` or `https://` link. If a valid URL is already on your clipboard, PyIDM will auto-detect and pre-fill it.
3. Configure optional settings:
   - **File Name:** Automatically resolved from the URL or server headers (`Content-Disposition`).
   - **Save To:** Choose your target destination directory.
   - **Connections:** Configure parallel streaming threads (default: 4, up to 32).
4. Click **OK** to enqueue and start downloading immediately.

### 4.2 Multi-Connection Acceleration
- When a server advertises byte-range support via `Accept-Ranges: bytes`, PyIDM divides the total byte length into contiguous, non-overlapping byte ranges.
- Independent worker threads (`SegmentWorker`) stream assigned chunks concurrently to temporary part files (`.pyidm_temp/<download_id>/segment_XXX.part`).
- If a server does not support byte ranges, PyIDM automatically and transparently falls back to a reliable single-stream download.

### 4.3 Pause, Resume, and Cancellation
- **Pause:** Select an active download and click **⏸ Pause** (or right-click and choose *Pause*). Active segment workers cooperatively flush chunks to disk and persist written offsets to the SQLite database and disk manifest.
- **Resume:** Click **▶ Resume**. PyIDM re-validates the remote resource (`ETag` / `Last-Modified`) and resumes streaming exactly where each worker left off without re-downloading existing bytes.
- **Stop / Cancel:** Click **⏹ Stop** to abort active workers and clean up temporary storage.

### 4.4 Dual-Mode Desktop Interface
PyIDM features two purpose-built viewing modes sharing the identical state and table model:
- **Expanded Mode (Default):**
  - Features the full left navigation sidebar:
    - Status groups with live count badges: *All Tasks*, *Downloading*, *Waiting*, *Finished*.
    - Category tree: *Documents*, *Archives*, *Videos*, *Audio*, *Applications*, *Other*.
    - Engine status indicator pill: `🟢 Engine Active`.
  - Header with connection profile selector, action toolbar, sort menu, and live search bar.
  - Footer bar displaying aggregate network velocity (`↓ 0.00 B/s  ↑ 0.00 B/s`).
- **Compact Mode:**
  - Designed for minimal desktop footprint (toggle via the **Compact Mode** button on the toolbar).
  - Minimalist vertical slim icon sidebar (`⬇`, `📋`, `✔`, `➕`, `⚙`).
  - High-density table columns optimized for compact window dimensions.

### 4.5 Live Search & Sorting
- **Search Bar:** Type any part of a filename or URL in the search input to filter downloads instantly.
- **Sort Menu:** Click **⇅ Sort** to reorder downloads by *Name*, *Size*, *Status*, or *Date Added*.

### 4.6 Inspecting Download Details & Diagnostics
- Double-click any row in the download table (or right-click and choose **ℹ View Details...**) to open the **Download Details Dialog**:
  - **General Tab:** Original URL, destination folder, file size, downloaded bytes, status, and server headers (`ETag`, `Last-Modified`).
  - **Segments Tab:** Detailed breakdown of every byte range, worker offset, and percentage completion.
  - **Diagnostics Tab:** Network timestamps and error messages with failure taxonomy.

---

## 5. Browser Integration Setup

PyIDM includes a secured local loopback REST API server and a Chrome / Chromium Manifest V3 browser extension.

### 5.1 Local API Architecture
- PyIDM embeds an asynchronous loopback API using FastAPI on `http://127.0.0.1:8743`.
- **Security Protections:**
  - Bound exclusively to loopback interface `127.0.0.1`.
  - Anti-DNS rebinding protection via strict `Host` header validation (`127.0.0.1:8743` or `localhost:8743`).
  - Token authentication: Requests must provide the configured `X-PyIDM-Key` secret header.
  - CORS policies strictly allow browser extension origins (`chrome-extension://*`, `moz-extension://*`).

### 5.2 Installing the Chrome Extension
1. Open Google Chrome, Brave, or Microsoft Edge.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer mode** in the top-right corner.
4. Click **Load unpacked**.
5. Select the `browser_extensions/chrome/` directory inside your PyIDM repository.
6. The PyIDM icon will appear in your browser toolbar. Right-clicking any link on the web presents **Download with PyIDM**, which sends the link directly to your desktop manager.

---

## 6. Application Configuration & Settings

Access the **Preferences Dialog** via **⚙ Settings** in the toolbar:
- **General Settings:** Change default download directory, enable/disable automatic clipboard URL monitoring, and select application theme (*Dark*, *Light*, *System Default*).
- **Engine & Network:** Configure maximum simultaneous downloads (1–10), default parallel connections per file (1–32), and global bandwidth speed limit (Token Bucket rate limiter).
- **Browser Integration:** View or modify the local API port (default: `8743`) and secret API token.

---

## 7. Crash Recovery & Resilience

PyIDM is built to survive power outages, network disconnections, and application restarts:
1. Each active download maintains an on-disk manifest at:
   ```text
   .pyidm_temp/<download_id>/manifest.json
   ```
2. When PyIDM starts up, the `RecoveryManager` scans the SQLite database and manifest store. Any tasks that were left in active states (`DOWNLOADING`, `INSPECTING`, `PAUSING`) are safely reconciled to `PAUSED`.
3. Incomplete `.part` files are verified against disk lengths, allowing you to resume with zero data corruption.

---

## 8. Packaging & Standalone Desktop Distribution

PyIDM can be packaged as a standalone desktop application without requiring users to install Python.

### 8.1 Building with PyInstaller (Windows & Linux)

The repository includes a tuned PyInstaller build specification: `packaging/pyinstaller/pyidm.spec`.

To build the standalone executable:
```bash
# Ensure development dependencies are installed
uv run pyinstaller packaging/pyinstaller/pyidm.spec
```

The resulting standalone distribution will be generated in:
```text
dist/PyIDM/
├── PyIDM.exe (Windows) or PyIDM (Linux)
└── _internal/ (Qt plugins, stylesheets, bundled Python runtime)
```

### 8.2 Inno Setup Windows Installer (Optional)
To bundle the `dist/PyIDM` directory into a standard Windows installer (`PyIDM-Setup.exe`), compile the Inno Setup script pointing to the `dist/PyIDM` folder.

---

## 9. Running Tests & Quality Verification

Execute the test suite and static analyzers to ensure full code integrity:

```bash
# Run all 37 automated tests:
uv run pytest

# Run tests with code coverage:
uv run pytest --cov=app --cov-report=term-missing

# Run strict static typing (mypy):
uv run mypy --explicit-package-bases app tests

# Run Ruff linter and formatter:
uv run ruff check .
uv run ruff format .
```

