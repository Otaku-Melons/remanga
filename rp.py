#!/usr/bin/python

import datetime
import logging
import json
import time
import sys
import os

sys.path.append("Source")

from Functions import SecondsToTimeString
from ProxyManager import ProxyManager
from TitleParser import TitleParser
from Updater import Updater
from DUBLIB import Shutdown
from Functions import Wait
from DUBLIB import Cls

#==========================================================================================#
# >>>>> ПРОВЕРКА ВЕРСИИ PYTHON <<<<< #
#==========================================================================================#

# Минимальная требуемая версия Python.
PythonMinimalVersion = (3, 9)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Создать директорию для логов, если такая отсутствует.
if os.path.exists("Logs/") is False:
	os.makedirs("Logs")

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(':', '-')
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO)

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#
# Вывод в лог заголовка: подготовка скрипта к работе.
logging.info("====== Preparing to starting ======")
# Запись в лог используемой версии Python.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")
# Запись времени начала работы скрипта.
logging.info("Script started at " + str(CurrentDate)[:-7] + ".")
# Запись команды, использовавшейся для запуска скрипта.
logging.info("Launch command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".")
# Хранилище настроек.
Settings = {
	"authorization": "",
	"native-formatting": True,
	"min-delay": 5,
	"max-delay": 15,
	"use-proxy": False,
	"check-updates-period": 60,
	"use-id-instead-slug": False,
	"covers-directory": "",
	"JSON-directory": "",
	"captcha-solver": {
		"provider": "",
		"api_key": ""
	}
}

# Проверка доступности файла.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json") as FileRead:
		# Чтение настроек.
		Settings = json.load(FileRead)
		# Запись в лог сообщения об успешном чтении файла настроек.
		logging.info("Settings file was found.")

		# Интерпретация выходной директории обложек.
		if Settings["covers-directory"] == "":
			Settings["covers-directory"] = "Covers/"

		# Интерпретация выходной директории обложек.
		if Settings["JSON-directory"] == "":
			Settings["JSON-directory"] = "Titles/"

#==========================================================================================#
# >>>>> ОБРАБОТКА СПЕЦИАЛЬНЫХ ФЛАГОВ <<<<< #
#==========================================================================================#

# Активна ли опция выключения компьютера по завершении работы парсера.
IsShutdowAfterEnd = False
# Сообщение для внутренних функций: выключение ПК.
InFuncMessage_Shutdown = ""
# Активен ли режим перезаписи при парсинге.
IsForceModeActivated = False
# Сообщение для внутренних функций: режим перезаписи.
InFuncMessage_ForceMode = ""

# Обработка флага: режим перезаписи.
if "-f" in sys.argv:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения о включении режима перезаписи.
	logging.info("Force mode: ON")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"
else:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "-s" in sys.argv:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the parser is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the parser is finished!\n"

#==========================================================================================#
# >>>>> ОБРАБОТКА ОСНОВНЫХ КОММАНД <<<<< #
#==========================================================================================#

# Двухкомпонентные команды: getcov, parce.
if len(sys.argv) >= 3:

	# Парсинг тайтла.
	if sys.argv[1] == "parce":
		# Вывод в лог заголовка: парсинг.
		logging.info("====== Parcing ======")
		# Парсинг тайтла.
		LocalTitle = TitleParser(Settings, sys.argv[2], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode)
		# Сохранение локальных файлов тайтла.
		LocalTitle.Save()

	# Загрузка обложки.
	elif sys.argv[1] == "getcov":
		# Вывод в лог заголовка: парсинг.
		logging.info("====== Parcing ======")
		# Парсинг тайтла.
		LocalTitle = TitleParser(Settings, sys.argv[2], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode, Amending = False)
		# Сохранение локальных файлов тайтла.
		LocalTitle.DownloadCovers()

# Однокомпонентные команды: update.
if len(sys.argv) >= 2:

	# Парсинг тайтлов, обновлённых за указанный в настройках интервал.
	if sys.argv[1] == "update":
		# Вывод в лог заголовка: обновление.
		logging.info("====== Updating ======")

		# Обновить все локальные файлы.
		if len(sys.argv) >= 3 and sys.argv[2] == "-local":
			# Получение списка файлов в директории.
			TitlesList = os.listdir(Settings["JSON-directory"])
			# Фильтрация только файлов формата JSON.
			TitlesList = list(filter(lambda x: x.endswith(".json"), TitlesList))
			# Индекс обрабатываемого тайтла.
			CurrentTitleIndex = 0
			# Запись в лог сообщения о количестве локальных тайтлов.
			logging.info("Local titles to update: " + str(len(TitlesList)) + ".")
			# Вывод в лог заголовка: парсинг.
			logging.info("====== Parcing ======")
			# Алиасы тайтлов.
			TitlesSlugs = list()

			# Чтение всех алиасов из локальных файлов.
			for File in TitlesList:
				# Открытие локального описательного файла JSON.
				with open(Settings["JSON-directory"] + File, encoding = "utf-8") as FileRead:
					# JSON файл тайтла.
					LocalTitle = json.load(FileRead)
					# Помещение алиаса в список.
					if "slug" in LocalTitle.keys():
						TitlesSlugs.append(str(LocalTitle["slug"]))
					elif "dir" in LocalTitle.keys():
						TitlesSlugs.append(str(LocalTitle["dir"]))

			# Парсинг обновлённых тайтлов.
			for Slug in TitlesSlugs:
				# Инкремент текущего индекса.
				CurrentTitleIndex += 1
				# Очистка терминала.
				Cls()
				# Вывод в терминал прогресса.
				print("Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(TitlesSlugs)))
				# Генерация сообщения.
				ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(TitlesSlugs)) + "\n"
				# Парсинг тайтла.
				LocalTitle = TitleParser(Settings, Slug.replace(".json", ""), ForceMode = IsForceModeActivated, Message = ExternalMessage)
				# Сохранение локальных файлов тайтла.
				LocalTitle.Save()

				# Выжидание указанного интервала, если не все обложки загружены.
				if CurrentTitleIndex < len(TitlesSlugs):
					Wait(Settings)

		# Обновить изменённые на сервере за последнее время тайтлы.
		else:
			# Инициализация проверки обновлений.
			UpdateChecker = Updater(Settings)
			# Получение списка обновлённых тайтлов.
			UpdatedTitlesList = UpdateChecker.GetUpdatesList()
			# Индекс обрабатываемого тайтла.
			CurrentTitleIndex = 0
			# Вывод в лог заголовка: парсинг.
			logging.info("====== Parcing ======")

			# Парсинг обновлённых тайтлов.
			for Slug in UpdatedTitlesList:
				# Инкремент текущего индекса.
				CurrentTitleIndex += 1
				# Генерация сообщения.
				ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(UpdatedTitlesList)) + "\n"
				# Парсинг тайтла.
				LocalTitle = TitleParser(Settings, Slug, ForceMode = IsForceModeActivated, Message = ExternalMessage)
				# Сохранение локальных файлов тайтла.
				LocalTitle.Save()

	# Проверка валидности прокси-серверов.
	elif sys.argv[1] == "proxval":
		# Вывод в лог заголовка: обновление.
		logging.info("====== Validation ======")
		# Очистка консоли.
		Cls()
		# Инициализация менеджера прокси.
		ProxyManagerObject = ProxyManager(Settings)
		# Список всех прокси.
		ProxiesList = ProxyManagerObject.GetProxies()

		# Проверка каждого прокси.
		for ProxyIndex in range(0, len(ProxiesList)):
			# Вывод результата.
			print(ProxiesList[ProxyIndex], "status code:", ProxyManagerObject.ValidateProxy(ProxyIndex))

			# Выжидание интервала.
			if ProxyIndex < len(ProxiesList) - 1:
				Wait(Settings)

		# Вывод в терминал сообщения о завершении работы.
		print("\nStatus codes:\n0 – invalid\n1 – valid\n2 – frobidden\n3 – raise Cloudflare V2 captcha4 – server error (502 Bad Gateway for example)\n\n\nPress ENTER to exit...")
		# Пауза.
		input()

# Обработка исключения: недостаточно аргументов.
elif len(sys.argv) == 1:
	logging.error("Not enough arguments.")

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

# Вывод в лог заголовка: завершение работы.
logging.info("====== Exiting ======")

# Очистка консоли.
Cls()

# Время завершения работы скрипта.
EndTime = time.time()
# Запись времени завершения работы скрипта.
logging.info("Script finished at " + str(datetime.datetime.now())[:-7] + ". Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения о немедленном выключении ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()

# Выключение логгирования.
logging.shutdown()