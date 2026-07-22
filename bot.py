import os
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# =============== الإعدادات الأساسية ===============

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN is required!")

CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME', 'bexo50')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID is required!")

# المشرفين (اختياري)
MODERATORS = []
for id_str in os.getenv('MODERATORS', '').split(','):
    id_str = id_str.strip()
    if id_str and id_str.isdigit():
        MODERATORS.append(int(id_str))

# =============== ملفات التخزين ===============

FILES = {
    'videos': 'videos.json',
    'playlists': 'playlists.json',
    'stats': 'stats.json',
    'users': 'users.json'
}

def load_file(name):
    if os.path.exists(FILES[name]):
        with open(FILES[name], 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_file(name, data):
    with open(FILES[name], 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

videos = load_file('videos')
playlists = load_file('playlists')
stats = load_file('stats')
users = load_file('users')

# =============== دوال مساعدة ===============

def is_admin(user_id): return user_id == ADMIN_ID
def is_moderator(user_id): return user_id in MODERATORS
def is_staff(user_id): return is_admin(user_id) or is_moderator(user_id)

def save_user(user_id, username=None, first_name=None):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {'id': user_id, 'username': username, 'first_name': first_name, 'joined_at': datetime.now().isoformat()}
        save_file('users', users)

def get_users(): return list(users.keys())

def increment_view(video_name, user_id):
    if video_name not in stats:
        stats[video_name] = {'views': 0, 'users': []}
    stats[video_name]['views'] += 1
    if user_id not in stats[video_name]['users']:
        stats[video_name]['users'].append(user_id)
    save_file('stats', stats)

# =============== أزرار ===============

def btn(text, callback): return [InlineKeyboardButton(text, callback_data=callback)]
def row(*buttons): return list(buttons)
def markup(buttons): return InlineKeyboardMarkup(buttons)

# =============== المعالجات ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id, update.effective_user.username, update.effective_user.first_name)
    context.user_data.clear()
    
    if is_admin(user_id):
        await update.message.reply_text(
            f"👋 مرحباً أيها الأدمن!\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة\n👥 {len(get_users())} مستخدم\n👀 {sum(s.get('views',0) for s in stats.values())} مشاهدة",
            reply_markup=markup([
                row(btn("📹 إدارة المقاطع", 'admin_panel')),
                row(btn("📂 إدارة القوائم", 'admin_playlists')),
                row(btn("📢 الإذاعة", 'admin_broadcast')),
                row(btn("📊 الإحصائيات", 'admin_stats')),
                row(btn("🔰 العلامة المائية", 'admin_watermark'))
            ])
        )
        return
    
    if is_moderator(user_id):
        await update.message.reply_text(
            f"👋 مرحباً أيها المشرف!\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة",
            reply_markup=markup([
                row(btn("📹 إدارة المقاطع", 'admin_panel')),
                row(btn("📂 إدارة القوائم", 'admin_playlists')),
                row(btn("📊 الإحصائيات", 'admin_stats'))
            ])
        )
        return
    
    # مستخدم عادي
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context)
        else:
            await update.message.reply_text(
                f"⚠️ اشترك في القناة أولاً!\n📢 @{CHANNEL_USERNAME}",
                reply_markup=markup([
                    row(btn("📢 اشترك", f'https://t.me/{CHANNEL_USERNAME}')),
                    row(btn("✅ تحقق", 'check_subscription'))
                ])
            )
    except:
        await update.message.reply_text("⚠️ حدث خطأ!")

async def show_user_menu(update, context, edit=False):
    buttons = []
    for name in playlists:
        buttons.append(row(btn(f"📂 {name} ({len(playlists[name])})", f'playlist_{name}')))
    if videos:
        buttons.append(row(btn("🎬 جميع المقاطع", 'all_videos')))
    if not buttons:
        buttons.append(row(btn("⚠️ لا توجد مقاطع", 'no_videos')))
    
    msg = "🎥 القوائم والمقاطع المتاحة:"
    if edit and update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=markup(buttons))
    else:
        await update.message.reply_text(msg, reply_markup=markup(buttons))

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    context.user_data.clear()
    await start(update, context)

async def back_to_user_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await show_user_menu(update, context, edit=True)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', query.from_user.id)
        if member.status in ['member', 'administrator', 'creator']:
            await show_user_menu(update, context, edit=True)
        else:
            await query.message.edit_text(
                f"❌ لم تشترك بعد!\n📢 @{CHANNEL_USERNAME}",
                reply_markup=markup([
                    row(btn("📢 اشترك", f'https://t.me/{CHANNEL_USERNAME}')),
                    row(btn("✅ تحقق مرة أخرى", 'check_subscription'))
                ])
            )
    except:
        await query.answer("حدث خطأ!", show_alert=True)

# =============== المقاطع ===============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ للفريق فقط!", show_alert=True)
        return
    await query.message.edit_text(
        f"📊 لوحة الأدمن\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة",
        reply_markup=markup([
            row(btn("➕ إضافة مقطع", 'admin_add_video')),
            row(btn("❌ حذف مقطع", 'admin_delete_video')),
            row(btn("📋 عرض المقاطع", 'admin_list_videos')),
            row(btn("🗑️ حذف الكل", 'admin_delete_all')),
            row(btn("🔙 رجوع", 'back_to_start'))
        ])
    )

async def admin_add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ للفريق فقط!", show_alert=True)
        return
    context.user_data['action'] = 'waiting_video_name'
    await query.message.edit_text("📤 إضافة مقطع\n\n1️⃣ أرسل الاسم\n2️⃣ أرسل الفيديو\n🔄 /cancel للإلغاء")

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id) or context.user_data.get('action') != 'waiting_video_name':
        return
    name = update.message.text.strip()
    if name in videos:
        await update.message.reply_text(f"⚠️ يوجد مقطع باسم '{name}'")
        return
    context.user_data['video_name'] = name
    context.user_data['action'] = 'waiting_video_file'
    await update.message.reply_text(f"✅ الاسم: {name}\n📤 أرسل الفيديو الآن")

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id) or context.user_data.get('action') != 'waiting_video_file':
        return
    if not update.message.video:
        await update.message.reply_text("⚠️ أرسل فيديو!")
        return
    name = context.user_data.get('video_name', f'مقطع {len(videos)+1}')
    videos[name] = update.message.video.file_id
    save_file('videos', videos)
    context.user_data.clear()
    await update.message.reply_text(f"✅ تم إضافة {name}!\n📹 {len(videos)} مقطع")

async def admin_delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id) or not videos:
        await query.answer("⚠️ لا توجد مقاطع!", show_alert=True)
        return
    buttons = [row(btn(f"🗑️ {n}", f'delete_{n}')) for n in videos.keys()]
    buttons.append(row(btn("🔙 رجوع", 'admin_panel')))
    await query.message.edit_text("❌ اختر المقطع للحذف:", reply_markup=markup(buttons))

async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace('delete_', '')
    if name in videos:
        del videos[name]
        save_file('videos', videos)
        for p in playlists:
            if name in playlists[p]:
                playlists[p].remove(name)
                save_file('playlists', playlists)
        await query.message.edit_text(f"✅ تم حذف {name}!")
        await admin_panel(update, context)

async def admin_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    text = "📋 المقاطع:\n\n" + "\n".join(f"{i}. {n}" for i, n in enumerate(videos.keys(), 1))
    await query.message.edit_text(text, reply_markup=markup([row(btn("🔙 رجوع", 'admin_panel'))]))

async def admin_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        f"⚠️ حذف الكل؟\n📹 {len(videos)} مقطع",
        reply_markup=markup([
            row(btn("✅ نعم", 'confirm_delete_all')),
            row(btn("❌ لا", 'admin_panel'))
        ])
    )

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    videos.clear()
    save_file('videos', videos)
    for p in playlists:
        playlists[p] = []
        save_file('playlists', playlists)
    await query.message.edit_text("✅ تم الحذف!")
    await admin_panel(update, context)

# =============== القوائم ===============

async def admin_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.edit_text(
        f"📂 إدارة القوائم\n📂 {len(playlists)} قائمة\n📹 {len(videos)} مقطع",
        reply_markup=markup([
            row(btn("➕ إنشاء قائمة", 'create_playlist')),
            row(btn("📝 إضافة مقطع", 'add_to_playlist')),
            row(btn("❌ حذف قائمة", 'delete_playlist')),
            row(btn("📋 عرض القوائم", 'list_playlists')),
            row(btn("🔙 رجوع", 'back_to_start'))
        ])
    )

async def create_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_playlist_name'
    await query.message.edit_text("📂 إنشاء قائمة\n✏️ أرسل الاسم\n🔄 /cancel للإلغاء")

async def handle_playlist_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id) or context.user_data.get('action') != 'waiting_playlist_name':
        return
    name = update.message.text.strip()
    if name in playlists:
        await update.message.reply_text(f"⚠️ توجد قائمة '{name}'")
        return
    playlists[name] = []
    save_file('playlists', playlists)
    context.user_data.clear()
    await update.message.reply_text(f"✅ تم إنشاء {name}!")

async def add_to_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    buttons = [row(btn(f"📂 {n}", f'select_playlist_{n}')) for n in playlists.keys()]
    buttons.append(row(btn("🔙 رجوع", 'admin_playlists')))
    await query.message.edit_text("📂 اختر القائمة:", reply_markup=markup(buttons))

async def select_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace('select_playlist_', '')
    context.user_data['selected_playlist'] = name
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    buttons = []
    for v in videos.keys():
        if v not in playlists.get(name, []):
            buttons.append(row(btn(f"➕ {v}", f'add_video_{name}||{v}')))
    if not buttons:
        await query.message.edit_text(f"✅ كل المقاطع في {name}!")
        return
    buttons.append(row(btn("🔙 رجوع", 'admin_playlists')))
    await query.message.edit_text(f"📂 إضافة مقطع لـ {name}:", reply_markup=markup(buttons))

async def add_video_to_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace('add_video_', '')
    if '||' not in data:
        await query.answer("⚠️ خطأ!", show_alert=True)
        return
    playlist, video = data.split('||', 1)
    if playlist in playlists and video not in playlists[playlist]:
        playlists[playlist].append(video)
        save_file('playlists', playlists)
        await query.message.edit_text(f"✅ تم إضافة {video} لـ {playlist}!")
        await admin_playlists(update, context)

async def delete_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not playlists:
        await query.answer("⚠️ لا توجد قوائم!", show_alert=True)
        return
    buttons = [row(btn(f"🗑️ {n} ({len(playlists[n])})", f'delete_pl_{n}')) for n in playlists.keys()]
    buttons.append(row(btn("🔙 رجوع", 'admin_playlists')))
    await query.message.edit_text("❌ اختر القائمة للحذف:", reply_markup=markup(buttons))

async def delete_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace('delete_pl_', '')
    if name in playlists:
        del playlists[name]
        save_file('playlists', playlists)
        await query.message.edit_text(f"✅ تم حذف {name}!")
        await admin_playlists(update, context)

async def list_playlists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not playlists:
        await query.message.edit_text("⚠️ لا توجد قوائم!")
        return
    text = "📂 القوائم:\n\n" + "\n".join(f"{i}. {n} - {len(playlists[n])} مقطع" for i, n in enumerate(playlists.keys(), 1))
    await query.message.edit_text(text, reply_markup=markup([row(btn("🔙 رجوع", 'admin_playlists'))]))

async def show_playlist_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    name = query.data.replace('playlist_', '')
    if name not in playlists:
        await query.message.edit_text("⚠️ القائمة غير موجودة!")
        return
    videos_list = playlists[name]
    buttons = []
    for v in videos_list:
        if v in videos:
            buttons.append(row(btn(f"🎬 {v}", f'play_{v}')))
    if not buttons:
        buttons.append(row(btn("⚠️ فارغة", 'no_videos')))
    buttons.append(row(btn("🔙 العودة", 'back_to_user_menu')))
    await query.message.edit_text(f"📂 {name}\n📹 {len(videos_list)} مقطع", reply_markup=markup(buttons))

async def show_all_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    buttons = [row(btn(f"🎬 {n}", f'play_{n}')) for n in videos.keys()]
    buttons.append(row(btn("🔙 العودة", 'back_to_user_menu')))
    await query.message.edit_text(f"🎥 جميع المقاطع ({len(videos)})", reply_markup=markup(buttons))

# =============== تشغيل الفيديو ===============

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    name = query.data.replace('play_', '')
    
    if not is_staff(user_id):
        try:
            member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                await query.message.edit_text(
                    f"⚠️ اشترك في القناة!\n📢 @{CHANNEL_USERNAME}",
                    reply_markup=markup([
                        row(btn("📢 اشترك", f'https://t.me/{CHANNEL_USERNAME}')),
                        row(btn("✅ تحقق", 'check_subscription'))
                    ])
                )
                return
        except:
            await query.answer("حدث خطأ!", show_alert=True)
            return
    
    if name in videos:
        try:
            increment_view(name, user_id)
            caption = f"🎥 {name}"
            if os.path.exists('watermark_text.txt'):
                with open('watermark_text.txt', 'r') as f:
                    caption += f"\n\n🔰 {f.read().strip()}"
            await query.message.reply_video(videos[name], caption=caption)
        except:
            await query.message.reply_text("⚠️ حدث خطأ في الإرسال!")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== الإذاعة ===============

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    await query.message.edit_text(
        f"📢 الإذاعة\n👥 {len(get_users())} مستخدم",
        reply_markup=markup([
            row(btn("📝 نص", 'broadcast_text')),
            row(btn("🖼️ صورة + نص", 'broadcast_photo')),
            row(btn("🎬 فيديو + نص", 'broadcast_video')),
            row(btn("📊 عدد المستخدمين", 'broadcast_stats')),
            row(btn("🔙 رجوع", 'back_to_start'))
        ])
    )

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_broadcast_text'
    await query.message.edit_text("📝 أرسل النص للإذاعة:\n🔄 /cancel للإلغاء")

async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_broadcast_photo'
    await query.message.edit_text("🖼️ أرسل الصورة ثم النص:\n🔄 /cancel للإلغاء")

async def broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_broadcast_video'
    await query.message.edit_text("🎬 أرسل الفيديو ثم النص:\n🔄 /cancel للإلغاء")

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_count = len(get_users())
    text = f"📊 المستخدمين: {user_count}\n\n🆕 آخر 5:\n"
    sorted_users = sorted(users.items(), key=lambda x: x[1].get('joined_at', ''), reverse=True)
    for i, (uid, data) in enumerate(sorted_users[:5], 1):
        name = data.get('first_name', 'مجهول')
        username = data.get('username', '')
        text += f"{i}. {name} (@{username})\n"
    await query.message.edit_text(text, reply_markup=markup([row(btn("🔙 رجوع", 'admin_broadcast'))]))

# =============== معالجات الإذاعة ===============

async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_text':
        return
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ أرسل نصاً!")
        return
    await send_broadcast(update, context, text=text)
    context.user_data.clear()

async def handle_broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_photo':
        return
    if update.message.photo:
        context.user_data['broadcast_photo'] = update.message.photo[-1].file_id
        context.user_data['action'] = 'waiting_broadcast_photo_caption'
        await update.message.reply_text("✅ الصورة مستلمة!\n📝 أرسل النص (أو /skip)")
    else:
        await update.message.reply_text("⚠️ أرسل صورة!")

async def handle_broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_video':
        return
    if update.message.video:
        context.user_data['broadcast_video'] = update.message.video.file_id
        context.user_data['action'] = 'waiting_broadcast_video_caption'
        await update.message.reply_text("✅ الفيديو مستلم!\n📝 أرسل النص (أو /skip)")
    else:
        await update.message.reply_text("⚠️ أرسل فيديو!")

async def handle_broadcast_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    action = context.user_data.get('action')
    text = update.message.text.strip() if update.message.text.strip() != '/skip' else None
    
    if action == 'waiting_broadcast_photo_caption':
        photo = context.user_data.get('broadcast_photo')
        await send_broadcast(update, context, photo=photo, caption=text)
    elif action == 'waiting_broadcast_video_caption':
        video = context.user_data.get('broadcast_video')
        await send_broadcast(update, context, video=video, caption=text)
    else:
        return
    context.user_data.clear()

async def send_broadcast(update, context, text=None, photo=None, video=None, caption=None):
    user_ids = get_users()
    total = len(user_ids)
    if total == 0:
        await update.message.reply_text("⚠️ لا يوجد مستخدمين!")
        return
    
    msg = await update.message.reply_text(f"📢 جاري الإرسال... 👥 {total}")
    success, failed = 0, 0
    
    for i in range(0, total, 30):
        batch = user_ids[i:i+30]
        tasks = []
        for uid in batch:
            try:
                if photo:
                    tasks.append(context.bot.send_photo(int(uid), photo, caption=caption or text or "📢 إذاعة"))
                elif video:
                    tasks.append(context.bot.send_video(int(uid), video, caption=caption or text or "📢 إذاعة"))
                else:
                    tasks.append(context.bot.send_message(int(uid), text or "📢 إذاعة"))
            except:
                failed += 1
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success += sum(1 for r in results if not isinstance(r, Exception))
            failed += sum(1 for r in results if isinstance(r, Exception))
        if i + 30 < total:
            await asyncio.sleep(1)
    
    await msg.edit_text(f"✅ تم!\n✅ نجح: {success}\n❌ فشل: {failed}\n👥 المجموع: {total}")

# =============== الإحصائيات ===============

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ للفريق فقط!", show_alert=True)
        return
    
    total_views = sum(s.get('views', 0) for s in stats.values())
    unique_users = set()
    for s in stats.values():
        unique_users.update(s.get('users', []))
    
    top = sorted(stats.items(), key=lambda x: x[1].get('views', 0), reverse=True)[:3]
    text = f"📊 الإحصائيات\n\n📹 {len(videos)} مقطع\n📂 {len(playlists)} قائمة\n👥 {len(get_users())} مستخدم\n👀 {total_views} مشاهدة\n👤 {len(unique_users)} مستخدم فريد\n\n"
    if top:
        text += "🏆 أكثر المقاطع مشاهدة:\n" + "\n".join(f"{i}. {n} - {d.get('views',0)}" for i, (n, d) in enumerate(top, 1))
    
    await query.message.edit_text(text, reply_markup=markup([row(btn("🔙 رجوع", 'back_to_start'))]))

# =============== العلامة المائية ===============

async def admin_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ للأدمن فقط!", show_alert=True)
        return
    
    status = "❌ غير مفعلة"
    if os.path.exists('watermark.png'):
        status = "✅ مفعلة (صورة)"
    elif os.path.exists('watermark_text.txt'):
        with open('watermark_text.txt', 'r') as f:
            status = f"✅ مفعلة (نص: {f.read().strip()})"
    
    await query.message.edit_text(
        f"🔰 العلامة المائية\nالحالة: {status}",
        reply_markup=markup([
            row(btn("🖼️ صورة", 'watermark_image')),
            row(btn("📝 نص", 'watermark_text')),
            row(btn("🗑️ إزالة", 'watermark_remove')),
            row(btn("🔙 رجوع", 'back_to_start'))
        ])
    )

async def watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_watermark_image'
    await query.message.edit_text("🖼️ أرسل صورة PNG:\n🔄 /cancel للإلغاء")

async def watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['action'] = 'waiting_watermark_text'
    await query.message.edit_text("📝 أرسل النص:\n🔄 /cancel للإلغاء")

async def handle_watermark_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_watermark_text':
        return
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ أرسل نصاً!")
        return
    with open('watermark_text.txt', 'w') as f:
        f.write(text)
    context.user_data.clear()
    await update.message.reply_text(f"✅ تم تعيين النص: {text}")

async def handle_watermark_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_watermark_image':
        return
    if update.message.photo:
        await update.message.photo[-1].get_file().download_to_drive('watermark.png')
        context.user_data.clear()
        await update.message.reply_text("✅ تم تعيين الصورة!")
    else:
        await update.message.reply_text("⚠️ أرسل صورة PNG!")

async def watermark_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    removed = [f for f in ['watermark.png', 'watermark_text.txt'] if os.path.exists(f) and not os.remove(f)]
    await query.message.edit_text("✅ تم إزالة العلامة المائية!" if removed else "ℹ️ لا توجد علامة مائية!")

# =============== معالج النصوص الشامل ===============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    
    if action == 'waiting_video_name':
        await handle_video_name(update, context)
    elif action == 'waiting_playlist_name':
        await handle_playlist_name(update, context)
    elif action == 'waiting_broadcast_text':
        await handle_broadcast_text(update, context)
    elif action in ['waiting_broadcast_photo_caption', 'waiting_broadcast_video_caption']:
        await handle_broadcast_caption(update, context)
    elif action == 'waiting_watermark_text':
        await handle_watermark_text(update, context)
    else:
        await update.message.reply_text("⚠️ لا يوجد إجراء نشط. استخدم /start")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_staff(update.effective_user.id):
        context.user_data.clear()
        await update.message.reply_text("✅ تم الإلغاء!")
        await start(update, context)

# =============== main ===============

def main():
    app = Application.builder().token(TOKEN).build()
    
    # أوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # أزرار الأدمن
    app.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    app.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    app.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    app.add_handler(CallbackQueryHandler(admin_list_videos, pattern='^admin_list_videos$'))
    app.add_handler(CallbackQueryHandler(admin_delete_all, pattern='^admin_delete_all$'))
    app.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all$'))
    app.add_handler(CallbackQueryHandler(delete_video, pattern='^delete_'))
    
    # أزرار القوائم
    app.add_handler(CallbackQueryHandler(admin_playlists, pattern='^admin_playlists$'))
    app.add_handler(CallbackQueryHandler(create_playlist, pattern='^create_playlist$'))
    app.add_handler(CallbackQueryHandler(add_to_playlist, pattern='^add_to_playlist$'))
    app.add_handler(CallbackQueryHandler(select_playlist, pattern='^select_playlist_'))
    app.add_handler(CallbackQueryHandler(add_video_to_playlist, pattern='^add_video_'))
    app.add_handler(CallbackQueryHandler(delete_playlist, pattern='^delete_playlist$'))
    app.add_handler(CallbackQueryHandler(delete_playlist_callback, pattern='^delete_pl_'))
    app.add_handler(CallbackQueryHandler(list_playlists, pattern='^list_playlists$'))
    
    # أزرار المستخدم
    app.add_handler(CallbackQueryHandler(show_playlist_videos, pattern='^playlist_'))
    app.add_handler(CallbackQueryHandler(show_all_videos, pattern='^all_videos$'))
    app.add_handler(CallbackQueryHandler(back_to_user_menu, pattern='^back_to_user_menu$'))
    app.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # أزرار الإذاعة
    app.add_handler(CallbackQueryHandler(admin_broadcast, pattern='^admin_broadcast$'))
    app.add_handler(CallbackQueryHandler(broadcast_text, pattern='^broadcast_text$'))
    app.add_handler(CallbackQueryHandler(broadcast_photo, pattern='^broadcast_photo$'))
    app.add_handler(CallbackQueryHandler(broadcast_video, pattern='^broadcast_video$'))
    app.add_handler(CallbackQueryHandler(broadcast_stats, pattern='^broadcast_stats$'))
    
    # أزرار الإحصائيات والعلامة المائية
    app.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    app.add_handler(CallbackQueryHandler(admin_watermark, pattern='^admin_watermark$'))
    app.add_handler(CallbackQueryHandler(watermark_image, pattern='^watermark_image$'))
    app.add_handler(CallbackQueryHandler(watermark_text, pattern='^watermark_text$'))
    app.add_handler(CallbackQueryHandler(watermark_remove, pattern='^watermark_remove$'))
    
    # معالجات الوسائط
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    app.add_handler(MessageHandler(filters.VIDEO, handle_broadcast_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_watermark_image))
    app.add_handler(MessageHandler(filters.PHOTO, handle_broadcast_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
