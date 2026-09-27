from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QLineEdit, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QTextEdit, QVBoxLayout, QWidget
)

from core.pipeline import DubPipeline, PipelineConfig


class Worker(QThread):
    log = Signal(str)
    progress = Signal(int)
    success = Signal(str)
    failure = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self) -> None:
        try:
            config = PipelineConfig(workspace=Path("workspace"), output_dir=Path("output"))
            pipeline = DubPipeline(config, self.log.emit, self.progress.emit)
            result = pipeline.run(self.url)
            self.success.emit(str(result))
        except Exception as exc:
            self.failure.emit(f"{type(exc).__name__}: {exc}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Douyin Smart Dubber")
        self.resize(900, 650)

        self.url = QLineEdit()
        self.url.setPlaceholderText("Dán link Douyin vào đây...")
        self.start = QPushButton("🚀 Lồng tiếng tự động")
        self.progress = QProgressBar()
        self.log = QTextEdit()
        self.log.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Douyin URL"))
        layout.addWidget(self.url)

        row = QHBoxLayout()
        row.addWidget(self.start)
        layout.addLayout(row)

        layout.addWidget(self.progress)
        layout.addWidget(QLabel("Pipeline log"))
        layout.addWidget(self.log)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.worker: Worker | None = None
        self.start.clicked.connect(self.start_job)

    def start_job(self) -> None:
        url = self.url.text().strip()
        if not url.startswith(("https://www.douyin.com/", "https://v.douyin.com/")):
            QMessageBox.warning(self, "URL không hợp lệ", "Hãy nhập URL Douyin hợp lệ.")
            return

        self.start.setEnabled(False)
        self.log.clear()
        self.progress.setValue(0)

        self.worker = Worker(url)
        self.worker.log.connect(self.log.append)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.success.connect(self.on_success)
        self.worker.failure.connect(self.on_failure)
        self.worker.finished.connect(lambda: self.start.setEnabled(True))
        self.worker.start()

    def on_success(self, path: str) -> None:
        self.progress.setValue(100)
        self.log.append(f"✅ Hoàn tất: {path}")
        QMessageBox.information(self, "Hoàn tất", f"Video đã tạo:\n{path}")

    def on_failure(self, message: str) -> None:
        self.log.append(f"❌ {message}")
        QMessageBox.critical(self, "Lỗi", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
