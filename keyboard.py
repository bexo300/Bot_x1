from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_keyboard(videos_count=0, playlists_count=0, users_count=0, total_views=0):
    """لوحة تحكم الأدمن الرئيسية"""
    keyboard = [
        [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
        [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
        [InlineKeyboardButton("📢 الإذاعة", callback_data='admin_broadcast')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')],
        [InlineKeyboardButton("🔰 العلامة المائية", callback_data='admin_watermark')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_moderator_keyboard():
    """لوحة تحكم المشرف"""
    keyboard = [
        [InlineKeyboardButton("📹 إدارة المقاطع", callback_data='admin_panel')],
        [InlineKeyboardButton("📂 إدارة القوائم", callback_data='admin_playlists')],
        [InlineKeyboardButton("📊 الإحصائيات", callback_data='admin_stats')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_user_menu_keyboard(playlists=None, videos=None):
    """قائمة المستخدم العادي"""
    keyboard = []
    
    if playlists:
        for name in playlists.keys():
            count = len(playlists[name])
            keyboard.append([InlineKeyboardButton(f"📂 {name} ({count})", callback_data=f'playlist_{name}')])
    
    if videos:
        keyboard.append([InlineKeyboardButton("🎬 جميع المقاطع", callback_data='all_videos')])
    
    if not videos and not playlists:
        keyboard.append([InlineKeyboardButton("⚠️ لا توجد مقاطع", callback_data='no_videos')])
    
    return InlineKeyboardMarkup(keyboard)

def get_subscription_keyboard():
    """أزرار الاشتراك في القناة"""
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=f'https://t.me/{CHANNEL_USERNAME}')],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data='check_subscription')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_panel_keyboard():
    """لوحة إدارة المقاطع"""
    keyboard = [
        [InlineKeyboardButton("➕ إضافة مقطع", callback_data='admin_add_video')],
        [InlineKeyboardButton("❌ حذف مقطع", callback_data='admin_delete_video')],
        [InlineKeyboardButton("📋 عرض المقاطع", callback_data='admin_list_videos')],
        [InlineKeyboardButton("🗑️ حذف الكل", callback_data='admin_delete_all')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_playlists_admin_keyboard():
    """لوحة إدارة القوائم"""
    keyboard = [
        [InlineKeyboardButton("➕ إنشاء قائمة", callback_data='create_playlist')],
        [InlineKeyboardButton("📂 قائمة فرعية", callback_data='create_sub_playlist')],
        [InlineKeyboardButton("📝 إضافة مقطع", callback_data='add_to_playlist')],
        [InlineKeyboardButton("↕️ ترتيب المقاطع", callback_data='reorder_playlist_select')],
        [InlineKeyboardButton("❌ حذف قائمة", callback_data='delete_playlist')],
        [InlineKeyboardButton("📋 عرض القوائم", callback_data='list_playlists')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_broadcast_keyboard():
    """لوحة الإذاعة"""
    keyboard = [
        [InlineKeyboardButton("📝 رسالة نصية", callback_data='broadcast_text')],
        [InlineKeyboardButton("🖼️ صورة + نص", callback_data='broadcast_photo')],
        [InlineKeyboardButton("🎬 فيديو + نص", callback_data='broadcast_video')],
        [InlineKeyboardButton("📊 عدد المستخدمين", callback_data='broadcast_stats')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_watermark_keyboard():
    """لوحة العلامة المائية"""
    keyboard = [
        [InlineKeyboardButton("🖼️ صورة", callback_data='watermark_image')],
        [InlineKeyboardButton("📝 نص", callback_data='watermark_text')],
        [InlineKeyboardButton("🗑️ إزالة", callback_data='watermark_remove')],
        [InlineKeyboardButton("🔙 رجوع", callback_data='back_to_start')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback_data='back_to_start'):
    """زر رجوع عام"""
    keyboard = [[InlineKeyboardButton("🔙 رجوع", callback_data=callback_data)]]
    return InlineKeyboardMarkup(keyboard)

def get_confirm_delete_keyboard(videos_count=0):
    """تأكيد حذف الكل"""
    keyboard = [
        [InlineKeyboardButton("✅ نعم", callback_data='confirm_delete_all')],
        [InlineKeyboardButton("❌ لا", callback_data='admin_panel')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reorder_keyboard(index, total):
    """أزرار ترتيب المقاطع"""
    keyboard = []
    if index > 0:
        keyboard.append([InlineKeyboardButton("⬆️ لأعلى", callback_data=f'move_up_{index}')])
    if index < total - 1:
        keyboard.append([InlineKeyboardButton("⬇️ لأسفل", callback_data=f'move_down_{index}')])
    
    keyboard.append([InlineKeyboardButton("✅ تخطي", callback_data='skip_reorder')])
    keyboard.append([InlineKeyboardButton("🔙 إنهاء", callback_data='finish_reorder')])
    
    return InlineKeyboardMarkup(keyboard)

def get_videos_list_keyboard(videos, back_callback='admin_panel'):
    """قائمة المقاطع مع أزرار"""
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🗑️ {name}", callback_data=f'delete_video_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_playlists_list_keyboard(playlists, back_callback='admin_playlists'):
    """قائمة القوائم مع أزرار"""
    keyboard = []
    for name in playlists.keys():
        count = len(playlists[name])
        keyboard.append([InlineKeyboardButton(f"🗑️ {name} ({count})", callback_data=f'delete_playlist_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data=back_callback)])
    return InlineKeyboardMarkup(keyboard)

def get_all_videos_keyboard(videos):
    """عرض جميع المقاطع للمستخدم"""
    keyboard = []
    for name in videos.keys():
        keyboard.append([InlineKeyboardButton(f"🎬 {name}", callback_data=f'play_{name}')])
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_user_menu')])
    return InlineKeyboardMarkup(keyboard)

def get_playlist_videos_keyboard(playlist_name, videos_list, sub_playlists, videos):
    """عرض مقاطع القائمة مع القوائم الفرعية"""
    keyboard = []
    
    for sub_name in sub_playlists:
        display_name = sub_name.replace(f"{playlist_name} › ", "")
        count = len(sub_playlists[sub_name]) if isinstance(sub_playlists, dict) else 0
        keyboard.append([InlineKeyboardButton(f"📂 {display_name} ({count})", callback_data=f'playlist_{sub_name}')])
    
    for video_name in videos_list:
        if video_name in videos:
            keyboard.append([InlineKeyboardButton(f"🎬 {video_name}", callback_data=f'play_{video_name}')])
    
    keyboard.append([InlineKeyboardButton("🔙 العودة", callback_data='back_to_user_menu')])
    return InlineKeyboardMarkup(keyboard)
