#!/usr/bin/env python3
"""
Build script for creating Audio Converter Pro executable
Creates a standalone .exe file with all dependencies bundled
"""

import os
import sys
import shutil
import subprocess
import zipfile
import requests
from pathlib import Path


def print_step(message):
    """Print a build step message"""
    print(f"\n{'=' * 60}")
    print(f"► {message}")
    print('=' * 60)


def check_requirements():
    """Check if required tools are installed"""
    print_step("Checking build requirements")

    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7+ is required")
        return False
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Check for required packages
    required_packages = {
        'PyQt5': 'PyQt5',
        'yt_dlp': 'yt-dlp',
        'ffmpeg': 'ffmpeg-python',
        'PyInstaller': 'pyinstaller'
    }

    missing_packages = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install " + ' '.join(missing_packages))
        return False

    return True


def download_ffmpeg():
    """Download FFmpeg binaries for Windows"""
    print_step("Downloading FFmpeg binaries")

    ffmpeg_dir = Path("ffmpeg_bin")
    ffmpeg_dir.mkdir(exist_ok=True)

    # Check if already downloaded
    if (ffmpeg_dir / "ffmpeg.exe").exists() and (ffmpeg_dir / "ffprobe.exe").exists():
        print("✓ FFmpeg binaries already present")
        return True

    print("Downloading FFmpeg for Windows...")

    # Download FFmpeg (using a reliable source)
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

    try:
        # Download the zip file
        response = requests.get(ffmpeg_url, stream=True)
        response.raise_for_status()

        zip_path = ffmpeg_dir / "ffmpeg.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        print("✓ Downloaded FFmpeg archive")

        # Extract the required executables
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file in zip_ref.namelist():
                if file.endswith('ffmpeg.exe') or file.endswith('ffprobe.exe'):
                    # Extract to temp location
                    zip_ref.extract(file, ffmpeg_dir / "temp")
                    # Move to main directory
                    extracted_path = ffmpeg_dir / "temp" / file
                    target_path = ffmpeg_dir / os.path.basename(file)
                    shutil.move(str(extracted_path), str(target_path))

        # Cleanup
        zip_path.unlink()
        shutil.rmtree(ffmpeg_dir / "temp", ignore_errors=True)

        print("✓ Extracted FFmpeg executables")
        return True

    except Exception as e:
        print(f"❌ Failed to download FFmpeg: {e}")
        print("\nPlease manually download FFmpeg and place ffmpeg.exe and ffprobe.exe in the 'ffmpeg_bin' folder")
        return False


def create_spec_file():
    """Create PyInstaller spec file with custom settings"""
    print_step("Creating PyInstaller spec file")

    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['audio_converter_gui.py'],
    pathex=[],
    binaries=[
        ('ffmpeg_bin/ffmpeg.exe', '.'),
        ('ffmpeg_bin/ffprobe.exe', '.')
    ],
    datas=[],
    hiddenimports=[
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.downloader',
        'yt_dlp.postprocessor',
        'ffmpeg',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AudioConverterPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want a console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # Add your icon file here
    version='version_info.txt'  # Version information file
)
'''

    with open('audio_converter.spec', 'w') as f:
        f.write(spec_content)

    print("✓ Created audio_converter.spec")


def create_version_info():
    """Create version information file for Windows"""
    print_step("Creating version information")

    version_info = '''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AudioTools'),
        StringStruct(u'FileDescription', u'Audio Converter Pro - Convert audio files and YouTube videos'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'AudioConverterPro'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2024'),
        StringStruct(u'OriginalFilename', u'AudioConverterPro.exe'),
        StringStruct(u'ProductName', u'Audio Converter Pro'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)'''

    with open('version_info.txt', 'w') as f:
        f.write(version_info)

    print("✓ Created version_info.txt")


def create_icon():
    """Create a simple icon for the application"""
    print_step("Creating application icon")

    # Create a simple icon using PIL if available, otherwise skip
    try:
        from PIL import Image, ImageDraw

        # Create a 256x256 icon
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw a gradient background
        for i in range(256):
            color = int(102 + (118 - 102) * i / 256)
            draw.rectangle([0, i, 256, i + 1], fill=(color, 126, 234, 255))

        # Draw a musical note symbol
        draw.ellipse([80, 100, 120, 140], fill='white')
        draw.rectangle([115, 60, 125, 140], fill='white')
        draw.ellipse([136, 100, 176, 140], fill='white')
        draw.rectangle([171, 60, 181, 140], fill='white')
        draw.rectangle([115, 60, 181, 70], fill='white')

        # Save as ICO
        img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
        print("✓ Created icon.ico")

    except ImportError:
        print("⚠ PIL not available, skipping icon creation")
        print("  You can add your own icon.ico file")


def build_executable():
    """Build the executable using PyInstaller"""
    print_step("Building executable with PyInstaller")

    # Run PyInstaller
    cmd = [
        sys.executable,
        '-m', 'PyInstaller',
        '--clean',
        '--noconfirm',
        'audio_converter.spec'
    ]

    print("Running PyInstaller...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print("✓ Build completed successfully!")

        # Find the output executable
        exe_path = Path('dist') / 'AudioConverterPro.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✓ Executable created: {exe_path}")
            print(f"  Size: {size_mb:.1f} MB")

        return True
    else:
        print("❌ Build failed!")
        print("\nError output:")
        print(result.stderr)
        return False


def create_portable_package():
    """Create a portable package with the executable and required files"""
    print_step("Creating portable package")

    # Create package directory
    package_dir = Path("AudioConverterPro_Portable")
    package_dir.mkdir(exist_ok=True)

    # Copy executable
    exe_source = Path('dist') / 'AudioConverterPro.exe'
    if exe_source.exists():
        shutil.copy2(exe_source, package_dir / 'AudioConverterPro.exe')
        print("✓ Copied executable")

    # Create README
    readme_content = """Audio Converter Pro - Portable Edition
=====================================

Features:
- Convert audio files between formats (MP3, OGG, WAV, FLAC, etc.)
- Download and convert YouTube videos
- Batch conversion support
- Game modding presets (HOI4, Stellaris, etc.)

Usage:
1. Double-click AudioConverterPro.exe to start
2. Drag and drop audio files or paste YouTube URLs
3. Select output format and settings
4. Click "Convert All Files"

The converted files will be saved to your Downloads/AudioConverter folder by default.

Enjoy!
"""

    with open(package_dir / 'README.txt', 'w') as f:
        f.write(readme_content)

    print("✓ Created README.txt")

    # Create a zip file
    zip_name = 'AudioConverterPro_Portable.zip'
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in package_dir.iterdir():
            zipf.write(file, file.name)

    print(f"✓ Created portable package: {zip_name}")


def cleanup():
    """Clean up build artifacts"""
    print_step("Cleaning up")

    dirs_to_remove = ['build', '__pycache__']
    files_to_remove = ['audio_converter.spec', 'version_info.txt']

    for dir_name in dirs_to_remove:
        if Path(dir_name).exists():
            shutil.rmtree(dir_name, ignore_errors=True)
            print(f"✓ Removed {dir_name}/")

    for file_name in files_to_remove:
        if Path(file_name).exists():
            Path(file_name).unlink()
            print(f"✓ Removed {file_name}")


def main():
    """Main build process"""
    print("\n🔨 Audio Converter Pro - Build Script")
    print("This will create a standalone .exe file\n")

    # Check requirements
    if not check_requirements():
        print("\n❌ Build failed: Missing requirements")
        return 1

    # Download FFmpeg for Windows
    if sys.platform == 'win32':
        if not download_ffmpeg():
            print("\n⚠ Warning: FFmpeg binaries not included")
            print("The executable will require FFmpeg to be installed on the target system")

    # Create required files
    create_version_info()
    create_icon()
    create_spec_file()

    # Build the executable
    if not build_executable():
        print("\n❌ Build failed!")
        return 1

    # Create portable package
    create_portable_package()

    # Cleanup
    cleanup()

    print("\n✅ Build completed successfully!")
    print("\nOutput files:")
    print("  - dist/AudioConverterPro.exe (standalone executable)")
    print("  - AudioConverterPro_Portable.zip (portable package)")
    print("\nThe executable can be distributed and run on any Windows PC!")

    return 0


if __name__ == '__main__':
    sys.exit(main())