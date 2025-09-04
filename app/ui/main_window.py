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
    def __init__(self, parent=None, skip_preview=False):
        super().__init__(parent)
        
        # Make it cover the entire main window
        self.setGeometry(0, 0, parent.width(), parent.height())
        
        # Get screen dimensions for responsive design
        screen = self.screen()
        screen_width = screen.size().width()
        screen_height = screen.size().height()
        
        # Calculate responsive dimensions
        is_small_screen = screen_width <= 800 or screen_height <= 600
        
        if is_small_screen:
            # Small screen (800x480, 1024x768, etc.)
            title_font_size = 28
            countdown_font_size = 72
            message_font_size = 16
            margins = 20
            spacing = 15
            countdown_size = 100
        else:
            # Large screen (1920x1080, etc.)
            title_font_size = 36
            countdown_font_size = 96
            message_font_size = 20
            margins = 30
            spacing = 20
            countdown_size = 160
        
        # Create a proper body container that covers the entire widget
        self.body_container = QFrame(self)
        self.body_container.setGeometry(0, 0, self.width(), self.height())
        self.body_container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border: none;
            }
        """)
        
        # Use a simple layout within the body container
        layout = QVBoxLayout(self.body_container)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(spacing)
        
        # Title - smaller and less prominent
        title = QLabel("Get Ready!")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {title_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: {spacing}px;
            }}
        """)
        layout.addWidget(title)
        
        # Camera preview area - only show if preview is enabled
        if not skip_preview:
            self.preview_label = QLabel("Camera preview will appear here")
            self.preview_label.setAlignment(Qt.AlignCenter)
            self.preview_label.setStyleSheet("""
                QLabel {
                    background-color: rgba(0, 0, 0, 100);
                    border: 2px solid rgba(255, 255, 255, 0.3);
                    border-radius: 10px;
                    color: white;
                    font-size: 16px;
                }
            """)
            layout.addWidget(self.preview_label, 1)  # Give it stretch priority
        else:
            self.preview_label = None
        
        # Countdown display - simplified
        countdown_layout = QHBoxLayout()
        countdown_layout.setSpacing(spacing)
        
        # Countdown number
        self.countdown_label = QLabel("3")
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {countdown_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: {countdown_size//2}px;
                padding: 15px;
                min-width: {countdown_size}px;
                min-height: {countdown_size}px;
            }}
        """)
        
        # Countdown message
        self.message_label = QLabel("Get ready!")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {message_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
        """)
        
        countdown_layout.addWidget(self.countdown_label, alignment=Qt.AlignCenter)
        countdown_layout.addWidget(self.message_label, alignment=Qt.AlignCenter)
        layout.addLayout(countdown_layout)
        
        self.hide()
    
    def set_preview_frame(self, frame):
        """Set the preview frame if preview is enabled"""
        if self.preview_label is not None:
            # Convert QImage to QPixmap and scale to fit the preview label
            pixmap = QPixmap.fromImage(frame)
            if not pixmap.isNull():
                # Scale the pixmap to fit the preview label while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.preview_label.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled_pixmap)
    
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle resize to cover full window"""
        super().resizeEvent(event)
        # Resize to cover the entire parent window
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        # Make body container cover full countdown widget
        if hasattr(self, 'body_container'):
            self.body_container.setGeometry(0, 0, self.width(), self.height())


class ReviewWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Make it cover the entire main window
        self.setGeometry(0, 0, parent.width(), parent.height())
        
        # Get screen dimensions for responsive design
        screen = self.screen()
        screen_width = screen.size().width()
        screen_height = screen.size().height()
        
        # Calculate responsive dimensions
        is_small_screen = screen_width <= 800 or screen_height <= 600
        
        if is_small_screen:
            # Small screen (800x480, 1024x768, etc.)
            title_font_size = 24
            button_font_size = 14
            button_width = 120
            button_height = 40
            panel_width = 280  # Increased to ensure title fits + margins + padding
            margins = 20
            spacing = 15
        else:
            # Large screen (1920x1080, etc.)
            title_font_size = 32
            button_font_size = 18
            button_width = 160
            button_height = 50
            panel_width = 360  # Increased to ensure title fits + margins + padding
            margins = 30
            spacing = 20
        
        # Store panel width for consistent reference
        self.panel_width = panel_width
        
        # Create a proper body container that covers the entire widget
        self.body_container = QFrame(self)
        self.body_container.setGeometry(0, 0, self.width(), self.height())
        self.body_container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border: none;
            }
        """)
        
        # Use horizontal layout: controls on left, image on right
        layout = QHBoxLayout(self.body_container)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(margins)
        
        # Left side controls container
        controls_container = QFrame()
        controls_container.setFixedWidth(panel_width)
        controls_container.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 200);
                border-radius: 15px;
                padding: 15px;
            }
        """)
        
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setSpacing(spacing)
        controls_layout.setContentsMargins(15, 15, 15, 15)  # Reduced margins for more content space
        
        # Title
        title = QLabel("Review")
        title.setAlignment(Qt.AlignCenter)
        title.setMinimumWidth(button_width + 20)  # Ensure title has enough width
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {title_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: {spacing}px;
            }}
        """)
        controls_layout.addWidget(title)
        
        # Add some spacing
        controls_layout.addSpacing(spacing)
        
        # Print button (primary action)
        self.print_btn = QPushButton("PRINT")
        self.print_btn.setFixedSize(button_width, button_height)
        self.print_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #229954);
                color: white;
                border: none;
                border-radius: {button_height//2}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2ecc71, stop:1 #27ae60);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #229954, stop:1 #1e8449);
            }}
        """)
        controls_layout.addWidget(self.print_btn, alignment=Qt.AlignCenter)
        
        # Add spacing between buttons
        controls_layout.addSpacing(spacing)
        
        # Discard button (secondary action)
        self.discard_btn = QPushButton("DISCARD")
        self.discard_btn.setFixedSize(button_width, button_height)
        self.discard_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #95a5a6, stop:1 #7f8c8d);
                color: white;
                border: none;
                border-radius: {button_height//2}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #bdc3c7, stop:1 #95a5a6);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7f8c8d, stop:1 #6c7b7d);
            }}
        """)
        controls_layout.addWidget(self.discard_btn, alignment=Qt.AlignCenter)
        
        # Add the controls container to the left side
        layout.addWidget(controls_container)
        
        # Photo display - takes remaining space (full height)
        self.photo_label = QLabel()
        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 100);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        layout.addWidget(self.photo_label, 1)  # Give it stretch priority
        
        self.hide()
        
        # Store the current photo path for refresh purposes
        self._current_photo_path = None
    
    def showEvent(self, event) -> None:  # type: ignore[override]
        """Handle show event to ensure photo is properly sized"""
        super().showEvent(event)
        # Refresh the photo when the widget becomes visible
        if self._current_photo_path:
            QTimer.singleShot(50, lambda: self.set_photo(self._current_photo_path))
        
        # Debug info about panel dimensions
        if hasattr(self, 'body_container'):
            panel_width = 280 if self.width() <= 800 else 360
            print(f"Review panel width: {panel_width}px, total width: {self.width()}px")
    
    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle resize to cover full window"""
        super().resizeEvent(event)
        # Resize to cover the entire parent window
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        # Make body container cover full review widget
        if hasattr(self, 'body_container'):
            self.body_container.setGeometry(0, 0, self.width(), self.height())
        # Update photo label size
        self._update_photo_label_size()

    def set_photo(self, photo_path: str) -> None:
        """Set the photo to display in the review widget, resized to fit the UI."""
        # Store the photo path for refresh purposes
        self._current_photo_path = photo_path
        
        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            self.photo_label.setText("Failed to load photo")
            return

        # Calculate the available space for the photo
        # Account for the left panel width and margins
        total_width = self.width()
        total_height = self.height()
        
        # Get the panel width and margins
        if hasattr(self, 'body_container'):
            margins = self.body_container.layout().contentsMargins()
            # Use the stored panel width from __init__
            panel_width = self.panel_width
            
            # Calculate available space for photo
            available_width = total_width - panel_width - margins.left() - margins.right()
            available_height = total_height - margins.top() - margins.bottom()
            
            # Account for photo label's own padding and border
            photo_padding = 20  # 10px padding on each side
            photo_border = 4    # 2px border on each side
            available_width -= (photo_padding + photo_border)
            available_height -= (photo_padding + photo_border)
        else:
            # Fallback if body_container not available
            available_width = total_width - 300  # Conservative estimate
            available_height = total_height - 60  # Conservative estimate
        
        # Ensure minimum sizes
        available_width = max(100, available_width)
        available_height = max(100, available_height)
        
        # Debug info
        print(f"Photo sizing: total={total_width}x{total_height}, panel={panel_width}, available={available_width}x{available_height}")
        print(f"Margins: left={margins.left()}, right={margins.right()}, top={margins.top()}, bottom={margins.bottom()}")
        print(f"Photo label size: {self.photo_label.size()}")
        
        # Scale the image to fit the available space while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            available_width, 
            available_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # Debug info after scaling
        print(f"Scaled pixmap size: {scaled_pixmap.size()}")
        
        # Set the scaled image
        self.photo_label.setPixmap(scaled_pixmap)
    
    def _update_photo_label_size(self) -> None:
        """Update the photo label size to match available space"""
        if hasattr(self, 'body_container') and hasattr(self, 'panel_width'):
            margins = self.body_container.layout().contentsMargins()
            total_width = self.width()
            total_height = self.height()
            
            # Calculate available space for photo
            available_width = total_width - self.panel_width - margins.left() - margins.right()
            available_height = total_height - margins.top() - margins.bottom()
            
            # Account for photo label's own padding and border
            photo_padding = 20  # 10px padding on each side
            photo_border = 4    # 2px border on each side
            available_width -= (photo_padding + photo_border)
            available_height -= (photo_padding + photo_border)
            
            # Set minimum size for photo label
            self.photo_label.setMinimumSize(available_width, available_height)
            print(f"Updated photo label size: {available_width}x{available_height}")
    
    def refresh_photo(self) -> None:
        """Refresh the photo display after resize events."""
        if self._current_photo_path:
            # Small delay to ensure the widget has been resized
            QTimer.singleShot(100, lambda: self.set_photo(self._current_photo_path))
    
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
        
        # Get screen dimensions for responsive design
        screen = self.screen()
        screen_width = screen.size().width()
        screen_height = screen.size().height()
        
        # Calculate responsive dimensions
        is_small_screen = screen_width <= 800 or screen_height <= 600
        
        # Responsive sizing
        if is_small_screen:
            # Small screen (800x480, 1024x768, etc.)
            title_font_size = 32
            subtitle_font_size = 14
            button_font_size = 16
            button_width = min(300, screen_width - 100)
            button_height = 60
            margins = 30
            spacing = 20
            title_margin = 15
            subtitle_margin = 25
        else:
            # Large screen (1920x1080, etc.)
            title_font_size = 48
            subtitle_font_size = 18
            button_font_size = 20
            button_width = 400
            button_height = 80
            margins = 50
            spacing = 30
            title_margin = 20
            subtitle_margin = 40
        
        # Set window styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c3e50, stop:1 #34495e);
            }
        """)
        
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setSpacing(spacing)
        layout.setContentsMargins(margins, margins, margins, margins)
        
        # Title
        title = QLabel("PHOTOKILLER")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {title_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
                margin-bottom: {title_margin}px;
            }}
        """)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Professional Photobooth")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: #ecf0f1;
                font-size: {subtitle_font_size}px;
                font-family: Arial, sans-serif;
                margin-bottom: {subtitle_margin}px;
            }}
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
        button_layout.setSpacing(spacing)
        
        # Take 1 Photo button
        self.take_one_btn = QPushButton("TAKE 1 PHOTO")
        self.take_one_btn.setFixedSize(button_width, button_height)
        self.take_one_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: {button_height//2}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #ecf0f1;
            }}
        """)
        
        # Take 3 Photos button
        self.take_three_btn = QPushButton("TAKE 3 PHOTOS")
        self.take_three_btn.setFixedSize(button_width, button_height)
        self.take_three_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e74c3c, stop:1 #c0392b);
                color: white;
                border: none;
                border-radius: {button_height//2}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ec7063, stop:1 #e74c3c);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #c0392b, stop:1 #a93226);
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #ecf0f1;
            }}
        """)
        
        button_layout.addWidget(self.take_one_btn, alignment=Qt.AlignCenter)
        button_layout.addWidget(self.take_three_btn, alignment=Qt.AlignCenter)
        
        # Re-print button (only enabled when there's a last photo)
        self.reprint_btn = QPushButton("RE-PRINT LAST PHOTO")
        self.reprint_btn.setFixedSize(button_width, button_height)
        self.reprint_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f39c12, stop:1 #e67e22);
                color: white;
                border: none;
                border-radius: {button_height//2}px;
                font-size: {button_font_size}px;
                font-weight: bold;
                font-family: Arial, sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7dc6f, stop:1 #f39c12);
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #e67e22, stop:1 #d35400);
            }}
            QPushButton:disabled {{
                background: #95a5a6;
                color: #ecf0f1;
            }}
        """)
        self.reprint_btn.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.reprint_btn, alignment=Qt.AlignCenter)
        
        layout.addWidget(button_container)
        
        # Camera thread for preview (only if preview is enabled)
        self.camera_thread = None
        if not config.camera.skip_preview:
            self.camera_thread = CameraPreview(self.config)
            self.camera_thread.frame_ready.connect(self._on_camera_frame)
            self.camera_thread.error_occurred.connect(self._on_camera_error)
            self.camera_thread.start()
        
        # Countdown widget
        self.countdown = CountdownWidget(self, skip_preview=config.camera.skip_preview)
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
        
        # Connect re-print button
        self.reprint_btn.clicked.connect(self._reprint_last_photo)
        
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
        self.reprint_btn.setEnabled(False)  # Disable re-print during capture
        
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
                    self._session_dir,
                    self._update_preview,  # Preview callback
                )
                if photos:
                    # Ensure consistent naming for multiple captures
                    old_path = photos[0]
                    new_path = self._session_dir / f"shot_{current_shot + 1}.jpg"
                    if old_path != new_path:
                        old_path.rename(new_path)
                        self._captured_photos.append(new_path)
                        print(f"Captured shot {current_shot + 1}: {new_path}")
                    else:
                        self._captured_photos.append(old_path)
                        print(f"Captured shot {current_shot + 1}: {old_path}")
        else:
            # DSLR capture using unified interface
            print(f"Using DSLR capture for shot {current_shot + 1}...")
            photos = capture_photos(
                self.config.camera.mode,
                self.config.camera.device_index,
                tuple(self.config.camera.resolution),
                self._session_dir,
                None,  # DSLR doesn't support preview
            )
            if photos:
                # DSLR saves as "shot.jpg", rename to "shot_X.jpg" for proper sequencing
                old_path = photos[0]
                new_path = self._session_dir / f"shot_{current_shot + 1}.jpg"
                if old_path != new_path:
                    old_path.rename(new_path)
                    self._captured_photos.append(new_path)
                    print(f"DSLR captured shot {current_shot + 1}: {new_path}")
                else:
                    self._captured_photos.append(old_path)
                    print(f"DSLR captured shot {current_shot + 1}: {old_path}")
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
        # Ensure countdown widget is visible
        self.countdown.show()
        self.countdown.raise_()
        
        # Show a brief transition message
        self.countdown.message_label.setText(f"Moving to shot {self._current_shot + 1}...")
        self.countdown.countdown_label.setText("→")
        
        # Brief pause to show the transition
        QTimer.singleShot(1500, self._start_next_shot_countdown)
    
    def _start_next_shot_countdown(self) -> None:
        """Start the actual countdown for the next shot"""
        self.countdown_seconds = int(self.config.session.capture_delay)
        self.countdown.countdown_label.setText(str(self.countdown_seconds))
        self.countdown.message_label.setText(f"Get ready for shot {self._current_shot + 1}!")
        
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
            print(f"Base mask path resolved to: {base_mask_path}")

                
        if self.config.layout.background_mask:
            background_mask_path = Path(self.config.layout.background_mask)
            if not background_mask_path.is_absolute():
                background_mask_path = Path.cwd() / background_mask_path
            print(f"Background mask path resolved to: {background_mask_path}")

                
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
        
        # Enable re-print button since we have a photo to review
        self.reprint_btn.setEnabled(True)

    def _show_error_review(self, error_message: str) -> None:
        """Show review screen with error message instead of photo"""
        # Show review widget with error
        self.review.set_error_message(error_message)
        self.review.show()
        self.review.raise_()
        
        # Re-enable main buttons
        self.take_one_btn.setEnabled(True)
        self.take_three_btn.setEnabled(True)
        
        # Disable re-print button since there's no photo to re-print
        self.reprint_btn.setEnabled(False)

    def _discard_photo(self) -> None:
        """Discard the photo and return to main screen"""
        # Hide review widget
        self.review.hide()
        
        # Hide countdown widget to ensure we return to main screen
        self.countdown.hide()
        
        self.statusBar().showMessage("Photo discarded (kept on disk)", 3000)
        # Keep the photo reference for re-printing - don't clear it
        # self.last_composed_photo = None
        
        # Re-print button remains enabled since photo is still available for re-printing

    def _print_photo(self) -> None:
        """Print the photo"""
        if not self.last_composed_photo:
            self.statusBar().showMessage("No photo to print", 3000)
            return

        if not self.config.printing.enabled:
            self.statusBar().showMessage("Printing is disabled in config", 3000)
            return
            
        try:
            self.statusBar().showMessage("Printing...")
            print_file_cups(self.last_composed_photo, self.config.printing.printer_name, self.config.printing.copies, self.config.printing.paper_name)
            self.statusBar().showMessage("Photo printed successfully!", 5000)
            print(f"Printed: {self.last_composed_photo}")
        except Exception as exc:
            print(f"Print error: {exc}")
            self.statusBar().showMessage(f"Print error: {exc}", 7000)
        
        # Hide review and countdown, return to main screen
        self.review.hide()
        self.countdown.hide()
        # Keep the photo reference for re-printing - don't set to None
        # self.last_composed_photo = None
        
        # Re-print button remains enabled since photo is still available

    def _reprint_last_photo(self) -> None:
        """Re-print the last captured photo"""
        if not self.last_composed_photo:
            self.statusBar().showMessage("No photo to re-print", 3000)
            return

        if not self.config.printing.enabled:
            self.statusBar().showMessage("Printing is disabled in config", 3000)
            return
            
        try:
            self.statusBar().showMessage("Re-printing...")
            print_file_cups(self.last_composed_photo, self.config.printing.printer_name, self.config.printing.copies, self.config.printing.paper_name)
            self.statusBar().showMessage("Photo re-printed successfully!", 5000)
            print(f"Re-printed: {self.last_composed_photo}")
        except Exception as exc:
            print(f"Re-print error: {exc}")
            self.statusBar().showMessage(f"Re-print error: {exc}", 7000)

    def _start_session(self, num_shots: int) -> None:
        """Start photo session with countdown"""
        self._start_countdown(num_shots)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window resize to keep widgets centered and update responsive sizing"""
        super().resizeEvent(event)
        
        # Update responsive sizing for all widgets
        self._update_responsive_sizing()
        
        if hasattr(self, 'countdown'):
            self.countdown.move(
                (self.width() - self.countdown.width()) // 2,
                (self.height() - self.countdown.height()) // 2
            )
            # Update countdown body container
            if hasattr(self.countdown, 'body_container'):
                self.countdown.body_container.setGeometry(0, 0, self.countdown.width(), self.countdown.height())
        if hasattr(self, 'review'):
            # Update review widget to cover full window
            self.review.setGeometry(0, 0, self.width(), self.height())
            # Make body container cover full review widget
            if hasattr(self.review, 'body_container'):
                self.review.body_container.setGeometry(0, 0, self.review.width(), self.review.height())
            # Refresh the photo display to fit the new size
            if hasattr(self.review, 'refresh_photo'):
                self.review.refresh_photo()

    def _update_responsive_sizing(self) -> None:
        """Update sizing for all widgets based on current screen dimensions"""
        # Get current screen dimensions
        screen = self.screen()
        screen_width = screen.size().width()
        screen_height = screen.size().height()
        
        # Calculate responsive dimensions
        is_small_screen = screen_width <= 800 or screen_height <= 600
        
        if is_small_screen:
            # Small screen (800x480, 1024x768, etc.)
            button_width = min(300, screen_width - 100)
            button_height = 60
        else:
            # Large screen (1920x1080, etc.)
            button_width = 400
            button_height = 80
        
        # Update button sizes if they exist
        if hasattr(self, 'take_one_btn'):
            self.take_one_btn.setFixedSize(button_width, button_height)
        if hasattr(self, 'take_three_btn'):
            self.take_three_btn.setFixedSize(button_width, button_height)
        if hasattr(self, 'reprint_btn'):
            self.reprint_btn.setFixedSize(button_width, button_height)

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



