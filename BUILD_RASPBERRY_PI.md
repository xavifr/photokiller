# Building Photokiller for Raspberry Pi

This guide explains how to build Photokiller for Raspberry Pi 4 running Raspbian (ARMv7).

## 🚀 **Quick Start**

### **Option 1: Cross-Compilation (Recommended)**
```bash
# Build ARMv7 binary on x86_64 development machine
make build-raspberry-pi

# Or use the build script directly
python build_appimage.py --raspberry-pi
```

### **Option 2: Build on Raspberry Pi**
```bash
# Clone and build directly on Raspberry Pi
git clone <your-repo-url>
cd photokiller
python3 -m venv .venv
source .venv/bin/activate
uv pip install -e .
uv pip install pyinstaller
pyinstaller --onefile --windowed --add-data=config:config main.py
```

## 📋 **Prerequisites**

### **For Cross-Compilation (x86_64 host):**
- **Docker**: Required for ARM emulation
- **Python 3.10+**: Development environment
- **uv**: Python package manager

### **For Direct Build (Raspberry Pi):**
- **Raspbian OS** (latest version recommended)
- **Python 3.10+** (should be pre-installed)
- **Git** (for cloning the repository)
- **Build tools** (for compiling dependencies)

### **Install Dependencies on Raspberry Pi:**
```bash
sudo apt update
sudo apt install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libgphoto2-dev \
    libcups2-dev \
    libcupsimage2-dev \
    libusb-1.0-0-dev \
    git \
    curl
```

## 🔧 **Cross-Compilation (Recommended)**

### **How It Works:**
1. **Docker Container**: Creates ARMv7 environment on x86_64 host
2. **QEMU Emulation**: Runs ARM instructions through emulation
3. **Native Build**: Compiles Python packages for ARMv7
4. **PyInstaller**: Creates ARMv7 binary
5. **Output**: Binary copied to `dist/armv7/photokiller`

### **Build Commands:**
```bash
# Using Makefile
make build-raspberry-pi

# Using build script
python build_appimage.py --raspberry-pi

# Manual Docker build
docker run --rm -v $(pwd):/app -w /app --platform linux/arm/v7 python:3.11-slim bash -c "
    apt-get update && apt-get install -y build-essential libffi-dev libssl-dev libjpeg-dev libpng-dev libtiff-dev libgphoto2-dev libcups2-dev libcupsimage2-dev libusb-1.0-0-dev curl
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH=\"/root/.cargo/bin:\$PATH\"
    uv sync --frozen
    uv pip install pyinstaller
    pyinstaller --onefile --windowed --add-data=config:config main.py
"
```

### **Cross-Compilation Benefits:**
- ✅ **Fast Development**: Build on powerful development machine
- ✅ **Consistent Environment**: Same build process every time
- ✅ **No RPi Setup**: Don't need to configure Raspberry Pi for development
- ✅ **Parallel Development**: Multiple developers can build for same target

### **ARMv7 Compatibility Notes:**
- **PySide6**: No pre-built wheels for ARMv7, compiled from source
- **Build Time**: PySide6 compilation adds 10-20 minutes to first build
- **Dependencies**: Additional system packages required for Qt compilation
- **Memory**: Qt compilation requires significant RAM (2GB+ recommended)

## 🐳 **Docker Build Details**

### **What Happens During Build:**
1. **Platform Detection**: Detects x86_64 host, ARMv7 target
2. **QEMU Setup**: Automatically installs ARM emulation
3. **Dockerfile Generation**: Creates ARM-specific Dockerfile
4. **Dependency Installation**: Installs system and Python packages
5. **PyInstaller Build**: Creates ARMv7 binary
6. **Cleanup**: Removes temporary files and containers

### **Build Time Expectations:**
- **First Build**: 15-30 minutes (downloads base images and dependencies)
- **Subsequent Builds**: 5-15 minutes (uses cached layers)
- **Binary Size**: 50-150 MB depending on dependencies

### **Troubleshooting Docker Builds:**
```bash
# Check Docker status
docker --version
docker system info

# Test ARM emulation
docker run --rm --platform linux/arm/v7 hello-world

# Clean up if needed
docker system prune -a
docker builder prune
```

## 🏗️ **Building on Raspberry Pi**

### **Setup Development Environment:**
```bash
# Clone repository
git clone <your-repo-url>
cd photokiller

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install uv (if not available via apt)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.cargo/env

# Install dependencies
uv pip install -e .
uv pip install pyinstaller
```

### **Build Commands:**
```bash
# Option 1: Using the build script
python build_appimage.py

# Option 2: Using make
make build

# Option 3: Direct PyInstaller
pyinstaller --onefile --windowed --add-data=config:config main.py
```

### **Build Output:**
- **Location**: `dist/photokiller`
- **Architecture**: ARMv7 (native)
- **Size**: 50-150 MB
- **Permissions**: Executable

## ✅ **Verification & Testing**

### **Check Binary Architecture:**
```bash
# On development machine
file dist/armv7/photokiller
# Should show: ELF 32-bit LSB executable, ARM, version 1 (SYSV), dynamically linked...

# On Raspberry Pi
file photokiller
# Should show: ELF 32-bit LSB executable, ARM, version 1 (SYSV), dynamically linked...
```

### **Test Execution:**
```bash
# Make executable if needed
chmod +x photokiller

# Test run
./photokiller
```

### **Check Dependencies:**
```bash
# List shared library dependencies
ldd photokiller

# Check for missing libraries
ldd photokiller | grep "not found"
```

## 🚨 **Common Issues & Solutions**

### **1. Missing Shared Libraries:**
```bash
# Install missing libraries
sudo apt install libpython3.x-dev

# Check what's missing
ldd photokiller | grep "not found"
```

### **2. gphoto2 Not Found:**
```bash
# Install gphoto2 CLI
sudo apt install gphoto2

# Test detection
gphoto2 --auto-detect
```

### **3. CUPS Printing Issues:**
```bash
# Ensure CUPS is running
sudo systemctl status cups
sudo systemctl enable cups

# Check printer status
lpstat -p
```

### **4. Permission Issues:**
```bash
# Add user to video group for camera access
sudo usermod -a -G video $USER
# Log out and back in

# Check groups
groups $USER
```

### **5. Docker Build Failures:**
```bash
# Check Docker logs
docker logs <container-id>

# Verify ARM emulation
docker run --rm --platform linux/arm/v7 python:3.11-slim python -c "import platform; print(platform.machine())"
# Should output: armv7l
```

## 📦 **Deployment**

### **Copy to Raspberry Pi:**
```bash
# From development machine
scp dist/armv7/photokiller pi@raspberrypi.local:/home/pi/

# Or use USB drive, network share, etc.
```
### **Setup on Raspberry Pi:**
```bash
# Make executable
chmod +x photokiller

# Test run
./photokiller

# Create desktop shortcut (optional)
cp photokiller ~/Desktop/
```

### **System Integration:**
```bash
# Add to PATH (optional)
sudo cp photokiller /usr/local/bin/

# Create systemd service (optional)
sudo nano /etc/systemd/system/photokiller.service
```

## 📊 **Performance Notes**

### **Build Performance:**
- **Cross-Compilation**: 15-45 minutes (PySide6 compilation adds time)
- **Direct Build**: 10-30 minutes on Raspberry Pi 4
- **Binary Size**: 50-150 MB depending on dependencies

### **Runtime Performance:**
- **Memory Usage**: 100-300 MB RAM
- **Startup Time**: 5-15 seconds on first run, faster on subsequent runs
- **Camera Response**: <100ms for webcam, 1-3s for DSLR preview

### **Storage Requirements:**
- **Binary**: 50-150 MB
- **Sessions**: 1-10 MB per photo session
- **Total**: <200 MB for typical installation

## 🔍 **Advanced Configuration**

### **Custom Build Options:**
```bash
# Build with debug symbols
pyinstaller --onefile --windowed --debug=all --add-data=config:config main.py

# Build without console
pyinstaller --onefile --noconsole --add-data=config:config main.py

# Build with specific Python version
docker run --rm -v $(pwd):/app -w /app --platform linux/arm/v7 python:3.11-slim bash -c "..."
```

### **Optimization Flags:**
```bash
# Strip debug symbols (smaller binary)
pyinstaller --onefile --windowed --strip --add-data=config:config main.py

# UPX compression (smaller binary, slower startup)
pyinstaller --onefile --windowed --upx-dir=/path/to/upx --add-data=config:config main.py
```

## 🆘 **Support & Troubleshooting**

### **If You Encounter Issues:**
1. **Check Build Logs**: Look for error messages in build output
2. **Verify Dependencies**: Ensure all system packages are installed
3. **Test Components**: Verify gphoto2, CUPS, and camera access separately
4. **Check Permissions**: Ensure user has access to camera and printer
5. **Review Configuration**: Verify `config.json` settings

### **Getting Help:**
- **Build Issues**: Check Docker logs and system requirements
- **Runtime Issues**: Test individual components (camera, printer)
- **Performance Issues**: Monitor system resources during operation

### **Debug Mode:**
```bash
# Run with debug output
./photokiller 2>&1 | tee debug.log

# Check system logs
dmesg | tail
journalctl -u cups -f
```

## 🎯 **Best Practices**

### **Development Workflow:**
1. **Test Locally**: Verify functionality on development machine
2. **Cross-Compile**: Use Docker for ARM builds
3. **Test on Target**: Verify binary works on Raspberry Pi
4. **Iterate**: Fix issues and rebuild

### **Deployment Checklist:**
- [ ] Binary is executable (`chmod +x`)
- [ ] Architecture is correct (`file` command)
- [ ] Dependencies are available (`ldd` command)
- [ ] Camera access works (`gphoto2 --auto-detect`)
- [ ] Printer is configured (`lpstat -p`)
- [ ] App runs without errors

### **Maintenance:**
- **Regular Updates**: Keep system packages updated
- **Dependency Updates**: Monitor Python package updates
- **Performance Monitoring**: Check resource usage over time
- **Backup Configuration**: Keep `config.json` backed up

This comprehensive guide should help you successfully build and deploy Photokiller on Raspberry Pi, whether you choose cross-compilation or direct building on the target device.
