#!/usr/bin/env python3
"""
Build script for Photokiller AppImage
Supports both local builds and ARMv7 builds for Raspberry Pi
"""

import os
import subprocess
import sys
import platform
from pathlib import Path

def detect_architecture():
    """Detect the current system architecture"""
    machine = platform.machine()
    if machine.startswith('arm'):
        return 'armv7' if 'armv7' in machine else 'arm64'
    elif machine == 'x86_64':
        return 'x86_64'
    else:
        return machine

def build_appimage(target_arch=None):
    """Build the AppImage using PyInstaller"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    current_arch = detect_architecture()
    target_arch = target_arch or current_arch
    
    print(f"Building Photokiller AppImage...")
    print(f"Current architecture: {current_arch}")
    print(f"Target architecture: {target_arch}")
    
    if target_arch != current_arch:
        print(f"⚠️  Cross-compiling from {current_arch} to {target_arch}")
        print("Note: PyInstaller cross-compilation is limited. Using Docker ARM emulation.")
        return build_with_docker_arm(target_arch)
    
    # Local build for same architecture
    return build_local()

def build_local():
    """Build locally for the current architecture"""
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name=photokiller",
        "--onefile",
        "--windowed",  # No console window on Linux
        "--add-data=config:config",  # Include config directory
        "--icon=assets/icon.png" if (Path.cwd() / "assets/icon.png").exists() else "",
        "main.py"  # Use the root-level entry point
    ]
    
    # Remove empty arguments
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running local build: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Local build successful!")
        print(f"Output: {result.stdout}")
        
        # Check if the binary was created
        dist_dir = Path.cwd() / "dist"
        if dist_dir.exists():
            binaries = list(dist_dir.glob("photokiller*"))
            if binaries:
                binary_path = binaries[0]
                print(f"\nAppImage created: {binary_path}")
                print(f"Size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
                print(f"Architecture: {detect_architecture()}")
                
                # Check if it's executable
                if os.access(binary_path, os.X_OK):
                    print("✅ Binary is executable")
                else:
                    print("⚠️  Binary is not executable (may need chmod +x)")
                    
            else:
                print("No binary found in dist/ directory")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Local build failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        return False
    except FileNotFoundError:
        print("PyInstaller not found. Please install it first:")
        print("uv pip install pyinstaller")
        return False

def build_with_docker_arm(target_arch):
    """Build for ARM using Docker with QEMU emulation"""
    print(f"Building for {target_arch} using Docker ARM emulation...")
    
    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker not found. Please install Docker first.")
        print("For Ubuntu/Debian: sudo apt install docker.io")
        print("For other systems: https://docs.docker.com/get-docker/")
        return False
    
    # Check if QEMU is available for ARM emulation
    try:
        subprocess.run(["docker", "run", "--rm", "--platform", "linux/arm/v7", "hello-world"], 
                      check=True, capture_output=True)
    except subprocess.CalledProcessError:
        print("❌ ARM emulation not available. Installing QEMU...")
        try:
            subprocess.run(["docker", "run", "--rm", "--privileged", "multiarch/qemu-user-static", 
                          "--reset", "-p", "yes"], check=True)
            print("✅ QEMU installed. Testing ARM emulation...")
            subprocess.run(["docker", "run", "--rm", "--platform", "linux/arm/v7", "hello-world"], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError:
            print("❌ Failed to install QEMU. ARM emulation not available.")
            return False
    
    # Try alternative base image approach first
    print("Trying alternative ARMv7 base image approach...")
    try:
        # Use a more compatible base image
        dockerfile_content = f"""
FROM --platform=linux/arm/v7 python:3.11-slim

# Install essential system dependencies only
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libffi-dev \\
    libssl-dev \\
    libjpeg-dev \\
    libpng-dev \\
    libtiff-dev \\
    libgphoto2-dev \\
    libcups2-dev \\
    libcupsimage2-dev \\
    libusb-1.0-0-dev \\
    curl \\
    git \\
    pkg-config \\
    # Minimal X11 runtime libraries for PySide6
    libxcb1 \\
    libxcb-cursor0 \\
    libxcb-keysyms1 \\
    libxcb-image0 \\
    libxcb-icccm4 \\
    libxcb-sync1 \\
    libxcb-xinerama0 \\
    libxcb-randr0 \\
    libxcb-render0 \\
    libxcb-shape0 \\
    libxcb-xfixes0 \\
    libxcb-util1 \\
    && rm -rf /var/lib/apt
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    /lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install all Python dependencies (including PySide6)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Install PyInstaller
RUN uv pip install pyinstaller

# Copy source code
COPY . .

# Build the application
RUN pyinstaller --onefile --windowed --add-data=config:config main.py
"""
        
        dockerfile_path = Path.cwd() / "Dockerfile.arm"
        dockerfile_path.write_text(dockerfile_content)
        
        # Build Docker image
        build_cmd = [
            "docker", "build", 
            "--platform", "linux/arm/v7",
            "-f", "Dockerfile.arm",
            "-t", "photokiller-arm-build",
            "."
        ]
        
        print(f"Running: {' '.join(build_cmd)}")
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        print("Docker build successful!")
        
        # Create output directory
        dist_dir = Path.cwd() / "dist" / target_arch
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy binary from container
        copy_cmd = [
            "docker", "create", "--name", "temp-container", "photokiller-arm-build"
        ]
        subprocess.run(copy_cmd, check=True)
        
        try:
            subprocess.run([
                "docker", "cp", "temp-container:/app/dist/photokiller", str(dist_dir / "photokiller")
            ], check=True)
            
            # Make binary executable
            binary_path = dist_dir / "photokiller"
            os.chmod(binary_path, 0o755)
            
            print(f"\n✅ ARM build successful!")
            print(f"Binary created: {binary_path}")
            print(f"Size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Verify architecture
            try:
                result = subprocess.run(["file", str(binary_path)], check=True, capture_output=True, text=True)
                print(f"Architecture: {result.stdout.strip()}")
            except FileNotFoundError:
                print("Note: 'file' command not available to verify architecture")
            
        finally:
            # Clean up container
            subprocess.run(["docker", "rm", "temp-container"], check=True)
        
        # Clean up Dockerfile
        dockerfile_path.unlink()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Alternative build failed: {e}")
        if 'dockerfile_path' in locals() and dockerfile_path.exists():
            dockerfile_path.unlink()
        
        # Fall back to original approach
        print("Falling back to original build approach...")
        return _build_with_original_dockerfile(target_arch)

def _build_with_original_dockerfile(target_arch):
    """Original Docker build approach"""
    # Create Dockerfile for ARM build
    dockerfile_content = f"""
FROM --platform=linux/arm/v7 python:3.11-slim

# Install essential system dependencies only
RUN apt-get update && apt-get install -y \\
    build-essential \\
    libffi-dev \\
    libssl-dev \\
    libjpeg-dev \\
    libpng-dev \\
    libtiff-dev \\
    libgphoto2-dev \\
    libcups2-dev \\
    libcupsimage2-dev \\
    libusb-1.0-0-dev \\
    curl \\
    git \\
    pkg-config \\
    # Minimal X11 runtime libraries for PySide6
    libxcb1 \\
    libxcb-cursor0 \\
    libxcb-keysyms1 \\
    libxcb-image0 \\
    libxcb-icccm4 \\
    libxcb-sync1 \\
    libxcb-xinerama0 \\
    libxcb-randr0 \\
    libxcb-render0 \\
    libxcb-shape0 \\
    libxcb-xfixes0 \\
    libxcb-util1 \\
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy requirements and install all Python dependencies (including PySide6)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Install PyInstaller
RUN uv pip install pyinstaller

# Copy source code
COPY . .

# Build the application
RUN pyinstaller --onefile --windowed --add-data=config:config main.py

# The binary will be in dist/photokiller
"""
    
    dockerfile_path = Path.cwd() / "Dockerfile.arm"
    dockerfile_path.write_text(dockerfile_content)
    
    print("Building Docker image for ARM...")
    try:
        # Build Docker image
        build_cmd = [
            "docker", "build", 
            "--platform", "linux/arm/v7",
            "-f", "Dockerfile.arm",
            "-t", "photokiller-arm-build",
            "."
        ]
        
        print(f"Running: {' '.join(build_cmd)}")
        result = subprocess.run(build_cmd, check=True, capture_output=True, text=True)
        print("Docker build successful!")
        
        # Create output directory
        dist_dir = Path.cwd() / "dist" / target_arch
        dist_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy binary from container
        copy_cmd = [
            "docker", "create", "--name", "temp-container", "photokiller-arm-build"
        ]
        subprocess.run(copy_cmd, check=True)
        
        try:
            subprocess.run([
                "docker", "cp", "temp-container:/app/dist/photokiller", str(dist_dir / "photokiller")
            ], check=True)
            
            # Make binary executable
            binary_path = dist_dir / "photokiller"
            os.chmod(binary_path, 0o755)
            
            print(f"\n✅ ARM build successful!")
            print(f"Binary created: {binary_path}")
            print(f"Size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
            
            # Verify architecture
            try:
                result = subprocess.run(["file", str(binary_path)], check=True, capture_output=True, text=True)
                print(f"Architecture: {result.stdout.strip()}")
            except FileNotFoundError:
                print("Note: 'file' command not available to verify architecture")
            
        finally:
            # Clean up container
            subprocess.run(["docker", "rm", "temp-container"], check=True)
        
        # Clean up Dockerfile
        dockerfile_path.unlink()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Docker build failed: {e}")
        if dockerfile_path.exists():
            dockerfile_path.unlink()
        return False

def build_for_raspberry_pi():
    """Build specifically for Raspberry Pi (ARMv7)"""
    print("Building for Raspberry Pi (ARMv7)...")
    return build_appimage(target_arch='armv7')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--raspberry-pi':
        success = build_for_raspberry_pi()
    else:
        success = build_appimage()
    
    if not success:
        sys.exit(1)
