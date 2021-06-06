import config
import random
import logging
import time
import json
import datetime
import random
import os
import re
import hashlib
from typing import Text
import telebot
from telebot import types
from db import SQLighter
import schedule
from multiprocessing import *


daily = []
now = datetime.datetime.now()

with open("intents.json", "r", encoding = 'utf-8') as read_file:
    data = json.load(read_file)

#logs
logger = telebot.logging
logger.basicConfig(filename='history.log', level=logging.DEBUG, encoding='utf-8')

#DB
dbase = SQLighter('db1.db')
#Config
bot = telebot.TeleBot(config.TOKEN, parse_mode='html')

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
		else: 
			bot.send_message(message.from_user.id, "Ви вже зареєстровані ")
			bot.register_next_step_handler(message,first_step)

def step_reg_2 (message):
	dbase.add_role(message.chat.id, message.text)
	bot.send_message(message.from_user.id, "Введіть email ")
	bot.register_next_step_handler(message,step_reg_3)

def step_reg_3 (message):
	dbase.add_login(message.text)
	if 'Лікар' in dbase.user_provider(message.chat.id):
		bot.send_message(message.from_user.id, "Введіть пароль ")
		bot.register_next_step_handler(message,step_reg_4)
	else:
		bot.send_message(message.from_user.id, "Ви зареєструвались, для продовження роботи привітайтесь")

salt = os.urandom(32)
def step_reg_4 (message):
	password = message.text
	key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
	dbase.add_password(key)
	bot.send_message(message.from_user.id, "Ви зареєструвались, для продовження роботи привітайтесь")

#/start
@bot.message_handler(commands = ['start'])
def welcome (message):
	sti = open(r'C:\Project\medical_bot\Project_files\AnimatedSticker.tgs','rb')
	bot.send_sticker(message.chat.id, sti)
	a = telebot.types.ReplyKeyboardRemove()
	bot.send_message(message.chat.id, "Вітаю, {0.first_name}!\nЯ - <b>{1.first_name}</b>, постараюсь домогти Вам! Щоб розпочати роботу зареєструйтесь - напишіть /reg".format(message.from_user, bot.get_me()), reply_markup=a)

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
def get_text_messages(message): #Розділення сценаріїв щодо ролі
	if message.text in data['Corpus']['Greetings']:
		if 'Лікар' in dbase.user_provider(message.chat.id):
			markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
			item = types.KeyboardButton("Інформаційна база")
			markup.add(item)
			bot.send_message(message.chat.id, 'Вітаю! Для отримання інформації натисніть кнопку нижче. ', reply_markup = markup)
			bot.register_next_step_handler(message,process_step)
		elif 'Пацієнт' in dbase.user_provider(message.chat.id):
			markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
			item = types.KeyboardButton("Моніторинг")
			markup.add(item)
			bot.send_message(message.from_user.id, "Вітаю! Для початку опитування натисніть кнопку нижче.", reply_markup = markup)
			bot.register_next_step_handler(message,process_step)
	elif message.text in data['Corpus']['Goodbye']:
		bot.send_message(message.from_user.id, random.choice(data['Responses']['Goodbye_bot']))
	elif message.text in data['Corpus']['Gratitude']:
		bot.send_message(message.from_user.id, random.choice(data['Responses']['Gratitude_bot']))
	if message.text in data['Corpus']['Well']:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.from_user.id, 'Радий це чути. Бажаєте пройти опитувальник?', reply_markup = markup)
		bot.register_next_step_handler(message,everyday_symptoms)
		daily.append(message.text)
	elif message.text in data['Corpus']['Bad']:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.from_user.id, 'Бажаєте пройти опитувальник?', reply_markup = markup)
		bot.register_next_step_handler(message,everyday_symptoms)
		daily.append(message.text)


#Крок після визначення ролі
def process_step(message):
	if message.text == 'Моніторинг':
		bot.send_message(message.chat.id, 'Як ви себе почуваєте?')
		daily.append(message.text)
		bot.register_next_step_handler(message,patient_step)
	elif message.text == 'Інформаційна база':
		if 'Лікар' in dbase.user_provider(message.chat.id):
			bot.send_message(message.chat.id, 'Введіть пароль: ')
			bot.register_next_step_handler(message,provider_step_1)
		else: bot.send_message(message.chat.id, 'Вам доступна інформація лише для пацієнта.')
	elif message.text == '/return':
		welcome(message)
def provider_step_1(message):
	new_pass = hashlib.pbkdf2_hmac('sha256',message.text.encode('utf-8'), salt, 100000)
	print(new_pass)
	print(dbase.pass_check(message.chat.id))
	if new_pass == dbase.pass_check(message.chat.id):
		bot.send_message(message.chat.id, 'Остання перевірка: Скільки днів бажано консервативно лікувати пацієнта з гострим панкреатитом перед оперативним втручанням?')
		bot.register_next_step_handler(message,provider_step)

#Гілка Лікаря
def provider_step(message):
	sti = open(r'C:\Project\medical_bot\Project_files\AnimatedSticker1.tgs','rb')
	bot.send_sticker(message.chat.id, sti)
	if message.text == '14':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
		item1 = types.KeyboardButton("Перша допомога")
		item2 = types.KeyboardButton("Протоколи операцій")
		markup.add(item1,item2)
		bot.send_message(message.chat.id, 'Вітаю в лікарській базі!', reply_markup = markup)
		bot.register_next_step_handler(message,provider_step_urgent)
	else:
		bot.send_message(message.chat.id, 'Ви відповіли невірно, спробуйте ще раз', parse_mode = 'html')
		bot.register_next_step_handler(message,provider_step)
	if message.text == '/return':
		welcome(message)

def provider_step_urgent(message):
	if message.text == 'Перша допомога':
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
	elif message.text == 'Протоколи операцій':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
		item1 = types.KeyboardButton("Рандомний протокол")
		markup.add(item1)
		#protocols = open(random.choice(os.listdir('Протоколи для бота')), 'rb')
		bot.send_message(message.chat.id, 'Натиснувши на кнопку, ви отримаєте випадковий протокол ', reply_markup = markup)
		#bot.send_document(message.from_user.id, protocols, reply_markup = markup)
		bot.register_next_step_handler(message,protocols)
	if message.text == '/return':
		welcome(message)

#Протоколи операцій
def protocols(message):
	if message.text == 'Рандомний протокол':
		directory = 'C:\Project\medical_bot\Протоколи для бота'
		all_files_in_directory = os.listdir(directory) 
		protocol = random.choice(all_files_in_directory)
		doc = open(directory + '/' + protocol, 'rb')
		bot.send_document(message.from_user.id, doc) #Надсилаємо рандомний протокол з папки
		bot.register_next_step_handler(message,protocols)
	if message.text == '/return':
		welcome(message)

#Інформація по патологіям (Перша допомога)
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
	if message.text == '/return':
		welcome(message)

#Гілка пацієнта
def patient_step(message):
	if message.text in data['Corpus']['Well']:
		bot.send_message(message.chat.id, 'Радий чути це')
		print(daily)
	elif message.text in data['Corpus']['Bad']:
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Біль в животі")
		item2 = types.KeyboardButton("Блювота")
		item3 = types.KeyboardButton("Лихоманка")
		markup.add(item1,item2,item3)
		bot.send_message(message.chat.id, 'Шкода це чути. Що вас турбує?',reply_markup = markup)
		bot.register_next_step_handler(message,symptoms)
	else:
		bot.send_message(message.chat.id, 'Перефразуйте, будь ласка')
		bot.register_next_step_handler(message,patient_step)
	if message.text == '/return':
		welcome(message)
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
	if message.text == '/return':
		welcome(message)
#Диференціація болю
def aches(message):
	if message.text in ['Навколо пупка',"В ділянці шлунка","У правій здухвинній ділянці","У правому підребер'ї"]:
		bot.send_message(message.chat.id, '1. Прийміть спазмолітик (не анальгетик, погіршить діагностику);\n2. Сконтактуйте з сімейним лікарем;\n3. Показані УЗД ОЧП, ФГДС')
	if message.text == '/return':
		welcome(message)
#Диференціація блювоти
def vomiting(message):
	if message.text in ["Одноразова, приносить полегшення", "Одноразова, не приносить полегшення", "Багаторазова, не приносить полегшення"]:
		bot.send_message(message.chat.id, '1. Прийміть спазмолітик, метоклопрамід;\n2. Сконтактуйте з сімейним лікарем;\n3. Показані УЗД ОЧП, ФГДС')
	if message.text == '/return':
		welcome(message)

#Щоденний опитувальник
def everyday_symptoms(message):
	if message.text == 'Так':
		bot.send_message(message.chat.id, 'Поміряйте, будь ласка, температуру і напишіть її.')
		bot.register_next_step_handler(message,everyday_symptoms_1)
		daily.append(message.text)
	elif message.text == 'Ні':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.chat.id, "Не ризикуйте своїм здоров'ям, при наявності симптомів запалення (лихоманка, почервоніння навколо рани, гнійні виділення з рани) зверніться до лікаря!")
		bot.register_next_step_handler(message,everyday_symptoms_1)
		a = f'Пацієнт відмовився від опитування.'
		dbase.set_msg(a,message.chat.id)

def everyday_symptoms_1(message):
	if message.text == re.match(r'\d{2}\.\d*', message.text).group(0):
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.chat.id, 'Чи є почервоніння навколо рани?',reply_markup = markup)
		bot.register_next_step_handler(message,everyday_symptoms_2)
		daily.append(message.text)

def everyday_symptoms_2(message):
	if message.text == 'Ні':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.chat.id, 'У Вас наявні виділення з рани?',reply_markup = markup)
		bot.register_next_step_handler(message,everyday_symptoms_3)
		daily.append(message.text)
	elif message.text == 'Так':
		markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
		item1 = types.KeyboardButton("Так")
		item2 = types.KeyboardButton("Ні")
		markup.add(item1,item2)
		bot.send_message(message.chat.id, "У Вас наявні виділення з рани?",reply_markup = markup)
		daily.append(message.text)
		bot.register_next_step_handler(message,everyday_symptoms_3)

#В кінці опитувальника, дані будуть вноситись в щоденник і через 5 хвилин надсилатись лікарю
def everyday_symptoms_3(message):
	if message.text == 'Ні':
		bot.send_message(message.chat.id, 'На сьогодні все, ваш щоденник буде надіслано Вашому лікарю')
		bot.register_next_step_handler(message,symptoms)
		daily.append(message.text)
		if daily[0] in data['Corpus']['Well']:
			a = f'{now.strftime("%d-%m-%Y")} - {message.from_user.first_name} {message.from_user.last_name} - Пацієнт почуває себе задовільно, температура - "{daily[2]}°C", наявність почервоніння навколо рани - "{daily[3]}", наявність виділень з рани - "{daily[4]}"'
			dbase.set_msg(a,message.chat.id)
		else:
			a = f'{now.strftime("%d-%m-%Y")} - {message.from_user.first_name} {message.from_user.last_name} - Загальний стан хворого середньої важкості, температура - "{daily[2]}°C", наявність почервоніння навколо рани - "{daily[3]}", наявність виділень з рани - "{daily[4]}"'
			dbase.set_msg(a,message.chat.id)
		
	elif message.text == 'Так':
		bot.send_message(message.chat.id, "На сьогодні все, ваш щоденник буде надіслано Вашому лікарю")
		daily.append(message.text)
		if daily[0] in data['Corpus']['Well']:
			a = f'{now.strftime("%d-%m-%Y")} - {message.from_user.first_name} {message.from_user.last_name} - Пацієнт почуває себе задовільно, температура - "{daily[2]}°C", наявність почервоніння навколо рани - "{daily[3]}", наявність виділень з рани - "{daily[4]}"'
			dbase.set_msg(a,message.chat.id)
		else:
			a = f'{now.strftime("%d-%m-%Y")} - {message.from_user.first_name} {message.from_user.last_name} - Загальний стан хворого середньої важкості, температура - "{daily[2]}°C", наявність почервоніння навколо рани - "{daily[3]}", наявність виділень з рани - "{daily[4]}"'
			dbase.set_msg(a,message.chat.id)
	

#Заплановане повідомлення
def start_process():
	p1 = Process(target = P_schedule.start_schedule, args =()).start()
class P_schedule():
	def start_schedule():
		schedule.every().day.at("13:56").do(test_send_message) #Заплановане повідомлення пацієнту
		schedule.every().day.at("13:57").do(test_prov_message) #Заплановане повідомлення пацієнту
		while True:
			schedule.run_pending()
			time.sleep(1)
def test_send_message():
	text = "Доброго ранку, у зв'язку з раннім післяопераційним періодом, рекомендовано щоденний моніторинг Вашого здоров'я. Як ви себе почуваєте?"
	bot.send_message(dbase.user_id('Пацієнт'), text)
def test_prov_message():
	msg = dbase.msg_to_prov()
	for i in msg:
		for j in i:
			bot.send_message(dbase.user_id('Лікар'), i)

@bot.message_handler(content_types=['photo'])
def handle_docs_photo(message):
    try:
		
        file_info = bot.get_file(message.photo[len(message.photo)-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        src= file_info.file_path
        bot.send_photo(dbase.user_id('Лікар'), downloaded_file, f'Фото рани пацієнта - John Doe')
        bot.reply_to(message,"Фото надіслано лікарю") 

    except Exception as e:
        bot.reply_to(message,e )
	
if __name__ == '__main__':
	start_process()
	try:
		bot.polling(none_stop=True, interval=0)
	except:
		pass



