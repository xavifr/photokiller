{
  description = "Photokiller - Modern photobooth application for Raspberry Pi";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        
        # Python environment (uv manages dependencies)
        pythonEnv = pkgs.python311;
        
        # System dependencies for running the app
        systemDeps = with pkgs; [
          # CUPS printing support
          cups
          cups-filters
          
          # OpenGL and graphics
          libGL
          libglvnd
          mesa
          
          # X11 and XCB libraries
          xorg.libX11
          xorg.libXext
          xorg.libXrender
          xorg.libXrandr
          xorg.libXinerama
          xorg.libXcursor
          xorg.libXfixes
          xorg.libXdamage
          xorg.libXcomposite
          xorg.libXtst
          xorg.libXi
          xorg.libXxf86vm
          xorg.libXv
          xorg.libXpm
          xorg.libXaw
          xorg.libXmu
          xorg.libXfont2
          xorg.libXft
          xorg.libXdmcp
          xorg.libXau
          xorg.libxcb
          xorg.xcbutil
          xorg.xcbutilcursor
          xorg.xcbutilerrors
          xorg.xcbutilimage
          xorg.xcbutilkeysyms
          xorg.xcbutilrenderutil
          xorg.xcbutilwm
          
          # Qt6 dependencies
          qt6.qtbase
          qt6.qtdeclarative
          qt6.qtmultimedia
          qt6.qtwayland
          
          # Camera support
          gphoto2
          libgphoto2
          libusb1
          
          # Image processing
          libjpeg
          libpng
          libtiff
          libwebp
          
          # Audio support (for Qt multimedia)
          alsa-lib
          pulseaudio
          
          # Font support
          fontconfig
          freetype
          
          # SSL/TLS support
          openssl
          
          # Other system libraries
          glib
          gtk3
          pango
          cairo
          gdk-pixbuf
          atk
          at-spi2-atk
          dbus
          udev
          
          # Development tools (optional, for debugging)
          pkg-config
          gdb
          strace
        ];
        
        # Runtime environment
        runtimeEnv = pkgs.buildEnv {
          name = "photokiller-runtime";
          paths = systemDeps;
        };
        
      in {
        # Development shell
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pythonEnv
            runtimeEnv
            pkgs.uv
          ];
          
          shellHook = ''
            echo "Photokiller development environment loaded!"
            echo "Python: $(python --version)"
            echo "CUPS: $(cups-config --version 2>/dev/null || echo 'Not available')"
            echo "OpenGL: $(glxinfo | grep 'OpenGL version' | head -1 || echo 'Not available')"
            
            # Set environment variables for runtime
            export LD_LIBRARY_PATH="${runtimeEnv}/lib:$LD_LIBRARY_PATH"
            export PKG_CONFIG_PATH="${runtimeEnv}/lib/pkgconfig:$PKG_CONFIG_PATH"
            export QT_PLUGIN_PATH="${runtimeEnv}/lib/qt6/plugins"
            export QT_QPA_PLATFORM_PLUGIN_PATH="${runtimeEnv}/lib/qt6/plugins/platforms"
            
            # CUPS environment
            export CUPS_DATADIR="${runtimeEnv}/share/cups"
            export CUPS_FILTERDIR="${runtimeEnv}/lib/cups/filter"
            
            echo "Environment variables set for runtime dependencies"
          '';
        };
        
        # Runtime package
        packages.default = pkgs.stdenv.mkDerivation {
          pname = "photokiller-runtime";
          version = "1.0.0";
          
          src = ./.;
          
          buildInputs = [ runtimeEnv pkgs.uv ];
          
          # Override build phase to do nothing (we don't need to build anything)
          buildPhase = "echo 'No build phase needed'";
          
          installPhase = ''
            mkdir -p $out/bin $out/app
            cp -r app $out/app
            cp pyproject.toml $out/
            cp .python-version $out/
            cp uv.lock $out/ 2>/dev/null || true
            
            # Create virtual environment structure (dependencies will be installed at runtime)
            cd $out
            
            # Create launcher script that uses the virtual environment
            cat > $out/bin/photokiller <<EOF
            #!${pkgs.bash}/bin/bash
            export LD_LIBRARY_PATH="${runtimeEnv}/lib:\$LD_LIBRARY_PATH"
            export PKG_CONFIG_PATH="${runtimeEnv}/lib/pkgconfig:\$PKG_CONFIG_PATH"
            export QT_PLUGIN_PATH="${runtimeEnv}/lib/qt6/plugins"
            export QT_QPA_PLATFORM_PLUGIN_PATH="${runtimeEnv}/lib/qt6/plugins/platforms"
            export CUPS_DATADIR="${runtimeEnv}/share/cups"
            export CUPS_FILTERDIR="${runtimeEnv}/lib/cups/filter"
            
            # Set up uv environment in user-writable location
            USER_HOME=\$(eval echo ~\$USER)
            export VIRTUAL_ENV="\$USER_HOME/.photokiller/.uv"
            export UV_CACHE_DIR="\$USER_HOME/.photokiller/.uv-cache"

            mkdir -p "\$VIRTUAL_ENV"
            mkdir -p "\$UV_CACHE_DIR"
            cd $out

            # Install dependencies if not already present
            echo "Installing dependencies with uv..."
            ${pkgs.uv}/bin/uv sync --frozen 
            
            # Run the app
            exec ${pkgs.uv}/bin/uv run --frozen -m app "\$@"
            EOF
            
            chmod +x $out/bin/photokiller
          '';
          
          meta = {
            description = "Runtime environment for Photokiller photobooth app";
            platforms = [ "x86_64-linux" "aarch64-linux" "armv7l-linux" ];
          };
        };
        
        # App definition
        apps.default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/photokiller";
        };
        
      }
    );
}
