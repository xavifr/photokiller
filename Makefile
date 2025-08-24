.PHONY: build clean run install-deps

# Build the AppImage
build: install-deps
	@echo "Building Photokiller AppImage..."
	python build_appimage.py

# Build for Raspberry Pi (ARMv7)
build-raspberry-pi: install-deps
	@echo "Building Photokiller AppImage for Raspberry Pi (ARMv7)..."
	python build_appimage.py --raspberry-pi

# Build using spec file (alternative method)
build-spec: install-deps
	@echo "Building using spec file..."
	pyinstaller photokiller.spec

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.spec
	rm -rf .venv/ venv/ env/
	rm -rf photokiller.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	rm -rf .uv/
	rm -rf .cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
# Clean everything including sessions
clean-all: clean
	@echo "Cleaning sessions and all temporary files..."
	rm -rf sessions/


# Install dependencies
install-deps:
	@echo "Installing build dependencies..."
	uv pip install pyinstaller

# Run the app in development mode
run:
	@echo "Running Photokiller in development mode..."
	python -m app

# Show help
help:
	@echo "Available targets:"
	@echo "  build      - Build AppImage using build script"
	@echo "  build-raspberry-pi - Build AppImage for Raspberry Pi (ARMv7)"
	@echo "  build-spec - Build using PyInstaller spec file"
	@echo "  clean      - Clean build artifacts, virtual envs, and cache files"
	@echo "  clean-all  - Clean everything including sessions and all temp files"
	@echo "  install-deps - Install build dependencies"
	@echo "  run        - Run app in development mode"
	@echo "  help       - Show this help message"
