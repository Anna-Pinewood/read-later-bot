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

# Getting materials
no_materials_msg = "🔍 У вас пока нет сохраненных материалов. Отправьте мне ссылку или сообщение, чтобы добавить первый материал!"
no_unread_materials_msg = "📭 У вас нет непрочитанных материалов. Попробуйте использовать команду /all, чтобы увидеть все ваши материалы, включая прочитанные."
mark_as_read_msg = "✅ Прочитано"
mark_as_unread_msg = "❌ Не прочитано"
material_marked_as_read_msg = "📝 Материал отмечен как прочитанный! Теперь команды /random и /last будут показывать другие непрочитанные материалы."

# Material info template
material_info_template = """
📎

{content}

📋 <b>Информация</b>
• Тип: {content_type}
• Добавлено: {date_added}
• Статус: {status}
"""

# Error messages
not_url_msg = "Это не похоже на ссылку. Пожалуйста, отправьте корректную ссылку."
