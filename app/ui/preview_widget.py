from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
from PySide6.QtCore import QMutex, QMutexLocker, Qt, QThread, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from ..config import AppConfig


class CameraThread(QThread):
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)

    def __init__(self, device_index: int, resolution: tuple[int, int]) -> None:
        super().__init__()
        self.device_index = device_index
        self.resolution = resolution
        self._running = True
        self._cap = None
        self._current_frame = None
        self._frame_mutex = QMutex()

    def run(self) -> None:  # type: ignore[override]
        try:
            self._cap = cv2.VideoCapture(self.device_index)
            if not self._cap.isOpened():
                self.error_occurred.emit(f"Could not open camera at index {self.device_index}")
                return
                
            width, height = self.resolution
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            while self._running:
                ok, frame = self._cap.read()
                if not ok:
                    time.sleep(0.05)
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb.shape
                img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
                self.frame_ready.emit(img.copy())
                
                # Store current frame for capture
                with QMutexLocker(self._frame_mutex):
                    self._current_frame = img.copy()
                    
        except Exception as e:
            self.error_occurred.emit(f"Camera error: {e}")
        finally:
            if self._cap is not None:
                self._cap.release()

    def get_current_frame(self) -> Optional[QImage]:
        """Get the most recent frame from the camera"""
        with QMutexLocker(self._frame_mutex):
            return self._current_frame.copy() if self._current_frame else None

    def stop(self) -> None:
        self._running = False
        if self._cap is not None:
            self._cap.release()


class PreviewWidget(QWidget):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.label = QLabel("Starting camera…")
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.thread = CameraThread(config.camera.device_index, config.camera.resolution)
        self.thread.frame_ready.connect(self._on_frame)
        self.thread.error_occurred.connect(self._on_error)
        self.thread.start()

    def _on_frame(self, frame: QImage) -> None:
        pix = QPixmap.fromImage(frame)
        self.label.setPixmap(pix.scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _on_error(self, error_msg: str) -> None:
        self.label.setText(f"Camera error: {error_msg}\n\nCheck permissions or try:\nsudo usermod -a -G video $USER")
        self.label.setStyleSheet("color: red; font-size: 14px;")

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        if self.label.pixmap() is not None:
            self.label.setPixmap(self.label.pixmap().scaled(self.label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        super().resizeEvent(event)

    def capture_sequence(self, num_shots: int, output_dir: Path) -> list[Path]:
        """Capture photos using the existing camera thread"""
        print(f"Starting capture sequence: {num_shots} photos to {output_dir}")
        
        if not hasattr(self, 'thread') or not self.thread.isRunning():
            print("Camera thread not running")
            return []
        
        captured = []
        for idx in range(num_shots):
            print(f"Capturing photo {idx + 1}/{num_shots}")
            
            # Get the current frame from the camera thread
            frame = self.thread.get_current_frame()
            if frame is not None:
                print(f"Got frame {idx + 1}, size: {frame.size()}")
                out_path = output_dir / f"shot_{idx + 1}.jpg"
                success = frame.save(str(out_path), "JPG", quality=95)
                if success:
                    captured.append(out_path)
                    print(f"Captured: {out_path}")
                else:
                    print(f"Failed to save: {out_path}")
            else:
                print(f"Failed to get frame {idx + 1}")
            
            # Small delay between captures
            time.sleep(0.3)
        
        print(f"Capture complete: {len(captured)} photos out of {num_shots} requested")
        return captured

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait(2000)  # Wait up to 2 seconds
            if self.thread.isRunning():
                self.thread.terminate()
                self.thread.wait(1000)
        super().closeEvent(event)


