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

VIDEOS_FILE = 'videos.json'
STATS_FILE = 'stats.json'
USERS_FILE = 'users.json'

def load_videos():
    if os.path.exists(VIDEOS_FILE):
        with open(VIDEOS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_videos(videos):
    with open(VIDEOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

def save_stats(stats):
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

videos = load_videos()
stats = load_stats()
users = load_users()

# =============== دوال مساعدة ===============

def is_admin(user_id): return user_id == ADMIN_ID
def is_moderator(user_id): return user_id in MODERATORS
def is_staff(user_id): return is_admin(user_id) or is_moderator(user_id)

def save_user(user_id, username=None, first_name=None):
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            'id': user_id,
            'username': username,
            'first_name': first_name,
            'joined_at': datetime.now().isoformat()
        }
        save_users(users)

def get_users(): return list(users.keys())

def increment_view(video_name, user_id):
    if video_name not in stats:
        stats[video_name] = {'views': 0, 'users': []}
    stats[video_name]['views'] += 1
    if user_id not in stats[video_name]['users']:
        stats[video_name]['users'].append(user_id)
    save_stats(stats)

def get_videos_list_keyboard(back_callback='admin_panel'):
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

# =============== المعالجات ===============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    save_user(user_id, update.effective_user.username, update.effective_user.first_name)
    context.user_data.clear()
    
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📢 الإذاعة", callback_data='admin_broadcast')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🎬 عرض المقاطع", callback_data='show_all_videos')]
        ]
        await update.message.reply_text(
            f"👋 مرحباً أيها الأدمن!\n\n📹 عدد المقاطع: {len(videos)}\n👥 المستخدمين: {len(get_users())}\n👀 المشاهدات: {sum(s.get('views', 0) for s in stats.values())}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    if is_moderator(user_id):
        keyboard = [
            [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
            [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
            [InlineKeyboardButton("🎬 عرض المقاطع", callback_data='show_all_videos')]
        ]
        await update.message.reply_text(
            f"👋 مرحباً أيها المشرف!\n\n📹 عدد المقاطع: {len(videos)}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # مستخدم عادي - التحقق من الاشتراك
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            keyboard = get_videos_list_keyboard('start')
            await update.message.reply_text(
                f"🎥 **المقاطع المتاحة:** ({len(videos)})\n\nاختر المقطع لمشاهدته:",
                reply_markup=keyboard
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
            ]
            await update.message.reply_text(
                f"⚠️ **للوصول إلى المحتوى، يرجى الاشتراك في قناتنا أولاً!**\n\n📢 **قناتنا:** @{CHANNEL_USERNAME}\n\n🔹 بعد الاشتراك، اضغط على زر التحقق.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("⚠️ حدث خطأ!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_staff(update.effective_user.id):
        context.user_data.clear()
        await update.message.reply_text("✅ تم الإلغاء!")
        await start(update, context)

async def back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await start(update, context)

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    try:
        member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
        if member.status in ['member', 'administrator', 'creator']:
            keyboard = get_videos_list_keyboard('start')
            await query.message.edit_text(
                f"🎥 **المقاطع المتاحة:** ({len(videos)})\n\nاختر المقطع لمشاهدته:",
                reply_markup=keyboard
            )
        else:
            keyboard = [
                [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                [InlineKeyboardButton("✅ تحقق مرة أخرى", callback_data='check_subscription')]
            ]
            await query.message.edit_text(
                f"❌ **لم تشترك بعد!**\n\n📢 @{CHANNEL_USERNAME}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    except Exception as e:
        logger.error(f"Error: {e}")
        await query.answer("حدث خطأ!", show_alert=True)

# =============== تشغيل الفيديو ===============

async def play_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    video_name = query.data.replace('play_', '')
    
    if not is_staff(user_id):
        try:
            member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                    [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
                ]
                await query.message.edit_text(
                    f"⚠️ **يجب الاشتراك في القناة لمشاهدة المقاطع!**\n\n📢 **قناتنا:** @{CHANNEL_USERNAME}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            await query.answer("حدث خطأ!", show_alert=True)
            return
    
    if video_name in videos:
        try:
            increment_view(video_name, user_id)
            caption = f"🎥 {video_name}"
            await query.message.reply_video(videos[video_name], caption=caption)
        except Exception as e:
            logger.error(f"Error sending video: {e}")
            await query.message.reply_text("⚠️ حدث خطأ في إرسال الفيديو!")
    else:
        await query.message.reply_text("⚠️ المقطع غير موجود!")

# =============== عرض المقاطع ===============

async def show_all_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    # التحقق من الاشتراك للمستخدم العادي
    if not is_staff(user_id):
        try:
            member = await context.bot.get_chat_member(f'@{CHANNEL_USERNAME}', user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                keyboard = [
                    [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
                    [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
                ]
                await query.message.edit_text(
                    f"⚠️ **يجب الاشتراك في القناة لمشاهدة المقاطع!**\n\n📢 @{CHANNEL_USERNAME}",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        except Exception as e:
            logger.error(f"Error checking subscription: {e}")
            await query.answer("حدث خطأ!", show_alert=True)
            return
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    
    keyboard = get_videos_list_keyboard('back_to_start')
    await query.message.edit_text(
        f"🎥 **جميع المقاطع:** ({len(videos)})\n\nاختر المقطع لمشاهدته:",
        reply_markup=keyboard
    )

# =============== إدارة المقاطع (للأدمن فقط) ===============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مقطع", callback_data='admin_add_video')],
        [InlineKeyboardButton("❌ حذف مقطع", callback_data='admin_delete_video')],
        [InlineKeyboardButton("📋 عرض المقاطع", callback_data='admin_list_videos')],
        [InlineKeyboardButton("🗑️ حذف الكل", callback_data='admin_delete_all')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    await query.message.edit_text(
        f"📊 **لوحة تحكم الأدمن**\n\n📹 عدد المقاطع: {len(videos)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_add_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    context.user_data['action'] = 'waiting_video_name'
    await query.message.edit_text(
        "📤 **إضافة مقطع جديد**\n\n"
        "1️⃣ أرسل **اسم** المقطع\n"
        "2️⃣ ثم أرسل **الفيديو**\n\n"
        "🔄 للإلغاء أرسل /cancel"
    )

async def handle_video_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id) or context.user_data.get('action') != 'waiting_video_name':
        return
    
    video_name = update.message.text.strip()
    if video_name in videos:
        await update.message.reply_text(f"⚠️ يوجد مقطع بنفس الاسم '{video_name}'")
        return
    
    context.user_data['video_name'] = video_name
    context.user_data['action'] = 'waiting_video_file'
    await update.message.reply_text(f"✅ تم حفظ الاسم: **{video_name}**\n\n📤 أرسل الفيديو الآن")

async def handle_video_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_staff(update.effective_user.id) or context.user_data.get('action') != 'waiting_video_file':
        await update.message.reply_text("⚠️ لا يوجد إجراء نشط لإضافة فيديو.")
        return
    
    if not update.message.video:
        await update.message.reply_text("⚠️ يرجى إرسال **فيديو** وليس نص أو صورة.")
        return
    
    try:
        file_id = update.message.video.file_id
        video_name = context.user_data.get('video_name', f'مقطع {len(videos) + 1}')
        
        videos[video_name] = file_id
        save_videos(videos)
        
        context.user_data.clear()
        await update.message.reply_text(
            f"✅ **تم إضافة المقطع بنجاح!**\n\n"
            f"📌 الاسم: **{video_name}**\n"
            f"📹 عدد المقاطع الآن: {len(videos)}"
        )
    except Exception as e:
        logger.error(f"Error saving video: {e}")
        await update.message.reply_text("⚠️ حدث خطأ أثناء حفظ الفيديو!")

async def admin_delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    if not videos:
        await query.answer("⚠️ لا توجد مقاطع!", show_alert=True)
        return
    
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f'delete_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')])
    
    await query.message.edit_text("❌ **اختر المقطع للحذف:**", reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    video_name = query.data.replace('delete_', '')
    
    if video_name in videos:
        del videos[video_name]
        save_videos(videos)
        await query.message.edit_text(f"✅ تم حذف **{video_name}** بنجاح!")
        await admin_panel(update, context)
    else:
        await query.answer("❌ المقطع غير موجود!", show_alert=True)

async def admin_list_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    if not videos:
        await query.message.edit_text("⚠️ لا توجد مقاطع!")
        return
    
    text = "📋 **قائمة المقاطع:**\n\n"
    for i, name in enumerate(videos.keys(), 1):
        text += f"{i}. **{name}**\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_panel')]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ نعم", callback_data='confirm_delete_all')],
        [InlineKeyboardButton("❌ لا", callback_data='admin_panel')]
    ]
    await query.message.edit_text(
        f"⚠️ **تحذير!**\n\nهل أنت متأكد من حذف جميع المقاطع؟\n📹 عدد المقاطع: {len(videos)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def confirm_delete_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    videos.clear()
    save_videos(videos)
    
    await query.message.edit_text("✅ تم حذف جميع المقاطع بنجاح!")
    await admin_panel(update, context)

# =============== الإذاعة ===============

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton("📝 رسالة نصية", callback_data='broadcast_text')],
        [InlineKeyboardButton("🖼️ صورة + نص", callback_data='broadcast_photo')],
        [InlineKeyboardButton("🎬 فيديو + نص", callback_data='broadcast_video')],
        [InlineKeyboardButton("📊 عدد المستخدمين", callback_data='broadcast_stats')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    await query.message.edit_text(
        f"📢 **لوحة الإذاعة**\n\n👥 عدد المستخدمين المسجلين: {len(get_users())}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['action'] = 'waiting_broadcast_text'
    await query.message.edit_text(
        "📝 **إذاعة نصية**\n\n✏️ أرسل النص الذي تريد إذاعته:\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['action'] = 'waiting_broadcast_photo'
    await query.message.edit_text(
        "🖼️ **إذاعة مع صورة**\n\n1️⃣ أرسل **الصورة**\n2️⃣ ثم أرسل **النص**\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    context.user_data['action'] = 'waiting_broadcast_video'
    await query.message.edit_text(
        "🎬 **إذاعة مع فيديو**\n\n1️⃣ أرسل **الفيديو**\n2️⃣ ثم أرسل **النص**\n\n🔄 للإلغاء أرسل /cancel"
    )

async def broadcast_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_admin(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للأدمن فقط!", show_alert=True)
        return
    
    user_count = len(get_users())
    text = f"📊 **إحصائيات المستخدمين**\n\n👥 عدد المستخدمين: {user_count}\n"
    
    if user_count > 0:
        text += "\n🆕 **آخر 5 مستخدمين:**\n"
        sorted_users = sorted(users.items(), key=lambda x: x[1].get('joined_at', ''), reverse=True)
        for i, (uid, data) in enumerate(sorted_users[:5], 1):
            name = data.get('first_name', 'مجهول')
            username = data.get('username', '')
            text += f"{i}. {name} (@{username})\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='admin_broadcast')]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# =============== معالجات الإذاعة ===============

async def handle_broadcast_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_text':
        return
    
    text = update.message.text.strip()
    if not text:
        await update.message.reply_text("⚠️ يرجى إرسال نص صحيح!")
        return
    
    await send_broadcast(update, context, text=text)
    context.user_data.clear()

async def handle_broadcast_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_photo':
        await update.message.reply_text("⚠️ لا يوجد إجراء نشط لإذاعة صورة.")
        return
    
    if update.message.photo:
        context.user_data['broadcast_photo'] = update.message.photo[-1].file_id
        context.user_data['action'] = 'waiting_broadcast_photo_caption'
        await update.message.reply_text("✅ تم استلام الصورة!\n\n📝 أرسل النص المرافق (أو /skip للتخطي):")
    else:
        await update.message.reply_text("⚠️ يرجى إرسال صورة!")

async def handle_broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or context.user_data.get('action') != 'waiting_broadcast_video':
        await update.message.reply_text("⚠️ لا يوجد إجراء نشط لإذاعة فيديو.")
        return
    
    if update.message.video:
        context.user_data['broadcast_video'] = update.message.video.file_id
        context.user_data['action'] = 'waiting_broadcast_video_caption'
        await update.message.reply_text("✅ تم استلام الفيديو!\n\n📝 أرسل النص المرافق (أو /skip للتخطي):")
    else:
        await update.message.reply_text("⚠️ يرجى إرسال فيديو!")

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
    
    msg = await update.message.reply_text(f"📢 جاري إرسال الإذاعة...\n👥 المستخدمين: {total}")
    
    success = 0
    failed = 0
    
    for i in range(0, total, 30):
        batch = user_ids[i:i+30]
        tasks = []
        
        for uid in batch:
            try:
                if photo:
                    tasks.append(context.bot.send_photo(
                        chat_id=int(uid),
                        photo=photo,
                        caption=caption or text or "📢 إذاعة من البوت"
                    ))
                elif video:
                    tasks.append(context.bot.send_video(
                        chat_id=int(uid),
                        video=video,
                        caption=caption or text or "📢 إذاعة من البوت"
                    ))
                else:
                    tasks.append(context.bot.send_message(
                        chat_id=int(uid),
                        text=text or "📢 إذاعة من البوت"
                    ))
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send broadcast to {uid}: {e}")
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, Exception):
                    failed += 1
                else:
                    success += 1
        
        if i + 30 < total:
            await asyncio.sleep(1)
    
    await msg.edit_text(
        f"✅ **تم إرسال الإذاعة!**\n\n"
        f"✅ نجح: {success}\n"
        f"❌ فشل: {failed}\n"
        f"👥 المجموع: {total}"
    )

# =============== الإحصائيات ===============

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if not is_staff(query.from_user.id):
        await query.answer("⚠️ هذا الإجراء للفريق فقط!", show_alert=True)
        return
    
    total_views = sum(s.get('views', 0) for s in stats.values())
    total_users = set()
    for s in stats.values():
        total_users.update(s.get('users', []))
    
    sorted_videos = sorted(stats.items(), key=lambda x: x[1].get('views', 0), reverse=True)
    top_videos = sorted_videos[:3]
    
    text = f"📊 **الإحصائيات**\n\n"
    text += f"📹 المقاطع: {len(videos)}\n"
    text += f"👥 المستخدمين: {len(get_users())}\n"
    text += f"👀 المشاهدات: {total_views}\n"
    text += f"👤 مستخدمين فريدين: {len(total_users)}\n\n"
    
    if top_videos:
        text += "🏆 **أكثر المقاطع مشاهدة:**\n"
        for i, (name, data) in enumerate(top_videos, 1):
            text += f"{i}. {name} - {data.get('views', 0)} مشاهدة\n"
    
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]]
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

# =============== معالج النصوص الشامل ===============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get('action')
    
    if action == 'waiting_video_name':
        await handle_video_name(update, context)
    elif action == 'waiting_broadcast_text':
        await handle_broadcast_text(update, context)
    elif action in ['waiting_broadcast_photo_caption', 'waiting_broadcast_video_caption']:
        await handle_broadcast_caption(update, context)
    else:
        await update.message.reply_text("⚠️ لا يوجد إجراء نشط. استخدم /start")

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
    
    # أزرار المستخدم
    app.add_handler(CallbackQueryHandler(show_all_videos, pattern='^show_all_videos$'))
    app.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    app.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # الإذاعة
    app.add_handler(CallbackQueryHandler(admin_broadcast, pattern='^admin_broadcast$'))
    app.add_handler(CallbackQueryHandler(broadcast_text, pattern='^broadcast_text$'))
    app.add_handler(CallbackQueryHandler(broadcast_photo, pattern='^broadcast_photo$'))
    app.add_handler(CallbackQueryHandler(broadcast_video, pattern='^broadcast_video$'))
    app.add_handler(CallbackQueryHandler(broadcast_stats, pattern='^broadcast_stats$'))
    
    # الإحصائيات
    app.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    
    # معالجات الوسائط
    app.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    app.add_handler(MessageHandler(filters.VIDEO, handle_broadcast_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_broadcast_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    logger.info("🚀 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
