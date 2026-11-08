"""Help and FAQs modal dialog for PyIDM desktop users."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from app.presentation.icons import IconColor, IconName, IconSize, get_icon_manager


class HelpDialog(QDialog):
    """User assistance dialog providing instructions, FAQs, and shortcuts."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("PyIDM — Help, Instructions & FAQs")
        self.resize(680, 520)

        icons = get_icon_manager()
        self.setWindowIcon(icons.get(IconName.HELP, IconColor.PRIMARY))

        main_layout = QVBoxLayout(self)

        header_label = QLabel("<h2>PyIDM User Guide & Frequently Asked Questions</h2>")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        tabs = QTabWidget()

        # Tab 1: Quickstart & Common Instructions
        instructions_browser = QTextBrowser()
        instructions_browser.setHtml(
            """
            <h3>Quickstart Guide</h3>
            <ol>
                <li><b>Add a Download:</b> Click <b>New</b> on the toolbar, paste any valid <code>http://</code> or <code>https://</code> URL, choose the target directory, and click <b>Start</b>.</li>
                <li><b>Multi-Connection Acceleration:</b> When supported by the remote server, PyIDM automatically divides the file into parallel byte-range streams (default 4 connections, up to 32).</li>
                <li><b>Pause and Resume:</b> Click <b>Pause</b> at any time. When paused, segment manifests are flushed to disk. Resuming continues from the exact byte offset without re-downloading.</li>
                <li><b>Compact vs. Expanded Mode:</b> Toggle the <b>Compact Mode</b> button in the toolbar to switch to a sleek high-density interface.</li>
                <li><b>Opening Files:</b> Right-click any completed download and choose <i>Open File</i> or <i>Open Containing Folder</i>.</li>
            </ol>
            """
        )
        tabs.addTab(
            instructions_browser,
            icons.get(IconName.DOWNLOAD, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Quickstart",
        )

        # Tab 2: FAQs
        faq_browser = QTextBrowser()
        faq_browser.setHtml(
            """
            <h3>Frequently Asked Questions (FAQs)</h3>
            <p><b>Q: Why do some downloads only use 1 connection?</b><br>
            A: If a remote server does not support HTTP Range requests (does not return <code>Accept-Ranges: bytes</code>), PyIDM safely falls back to a reliable single-stream download.</p>

            <p><b>Q: Where are unfinished downloads stored?</b><br>
            A: Incomplete segments are stored in the temporary directory (<code>.pyidm_temp/&lt;download_id&gt;/</code>). If the application or system restarts abruptly, PyIDM's startup recovery scanner reconciles the manifests so you can resume.</p>

            <p><b>Q: How does clipboard monitoring work?</b><br>
            A: When enabled in <b>Settings</b>, PyIDM inspects your system clipboard for valid downloadable URLs and prompts you to enqueue them automatically.</p>

            <p><b>Q: How can I integrate with Google Chrome or Firefox?</b><br>
            A: Install the PyIDM extension from the <code>browser_extensions/chrome/</code> folder as an unpacked developer extension. PyIDM runs a local API on <code>127.0.0.1:8743</code> that intercepts download links.</p>
            """
        )
        tabs.addTab(
            faq_browser,
            icons.get(IconName.INFO, IconColor.PRIMARY, IconSize.SIDEBAR),
            "FAQs",
        )

        # Tab 3: Shortcuts & Controls
        shortcuts_browser = QTextBrowser()
        shortcuts_browser.setHtml(
            """
            <h3>Keyboard Shortcuts & Navigation</h3>
            <table border="0" cellpadding="6" style="width:100%;">
                <tr><td><b>Double Click</b></td><td>View detailed diagnostics and segment breakdown</td></tr>
                <tr><td><b>Right Click</b></td><td>Context menu (Pause, Resume, Open Folder, Delete, Select)</td></tr>
                <tr><td><b>Search Box</b></td><td>Filters downloads in real-time by filename or URL</td></tr>
                <tr><td><b>Sort Button</b></td><td>Sorts by Name, Size, Status, or Date Added</td></tr>
                <tr><td><b>Categories</b></td><td>Filters by Documents, Archives, Videos, Audio, Applications</td></tr>
            </table>
            """
        )
        tabs.addTab(
            shortcuts_browser,
            icons.get(IconName.MENU, IconColor.PRIMARY, IconSize.SIDEBAR),
            "Controls & Shortcuts",
        )

        # Tab 4: About
        about_browser = QTextBrowser()
        about_browser.setHtml(
            """
            <h3>About PyIDM</h3>
            <p><b>Version:</b> 1.0.0<br>
            <b>Engine:</b> Python 3.11+, PySide6, HTTPX, SQLAlchemy 2.0, QtAwesome<br>
            <b>License:</b> MIT License</p>
            <p>PyIDM is designed for high-performance, multi-threaded segmented file downloads with zero external bloatware.</p>
            """
        )
        tabs.addTab(
            about_browser,
            icons.get(IconName.HELP, IconColor.PRIMARY, IconSize.SIDEBAR),
            "About",
        )

        main_layout.addWidget(tabs)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.accept)
        main_layout.addWidget(button_box)

