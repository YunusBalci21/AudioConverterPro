import os
import re
import json
import uuid
import shutil
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from ffmpeg._run import Error as FFmpegError
import yt_dlp
import ffmpeg



# Try to import config, use defaults if not available
try:
    from config import CONFIG, get_config
except ImportError:
    # Default configuration if config.py doesn't exist
    CONFIG = {
        'server': {'max_content_length': 500 * 1024 * 1024},
        'directories': {
            'upload_folder': 'uploads',
            'output_folder': 'outputs',
            'temp_folder': 'temp'
        },
        'formats': {
            'mp3': {'ext': 'mp3', 'codec': 'libmp3lame'},
            'ogg': {'ext': 'ogg', 'codec': 'libvorbis'},
            'wav': {'ext': 'wav', 'codec': 'pcm_s16le'},
            'flac': {'ext': 'flac', 'codec': 'flac'},
            'aac': {'ext': 'aac', 'codec': 'aac'},
            'm4a': {'ext': 'm4a', 'codec': 'aac'},
            'opus': {'ext': 'opus', 'codec': 'libopus'},
            'wma': {'ext': 'wma', 'codec': 'wmav2'}
        }
    }


    def get_config(key=None):
        return CONFIG.get(key) if key else CONFIG

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = CONFIG['server']['max_content_length']
app.config['UPLOAD_FOLDER'] = CONFIG['directories']['upload_folder']
app.config['OUTPUT_FOLDER'] = CONFIG['directories']['output_folder']

# Create necessary directories
for folder in CONFIG['directories'].values():
    os.makedirs(folder, exist_ok=True)

# Supported audio formats
AUDIO_FORMATS = CONFIG['formats']

# Conversion jobs tracking
conversion_jobs = {}


def is_youtube_url(url):
    """Check if URL is a YouTube link"""
    youtube_regex = r'(youtube\.com|youtu\.be)'
    return re.search(youtube_regex, url) is not None


def download_youtube_audio(url, job_id):
    """Download audio from YouTube video"""
    output_path = os.path.join('temp', f'{job_id}_youtube.%(ext)s')

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
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Unknown')
            # Find the downloaded file
            for file in os.listdir('temp'):
                if file.startswith(f'{job_id}_youtube'):
                    return os.path.join('temp', file), title
    except Exception as e:
        raise Exception(f"YouTube download failed: {str(e)}")


def convert_audio(input_path, output_format, sample_rate=None, bitrate=None, job_id=None):
    """Convert audio file to specified format"""
    if output_format not in AUDIO_FORMATS:
        raise ValueError(f"Unsupported format: {output_format}")

    format_info = AUDIO_FORMATS[output_format]
    output_filename = f"{Path(input_path).stem}.{format_info['ext']}"
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], f"{job_id}_{output_filename}")

    try:
        # Build ffmpeg command
        stream = ffmpeg.input(input_path)

        # Audio parameters
        audio_params = {'acodec': format_info['codec']}

        if sample_rate:
            audio_params['ar'] = sample_rate

        if bitrate:
            audio_params['audio_bitrate'] = bitrate

        # Apply audio parameters
        stream = ffmpeg.output(stream, output_path, **audio_params)

        # Run conversion
        ffmpeg.run(stream, overwrite_output=True, capture_stdout=True, capture_stderr=True)

        return output_path

    except FFmpegError as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f"Conversion failed: {error_message}")


def process_conversion_job(job_id, source_type, source_data, output_format, sample_rate, bitrate):
    """Process a single conversion job"""
    try:
        conversion_jobs[job_id]['status'] = 'processing'
        conversion_jobs[job_id]['progress'] = 20

        # Get input file
        if source_type == 'youtube':
            conversion_jobs[job_id]['message'] = 'Downloading from YouTube...'
            input_path, title = download_youtube_audio(source_data, job_id)
            conversion_jobs[job_id]['filename'] = title
            conversion_jobs[job_id]['progress'] = 60
        else:  # file upload
            input_path = source_data
            conversion_jobs[job_id]['progress'] = 60

        # Convert audio
        conversion_jobs[job_id]['message'] = 'Converting audio...'
        output_path = convert_audio(input_path, output_format, sample_rate, bitrate, job_id)

        # Update job status
        conversion_jobs[job_id]['status'] = 'completed'
        conversion_jobs[job_id]['progress'] = 100
        conversion_jobs[job_id]['output_path'] = output_path
        conversion_jobs[job_id]['message'] = 'Conversion completed!'

        # Clean up temp file
        if source_type == 'youtube' and os.path.exists(input_path):
            os.remove(input_path)

    except Exception as e:
        conversion_jobs[job_id]['status'] = 'failed'
        conversion_jobs[job_id]['error'] = str(e)
        conversion_jobs[job_id]['message'] = f'Error: {str(e)}'


@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html', formats=list(AUDIO_FORMATS.keys()))


@app.route('/convert', methods=['POST'])
def convert():
    """Handle conversion request"""
    data = request.get_json()

    output_format = data.get('format', 'ogg')
    sample_rate = data.get('sampleRate')
    bitrate = data.get('bitrate')
    sources = data.get('sources', [])

    if not sources:
        return jsonify({'error': 'No sources provided'}), 400

    job_ids = []

    for source in sources:
        job_id = str(uuid.uuid4())
        source_type = source['type']

        # Initialize job
        conversion_jobs[job_id] = {
            'id': job_id,
            'status': 'queued',
            'progress': 0,
            'filename': source.get('name', 'Unknown'),
            'message': 'Queued for processing...'
        }

        if source_type == 'youtube':
            source_data = source['url']
        else:  # file
            source_data = source['path']

        # Start conversion in background thread
        thread = threading.Thread(
            target=process_conversion_job,
            args=(job_id, source_type, source_data, output_format, sample_rate, bitrate)
        )
        thread.start()

        job_ids.append(job_id)

    return jsonify({'jobIds': job_ids})


@app.route('/upload', methods=['POST'])
def upload():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save uploaded file
    filename = secure_filename(file.filename)
    file_id = str(uuid.uuid4())
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{file_id}_{filename}")
    file.save(filepath)

    return jsonify({
        'path': filepath,
        'name': filename
    })


@app.route('/status/<job_id>')
def get_status(job_id):
    """Get conversion job status"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(conversion_jobs[job_id])


@app.route('/download/<job_id>')
def download(job_id):
    """Download converted file"""
    if job_id not in conversion_jobs:
        return jsonify({'error': 'Job not found'}), 404

    job = conversion_jobs[job_id]
    if job['status'] != 'completed' or 'output_path' not in job:
        return jsonify({'error': 'File not ready'}), 400

    output_path = job['output_path']
    filename = os.path.basename(output_path)

    # Remove job ID from filename for cleaner download
    clean_filename = '_'.join(filename.split('_')[1:])

    return send_file(output_path, as_attachment=True, download_name=clean_filename)


@app.route('/formats')
def get_formats():
    """Get supported audio formats with details"""
    format_details = {
        'mp3': {'name': 'MP3', 'description': 'Most compatible format'},
        'ogg': {'name': 'OGG Vorbis', 'description': 'Open format, great for games'},
        'wav': {'name': 'WAV', 'description': 'Uncompressed, highest quality'},
        'flac': {'name': 'FLAC', 'description': 'Lossless compression'},
        'aac': {'name': 'AAC', 'description': 'Advanced audio coding'},
        'm4a': {'name': 'M4A', 'description': 'Apple audio format'},
        'opus': {'name': 'Opus', 'description': 'Modern, efficient codec'},
        'wma': {'name': 'WMA', 'description': 'Windows Media Audio'}
    }
    return jsonify(format_details)


# Cleanup old files periodically
def cleanup_old_files():
    """Remove old temporary and output files"""
    import time
    while True:
        time.sleep(3600)  # Run every hour

        # Clean files older than 24 hours
        for folder in ['temp', 'uploads', 'outputs']:
            for file in os.listdir(folder):
                filepath = os.path.join(folder, file)
                if os.path.getmtime(filepath) < time.time() - 86400:  # 24 hours
                    try:
                        os.remove(filepath)
                    except:
                        pass


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

if __name__ == '__main__':
    # Use configuration settings if available
    server_config = get_config('server') if 'get_config' in globals() else {}
    app.run(
        host=server_config.get('host', '127.0.0.1'),
        port=server_config.get('port', 5000),
        debug=server_config.get('debug', True),
        threaded=server_config.get('threaded', True)
    )