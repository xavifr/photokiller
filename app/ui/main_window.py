from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent, QFont, QPalette, QColor, QPixmap, QPainter, QPen, QImage
from PySide6.QtWidgets import (
    QWidget,
    QMainWindow,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QHBoxLayout,
    QFrame,
)

from ..config import AppConfig
from .preview_widget import PreviewWidget, CameraPreview

# Import capture modules conditionally
from ..capture import capture_photos
from ..compose.layouts import compose_10x15_strip
from ..print.cups_print import print_file_cups
from ..utils.paths import make_session_dir
from pathlib import Path


class CountdownWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make it cover the entire main window
        self.setGeometry(0, 0, parent.width(), parent.height())
        
        # Create a dark overlay background
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
            }
        """)
        
        # Main container for the countdown content
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.width(), self.height())
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 240);
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Get Ready!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Camera preview area
        self.preview_label = QLabel("Camera preview will appear here")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 4px solid #ffffff;
                border-radius: 15px;
                padding: 20px;
                color: white;
                font-size: 18px;
            }
        """)
        self.preview_label.setMinimumSize(800, 600)
        layout.addWidget(self.preview_label, 1)  # Give it stretch priority
        
        # Countdown display
        countdown_layout = QHBoxLayout()
        countdown_layout.setSpacing(20)
        
        # Countdown number
        self.countdown_label = QLabel("3")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 120px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                background-color: rgba(255, 255, 255, 20);
                border-radius: 60px;
                padding: 20px;
                min-width: 200px;
                min-height: 200px;
            }
        """)
        
        # Countdown message
        self.message_label = QLabel("Get ready!")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
        """)
        
        countdown_layout.addWidget(self.countdown_label, alignment=Qt.AlignCenter)
        countdown_layout.addWidget(self.message_label, alignment=Qt.AlignCenter)
        layout.addLayout(countdown_layout)
        
        self.hide()
    
    def set_preview_frame(self, frame):
        """Render preview with high-contrast background and a non-destructive outline."""
        if frame is None:
            self.preview_label.clear()
            self.preview_label.setText("Camera preview will appear here")
            return
        
        # Create a canvas equal to label size
        label_size = self.preview_label.size()
        canvas = QPixmap(label_size)
        canvas.fill(QColor("#1a1a1a"))  # dark background
        
        # Compute scaled image size with margin
        margin = 16
        target_w = max(1, label_size.width() - margin * 2)
        target_h = max(1, label_size.height() - margin * 2)
        scaled = QPixmap.fromImage(frame).scaled(
            target_w,
            target_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        
        # Center position
        x = (label_size.width() - scaled.width()) // 2
        y = (label_size.height() - scaled.height()) // 2
        
        painter = QPainter(canvas)
        painter.drawPixmap(x, y, scaled)
        # Draw a subtle outline around the drawn image (preview-only)
        pen = QPen(QColor("#FFFFFF"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(x, y, scaled.width() - 1, scaled.height() - 1)
        painter.end()
        
        self.preview_label.setPixmap(canvas)
    
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle resize to cover full window"""
        super().resizeEvent(event)
        # Resize to cover the entire parent window
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        # Make container cover full countdown widget
        self.container.setGeometry(0, 0, self.width(), self.height())


class ReviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make it cover the entire main window (including title bar)
        self.setGeometry(0, 0, parent.width(), parent.height())
        
        # Create a dark overlay background that covers everything
        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 200);
            }
        """)
        
        # Main container for the review content - now fullscreen
        self.container = QFrame(self)
        self.container.setGeometry(0, 0, self.width(), self.height())
        self.container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 240);
            }
        """)
        
        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        
        # Title
        title = QLabel("Review Your Photos")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Photo display - now larger and more prominent
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 4px solid #ffffff;
                border-radius: 15px;
                padding: 20px;
            }
        """)
        self.photo_label.setMinimumSize(800, 600)
        layout.addWidget(self.photo_label, 1)  # Give it stretch priority
        
        # Button container
        button_layout = QHBoxLayout()
        button_layout.setSpacing(40)
        
        # Discard button - larger for fullscreen
        self.discard_btn = QPushButton("DISCARD")
        self.discard_btn.setFixedSize(200, 70)
        self.discard_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: none;
                border-radius: 35px;
                font-size: 20px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }
        """)
        
        # Print button - larger for fullscreen
        self.print_btn = QPushButton("PRINT")
        self.print_btn.setFixedSize(200, 70)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                border-radius: 35px;
                font-size: 20px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
            }
        """)
        
        button_layout.addWidget(self.discard_btn, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.print_btn, alignment=Qt.AlignCenter)
        layout.addLayout(button_layout)
        
        self.hide()
    
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle resize to cover full window"""
        super().resizeEvent(event)
        # Resize to cover the entire parent window
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        # Make container cover full review widget
        self.container.setGeometry(0, 0, self.width(), self.height())
    
    def set_photo(self, photo_path: str) -> None:
        """Set the photo to display with dark background and outline for clear borders."""
        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            self.photo_label.setText("Failed to load photo")
            return

        label_size = self.photo_label.size()
        canvas = QPixmap(label_size)
        canvas.fill(QColor("#1a1a1a"))

        # Fit image within label with margins
        margin = 16
        target_w = max(1, label_size.width() - margin * 2)
        target_h = max(1, label_size.height() - margin * 2)
        scaled = pixmap.scaled(target_w, target_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        x = (label_size.width() - scaled.width()) // 2
        y = (label_size.height() - scaled.height()) // 2

        painter = QPainter(canvas)
        painter.drawPixmap(x, y, scaled)
        # Draw an outline strictly for on-screen clarity; does not alter file
        pen = QPen(QColor("#FFFFFF"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawRect(x, y, scaled.width() - 1, scaled.height() - 1)
        painter.end()

        self.photo_label.setPixmap(canvas)
    
    def set_error_message(self, message: str) -> None:
        """Set the error message to display in the review widget"""
        self.photo_label.setText(message)
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                color: red;
                font-size: 20px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
        """)
        self.discard_btn.setEnabled(True)
        self.print_btn.setEnabled(False)


class MainWindow(QMainWindow):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self.setWindowTitle("Photokiller")
        self.config = config
        
        # Set window to fullscreen by default
        self.setWindowState(Qt.WindowFullScreen)
        
        # Set window styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
        """)
        
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Title
        title = QLabel("PHOTOKILLER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Professional Photobooth")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                font-size: 18px;
                font-family: Arial, sans-serif;
                margin-bottom: 40px;
            }
        """)
        layout.addWidget(subtitle)
        
        # Button container
        button_container = QFrame()
        button_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        button_layout = QVBoxLayout(button_container)
        button_layout.setSpacing(20)
        
        # Take 1 Photo button
        self.take_one_btn = QPushButton("TAKE 1 PHOTO")
        self.take_one_btn.setFixedSize(400, 80)
        self.take_one_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 40px;
                font-size: 20px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }
            QPushButton:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }
        """)
        
        # Take 3 Photos button
        self.take_three_btn = QPushButton("TAKE 3 PHOTOS")
        self.take_three_btn.setFixedSize(400, 80)
        self.take_three_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                border-radius: 40px;
                font-size: 20px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }
            QPushButton:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }
        """)
        
        button_layout.addWidget(self.take_one_btn, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.take_three_btn, alignment=Qt.AlignCenter)
        layout.addWidget(button_container)
        
        # Camera thread for preview (only if preview is enabled)
        self.camera_thread = None
        if not config.camera.skip_preview:
            self.camera_thread = CameraPreview(self.config)
            self.camera_thread.frame_ready.connect(self._on_camera_frame)
            self.camera_thread.error_occurred.connect(self._on_camera_error)
            self.camera_thread.start()
        
        # Countdown widget
        self.countdown = CountdownWidget(self)
        self.countdown.move(
            (self.width() - self.countdown.width()) // 2,
            (self.height() - self.countdown.height()) // 2
        )
        
        # Review widget
        self.review = ReviewWidget(self)
        self.review.move(
            (self.width() - self.review.width()) // 2,
            (self.height() - self.review.height()) // 2
        )
        
        # Countdown timer
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self._update_countdown)
        self.countdown_seconds = 0
        
        # Store the last composed photo path
        self.last_composed_photo = None
        
        self.setCentralWidget(central)
        
        # Add status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                color: white;
                background-color: rgba(0, 0, 0, 100);
                font-size: 14px;
                font-family: Arial, sans-serif;
            }
        """)

        self.take_one_btn.clicked.connect(lambda: self._start_session(1))
        self.take_three_btn.clicked.connect(lambda: self._start_session(3))
        
        # Connect review buttons
        self.review.discard_btn.clicked.connect(self._discard_photo)
        self.review.print_btn.clicked.connect(self._print_photo)

    def _on_camera_frame(self, frame):
        """Handle camera frame updates"""
        # Update countdown widget preview if it's visible
        if self.countdown.isVisible():
            self.countdown.set_preview_frame(frame)

    def _on_camera_error(self, error_msg):
        """Handle camera errors"""
        print(f"Camera error: {error_msg}")
        # Could show error in countdown widget if needed

    def _update_preview(self, frame: QImage) -> None:
        """Update preview during capture (callback for capture functions)"""
        if self.countdown.isVisible():
            self.countdown.set_preview_frame(frame)

    def _start_countdown(self, num_shots: int) -> None:
        """Start countdown before capture"""
        self.countdown_seconds = self.config.session.countdown_seconds
        self.countdown.countdown_label.setText(str(self.countdown_seconds))
        self.countdown.message_label.setText("Get ready!")
        self.countdown.show()
        self.countdown.raise_()
        
        # Disable buttons during countdown
        self.take_one_btn.setEnabled(False)
        self.take_three_btn.setEnabled(False)
        
        # Store session info for multi-capture
        self._pending_session = num_shots
        self._current_shot = 0
        self._captured_photos = []
        # Create one session directory to hold all shots and the composed print
        self._session_dir = make_session_dir(self.config.session.save_dir)
        
        self.countdown_timer.start(1000)  # Update every second
        self._update_countdown()

    def _update_countdown(self) -> None:
        """Update countdown display"""
        if self.countdown_seconds > 0:
            self.countdown.countdown_label.setText(str(self.countdown_seconds))
            self.countdown_seconds -= 1
        else:
            self.countdown_timer.stop()
            self._execute_single_capture()

    def _execute_single_capture(self) -> None:
        """Execute a single photo capture"""
        if not hasattr(self, '_pending_session'):
            return
            
        num_shots = self._pending_session
        current_shot = self._current_shot
        
        self.statusBar().showMessage(f"Capturing shot {current_shot + 1} of {num_shots}...")
        
        # Capture the current frame
        if self.config.camera.mode == "webcam":
            if self.camera_thread and not self.config.camera.skip_preview:
                frame = self.camera_thread.get_current_frame()
                if frame is not None:
                    out_path = self._session_dir / f"shot_{current_shot + 1}.jpg"
                    success = frame.save(str(out_path), "JPG", quality=95)
                    if success:
                        self._captured_photos.append(out_path)
                        print(f"Captured shot {current_shot + 1}: {out_path}")
                    else:
                        print(f"Failed to save shot {current_shot + 1}")
                else:
                    print(f"Failed to get frame for shot {current_shot + 1}")
            else:
                # Fall back to unified capture function for single shot
                photos = capture_photos(
                    self.config.camera.mode,
                    self.config.camera.device_index,
                    tuple(self.config.camera.resolution),
                    1,  # Single shot
                    self._session_dir,
                    0,  # No delay needed
                    self._update_preview,  # Preview callback
                )
                if photos:
                    self._captured_photos.extend(photos)
        else:
            # DSLR capture using unified interface
            print(f"Using DSLR capture for shot {current_shot + 1}...")
            photos = capture_photos(
                self.config.camera.mode,
                self.config.camera.device_index,
                tuple(self.config.camera.resolution),
                1,  # Single shot
                self._session_dir,
                0,  # No delay needed
                None,  # DSLR doesn't support preview
            )
            if photos:
                self._captured_photos.extend(photos)
                print(f"DSLR captured shot {current_shot + 1}: {photos[0]}")
            else:
                print(f"DSLR failed to capture shot {current_shot + 1}")

        # Check if we need more shots
        if current_shot + 1 < num_shots:
            # More shots needed - start countdown for next shot
            self._current_shot += 1
            self._start_shot_countdown()
        else:
            # All shots captured - compose and show review
            self._finish_capture_session()

    def _start_shot_countdown(self) -> None:
        """Start countdown for the next shot in a multi-capture session"""
        self.countdown_seconds = int(self.config.session.capture_delay)
        self.countdown.countdown_label.setText(str(self.countdown_seconds))
        self.countdown.message_label.setText(f"Get ready for shot {self._current_shot + 1}!")
        self.countdown.show()
        self.countdown.raise_()
        
        self.countdown_timer.start(1000)  # Update every second

    def _finish_capture_session(self) -> None:
        """Finish the capture session and show review"""
        if not self._captured_photos:
            self.statusBar().showMessage("No photos captured - showing error review", 5000)
            self._show_error_review("No photos were captured.\nPlease check camera connection.")
            self.take_one_btn.setEnabled(True)
            self.take_three_btn.setEnabled(True)
            return

        self.statusBar().showMessage("Composing layout...")
        
        # Compose the final layout into the session directory
        base_mask_path = None
        background_mask_path = None
        
        if self.config.layout.base_mask:
            base_mask_path = Path(self.config.layout.base_mask)
            if not base_mask_path.is_absolute():
                base_mask_path = Path.cwd() / base_mask_path
                
        if self.config.layout.background_mask:
            background_mask_path = Path(self.config.layout.background_mask)
            if not background_mask_path.is_absolute():
                background_mask_path = Path.cwd() / background_mask_path
            print(f"Background mask path resolved to: {background_mask_path}")
            print(f"Background mask file exists: {background_mask_path.exists()}")
        else:
            print("No background_mask configured in config")
                
        composed = compose_10x15_strip(self._captured_photos, self._session_dir / "print.jpg", base_mask_path, background_mask_path)
        print(f"Composed layout: {composed}")
        
        # Store the composed photo path and show review
        self.last_composed_photo = composed
        self._show_review(composed)
        
        # Clean up session data
        delattr(self, '_pending_session')
        delattr(self, '_current_shot')
        delattr(self, '_captured_photos')
        # keep _session_dir for reference to print path; it will be reset on next session

    def _show_review(self, photo_path) -> None:
        """Show the review screen with the composed photo"""
        # Show review widget
        self.review.set_photo(str(photo_path))
        self.review.show()
        self.review.raise_()
        
        # Re-enable main buttons
        self.take_one_btn.setEnabled(True)
        self.take_three_btn.setEnabled(True)

    def _show_error_review(self, error_message: str) -> None:
        """Show review screen with error message instead of photo"""
        # Show review widget with error
        self.review.set_error_message(error_message)
        self.review.show()
        self.review.raise_()
        
        # Re-enable main buttons
        self.take_one_btn.setEnabled(True)
        self.take_three_btn.setEnabled(True)

    def _discard_photo(self) -> None:
        """Discard the photo and return to main screen"""
        # Hide review widget
        self.review.hide()
        
        # Hide countdown widget to ensure we return to main screen
        self.countdown.hide()
        
        self.statusBar().showMessage("Photo discarded (kept on disk)", 3000)
        # Do NOT delete composed image; just clear reference
        self.last_composed_photo = None

    def _print_photo(self) -> None:
        """Print the photo"""
        if not self.last_composed_photo:
            return
            
        try:
            self.statusBar().showMessage("Printing...")
            print_file_cups(self.last_composed_photo, self.config.printing.printer_name, self.config.printing.copies)
            self.statusBar().showMessage("Photo printed successfully!", 5000)
            print(f"Printed: {self.last_composed_photo}")
        except Exception as exc:
            print(f"Print error: {exc}")
            self.statusBar().showMessage(f"Print error: {exc}", 7000)
        
        # Hide review and countdown, return to main screen
        self.review.hide()
        self.countdown.hide()
        self.last_composed_photo = None

    def _start_session(self, num_shots: int) -> None:
        """Start photo session with countdown"""
        self._start_countdown(num_shots)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window resize to keep widgets centered"""
        super().resizeEvent(event)
        if hasattr(self, 'countdown'):
            self.countdown.move(
                (self.width() - self.countdown.width()) // 2,
                (self.height() - self.countdown.height()) // 2
            )
        if hasattr(self, 'review'):
            # Update review widget to cover full window
            self.review.setGeometry(0, 0, self.width(), self.height())
            # Make container cover full review widget
            self.review.container.setGeometry(0, 0, self.review.width(), self.review.height())

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.camera_thread:
            self.camera_thread.stop()
            self.camera_thread.wait(2000)
        super().closeEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # type: ignore[override]
        if event.key() == Qt.Key_Escape:
            # If review is showing, hide it first
            if hasattr(self, 'review') and self.review.isVisible():
                self._discard_photo()
                return
            self.close()
            return
        elif event.key() == Qt.Key_F11:
            # Toggle fullscreen mode (useful for development)
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
            return
        super().keyPressEvent(event)


