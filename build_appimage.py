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
        print("Note: Cross-compilation may not work perfectly. Consider building on the target device.")
    
    # PyInstaller command
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--clean",
        "--name=photokiller",
        "--onefile",
        "--windowed",  # No console window on Linux
        "--add-data=config:config",  # Include config directory
        "--icon=assets/icon.png" if (project_root / "assets/icon.png").exists() else "",
        "main.py"  # Use the root-level entry point
    ]
    
    # Add architecture-specific options
    if target_arch == 'armv7':
        # For ARMv7 builds, we might need additional options
        cmd.extend([
            "--target-architecture=armv7",
            "--distpath=dist/armv7"
        ])
    elif target_arch == 'arm64':
        cmd.extend([
            "--target-architecture=arm64",
            "--distpath=dist/arm64"
        ])
    
    # Remove empty arguments
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Output: {result.stdout}")
        
        # Check if the binary was created
        dist_dir = project_root / "dist"
        if target_arch != current_arch:
            dist_dir = dist_dir / target_arch
        
        if dist_dir.exists():
            binaries = list(dist_dir.glob("photokiller*"))
            if binaries:
                binary_path = binaries[0]
                print(f"\nAppImage created: {binary_path}")
                print(f"Size: {binary_path.stat().st_size / (1024*1024):.1f} MB")
                print(f"Architecture: {target_arch}")
                
                # Check if it's executable
                if os.access(binary_path, os.X_OK):
                    print("✅ Binary is executable")
                else:
                    print("⚠️  Binary is not executable (may need chmod +x)")
                    
            else:
                print("No binary found in dist/ directory")
        
    except subprocess.CalledProcessError as e:
        print(f"Build failed with exit code {e.returncode}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("PyInstaller not found. Please install it first:")
        print("uv pip install pyinstaller")
        sys.exit(1)

def build_for_raspberry_pi():
    """Build specifically for Raspberry Pi ARMv7"""
    print("Building for Raspberry Pi (ARMv7)...")
    build_appimage(target_arch='armv7')

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--raspberry-pi':
        build_for_raspberry_pi()
    else:
        build_appimage()
