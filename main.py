import telebot
import whisper
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
import os
from telebot.types import Message
from docx import Document
import PyPDF2
from dotenv import load_dotenv
from telebot import types

load_dotenv()

token  = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(token)

questions = ''
text = ''
text_from_audio = ''


model = GigaChat(
    credentials=os.getenv('CREDENTIALS'),
    scope=os.getenv('SCOPE'),
    model='GigaChat',
    verify_ssl_certs=False
)

model_whisper = whisper.load_model("base")


def pdf_to_text(pdf_path, output_txt):
    # Open the PDF file in read-binary mode
    text = ''
    with open(pdf_path, 'rb') as pdf_file:
        # Create a PdfReader object instead of PdfFileReader
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Initialize an empty string to store the text

        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()

    # Write the extracted text to a text file
    with open('output.txt', 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)


def docx_to_txt(docx_path, txt_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

bot.set_my_commands([
    types.BotCommand("start", "Запустить бота"),
    types.BotCommand("help", "Помощь"),
    types.BotCommand("question", "Задать вопрос")
])

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 👋 Отправь команду /question чтобы задать вопросы по интересующим тебя темам")

@bot.message_handler(commands=['question'])
def send_welcome(message):
    bot.reply_to(message, "Скинь лонгрид (pdf или docx) или аудио записанной лекции (mp3)")

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.reply_to(message, "Этот бот в роли преподавателя ответит на все твои вопросы по учебному материалу. Чтобы это сделать пропиши команду /start, а затем выгрузи файл с информацией или аудиофайл записанной лекции.")

@bot.message_handler(content_types=['audio'])
def handle_audio(message):
    global text
    bot.reply_to(message, 'Вижу твое сообщение! Получаю файл...')
    file_info = bot.get_file(message.audio.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    bot.reply_to(message, 'Получил твой файл! обрабатываю...')

    audio_path = "audio_file.mp3"
    with open(audio_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    print('записал файл')

    # Преобразуем аудио в текст с помощью Whisper
    result = model_whisper.transcribe(audio_path, language="ru")
    text = result["text"]



    # Отправляем текст пользователю
    print(text)
    os.remove(audio_path)

    bot.reply_to(message, 'Отправь все вопросы, которые тебя интересуют или напиши что хочешь краткий пересказ материала')
    bot.register_next_step_handler(message, handle_questions)

@bot.message_handler(content_types=['document'])
def file(message):
    global text
    bot.reply_to(message,
                 'Вижу твое сообщение! Получаю файл...')
    try:
        file_info = bot.get_file(message.document.file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_name = message.document.file_name
        save_path = os.path.join('C:/mine/programming/CU/IT-holidays/Lcracker', file_name)

        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.reply_to(message, 'Получил твой файл! обрабатываю...')

        if message.document.mime_type == 'application/pdf':  # PDF
            pdf_to_text(file_name, 'output.txt')

        if message.document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':  # docx
            docx_to_txt(file_name, 'output.txt')

        os.remove(file_name)

        with open('output.txt', 'r', encoding='utf-8') as file:
            text = file.read()


        print(text)

    except Exception as e:
        # В случае ошибки отправляем сообщение пользователю
        bot.reply_to(message, f"Ошибка при сохранении файла: {e}")

    bot.reply_to(message, 'Отправь все вопросы, которые тебя интересуют в одно сообщение или напиши, что хочешь краткий пересказ материала')

    bot.register_next_step_handler(message, handle_questions)


def handle_questions(message: Message):
    global questions
    questions = message.text
    bot.send_message(message.chat.id, f'Твои вопросы: {questions}. Сейчас подумаю над ответами...')

    # Формируем запрос
    task = f"Сейчас я пришлю тебе текст. Ответь на вопросы, которые я тебе задам. Пользуйся информацией только из данного текста, больше никакую информацию использовать нельзя. \n {text} \n Ответь на мои вопросы: {questions}"
    messages = [HumanMessage(content=task)]

    print("я сформировал request")

    # Отправляем запрос и дожидаемся ответа
    response = model.invoke(messages)
    print(response.content)

    bot.reply_to(message, response.content)

    with open('output.txt', 'w', encoding='utf-8') as file:
        file.write('')



bot.infinity_polling()

