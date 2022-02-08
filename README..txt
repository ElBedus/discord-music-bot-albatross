Developer: ElBedus#8858


===========================

    Albatross-bot v-1.0
	
===========================


Required (besides requirements.txt):
	Python 3.9+                       | https://www.python.org/downloads/
	FFmpeg git-2019-12-17-bd83191+    | https://ffmpeg.org/download.html

Before using, paste the required values into config.py:
	"bot": {
		"name"       | Discord bot name
		"id"         | Discord bot id
		"token"      | Discord bot token
		...
	}
	"spotify": {
		"client_id"  | Spotify client id
		"secret"     | Spotify secret
	}

Discord bot values: https://discord.com/developers/applications/
Spotify values:     https://developer.spotify.com/



Discord developers:
	Bot (Privileged Gateway Intents):
		PRESENCE INTENT        | True
		SERVER MEMBERS INTENT  | True
	
	Discord-bot OAuth2:
		SCOPES:
			├ bot
			└ applications.commands
		GENERAL PERMISSIONS:
			└ Administrator
				or
			├ Read Messages/View Channels
			├ Seend Messages
			├ Embed Links
			├ Read Message History
			├ Use Slash Commands
			├ Connect
			├ Speak
			└ Defean Members