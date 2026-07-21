#bot.py 
import os
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from utils import TOKEN, videos, playlists, stats, users
from handlers import (
    start, cancel, show_user_menu, show_all_videos, back_to_start, back_to_user_menu,
    play_video, check_subscription, admin_panel, admin_add_video, admin_delete_video,
    delete_video_callback, admin_list_videos, admin_delete_all, confirm_delete_all,
    admin_playlists, create_playlist, add_to_playlist, select_playlist_for_add,
    add_video_to_playlist_callback, delete_playlist, delete_playlist_callback,
    list_playlists, create_sub_playlist, select_sub_parent, handle_sub_playlist_name,
    reorder_playlist_select, reorder_playlist, show_reorder_options,
    move_video_up, move_video_down, skip_reorder, finish_reorder,
    show_playlist_videos, admin_broadcast, broadcast_text, broadcast_photo,
    broadcast_video, broadcast_stats, handle_broadcast_text,
    handle_broadcast_photo, handle_broadcast_photo_caption,
    handle_broadcast_video, handle_broadcast_video_caption,
    admin_stats, admin_watermark, watermark_image, watermark_text,
    handle_watermark_text, handle_watermark_image, watermark_remove,
    handle_text_messages, handle_video_file, handle_video_name
)

logger = logging.getLogger(__name__)

def main():
    application = Application.builder().token(TOKEN).build()
    
    # أوامر عامة
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("cancel", cancel))
    
    # لوحة الأدمن
    application.add_handler(CallbackQueryHandler(admin_panel, pattern='^admin_panel$'))
    application.add_handler(CallbackQueryHandler(admin_add_video, pattern='^admin_add_video$'))
    application.add_handler(CallbackQueryHandler(admin_delete_video, pattern='^admin_delete_video$'))
    application.add_handler(CallbackQueryHandler(admin_list_videos, pattern='^admin_list_videos$'))
    application.add_handler(CallbackQueryHandler(admin_delete_all, pattern='^admin_delete_all$'))
    application.add_handler(CallbackQueryHandler(confirm_delete_all, pattern='^confirm_delete_all$'))
    application.add_handler(CallbackQueryHandler(delete_video_callback, pattern='^delete_video_'))
    
    # القوائم
    application.add_handler(CallbackQueryHandler(admin_playlists, pattern='^admin_playlists$'))
    application.add_handler(CallbackQueryHandler(create_playlist, pattern='^create_playlist$'))
    application.add_handler(CallbackQueryHandler(create_sub_playlist, pattern='^create_sub_playlist$'))
    application.add_handler(CallbackQueryHandler(select_sub_parent, pattern='^sub_parent_'))
    application.add_handler(CallbackQueryHandler(add_to_playlist, pattern='^add_to_playlist$'))
    application.add_handler(CallbackQueryHandler(select_playlist_for_add, pattern='^select_playlist_'))
    application.add_handler(CallbackQueryHandler(add_video_to_playlist_callback, pattern='^add_video_to_'))
    application.add_handler(CallbackQueryHandler(delete_playlist, pattern='^delete_playlist$'))
    application.add_handler(CallbackQueryHandler(delete_playlist_callback, pattern='^delete_playlist_'))
    application.add_handler(CallbackQueryHandler(list_playlists, pattern='^list_playlists$'))
    
    # ترتيب القوائم
    application.add_handler(CallbackQueryHandler(reorder_playlist_select, pattern='^reorder_playlist_select$'))
    application.add_handler(CallbackQueryHandler(reorder_playlist, pattern='^reorder_'))
    application.add_handler(CallbackQueryHandler(move_video_up, pattern='^move_up_'))
    application.add_handler(CallbackQueryHandler(move_video_down, pattern='^move_down_'))
    application.add_handler(CallbackQueryHandler(skip_reorder, pattern='^skip_reorder$'))
    application.add_handler(CallbackQueryHandler(finish_reorder, pattern='^finish_reorder$'))
    
    # المستخدمين
    application.add_handler(CallbackQueryHandler(show_playlist_videos, pattern='^playlist_'))
    application.add_handler(CallbackQueryHandler(show_all_videos, pattern='^all_videos$'))
    application.add_handler(CallbackQueryHandler(back_to_user_menu, pattern='^back_to_user_menu$'))
    application.add_handler(CallbackQueryHandler(play_video, pattern='^play_'))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern='^check_subscription$'))
    application.add_handler(CallbackQueryHandler(back_to_start, pattern='^back_to_start$'))
    
    # الإحصائيات
    application.add_handler(CallbackQueryHandler(admin_stats, pattern='^admin_stats$'))
    
    # الإذاعة
    application.add_handler(CallbackQueryHandler(admin_broadcast, pattern='^admin_broadcast$'))
    application.add_handler(CallbackQueryHandler(broadcast_text, pattern='^broadcast_text$'))
    application.add_handler(CallbackQueryHandler(broadcast_photo, pattern='^broadcast_photo$'))
    application.add_handler(CallbackQueryHandler(broadcast_video, pattern='^broadcast_video$'))
    application.add_handler(CallbackQueryHandler(broadcast_stats, pattern='^broadcast_stats$'))
    
    # العلامة المائية
    application.add_handler(CallbackQueryHandler(admin_watermark, pattern='^admin_watermark$'))
    application.add_handler(CallbackQueryHandler(watermark_image, pattern='^watermark_image$'))
    application.add_handler(CallbackQueryHandler(watermark_text, pattern='^watermark_text$'))
    application.add_handler(CallbackQueryHandler(watermark_remove, pattern='^watermark_remove$'))
    
    # معالجة الوسائط
    application.add_handler(MessageHandler(filters.VIDEO, handle_video_file))
    application.add_handler(MessageHandler(filters.VIDEO, handle_broadcast_video))
    application.add_handler(MessageHandler(filters.PHOTO, handle_watermark_image))
    application.add_handler(MessageHandler(filters.PHOTO, handle_broadcast_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    
    # تشغيل البوت
    if os.getenv('RAILWAY_ENVIRONMENT'):
        logger.info("Starting bot in Railway mode...")
        application.run_polling()
    else:
        logger.info("Starting bot in local mode...")
        application.run_polling()

if __name__ == '__main__':
    main()
