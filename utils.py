import os
import json
import logging
import asyncio
from datetime import datetime

# تفعيل التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# قراءة المتغيرات
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN is not set!")

CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'bexo50')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID is not set!")

# =============== معالجة آمنة للمشرفين ===============
MODERATORS = []
moderators_str = os.getenv('MODERATORS', '')
if moderators_str:
    for id_str in moderators_str.split(','):
        id_str = id_str.strip()
        if id_str and id_str.isdigit():
            MODERATORS.append(int(id_str))

# ملفات التخزين
VIDEOS_FILE = 'videos.json'
PLAYLISTS_FILE = 'playlists.json'
STATS_FILE = 'stats.json'
USERS_FILE = 'users.json'

# =============== قفل للملفات (File I/O Lock) ===============
_file_lock = asyncio.Lock()

# =============== دوال التخزين مع القفل ===============

async def load_videos_async():
    async with _file_lock:
        if os.path.exists(VIDEOS_FILE):
            with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_playlists_async():
    async with _file_lock:
        if os.path.exists(PLAYLISTS_FILE):
            with open(PLAYLISTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_stats_async():
    async with _file_lock:
        if os.path.exists(STATS_FILE):
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def load_users_async():
    async with _file_lock:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    return {}

async def save_videos_async(videos):
    async with _file_lock:
        with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(videos, f, ensure_ascii=False, indent=2)

async def save_playlists_async(playlists):
    async with _file_lock:
        with open(PLAYLISTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(playlists, f, ensure_ascii=False, indent=2)

async def save_stats_async(stats):
    async with _file_lock:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

async def save_users_async(users):
    async with _file_lock:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

# دوال متزامنة تستخدم القفل أيضاً
def load_videos():
    return asyncio.run(load_videos_async())

def load_playlists():
    return asyncio.run(load_playlists_async())

def load_stats():
    return asyncio.run(load_stats_async())

def load_users():
    return asyncio.run(load_users_async())

def save_videos(videos):
    asyncio.run(save_videos_async(videos))

def save_playlists(playlists):
    asyncio.run(save_playlists_async(playlists))

def save_stats(stats):
    asyncio.run(save_stats_async(stats))

def save_users(users):
    asyncio.run(save_users_async(users))

# =============== دوال الإحصائيات ===============

def increment_view(video_name, user_id, stats):
    if video_name not in stats:
        stats[video_name] = {'views': 0, 'users': []}
    stats[video_name]['views'] += 1
    if user_id not in stats[video_name]['users']:
        stats[video_name]['users'].append(user_id)
    save_stats(stats)

def get_video_stats(video_name, stats):
    if video_name in stats:
        return stats[video_name]
    return {'views': 0, 'users': []}

# =============== دوال المستخدمين ===============

def save_user(user_id, username=None, first_name=None, users=None):
    if users is None:
        users = load_users()
    
    if str(user_id) not in users:
        users[str(user_id)] = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'joined_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat()
        }
        save_users(users)
    else:
        users[str(user_id)]['last_active'] = datetime.now().isoformat()
        if username:
            users[str(user_id)]['username'] = username
        if first_name:
            users[str(user_id)]['first_name'] = first_name
        save_users(users)
    return users

def get_all_users(users):
    return list(users.keys())

# =============== دوال الصلاحيات ===============

def is_admin(user_id):
    return user_id == ADMIN_ID

def is_moderator(user_id):
    return user_id in MODERATORS

def is_staff(user_id):
    return is_admin(user_id) or is_moderator(user_id)
