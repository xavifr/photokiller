# Photokiller

A lean, modern photobooth application for Raspberry Pi 4 with DSLR support, designed for professional use with minimal configuration.

## 🎯 **Project Overview**

Photokiller is a streamlined alternative to pibooth, built with modern dependencies and a focus on simplicity. It's designed for one-time use scenarios where you need a reliable, fast photobooth without complex configuration.

## 🏗️ **Architecture Decisions**

### **Technology Stack**
- **Language**: Python 3.10+ (modern, well-supported)
- **GUI Framework**: PySide6 (Qt6) - mature, great for touch interfaces, easy packaging
- **Camera Handling**: 
  - Webcam: OpenCV (`cv2.VideoCapture`) for USB cameras
  - DSLR: `gphoto2` CLI binary (more reliable on RPi than Python bindings)
- **Image Processing**: Pillow (PIL) for compositing and overlays
- **Configuration**: Pydantic for validation with sensible defaults
- **Printing**: pycups for CUPS integration on Linux
- **Build System**: PyInstaller for standalone executables
- **Package Management**: uv for fast dependency resolution

### **Why These Choices?**
- **PySide6 over Tkinter**: Better touch support, modern UI capabilities, professional appearance
- **gphoto2 CLI over Python bindings**: More reliable on Raspberry Pi, no ABI/compilation issues
- **OpenCV for webcam**: Industry standard, excellent performance, wide camera support
- **Pydantic**: Type safety, automatic validation, great defaults system

## 🎨 **UI/UX Design Decisions**

### **Fullscreen Experience**
- **Main Window**: Fullscreen by default for immersive photobooth experience
- **Preview Hidden**: Camera preview only shows during capture (configurable)
- **Large Buttons**: 400x80px buttons for easy touch/button interaction
- **Dark Theme**: Professional dark gradient background (#2c3e50 to #34495e)

### **Workflow Design**
1. **Main Screen**: Clean interface with two prominent buttons (Take 1 Photo, Take 3 Photos)
2. **Initial Countdown**: Fullscreen overlay with live preview and countdown (3-2-1)
3. **Multi-Capture Sequence**: For 3+ photos, each shot gets its own countdown with preview
4. **Capture**: Photos taken one by one with configurable delays between shots
5. **Review**: Fullscreen overlay showing composed photo with DISCARD/PRINT options
6. **Actions**: Simple decision point - keep or discard

### **Multi-Capture System**
- **Individual Countdowns**: Each shot has its own countdown (configurable via `capture_delay`)
- **Live Preview**: Camera feed visible during all countdowns for perfect positioning
- **Sequential Capture**: Shots taken one at a time, not simultaneously
- **Progress Feedback**: Status messages show current shot progress (e.g., "Shot 2 of 3")
- **Configurable Timing**: Adjust delay between shots in `config.json`

### **Button Layout**
- **Take 1 Photo**: Blue gradient button (primary action)
- **Take 3 Photos**: Red gradient button (secondary action)
- **DISCARD**: Gray button (safe, non-destructive)
- **PRINT**: Green button (positive action)

## 📸 **Camera & Capture Decisions**

### **Dual Camera Support**
- **Webcam Mode**: Live preview, real-time capture, OpenCV-based
- **DSLR Mode**: No preview (configurable), gphoto2 capture, professional quality
- **Skip Preview Option**: `camera.skip_preview` for DSLRs without live view

### **Unified Capture Architecture**
- **Consistent Interface**: Both webcam and DSLR use identical function signatures
- **Dependency Injection**: Preview callback passed to capture functions
- **Modular Design**: Camera modules handle their own preview logic
- **Easy Extension**: Add new camera types by implementing the same interface

### **Capture Strategy**
- **Webcam**: Uses existing camera thread, captures current frame with preview callback
- **DSLR**: Spawns gphoto2 process, downloads images with configurable delays
- **Error Handling**: Graceful fallback when camera unavailable
- **Session Management**: Automatic timestamped directories

### **Image Processing**
- **Resolution**: Configurable (default: 1280x720)
- **Format**: JPEG with 95% quality
- **Storage**: Organized by timestamp in `sessions/` directory

## 🖨️ **Layout & Printing Decisions**

### **Photo Layouts**
- **Single Photo**: Centered with margins, optimized for 10x15cm paper
- **3-Photo Strip**: Vertical arrangement with equal spacing
- **Dimensions**: 1200x1800px (300 DPI equivalent)
- **Composition**: Automatic scaling while maintaining aspect ratio

### **Printing System**
- **CUPS Integration**: Native Linux printing support
- **Printer Selection**: Configurable printer name or system default
- **Paper Size**: 10x15cm (100x150mm) optimized for Canon Selphy
- **Error Handling**: Graceful fallback when printing fails

## ⚙️ **Configuration Decisions**

### **Minimal Configuration**
- **Single File**: `config/config.json` with all settings
- **Sensible Defaults**: App works out-of-the-box
- **Validation**: Pydantic ensures config integrity
- **Hot Reload**: No restart required for most changes

### **Key Config Options**
```json
{
  "camera": {
    "mode": "webcam" | "dslr",
    "skip_preview": false,
    "resolution": [1280, 720]
  },
  "session": {
    "shots": 1 | 3,
    "countdown_seconds": 3,
    "capture_delay": 1.0
  },
  "printing": {
    "enabled": true,
    "printer_name": "",
    "copies": 1,
    "paper_size_mm": [100, 150]
  },
  "gpio": {
    "enabled": false,
    "button_shoot_pin": 17,
    "button_print_pin": 27
  }
}
```

**New Features:**
- **`capture_delay`**: Configurable delay between multiple shots (default: 1.0 seconds)
- **Integrated Preview**: Camera preview appears in countdown view for better positioning
- **Distinct Preview Background**: Dark blue background with white border for clear image boundaries

## 🔧 **Development & Build Decisions**

### **Project Structure**
```
photokiller/
├── app/                    # Main application code
│   ├── capture/           # Camera modules (webcam, DSLR)
│   ├── compose/           # Photo layout composition
│   ├── print/             # CUPS printing integration
│   ├── ui/                # PySide6 user interface
│   └── utils/             # Helper functions
├── config/                 # Configuration files
├── main.py                 # Entry point for PyInstaller
└── build_appimage.py       # Build automation
```

### **Build System**
- **PyInstaller**: Creates standalone executables
- **One-File Mode**: Single binary for easy distribution
- **Data Inclusion**: Config directory bundled with executable
- **Cross-Platform**: Ready for Linux AppImage creation

### **Dependency Management**
- **uv**: Fast Python package manager
- **Virtual Environments**: Isolated development environment
- **Locked Dependencies**: Reproducible builds

## 🚀 **Deployment Decisions**

### **Raspberry Pi Optimization**
- **ARM Compatibility**: OpenCV headless for ARM processors
- **System Dependencies**: Minimal external requirements
- **Performance**: Optimized for RPi4 performance characteristics
- **Fullscreen**: Kiosk mode for professional installations

### **Distribution**
- **AppImage**: Single-file distribution for Linux
- **Standalone Binary**: No Python installation required
- **Config Bundling**: Settings included in executable
- **Portable**: Works on any compatible Linux system

## 🎮 **User Experience Decisions**

### **Accessibility**
- **Large UI Elements**: Easy to see and interact
- **Clear Feedback**: Status messages and visual indicators
- **Error Handling**: User-friendly error messages
- **Keyboard Shortcuts**: F11 (fullscreen toggle), ESC (close)

### **Professional Use**
- **Kiosk Mode**: Fullscreen prevents accidental exits
- **Session Management**: Organized file storage
- **Quality Output**: High-resolution photo composition
- **Reliable Capture**: Robust error handling

## 🔮 **Future Considerations**

### **Potential Enhancements**
- **GPIO Integration**: Hardware button support for RPi
- **Network Sharing**: QR codes for photo sharing
- **Custom Layouts**: User-defined photo arrangements
- **Video Support**: Short video clips or GIFs
- **Cloud Integration**: Automatic backup and sharing

### **Maintenance**
- **Dependency Updates**: Regular security and feature updates
- **Platform Support**: Monitor Qt6 and Python compatibility
- **Performance**: Optimize for newer Raspberry Pi models

## 📋 **Installation & Usage**

### **Quick Start**
```bash
# Install system dependencies
sudo apt install gphoto2 libgphoto2-dev libcups2-dev

# Setup Python environment
uv venv
source .venv/bin/activate
uv pip install -e .

# Run the app
python -m app
```

### **Build AppImage**
```bash
# Build standalone executable
python build_appimage.py

# Run the binary
./dist/photokiller
```

## 🎯 **Design Philosophy**

Photokiller follows these core principles:
1. **Simplicity**: Do one thing well - take photos and print them
2. **Reliability**: Robust error handling and graceful degradation
3. **Performance**: Optimized for Raspberry Pi hardware
4. **Professional**: Clean, modern interface suitable for events
5. **Maintainable**: Clear code structure and minimal dependencies

This project represents a focused approach to photobooth software - removing complexity while maintaining professional quality and reliability.
