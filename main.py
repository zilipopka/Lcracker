import telebot
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
import os
from telebot.types import Message
from docx import Document
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

token  = os.getenv('TELEGRAM_TOKEN')

bot = telebot.TeleBot(token)

questions = ''
text = ''


model = GigaChat(
    credentials=os.getenv('CREDENTIALS'),
    scope=os.getenv('SCOPE'),
    model='GigaChat',
    verify_ssl_certs=False
)


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

    print('PDF')




def docx_to_txt(docx_path, txt_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

    print('DOCX')



@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 👋 Скинь лонгрид")

@bot.message_handler(content_types=['document'])
def file(message):
    global text
    try:
        file_info = bot.get_file(message.document.file_id)

        downloaded_file = bot.download_file(file_info.file_path)

        file_name = message.document.file_name
        save_path = os.path.join('C:/mine/programming/CU/IT-holidays/Lcracker', file_name)

        with open(save_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Отправляем подтверждение пользователю
        bot.reply_to(message, f"Файл '{file_name}' успешно сохранен!")

        print(message.document.mime_type)

        if message.document.mime_type == 'application/pdf':  # PDF
            print('im here')
            pdf_to_text(file_name, 'output.txt')

        if message.document.mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':  # docx
            print('lol')
            docx_to_txt(file_name, 'output.txt')

        with open('output.txt', 'r', encoding='utf-8') as file:
            text = file.read()


        print(text)

    except Exception as e:
        # В случае ошибки отправляем сообщение пользователю
        bot.reply_to(message, f"Ошибка при сохранении файла: {e}")

    bot.reply_to(message, 'Отправь все вопросы, которые тебя интересуют')

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



bot.infinity_polling()

