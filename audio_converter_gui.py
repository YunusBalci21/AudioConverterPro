#!/usr/bin/env python3
"""
Audio Converter Pro - Desktop GUI Version
A standalone audio converter with YouTube download support
"""

import sys
import subprocess
import os
import json
import threading
import queue
from pathlib import Path
from datetime import datetime

# GUI imports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# Audio processing imports
import yt_dlp
import ffmpeg

from ffmpeg._run import Error as FFmpegError


class ConversionThread(QThread):
    """Thread for handling audio conversion"""
    progress = pyqtSignal(int, str)  # progress percentage, status message
    finished = pyqtSignal(bool, str)  # success, output path or error message

    def __init__(self, source, output_format, output_dir, settings):
        super().__init__()
        self.source = source
        self.output_format = output_format
        self.output_dir = output_dir
        self.settings = settings
        self.is_youtube = self._is_youtube_url(source)

    def _is_youtube_url(self, url):
        """Check if URL is from YouTube"""
        return isinstance(url, str) and ('youtube.com' in url or 'youtu.be' in url)

    def _download_youtube(self, url):
        """Download audio from YouTube"""
        self.progress.emit(10, "Connecting to YouTube...")

        output_path = os.path.join(self.output_dir, 'youtube_temp_%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self._youtube_progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.progress.emit(20, "Downloading audio...")
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')

                # Find the downloaded file
                for file in os.listdir(self.output_dir):
                    if file.startswith('youtube_temp_') and file.endswith('.mp3'):
                        return os.path.join(self.output_dir, file), title

        except Exception as e:
            raise Exception(f"YouTube download failed: {str(e)}")

    def _youtube_progress_hook(self, d):
        """Handle YouTube download progress"""
        if d['status'] == 'downloading':
            percent = d.get('downloaded_bytes', 0) / d.get('total_bytes', 1) * 50
            self.progress.emit(int(20 + percent), f"Downloading... {int(percent * 2)}%")

    def _convert_audio(self, input_path, title=None):
        """Convert audio file"""
        self.progress.emit(70, "Converting audio...")

        # Determine output filename
        if title:
            base_name = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        else:
            base_name = Path(input_path).stem

        output_filename = f"{base_name}.{self.output_format}"
        output_path = os.path.join(self.output_dir, output_filename)

        # Prevent overwriting
        counter = 1
        while os.path.exists(output_path):
            output_filename = f"{base_name}_{counter}.{self.output_format}"
            output_path = os.path.join(self.output_dir, output_filename)
            counter += 1

        try:
            # Build ffmpeg command
            stream = ffmpeg.input(input_path)

            # Audio parameters based on format and settings
            audio_params = self._get_audio_params()

            # Apply parameters and convert
            stream = ffmpeg.output(stream, output_path, **audio_params)
            ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

            self.progress.emit(90, "Finalizing...")
            return output_path

        except FFmpegError as e:
            error_msg = e.stderr.decode() if e.stderr else str(e)
            raise Exception(f"Conversion failed: {error_msg}")

    def _get_audio_params(self):
        """Get audio parameters based on settings"""
        params = {}

        # Codec mapping
        codec_map = {
            'mp3': 'libmp3lame',
            'ogg': 'libvorbis',
            'wav': 'pcm_s16le',
            'flac': 'flac',
            'aac': 'aac',
            'm4a': 'aac',
            'opus': 'libopus',
            'wma': 'wmav2'
        }

        params['acodec'] = codec_map.get(self.output_format, 'copy')

        # Apply quality settings
        if self.settings.get('sample_rate'):
            params['ar'] = self.settings['sample_rate']

        if self.settings.get('bitrate'):
            params['audio_bitrate'] = self.settings['bitrate']

        if self.settings.get('channels'):
            params['ac'] = self.settings['channels']

        return params

    def run(self):
        """Run the conversion process"""
        temp_file = None

        try:
            if self.is_youtube:
                # Download from YouTube first
                temp_file, title = self._download_youtube(self.source)
                output_path = self._convert_audio(temp_file, title)
            else:
                # Convert local file
                output_path = self._convert_audio(self.source)

            self.progress.emit(100, "Completed!")
            self.finished.emit(True, output_path)

        except Exception as e:
            self.finished.emit(False, str(e))

        finally:
            # Cleanup temporary file
            if temp_file and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass


class AudioConverterGUI(QMainWindow):
    """Main GUI window for Audio Converter"""

    def __init__(self):
        super().__init__()
        self.conversion_threads = []
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Audio Converter Pro")
        self.setWindowIcon(QIcon())
        self.setGeometry(100, 100, 800, 600)

        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f0f0f0;
            }
            QPushButton {
                background-color: #667eea;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a67d8;
            }
            QPushButton:pressed {
                background-color: #4c51bf;
            }
            QPushButton:disabled {
                background-color: #a0a0a0;
            }
            QLineEdit, QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 4px;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #667eea;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Header
        header_label = QLabel("🎵 Audio Converter Pro")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
            margin: 10px;
        """)
        main_layout.addWidget(header_label)

        # Input section
        self.create_input_section(main_layout)

        # Settings section
        self.create_settings_section(main_layout)

        # Queue section
        self.create_queue_section(main_layout)

        # Create menu bar
        self.create_menu_bar()

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to convert audio files")

    def create_input_section(self, parent_layout):
        """Create input section with tabs"""
        input_group = QGroupBox("Input Source")
        input_layout = QVBoxLayout()

        # Tab widget for different input methods
        self.input_tabs = QTabWidget()

        # YouTube tab
        youtube_tab = QWidget()
        youtube_layout = QVBoxLayout()

        self.youtube_input = QLineEdit()
        self.youtube_input.setPlaceholderText("Paste YouTube URL here...")
        youtube_layout.addWidget(self.youtube_input)

        youtube_add_btn = QPushButton("Add to Queue")
        youtube_add_btn.clicked.connect(self.add_youtube_to_queue)
        youtube_layout.addWidget(youtube_add_btn)

        youtube_tab.setLayout(youtube_layout)
        self.input_tabs.addTab(youtube_tab, "📹 YouTube URL")

        # File tab
        file_tab = QWidget()
        file_layout = QVBoxLayout()

        # Drag and drop area
        self.drop_area = QListWidget()
        self.drop_area.setAcceptDrops(True)
        self.drop_area.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setStyleSheet("""
            QListWidget {
                border: 2px dashed #667eea;
                border-radius: 5px;
                background-color: #f8f9ff;
            }
        """)

        # Override drag and drop events
        self.drop_area.dragEnterEvent = self.drag_enter_event
        self.drop_area.dragMoveEvent = self.drag_move_event
        self.drop_area.dropEvent = self.drop_event

        # Add placeholder text
        self.update_drop_area_placeholder()

        file_layout.addWidget(self.drop_area)

        # File buttons
        file_btn_layout = QHBoxLayout()

        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(self.browse_files)
        file_btn_layout.addWidget(browse_btn)

        clear_btn = QPushButton("Clear Selected")
        clear_btn.clicked.connect(self.clear_selected_files)
        file_btn_layout.addWidget(clear_btn)

        file_layout.addLayout(file_btn_layout)

        file_tab.setLayout(file_layout)
        self.input_tabs.addTab(file_tab, "📁 Local Files")

        input_layout.addWidget(self.input_tabs)
        input_group.setLayout(input_layout)
        parent_layout.addWidget(input_group)

    def create_settings_section(self, parent_layout):
        """Create settings section"""
        settings_group = QGroupBox("Conversion Settings")
        settings_layout = QGridLayout()

        # Output format
        settings_layout.addWidget(QLabel("Output Format:"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['mp3', 'ogg', 'wav', 'flac', 'aac', 'm4a', 'opus', 'wma'])
        self.format_combo.setCurrentText('ogg')
        settings_layout.addWidget(self.format_combo, 0, 1)

        # Sample rate
        settings_layout.addWidget(QLabel("Sample Rate:"), 0, 2)
        self.sample_rate_combo = QComboBox()
        self.sample_rate_combo.addItems(['Original', '22050 Hz', '32000 Hz', '44100 Hz', '48000 Hz', '96000 Hz'])
        self.sample_rate_combo.setCurrentText('32000 Hz')
        settings_layout.addWidget(self.sample_rate_combo, 0, 3)

        # Bitrate
        settings_layout.addWidget(QLabel("Bitrate:"), 1, 0)
        self.bitrate_combo = QComboBox()
        self.bitrate_combo.addItems(['Auto', '64k', '96k', '128k', '192k', '256k', '320k'])
        self.bitrate_combo.setCurrentText('128k')
        settings_layout.addWidget(self.bitrate_combo, 1, 1)

        # Output folder
        settings_layout.addWidget(QLabel("Output Folder:"), 1, 2)
        self.output_path = QLineEdit()
        self.output_path.setText(str(Path.home() / "Downloads" / "AudioConverter"))
        settings_layout.addWidget(self.output_path, 1, 3)

        browse_output_btn = QPushButton("Browse")
        browse_output_btn.clicked.connect(self.browse_output_folder)
        settings_layout.addWidget(browse_output_btn, 1, 4)

        # Preset buttons
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Presets:"))

        hoi4_btn = QPushButton("🎮 HOI4 Mod")
        hoi4_btn.clicked.connect(lambda: self.apply_preset('hoi4'))
        preset_layout.addWidget(hoi4_btn)

        hq_btn = QPushButton("🎧 High Quality")
        hq_btn.clicked.connect(lambda: self.apply_preset('hq'))
        preset_layout.addWidget(hq_btn)

        compressed_btn = QPushButton("📱 Compressed")
        compressed_btn.clicked.connect(lambda: self.apply_preset('compressed'))
        preset_layout.addWidget(compressed_btn)

        preset_layout.addStretch()
        settings_layout.addLayout(preset_layout, 2, 0, 1, 5)

        settings_group.setLayout(settings_layout)
        parent_layout.addWidget(settings_group)

        # Convert button
        self.convert_btn = QPushButton("🚀 Convert All Files")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                background-color: #667eea;
            }
            QPushButton:hover {
                background-color: #5a67d8;
            }
        """)
        self.convert_btn.clicked.connect(self.start_conversion)
        parent_layout.addWidget(self.convert_btn)

    def create_queue_section(self, parent_layout):
        """Create conversion queue section"""
        queue_group = QGroupBox("Conversion Queue")
        queue_layout = QVBoxLayout()

        # Queue table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(4)
        self.queue_table.setHorizontalHeaderLabels(['File', 'Status', 'Progress', 'Action'])
        self.queue_table.horizontalHeader().setStretchLastSection(False)
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.queue_table.setAlternatingRowColors(True)
        self.queue_table.setSelectionBehavior(QAbstractItemView.SelectRows)

        queue_layout.addWidget(self.queue_table)
        queue_group.setLayout(queue_layout)
        parent_layout.addWidget(queue_group)

    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu('File')

        add_files_action = QAction('Add Files...', self)
        add_files_action.setShortcut('Ctrl+O')
        add_files_action.triggered.connect(self.browse_files)
        file_menu.addAction(add_files_action)

        file_menu.addSeparator()

        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tools menu
        tools_menu = menubar.addMenu('Tools')

        clear_queue_action = QAction('Clear Queue', self)
        clear_queue_action.triggered.connect(self.clear_queue)
        tools_menu.addAction(clear_queue_action)

        # Help menu
        help_menu = menubar.addMenu('Help')

        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def update_drop_area_placeholder(self):
        """Update placeholder text in drop area"""
        if self.drop_area.count() == 0:
            item = QListWidgetItem("Drag and drop audio files here or click 'Browse Files'")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            self.drop_area.addItem(item)

    def drag_enter_event(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def drag_move_event(self, event):
        """Handle drag move event"""
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def drop_event(self, event):
        """Handle drop event"""
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        self.add_files_to_list(files)

    def add_files_to_list(self, files):
        """Add files to the drop area list"""
        # Clear placeholder if it exists
        if self.drop_area.count() == 1 and self.drop_area.item(0).flags() == Qt.NoItemFlags:
            self.drop_area.clear()

        for file in files:
            if os.path.isfile(file):
                # Check if it's an audio file
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma', '.opus', '.mp4', '.avi', '.mkv']:
                    item = QListWidgetItem(os.path.basename(file))
                    item.setData(Qt.UserRole, file)
                    self.drop_area.addItem(item)

    def browse_files(self):
        """Browse for audio files"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio Files",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma *.opus);;Video Files (*.mp4 *.avi *.mkv);;All Files (*.*)"
        )
        if files:
            self.add_files_to_list(files)

    def clear_selected_files(self):
        """Clear selected files from the list"""
        for item in self.drop_area.selectedItems():
            self.drop_area.takeItem(self.drop_area.row(item))

        self.update_drop_area_placeholder()

    def browse_output_folder(self):
        """Browse for output folder"""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)

    def apply_preset(self, preset):
        """Apply conversion preset"""
        presets = {
            'hoi4': {
                'format': 'ogg',
                'sample_rate': '32000 Hz',
                'bitrate': '128k'
            },
            'hq': {
                'format': 'flac',
                'sample_rate': 'Original',
                'bitrate': 'Auto'
            },
            'compressed': {
                'format': 'mp3',
                'sample_rate': '44100 Hz',
                'bitrate': '128k'
            }
        }

        if preset in presets:
            settings = presets[preset]
            self.format_combo.setCurrentText(settings['format'])
            self.sample_rate_combo.setCurrentText(settings['sample_rate'])
            self.bitrate_combo.setCurrentText(settings['bitrate'])

            self.status_bar.showMessage(f"Applied {preset.upper()} preset")

    def add_youtube_to_queue(self):
        """Add YouTube URL to conversion queue"""
        url = self.youtube_input.text().strip()
        if url:
            self.add_to_queue(url, "YouTube Video")
            self.youtube_input.clear()

    def add_to_queue(self, source, display_name):
        """Add item to conversion queue"""
        row = self.queue_table.rowCount()
        self.queue_table.insertRow(row)

        # File name
        self.queue_table.setItem(row, 0, QTableWidgetItem(display_name))

        # Status
        status_item = QTableWidgetItem("Queued")
        self.queue_table.setItem(row, 1, status_item)

        # Progress bar
        progress = QProgressBar()
        progress.setMinimum(0)
        progress.setMaximum(100)
        self.queue_table.setCellWidget(row, 2, progress)

        # Action button
        action_btn = QPushButton("Remove")
        action_btn.clicked.connect(lambda: self.remove_from_queue(row))
        self.queue_table.setCellWidget(row, 3, action_btn)

        # Store source data
        self.queue_table.item(row, 0).setData(Qt.UserRole, source)

    def remove_from_queue(self, row):
        """Remove item from queue"""
        self.queue_table.removeRow(row)

    def start_conversion(self):
        """Start the conversion process"""
        # Get all queued items
        sources = []

        # Add files from drop area
        for i in range(self.drop_area.count()):
            item = self.drop_area.item(i)
            if item.data(Qt.UserRole):
                sources.append((item.data(Qt.UserRole), item.text()))

        # Add items from queue table
        for row in range(self.queue_table.rowCount()):
            source = self.queue_table.item(row, 0).data(Qt.UserRole)
            display_name = self.queue_table.item(row, 0).text()
            if source:
                sources.append((source, display_name))

        if not sources:
            QMessageBox.warning(self, "No Files", "Please add some files or URLs to convert.")
            return

        # Create output directory if it doesn't exist
        output_dir = self.output_path.text()
        os.makedirs(output_dir, exist_ok=True)

        # Get conversion settings
        settings = self.get_conversion_settings()

        # Clear the file list and prepare queue
        self.drop_area.clear()
        self.update_drop_area_placeholder()

        # Start conversion for each source
        for source, display_name in sources:
            if not any(item.data(Qt.UserRole) == source for row in range(self.queue_table.rowCount())
                       for item in [self.queue_table.item(row, 0)] if item):
                self.add_to_queue(source, display_name)

        # Process queue
        for row in range(self.queue_table.rowCount()):
            source = self.queue_table.item(row, 0).data(Qt.UserRole)
            if source:
                self.convert_file(row, source, self.format_combo.currentText(), output_dir, settings)

    def get_conversion_settings(self):
        """Get current conversion settings"""
        settings = {}

        # Sample rate
        sample_rate_text = self.sample_rate_combo.currentText()
        if sample_rate_text != 'Original':
            settings['sample_rate'] = int(sample_rate_text.split()[0])

        # Bitrate
        bitrate_text = self.bitrate_combo.currentText()
        if bitrate_text != 'Auto':
            settings['bitrate'] = bitrate_text

        return settings

    def convert_file(self, row, source, output_format, output_dir, settings):
        """Convert a single file"""
        # Update status
        self.queue_table.item(row, 1).setText("Converting...")

        # Create conversion thread
        thread = ConversionThread(source, output_format, output_dir, settings)

        # Connect signals
        thread.progress.connect(lambda p, s: self.update_progress(row, p, s))
        thread.finished.connect(lambda success, result: self.conversion_finished(row, success, result))

        # Start conversion
        thread.start()
        self.conversion_threads.append(thread)

    def update_progress(self, row, progress, status):
        """Update conversion progress"""
        if row < self.queue_table.rowCount():
            self.queue_table.item(row, 1).setText(status)
            progress_bar = self.queue_table.cellWidget(row, 2)
            if progress_bar:
                progress_bar.setValue(progress)

    def conversion_finished(self, row, success, result):
        """Handle conversion completion"""
        if row < self.queue_table.rowCount():
            if success:
                self.queue_table.item(row, 1).setText("✓ Completed")

                # Change action button to "Open"
                open_btn = QPushButton("Open")
                open_btn.clicked.connect(lambda: self.open_file(result))
                self.queue_table.setCellWidget(row, 3, open_btn)

                self.status_bar.showMessage(f"Converted: {os.path.basename(result)}")
            else:
                self.queue_table.item(row, 1).setText("✗ Failed")
                QMessageBox.warning(self, "Conversion Failed", f"Error: {result}")

    def open_file(self, filepath):
        """Open the converted file location"""
        if sys.platform == 'win32':
            os.startfile(os.path.dirname(filepath))
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', os.path.dirname(filepath)])
        else:
            subprocess.Popen(['xdg-open', os.path.dirname(filepath)])

    def clear_queue(self):
        """Clear the conversion queue"""
        self.queue_table.setRowCount(0)

    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(self, "About Audio Converter Pro",
                          "<h2>Audio Converter Pro</h2>"
                          "<p>Version 1.0</p>"
                          "<p>A powerful audio converter with YouTube download support.</p>"
                          "<p>Perfect for game modding and audio format conversion.</p>"
                          "<br>"
                          "<p>Supports: MP3, OGG, WAV, FLAC, AAC, M4A, Opus, WMA</p>"
                          "<br><br>"
                          "<p><b>Made by <a href='https://www.linkedin.com/in/yunus-emre-balci/'>Yunus Emre Balci</a></b></p>"
                          )

    def save_settings(self):
        """Save application settings"""
        settings = {
            'output_path': self.output_path.text(),
            'format': self.format_combo.currentText(),
            'sample_rate': self.sample_rate_combo.currentText(),
            'bitrate': self.bitrate_combo.currentText()
        }

        try:
            with open('settings.json', 'w') as f:
                json.dump(settings, f)
        except:
            pass

    def load_settings(self):
        """Load application settings"""
        try:
            with open('settings.json', 'r') as f:
                settings = json.load(f)

            self.output_path.setText(settings.get('output_path', str(Path.home() / "Downloads" / "AudioConverter")))
            self.format_combo.setCurrentText(settings.get('format', 'ogg'))
            self.sample_rate_combo.setCurrentText(settings.get('sample_rate', '32000 Hz'))
            self.bitrate_combo.setCurrentText(settings.get('bitrate', '128k'))
        except:
            # Use defaults
            pass

    def closeEvent(self, event):
        """Handle application close event"""
        self.save_settings()

        # Stop all conversion threads
        for thread in self.conversion_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()

        event.accept()


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Set application metadata
    app.setApplicationName("Audio Converter Pro")
    app.setOrganizationName("AudioTools")

    # Create and show main window
    window = AudioConverterGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()