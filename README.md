# PyIDM — Production-Grade Python Internet Download Manager

PyIDM is a modern, enterprise-grade desktop Internet Download Manager written in Python. It provides high-throughput multi-connection segmented downloads, cooperative pause/resume, automatic crash recovery, bandwidth throttling, and a responsive native desktop user interface built with PySide6 (Qt 6).

---

## 1. Key Features

- **Multi-Connection Acceleration**: Splits files into contiguous byte ranges across parallel HTTP/1.1 connections.
- **Resilient Lifecycle**: Reliable pause, resume, cancel, and automatic crash recovery via disk manifests.
- **Automatic Fallback**: Gracefully detects servers lacking byte-range support and falls back to single-stream downloads.
- **Bandwidth Throttling**: Precision token bucket rate limiting (global and per-download caps).
- **Persistent State**: SQLite with Write-Ahead Logging (WAL) and SQLAlchemy 2.0 mapped models.
- **Strict Architecture**: Layered design (Presentation, Application, Domain, Engine, Infrastructure), strictly typed with zero `Any` usage.
- **Cross-Platform**: Full native desktop support for Windows, Linux, and macOS.

---

## 2. Prerequisites

- **Python**: Version 3.11 or higher (Python 3.12+ recommended).
- **Package Manager**: [uv](https://docs.astral.sh/uv/) (recommended) or standard `pip`.

---

## 3. Installation Guide by Operating System

### Windows

1. **Install Python & uv** (if not already installed):
   ```powershell
   winget install astral-sh.uv
   ```

2. **Clone the Repository**:
   ```powershell
   git clone https://github.com/pyidm/pyidm.git
   cd pyidm
   ```

3. **Set Up Virtual Environment & Dependencies**:
   Using `uv` (recommended):
   ```powershell
   # Creates virtual environment and installs all runtime + dev dependencies
   uv sync --active --group dev
   ```

   Or using standard `venv` + `pip`:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   pip install -e ".[dev]"
   ```

---

### Linux (Ubuntu / Debian / Fedora / Arch)

1. **Install System Dependencies (Qt 6 libraries)**:
   On Ubuntu/Debian:
   ```bash
   sudo apt update
   sudo apt install -y python3-dev build-essential libgl1-mesa-dev libxkbcommon-x11-0 libegl1
   ```
   On Fedora:
   ```bash
   sudo dnf install -y python3-devel mesa-libGL-devel libxkbcommon-x11
   ```

2. **Install uv & Clone Repository**:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   git clone https://github.com/pyidm/pyidm.git
   cd pyidm
   ```

3. **Install Dependencies**:
   ```bash
   uv sync --active --group dev
   ```

---

### macOS

1. **Install uv**:
   ```bash
   brew install uv
   ```

2. **Clone and Install**:
   ```bash
   git clone https://github.com/pyidm/pyidm.git
   cd pyidm
   uv sync --active --group dev
   ```

---

## 4. How to Run PyIDM

### Launch Desktop Application
Once dependencies are synced:

With `uv`:
```bash
uv run python app/main.py
```

With an activated virtual environment:
```bash
# Windows
.\venv\Scripts\activate
python app/main.py
or 
python -m app.main # run as a module

# Linux / macOS
source venv/bin/activate
python app/main.py
```

---

## 5. Development & Testing Workflow

### Running Tests
Execute the full automated test suite (including unit, integration, and mock HTTP tests):
```bash
uv run pytest
```

### Static Type Checking (Strict Mode)
Verify type safety with `mypy` strict mode (zero `Any` tolerance):
```bash
uv run mypy --explicit-package-bases app tests
```

### Linting & Formatting
Format and lint with `ruff`:
```bash
uv run ruff check .
uv run ruff format .
```

---

## 6. Project Architecture Overview

```text
PyIDM/
├── app/
│   ├── domain/           # Pure business models (Download, Segment, ByteRange) - zero dependencies
│   ├── engine/           # Multi-threaded download execution, workers, rate limiting, file assembler
│   ├── infrastructure/   # HTTPX client, SQLAlchemy 2.0 SQLite persistence (WAL mode), filesystem
│   ├── application/      # Orchestration, container, use cases, signal adapters
│   └── presentation/     # PySide6 desktop interface, Model/View, delegates, themes
├── tests/
│   ├── unit/             # Domain and calculator unit tests
│   ├── integration/      # SQLite persistence and multi-segment parallel download tests
│   └── fixtures/         # Mock HTTP test server simulating byte ranges & errors
└── docs/planning/        # Stage 1 research, architecture, specifications, and roadmap
```

---

## 7. License

Distributed under the MIT License. See `LICENSE` for details.
