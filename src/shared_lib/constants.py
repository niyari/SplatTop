MODES = [
    "Splat Zones",
    "Tower Control",
    "Rainmaker",
    "Clam Blitz",
]
REGIONS = [
    "Tentatek",
    "Takoroka",
]
REDIS_PORT = 6379
REDIS_HOST = "redis"
REDIS_URI = f"redis://{REDIS_HOST}:{REDIS_PORT}"
PLAYER_PUBSUB_CHANNEL = "player_data_channel"
PLAYER_LATEST_REDIS_KEY = "player_latest_data"
PLAYER_DATA_REDIS_KEY = "player_data"
WEAPON_INFO_URL = (
    "https://splat-top.nyc3.cdn.digitaloceanspaces.com/data/weapon_info.json"
)
WEAPON_INFO_REDIS_KEY = "weapon_info"
