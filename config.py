config = {
    # https://discord.com/developers/
    'bot': {
        'name': 'DISCORD-BOT-NAME',        # [!]
        'id': 'INTEGER-DISCORD-BOT-ID',    # [!]
        'token': 'DISCORD-BOT-TOKEN',      # [!]
        'prefix': '%',
        'queue_limit': 50
    },

    # https://developer.spotify.com/
    'spotify': {
        'client_id': 'SPOTIFY-CLIENT-ID',  # [!]
        'secret': 'SPOTIFY-SECRET-ID'      # [!]
    },

    'color': {
        'system': 0xbd92ff,
        'main': 0xa2e4ff,
        'lime': 0x5ce68d,
        'red': 0xec2e34,
        'gray': 0x515457
    }
}

YDL_OPTS = {
    'format': 'bestaudio',
    'noplaylist':'True',
    'quiet': 'True',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'youtube_include_dash_manifest': False
}

FFMPEG_OPTS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
