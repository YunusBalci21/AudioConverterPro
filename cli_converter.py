#!/usr/bin/env python3
"""
Audio Converter CLI - Command line version of the audio converter
Usage: python cli_converter.py [input] -f [format] -s [sample_rate] -b [bitrate]
"""

import os
import sys
import argparse
import glob
from pathlib import Path
import yt_dlp
import ffmpeg
from concurrent.futures import ThreadPoolExecutor, as_completed


class AudioConverter:
    def __init__(self):
        self.formats = {
            'mp3': {'ext': 'mp3', 'codec': 'libmp3lame'},
            'ogg': {'ext': 'ogg', 'codec': 'libvorbis'},
            'wav': {'ext': 'wav', 'codec': 'pcm_s16le'},
            'flac': {'ext': 'flac', 'codec': 'flac'},
            'aac': {'ext': 'aac', 'codec': 'aac'},
            'm4a': {'ext': 'm4a', 'codec': 'aac'},
            'opus': {'ext': 'opus', 'codec': 'libopus'},
            'wma': {'ext': 'wma', 'codec': 'wmav2'}
        }

    def is_youtube_url(self, url):
        """Check if URL is a YouTube link"""
        return 'youtube.com' in url or 'youtu.be' in url

    def download_youtube(self, url, output_dir='downloads'):
        """Download audio from YouTube"""
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, '%(title)s.%(ext)s')

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'quiet': False,
            'no_warnings': False,
        }

        print(f"Downloading: {url}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get('title', 'Unknown')
                # Find the downloaded file
                for file in os.listdir(output_dir):
                    if title in file and file.endswith('.mp3'):
                        return os.path.join(output_dir, file)
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            return None

    def convert_audio(self, input_path, output_format, sample_rate=None, bitrate=None, output_dir='converted'):
        """Convert audio file to specified format"""
        if output_format not in self.formats:
            raise ValueError(f"Unsupported format: {output_format}")

        os.makedirs(output_dir, exist_ok=True)

        format_info = self.formats[output_format]
        output_filename = f"{Path(input_path).stem}.{format_info['ext']}"
        output_path = os.path.join(output_dir, output_filename)

        print(f"Converting: {os.path.basename(input_path)} -> {output_filename}")

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

            print(f"✓ Converted: {output_filename}")
            return output_path

        except ffmpeg.Error as e:
            error_message = e.stderr.decode() if e.stderr else str(e)
            print(f"✗ Error converting {os.path.basename(input_path)}: {error_message}")
            return None

    def process_file(self, input_item, output_format, sample_rate, bitrate, output_dir):
        """Process a single file or URL"""
        if self.is_youtube_url(input_item):
            # Download from YouTube first
            downloaded_file = self.download_youtube(input_item)
            if downloaded_file:
                result = self.convert_audio(downloaded_file, output_format, sample_rate, bitrate, output_dir)
                # Clean up downloaded file
                os.remove(downloaded_file)
                return result
        else:
            # Convert local file
            return self.convert_audio(input_item, output_format, sample_rate, bitrate, output_dir)

    def batch_convert(self, input_items, output_format, sample_rate=None, bitrate=None, output_dir='converted',
                      max_workers=4):
        """Convert multiple files in parallel"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for item in input_items:
                future = executor.submit(self.process_file, item, output_format, sample_rate, bitrate, output_dir)
                futures.append(future)

            results = []
            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

            return results


def main():
    parser = argparse.ArgumentParser(
        description='Audio Converter CLI - Convert audio files and YouTube videos to various formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file to OGG (HOI4 preset)
  python cli_converter.py audio.mp3 -f ogg -s 32000 -b 128k

  # Convert YouTube video to MP3
  python cli_converter.py "https://youtube.com/watch?v=..." -f mp3

  # Batch convert all MP3 files in a directory
  python cli_converter.py *.mp3 -f ogg -s 32000

  # Use preset
  python cli_converter.py audio.wav --preset hoi4

Supported formats: mp3, ogg, wav, flac, aac, m4a, opus, wma
        """
    )

    parser.add_argument('input', nargs='+', help='Input files or YouTube URLs')
    parser.add_argument('-f', '--format', default='ogg', help='Output format (default: ogg)')
    parser.add_argument('-s', '--sample-rate', type=int, help='Sample rate in Hz (e.g., 32000 for HOI4)')
    parser.add_argument('-b', '--bitrate', help='Bitrate (e.g., 128k, 256k)')
    parser.add_argument('-o', '--output-dir', default='converted', help='Output directory (default: converted)')
    parser.add_argument('--preset', choices=['hoi4', 'hq', 'compressed'], help='Use preset settings')
    parser.add_argument('-j', '--jobs', type=int, default=4, help='Number of parallel jobs (default: 4)')

    args = parser.parse_args()

    # Apply presets
    if args.preset:
        if args.preset == 'hoi4':
            args.format = 'ogg'
            args.sample_rate = 32000
            args.bitrate = '128k'
            print("Using HOI4 preset: OGG format, 32kHz, 128kbps")
        elif args.preset == 'hq':
            args.format = 'flac'
            args.sample_rate = None
            args.bitrate = None
            print("Using HQ preset: FLAC format, original quality")
        elif args.preset == 'compressed':
            args.format = 'mp3'
            args.sample_rate = 44100
            args.bitrate = '128k'
            print("Using compressed preset: MP3 format, 44.1kHz, 128kbps")

    # Expand wildcards and collect all input items
    input_items = []
    for pattern in args.input:
        if '*' in pattern or '?' in pattern:
            # It's a wildcard pattern
            files = glob.glob(pattern)
            input_items.extend(files)
        else:
            # It's a single file or URL
            input_items.append(pattern)

    if not input_items:
        print("No input files found!")
        return 1

    print(f"\nProcessing {len(input_items)} item(s)...")
    print(f"Output format: {args.format}")
    if args.sample_rate:
        print(f"Sample rate: {args.sample_rate} Hz")
    if args.bitrate:
        print(f"Bitrate: {args.bitrate}")
    print(f"Output directory: {args.output_dir}\n")

    # Create converter and process files
    converter = AudioConverter()
    results = converter.batch_convert(
        input_items,
        args.format,
        args.sample_rate,
        args.bitrate,
        args.output_dir,
        args.jobs
    )

    print(f"\n{'=' * 50}")
    print(f"Conversion complete! {len(results)}/{len(input_items)} files converted successfully.")
    print(f"Output directory: {os.path.abspath(args.output_dir)}")

    return 0 if len(results) == len(input_items) else 1


if __name__ == '__main__':
    sys.exit(main())