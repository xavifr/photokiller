.PHONY: build clean run install-deps

# Build the AppImage
build: install-deps
	@echo "Building Photokiller AppImage..."
	python build_appimage.py

# Build using spec file (alternative method)
build-spec: install-deps
	@echo "Building using spec file..."
	pyinstaller photokiller.spec

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.spec
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

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
	@echo "  build-spec - Build using PyInstaller spec file"
	@echo "  clean      - Clean build artifacts"
	@echo "  install-deps - Install build dependencies"
	@echo "  run        - Run app in development mode"
	@echo "  help       - Show this help message"
