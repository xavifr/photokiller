#!/usr/bin/env python3
"""
Build script for Photokiller AppImage
"""

import os
import subprocess
import sys
from pathlib import Path

def build_appimage():
    """Build the AppImage using PyInstaller"""
    
    # Ensure we're in the right directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("Building Photokiller AppImage...")
    
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
    
    # Remove empty arguments
    cmd = [arg for arg in cmd if arg]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Build successful!")
        print(f"Output: {result.stdout}")
        
        # Check if the binary was created
        dist_dir = project_root / "dist"
        if dist_dir.exists():
            binaries = list(dist_dir.glob("photokiller*"))
            if binaries:
                print(f"\nAppImage created: {binaries[0]}")
                print(f"Size: {binaries[0].stat().st_size / (1024*1024):.1f} MB")
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

if __name__ == "__main__":
    build_appimage()
