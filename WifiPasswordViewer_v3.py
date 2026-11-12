"""
Desktop app (PyQt6) that lists the Wi-Fi networks saved on this Windows
computer and, on request, shows the password stored for each one.

Everything it reads is already stored locally by Windows. Run it only on a
machine you own or administer, where you are allowed to view the saved
wireless credentials.

Developed by EAF microservice.

Usage:
    pip install PyQt6
    python WifiPasswordViewer_v3.py
"""

from __future__ import annotations

import os
import platform
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

DEVELOPER = "EAF microservice"
APP_NAME = "Saved Wi-Fi Networks"
MASK = "•" * 6  # six bullet characters


def resource_path(name: str) -> str:
    """Resolve a bundled resource, whether run from source or a PyInstaller exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def run_netsh(*arguments: str) -> str:
    """Run netsh without a shell, returning its output or raising an error."""
    result = subprocess.run(
        ["netsh", *arguments],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message or f"netsh exited with code {result.returncode}")
    return result.stdout


def get_profile_names(output: str) -> list[str]:
    """Extract profile names from `netsh wlan show profiles` output."""
    names: list[str] = []
    for line in output.splitlines():
        if "All User Profile" in line or "Current User Profile" in line:
            _, separator, name = line.partition(":")
            if separator and name.strip():
                names.append(name.strip())
    return names


def get_password(profile: str) -> str:
    """Return the saved key for a profile, or a short note when there is none."""
    details = run_netsh("wlan", "show", "profile", profile, "key=clear")
    for line in details.splitlines():
        label, separator, value = line.partition(":")
        if separator and label.strip() == "Key Content":
            return value.strip() or "(no password saved)"
    # Open networks, or a localized Windows that labels the line differently,
    # have no "Key Content" line at all.
    return "(no password saved)"


class WifiViewer(QWidget):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.profiles: list[str] = []

        self.setWindowTitle(APP_NAME)
        icon_file = resource_path("icon.ico")
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
        self.resize(560, 440)
        self._build_ui()

        self.load_profiles()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        caption = QLabel(
            "Reads the wireless profiles Windows has already saved on this "
            "computer. Use it only on a machine you are allowed to inspect."
        )
        caption.setWordWrap(True)
        layout.addWidget(caption)

        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("Search:"))
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to filter by name")
        self.search_box.textChanged.connect(self._refresh_table)
        search_row.addWidget(self.search_box)
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.load_profiles)
        search_row.addWidget(refresh_button)
        layout.addLayout(search_row)

        self.reveal_box = QCheckBox("Show saved passwords (shown in clear text)")
        self.reveal_box.stateChanged.connect(self._refresh_table)
        layout.addWidget(self.reveal_box)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Network", "Password"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.status = QLabel("Loading saved networks...")
        layout.addWidget(self.status)

        credit = QLabel(f"Developed by {DEVELOPER}")
        credit.setAlignment(Qt.AlignmentFlag.AlignRight)
        credit.setStyleSheet("color: gray;")
        layout.addWidget(credit)

    def load_profiles(self) -> None:
        """Read saved profile names from Windows and repopulate the table."""
        if platform.system() != "Windows":
            self.status.setText("Runs only on Windows.")
            QMessageBox.critical(
                self,
                "Unsupported system",
                "This tool reads saved Wi-Fi profiles with the Windows 'netsh' "
                "command and runs only on Windows.",
            )
            return
        try:
            output = run_netsh("wlan", "show", "profiles")
            self.profiles = sorted(get_profile_names(output), key=str.casefold)
        except (OSError, RuntimeError) as error:
            self.profiles = []
            self.status.setText("Could not read saved Wi-Fi profiles.")
            QMessageBox.critical(
                self, "Error", f"Could not read saved Wi-Fi profiles:\n{error}"
            )
            return
        self._refresh_table()

    def _refresh_table(self) -> None:
        """Redraw the table from the current profiles, search and reveal state."""
        query = self.search_box.text().casefold()
        matches = [p for p in self.profiles if query in p.casefold()]
        reveal = self.reveal_box.isChecked()

        self.table.setRowCount(len(matches))
        for row, name in enumerate(matches):
            if reveal:
                try:
                    password = get_password(name)
                except (OSError, RuntimeError) as error:
                    password = f"(could not read: {error})"
            else:
                password = MASK
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(password))

        total = len(self.profiles)
        self.status.setText(
            f"{total} saved network{'s' if total != 1 else ''}"
            f" · {len(matches)} shown"
        )


def main() -> int:
    app = QApplication(sys.argv)
    icon_file = resource_path("icon.ico")
    if os.path.exists(icon_file):
        app.setWindowIcon(QIcon(icon_file))
    window = WifiViewer()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
