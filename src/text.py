"""
Bot text messages.
"""

# Command responses
help_msg = """
📚 *ReadLater Bot* 📚

Этот бот поможет вам сохранять и организовывать материалы для чтения/просмотра на потом.

Основные команды:
• Отправьте ссылку, чтобы добавить материал
• /last - получить последний добавленный материал
• /random - получить случайный непрочитанный материал

Чтобы увидеть все материалы, нажмите кнопку "Все" в меню.
"""

# Material handling
material_received_msg = "📌 Получено! Материал добавлен в вашу коллекцию."
ask_content_type_msg = "Выберите тип контента:"
video_type_msg = "▶️ Видео"
text_type_msg = "📃 Текст"
skip_type_msg = "⏩ Skip this step"
content_type_selected_msg = "Тип контента установлен: {content_type}"
content_skipped_msg = "⏩ Skipped, moving forward..."
ask_tags_msg = "Выберите теги или добавьте новый:"
skip_tags_msg = "⏩ Skip this step"
add_new_tag_msg = "🎳 Добавить новый тег"
tag_selected_msg = "🎳 Тег добавлен: {tag_name}"
new_tag_prompt_msg = "🚦 Отправьте название для нового тега:"
tag_skipped_msg = "⏩ Done with tags."
material_saved_msg = "🌱 Материал сохранен! Вы можете просмотреть его позже."

# Error messages
not_url_msg = "Это не похоже на ссылку. Пожалуйста, отправьте корректную ссылку."
