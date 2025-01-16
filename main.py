import requests
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from config import TELEGRAM_TOKEN, MINIMAX_API_KEY, MINIMAX_API_URL

# Функция для генерации видео через MiniMax API
def generate_video(prompt):
    payload = json.dumps({
        "model": "video-01",
        "prompt": prompt
    })
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }

    response = requests.post(MINIMAX_API_URL, headers=headers, data=payload)

    if response.status_code == 200:
        video_data = response.json()
        task_id = video_data.get('task_id')  # Получаем task_id
        return task_id
    else:
        return f"Ошибка: {response.status_code} - {response.text}"

# Функция для получения ссылки на готовое видео по task_id
def get_video_file(task_id):
    status_url = f"https://api.minimaxi.chat/v1/query/video_generation?task_id={task_id}"
    headers = {
        'Authorization': f'Bearer {MINIMAX_API_KEY}',
        'Content-Type': 'application/json'
    }

    response = requests.get(status_url, headers=headers)

    if response.status_code == 200:
        video_data = response.json()
        file_url = video_data.get('file', {}).get('download_url')  # Получаем ссылку на видео
        return file_url
    else:
        return f"Ошибка: {response.status_code} - {response.text}"

# Обработчик команды /start
async def start(update: Update, context: CallbackContext):
    keyboard = [["Запросить все видео"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

# Обработчик команды /launch
async def launch(update: Update, context: CallbackContext):
    if update.message and context.args:
        prompt = ' '.join(context.args)
        task_id = generate_video(prompt)

        if isinstance(task_id, str) and task_id.startswith("Ошибка"):
            await update.message.reply_text(f"Произошла ошибка при генерации видео: {task_id}")
            return

        await update.message.reply_text(f"Видео создается! Task ID: {task_id}. Ожидайте.")

        # Получаем ссылку на готовое видео
        video_url = get_video_file(task_id)
        if video_url.startswith("http"):
            await update.message.reply_text(f"Видео готово! Скачайте его здесь: {video_url}")
        else:
            await update.message.reply_text(f"Статус видео: {video_url}")
    else:
        await update.message.reply_text("Пожалуйста, укажите описание для видео после команды /launch.")

# Обработчик кнопки "Запросить все видео"
async def get_videos(update: Update, context: CallbackContext):
    if update.message:
        videos = get_all_videos()

        if videos:
            message = "Доступные видео:\n\n"
            for video in videos:
                message += f"Видео Task ID: {video['task_id']} - [Скачать видео]({video['url']})\n"
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("Видео не найдены.")

# Основная функция
def main():
    # Проверка наличия токенов
    if not TELEGRAM_TOKEN or not MINIMAX_API_KEY:
        raise ValueError("Убедитесь, что TELEGRAM_TOKEN и MINIMAX_API_KEY указаны в config.py")

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("launch", launch))
    application.add_handler(MessageHandler(filters.Text(["Запросить все видео"]), get_videos))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
