import telebot
from telebot import types
import random
import logging
from db import SQLighter
import json
'''import schedule
import time'''



with open("intents.json", "r", encoding = 'utf-8') as read_file:
    data = json.load(read_file)

#logs
logger = telebot.logging
logger.basicConfig(filename='history.log', level=logging.DEBUG, encoding='utf-8')


#DB
dbase = SQLighter('db1.db')


bot = telebot.TeleBot('1745020237:AAGYnbRhHf8ZnImx1nYqyHq8j0hkELADuno', parse_mode='html')

#/reg - реєстрація користувача в базі даних
@bot.message_handler(commands = ['reg'])
def registr (message):
	markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	item1 = types.KeyboardButton("Зареєстрований")
	item2 = types.KeyboardButton("Зареєструватись")
	markup.add(item1,item2)
	bot.send_message(message.chat.id, "Вітаю, {0.first_name}!\nВи можете зареєструватись для отримання інформації з бази даних!".format(message.from_user), reply_markup = markup)
	bot.register_next_step_handler(message,step_reg_1)

def step_reg_1 (message):
	if message.text == "Зареєструватись":
		if (not dbase.user_exist(message.chat.id)):
			markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
			item1 = types.KeyboardButton("Пацієнт")
			item2 = types.KeyboardButton("Лікар")
			markup.add(item1,item2)
			bot.send_message(message.from_user.id, "Введіть роль ", reply_markup = markup)
			bot.register_next_step_handler(message,step_reg_2)
		else: bot.send_message(message.from_user.id, "Ви вже зареєстровані ")

def step_reg_2 (message):
	dbase.add_role(message.chat.id, message.text)
	bot.send_message(message.from_user.id, "Введіть логін ")
	bot.register_next_step_handler(message,step_reg_3)

def step_reg_3 (message):
	dbase.add_login(message.text)
	bot.send_message(message.from_user.id, "Введіть пароль ")
	bot.register_next_step_handler(message,step_reg_4)

def step_reg_4 (message):
	dbase.add_password(message.text)
	bot.send_message(message.from_user.id, "Ви зареєструвались")

#/start
@bot.message_handler(commands = ['start'])
def welcome (message):
	sti = open(r'C:\Project\medical_bot\Project_files\AnimatedSticker.tgs','rb')
	bot.send_sticker(message.chat.id, sti)
	a = telebot.types.ReplyKeyboardRemove()
	bot.send_message(message.chat.id, "Вітаю, {0.first_name}!\nЯ - <b>{1.first_name}</b>, постараюсь домогти Вам! Щоб розпочати роботу достатньо всього лиш привітатись".format(message.from_user, bot.get_me()), reply_markup=a)

#/help
@bot.message_handler(commands = ['help'])
def help (message):
	bot.send_message(message.chat.id, "Список команд:\n1.\\start - початкова інформація\n2.\\reg - реєстрація в базі даних\n3.\\return - повертає на start")

#/return
@bot.message_handler(commands = ['return'])
def first_step (message):
		welcome(message)

#Прийом тексту незалежно від рулів
@bot.message_handler(content_types=['text'])
def get_text_messages(message):
	if message.text in data['Corpus']['Greetings']:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Для пацієнта")
		item2 = types.KeyboardButton("Для лікаря")
		markup.add(item1,item2)
		bot.send_message(message.from_user.id, "Доброго дня, виберіть, яку інформацію Ви бажаєте отримати", reply_markup = markup)
		bot.register_next_step_handler(message,process_step)
	elif message.text in data['Corpus']['Goodbye']:
		bot.send_message(message.from_user.id, random.choice(data['Responses']['Goodbye_bot']))
	elif message.text in data['Corpus']['Gratitude']:
		bot.send_message(message.from_user.id, random.choice(data['Responses']['Gratitude_bot']))


#Крок після визначення ролі
def process_step(message):
	if message.text == 'Для пацієнта':
		bot.send_message(message.chat.id, 'Як ви себе почуваєте?')
		bot.register_next_step_handler(message,patient_step)
	elif message.text == 'Для лікаря':
		if 'Лікар' in dbase.user_provider(message.chat.id):
			bot.send_message(message.chat.id, 'Введіть пароль: ')
			bot.register_next_step_handler(message,provider_step_1)
		else: bot.send_message(message.chat.id, 'Вам доступна інформація лише для пацієнта.')

def provider_step_1(message):
	if message.text == dbase.pass_check(message.chat.id):
		bot.send_message(message.chat.id, 'Остання перевірка: Скільки днів бажано консервативно лікувати пацієнта з гострим панкреатитом перед оперативним втручанням?')
		bot.register_next_step_handler(message,provider_step)

#Гілка Лікаря
def provider_step(message):
	sti = open(r'C:\Project\medical_bot\Project_files\AnimatedSticker1.tgs','rb')
	bot.send_sticker(message.chat.id, sti)
	if message.text == '14':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
		item1 = types.KeyboardButton("Гострий апендицит")
		item2 = types.KeyboardButton("Гострий панкреатит")
		item3 = types.KeyboardButton("Гострий холецистит")
		item4 = types.KeyboardButton("Защемлена грижа")
		item5 = types.KeyboardButton("Гостра кишкова непрохідність")
		item6 = types.KeyboardButton("Політравма")
		item7 = types.KeyboardButton("Шлунково-кишкова кровотеча")
		item8 = types.KeyboardButton("Перфоративна виразка шлунка")
		markup.add(item1,item2,item3,item4,item5,item6,item7,item8)
		bot.send_message(message.chat.id, 'Вітаю в лікарській базі, виберіть патологію: ', reply_markup = markup)
		bot.register_next_step_handler(message,patology)
	else:
		bot.send_message(message.chat.id, 'Ви відповіли невірно, спробуйте ще раз', parse_mode = 'html')
		bot.register_next_step_handler(message,provider_step)
#Інформація по патологіям
def patology(message):
	if message.text == 'Гострий апендицит':
		doc = open(r'C:\Project\medical_bot\Project_files\ГА.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Гострий панкреатит':
		doc = open(r'C:\Project\medical_bot\Project_files\ГП.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Гострий холецистит':
		doc = open(r'C:\Project\medical_bot\Project_files\ГХ.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Гостра кишкова непрохідність':
		doc = open(r'C:\Project\medical_bot\Project_files\ГКН.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Защемлена грижа':
		doc = open(r'C:\Project\medical_bot\Project_files\ЗГ.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Перфоративна виразка шлунка':
		doc = open(r'C:\Project\medical_bot\Project_files\ПВ.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Шлунково-кишкова кровотеча':
		doc = open(r'C:\Project\medical_bot\Project_files\ШКК.txt', 'r',encoding = 'utf-8')
		doc1 = doc.read()
		doc.close
		bot.send_message(message.chat.id, doc1)
		bot.register_next_step_handler(message,patology)
	elif message.text == 'Політравма':
		doc = open(r'C:\Project\medical_bot\Project_files\ПТР.txt', 'rb')
		bot.send_document(message.chat.id, doc)
		bot.register_next_step_handler(message,patology)

#Гілка пацієнта
def patient_step(message):
	if message.text == 'Добре':
		bot.send_message(message.chat.id, 'Радий чути це')
	elif message.text == 'Погано':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Біль в животі")
		item2 = types.KeyboardButton("Блювота")
		item3 = types.KeyboardButton("Лихоманка")
		markup.add(item1,item2,item3)
		bot.send_message(message.chat.id, 'Шкода це чути. Що вас турбує?',reply_markup = markup)
		bot.register_next_step_handler(message,symptoms)
	else:
		bot.send_message(message.chat.id, 'Варіанти відповідей: Добре або Погано')
		bot.register_next_step_handler(message,patient_step)

#Симптоми з кнопками їх диференціації
def symptoms(message):
	if message.text == 'Біль в животі':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Навколо пупка")
		item2 = types.KeyboardButton("В ділянці шлунка")
		item3 = types.KeyboardButton("У правій здухвинній ділянці")
		item4 = types.KeyboardButton("У правому підребер'ї")
		markup.add(item1,item2,item3,item4)
		bot.send_message(message.chat.id, 'Де саме знаходиться біль?',reply_markup = markup)
		bot.register_next_step_handler(message,aches)
	elif message.text == 'Блювота':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Одноразова, приносить полегшення")
		item2 = types.KeyboardButton("Одноразова, не приносить полегшення")
		item3 = types.KeyboardButton("Багаторазова, не приносить полегшення")
		markup.add(item1,item2,item3)
		bot.send_message(message.chat.id, 'Виберіть тип блювоти',reply_markup = markup)
		bot.register_next_step_handler(message,vomiting)
	elif message.text == 'Лихоманка':
		bot.send_message(message.chat.id, 'Поміряйте температуру, якщо > 37.8 - показані антипіретики. Якщо наявні симптоми COVID-19 зателефонуйте сімейному лікарю. Якщо відчуваєте задишку показана КТ ОГК')
#Диференціація болю
def aches(message):
	if message.text in ['Навколо пупка',"В ділянці шлунка","У правій здухвинній ділянці","У правому підребер'ї"]:
		bot.send_message(message.chat.id, '1. Прийміть спазмолітик (не анальгетик, погіршить діагностику);\n2. Сконтактуйте з сімейним лікарем;\n3. Показані УЗД ОЧП, ФГДС')
#Диференціація блювоти
def vomiting(message):
	if message.text in ["Одноразова, приносить полегшення", "Одноразова, не приносить полегшення", "Багаторазова, не приносить полегшення"]:
		bot.send_message(message.chat.id, '1. Прийміть спазмолітик, метоклопрамід;\n2. Сконтактуйте з сімейним лікарем;\n3. Показані УЗД ОЧП, ФГДС')

'''@bot.message_handler(content_types=['text'])
def test_send_message():
	text = 'Доброго ранку, як Ви себе почуваєте?'
	bot.send_message(dbase.user_id('Пацієнт'), text)

schedule.every().day.at("14:26").do(test_send_message)
while True:
	schedule.run_pending()
	time.sleep(1)'''

if __name__ == '__main__':
	bot.polling(none_stop=True, interval=0)

