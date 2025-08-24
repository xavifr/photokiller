from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QMutex, QMutexLocker, Qt, QThread, Signal, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout

from ..config import AppConfig
from ..capture import capture_photos


class CameraPreview(QThread):
    """Camera preview thread that works with both webcam and DSLR modes"""
    frame_ready = Signal(QImage)
    error_occurred = Signal(str)

    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self._running = True
        self._current_frame = None
        self._frame_mutex = QMutex()
        self._preview_timer = None

    def run(self) -> None:  # type: ignore[override]
        """Start preview based on camera mode"""
        if self.config.camera.skip_preview:
            # Show placeholder when preview is disabled
            self.frame_ready.emit(self._create_placeholder())
            return

        if self.config.camera.mode == "webcam":
            self._run_webcam_preview()
        elif self.config.camera.mode == "dslr":
            self._run_dslr_preview()
        else:
            self.error_occurred.emit(f"Unknown camera mode: {self.config.camera.mode}")

    def _run_webcam_preview(self) -> None:
        """Run webcam preview using OpenCV"""
        import cv2
        try:
            cap = cv2.VideoCapture(self.config.camera.device_index)
            if not cap.isOpened():
                self.error_occurred.emit(f"Could not open camera at index {self.config.camera.device_index}")
                return
                
            width, height = self.config.camera.resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            while self._running:
                ok, frame = cap.read()
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
            self.error_occurred.emit(f"Webcam preview error: {e}")
        finally:
            if 'cap' in locals():
                cap.release()

    def _run_dslr_preview(self) -> None:
        """Run DSLR preview using gphoto2"""
        import subprocess
        try:
            # Check if gphoto2 is available
            try:
                subprocess.run(["gphoto2", "--version"], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                self.error_occurred.emit("gphoto2 not found. Please install it: sudo apt install gphoto2")
                return

            # Auto-detect camera
            try:
                result = subprocess.run(["gphoto2", "--auto-detect"], check=True, capture_output=True, text=True)
                if "No cameras found" in result.stdout:
                    self.error_occurred.emit("No DSLR camera detected. Please check USB connection.")
                    return
                print(f"DSLR detected: {result.stdout.strip()}")
            except subprocess.CalledProcessError:
                self.error_occurred.emit("Failed to detect DSLR camera")
                return

            # Start preview timer for DSLR
            self._preview_timer = QTimer()
            self._preview_timer.timeout.connect(self._capture_dslr_preview)
            interval_ms = int(self.config.camera.dslr_preview_interval * 1000)
            self._preview_timer.start(interval_ms)
            
            # Keep thread alive
            while self._running:
                time.sleep(0.1)
                
        except Exception as e:
            self.error_occurred.emit(f"DSLR preview error: {e}")

    def _capture_dslr_preview(self) -> None:
        """Capture a preview image from DSLR for display"""
        if not self._running:
            return
            
        import subprocess
        try:
            # Capture a small preview image
            result = subprocess.run([
                "gphoto2", 
                "--capture-preview", 
                "--stdout"
            ], check=True, capture_output=True)
            
            if result.stdout:
                # Convert captured preview to QImage
                img = QImage()
                if img.loadFromData(result.stdout):
                    # Scale to reasonable preview size
                    scaled_img = img.scaled(
                        self.config.camera.resolution[0], 
                        self.config.camera.resolution[1], 
                        Qt.KeepAspectRatio, 
                        Qt.SmoothTransformation
                    )
                    self.frame_ready.emit(scaled_img.copy())
                    
                    # Store current frame for capture
                    with QMutexLocker(self._frame_mutex):
                        self._current_frame = scaled_img.copy()
                        
        except subprocess.CalledProcessError as e:
            # Don't emit error for preview failures, just log
            print(f"DSLR preview capture failed: {e}")
        except Exception as e:
            print(f"DSLR preview error: {e}")

    def _create_placeholder(self) -> QImage:
        """Create a placeholder image when preview is disabled"""
        width, height = self.config.camera.resolution
        img = QImage(width, height, QImage.Format_RGB888)
        img.fill(Qt.black)
        return img

    def get_current_frame(self) -> Optional[QImage]:
        """Get the most recent frame from the camera"""
        with QMutexLocker(self._frame_mutex):
            return self._current_frame.copy() if self._current_frame else None

    def stop(self) -> None:
        """Stop the preview thread"""
        self._running = False
        if self._preview_timer:
            self._preview_timer.stop()


class PreviewWidget(QWidget):
    """Widget for displaying camera preview"""
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.config = config
        self.label = QLabel("Starting camera…")
        self.label.setAlignment(Qt.AlignCenter)
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)

        self.preview = CameraPreview(config)
        self.preview.frame_ready.connect(self._on_frame)
        self.preview.error_occurred.connect(self._on_error)
        self.preview.start()

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

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if hasattr(self, 'preview') and self.preview.isRunning():
            self.preview.stop()
            self.preview.wait(2000)  # Wait up to 2 seconds
            if self.preview.isRunning():
                self.preview.terminate()
                self.preview.wait(1000)
        super().closeEvent(event)


