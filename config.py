"""
Audio Converter Configuration File
Customize these settings to match your needs
"""

# Server Configuration
SERVER_CONFIG = {
    'host': '0.0.0.0',  # '0.0.0.0' allows external connections, '127.0.0.1' for localhost only
    'port': 5000,
    'debug': True,  # Set to False in production
    'threaded': True,
    'max_content_length': 500 * 1024 * 1024,  # 500MB max upload size
}

# Directory Configuration
DIRECTORIES = {
    'upload_folder': 'uploads',
    'output_folder': 'outputs',
    'temp_folder': 'temp',
    'youtube_folder': 'downloads',
}

# Audio Format Configuration
AUDIO_FORMATS = {
    'mp3': {
        'ext': 'mp3',
        'codec': 'libmp3lame',
        'name': 'MP3',
        'description': 'Most compatible format',
        'default_bitrate': '192k',
        'quality_options': ['96k', '128k', '192k', '256k', '320k']
    },
    'ogg': {
        'ext': 'ogg',
        'codec': 'libvorbis',
        'name': 'OGG Vorbis',
        'description': 'Open format, perfect for game modding',
        'default_bitrate': '128k',
        'quality_options': ['64k', '96k', '128k', '192k', '256k']
    },
    'wav': {
        'ext': 'wav',
        'codec': 'pcm_s16le',
        'name': 'WAV',
        'description': 'Uncompressed, highest quality',
        'default_bitrate': None,
        'quality_options': []
    },
    'flac': {
        'ext': 'flac',
        'codec': 'flac',
        'name': 'FLAC',
        'description': 'Lossless compression',
        'default_bitrate': None,
        'quality_options': []
    },
    'aac': {
        'ext': 'aac',
        'codec': 'aac',
        'name': 'AAC',
        'description': 'Advanced audio coding',
        'default_bitrate': '192k',
        'quality_options': ['96k', '128k', '192k', '256k', '320k']
    },
    'm4a': {
        'ext': 'm4a',
        'codec': 'aac',
        'name': 'M4A',
        'description': 'Apple audio format',
        'default_bitrate': '192k',
        'quality_options': ['96k', '128k', '192k', '256k', '320k']
    },
    'opus': {
        'ext': 'opus',
        'codec': 'libopus',
        'name': 'Opus',
        'description': 'Modern, efficient codec',
        'default_bitrate': '128k',
        'quality_options': ['64k', '96k', '128k', '192k', '256k']
    },
    'wma': {
        'ext': 'wma',
        'codec': 'wmav2',
        'name': 'WMA',
        'description': 'Windows Media Audio',
        'default_bitrate': '128k',
        'quality_options': ['64k', '96k', '128k', '192k', '256k']
    }
}

# Sample Rate Options
SAMPLE_RATES = {
    'original': {'value': None, 'name': 'Original'},
    '22050': {'value': 22050, 'name': '22.05 kHz'},
    '32000': {'value': 32000, 'name': '32 kHz (HOI4 Standard)'},
    '44100': {'value': 44100, 'name': '44.1 kHz (CD Quality)'},
    '48000': {'value': 48000, 'name': '48 kHz (Professional)'},
    '96000': {'value': 96000, 'name': '96 kHz (High-Res)'},
}

# Preset Configurations
PRESETS = {
    'hoi4': {
        'name': 'Hearts of Iron IV Mod',
        'format': 'ogg',
        'sample_rate': 32000,
        'bitrate': '128k',
        'description': 'Optimal settings for HOI4 game mods'
    },
    'stellaris': {
        'name': 'Stellaris Mod',
        'format': 'ogg',
        'sample_rate': 44100,
        'bitrate': '192k',
        'description': 'Settings for Stellaris game mods'
    },
    'ck3': {
        'name': 'Crusader Kings III Mod',
        'format': 'ogg',
        'sample_rate': 48000,
        'bitrate': '192k',
        'description': 'Settings for CK3 game mods'
    },
    'hq': {
        'name': 'High Quality',
        'format': 'flac',
        'sample_rate': None,
        'bitrate': None,
        'description': 'Lossless audio preservation'
    },
    'compressed': {
        'name': 'Compressed',
        'format': 'mp3',
        'sample_rate': 44100,
        'bitrate': '128k',
        'description': 'Small file size, good quality'
    },
    'podcast': {
        'name': 'Podcast',
        'format': 'mp3',
        'sample_rate': 44100,
        'bitrate': '96k',
        'description': 'Optimized for speech'
    },
    'music_hq': {
        'name': 'Music HQ',
        'format': 'mp3',
        'sample_rate': 44100,
        'bitrate': '320k',
        'description': 'High quality music'
    },
    'voice': {
        'name': 'Voice Recording',
        'format': 'mp3',
        'sample_rate': 22050,
        'bitrate': '64k',
        'description': 'Optimized for voice recordings'
    }
}

# YouTube Download Configuration
YOUTUBE_CONFIG = {
    'format': 'bestaudio/best',
    'extract_audio': True,
    'audio_format': 'mp3',
    'audio_quality': '320',
    'quiet': False,
    'no_warnings': False,
    'age_limit': None,  # Set to restrict age-limited content
    'geo_bypass': True,  # Try to bypass geographic restrictions
}

# FFmpeg Configuration
FFMPEG_CONFIG = {
    'threads': 0,  # 0 = auto-detect
    'overwrite': True,
    'loglevel': 'error',  # quiet, panic, fatal, error, warning, info, verbose, debug
    'hide_banner': True,
}

# Conversion Configuration
CONVERSION_CONFIG = {
    'max_parallel_jobs': 4,
    'cleanup_temp_files': True,
    'cleanup_after_hours': 24,  # Delete old files after this many hours
    'max_file_size_mb': 500,
    'allowed_extensions': [
        '.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac',
        '.wma', '.opus', '.mp4', '.avi', '.mkv', '.webm'
    ]
}

# UI Configuration
UI_CONFIG = {
    'theme': 'modern',  # modern, classic, dark
    'show_advanced_settings': True,
    'enable_batch_upload': True,
    'max_batch_size': 50,
    'enable_drag_drop': True,
    'show_format_descriptions': True,
    'enable_presets': True,
}

# Advanced FFmpeg Options (for power users)
ADVANCED_FFMPEG_OPTIONS = {
    'mp3': {
        'compression_level': 2,  # 0-9, lower = better quality but larger file
        'vbr': True,  # Variable bitrate
    },
    'ogg': {
        'compression_level': 5,  # 0-10, higher = better compression
        'vbr': True,
    },
    'flac': {
        'compression_level': 5,  # 0-8, higher = better compression
    },
    'opus': {
        'vbr': 'on',  # on, off, constrained
        'compression_level': 10,  # 0-10
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'enable_csrf': True,
    'session_timeout_minutes': 60,
    'max_urls_per_request': 10,
    'rate_limit_enabled': True,
    'rate_limit_per_minute': 100,
    'allowed_domains': [],  # Empty = all domains allowed
    'blocked_domains': [],  # Domains to block
}

# Logging Configuration
LOGGING_CONFIG = {
    'enable_logging': True,
    'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'log_file': 'audio_converter.log',
    'log_max_size_mb': 10,
    'log_backup_count': 5,
    'log_format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
}

# Feature Flags
FEATURES = {
    'youtube_download': True,
    'batch_conversion': True,
    'custom_settings': True,
    'presets': True,
    'api_mode': True,  # Enable REST API endpoints
    'web_ui': True,
    'cli_mode': True,
    'auto_cleanup': True,
    'progress_tracking': True,
    'format_detection': True,  # Auto-detect input format
    'metadata_preservation': True,  # Try to preserve audio metadata
}

# Export all configuration
CONFIG = {
    'server': SERVER_CONFIG,
    'directories': DIRECTORIES,
    'formats': AUDIO_FORMATS,
    'sample_rates': SAMPLE_RATES,
    'presets': PRESETS,
    'youtube': YOUTUBE_CONFIG,
    'ffmpeg': FFMPEG_CONFIG,
    'conversion': CONVERSION_CONFIG,
    'ui': UI_CONFIG,
    'advanced': ADVANCED_FFMPEG_OPTIONS,
    'security': SECURITY_CONFIG,
    'logging': LOGGING_CONFIG,
    'features': FEATURES,
}

# Game-specific configurations
GAME_CONFIGS = {
    'hoi4': {
        'name': 'Hearts of Iron IV',
        'audio_format': 'ogg',
        'sample_rate': 32000,
        'channels': 2,
        'bitrate': '128k',
        'notes': 'Place converted files in mod/music or mod/sound folders'
    },
    'stellaris': {
        'name': 'Stellaris',
        'audio_format': 'ogg',
        'sample_rate': 44100,
        'channels': 2,
        'bitrate': '192k',
        'notes': 'Use for custom music and sound effects'
    },
    'ck3': {
        'name': 'Crusader Kings III',
        'audio_format': 'ogg',
        'sample_rate': 48000,
        'channels': 2,
        'bitrate': '192k',
        'notes': 'Place in mod/music or mod/sound folders'
    },
    'eu4': {
        'name': 'Europa Universalis IV',
        'audio_format': 'ogg',
        'sample_rate': 44100,
        'channels': 2,
        'bitrate': '128k',
        'notes': 'Compatible with music mods'
    },
    'vic3': {
        'name': 'Victoria 3',
        'audio_format': 'ogg',
        'sample_rate': 48000,
        'channels': 2,
        'bitrate': '192k',
        'notes': 'Use for era-appropriate music'
    }
}

def get_config(key=None):
    """Get configuration value"""
    if key:
        keys = key.split('.')
        value = CONFIG
        for k in keys:
            value = value.get(k)
        return value
    return CONFIG

def update_config(key, value):
    """Update configuration value"""
    keys = key.split('.')
    config = CONFIG
    for k in keys[:-1]:
        config = config[k]
    config[keys[-1]] = value