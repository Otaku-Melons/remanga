#!/usr/bin/python

import datetime
import logging
import json
import time
import sys
import os

sys.path.append("Source")

from Functions import SecondsToTimeString
from TitleParser import TitleParser
from Updater import Updater
from DUBLIB import Shutdown
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

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs\\" + str(CurrentDate)[:-7] + ".log"
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
	"tome-to-tom": True,
	"delay": 5,
	"use-proxy": False,
    "proxy": [],
	"check-updates-period": 60
	}

# Проверка доступности файла.
if os.path.exists("Settings.json"):
	# Открытие файла настроек.
	with open("Settings.json") as FileRead:
		Settings = json.load(FileRead)
		# Проверка успешной загрузки файла.
		if Settings == None:
			# Запись в лог ошибки о невозможности прочитать битый файл.
			logging.error("Unable to read \"Settings.json\". File is broken.")
		else:
			# Запись в лог сообщения об успешном чтении файла настроек.
			logging.info("Settings file was found.")

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
		LocalTitle = TitleParser(Settings, sys.argv[2], ForceMode = IsForceModeActivated, Message = InFuncMessage_ForceMode)
		# Сохранение локальных файлов тайтла.
		LocalTitle.Save()

	# Загрузка обложки.
	elif sys.argv[1] == "getcov":
		# Вывод в лог заголовка: парсинг.
		logging.info("====== Parcing ======")
		# Парсинг тайтла.
		LocalTitle = TitleParser(Settings, sys.argv[2], ForceMode = IsForceModeActivated, Message = InFuncMessage_ForceMode, Amending = False)
		# Сохранение локальных файлов тайтла.
		LocalTitle.DownloadCovers()

# Однокомпонентные команды: update.
if len(sys.argv) >= 2:

	# Парсинг тайтлов, обновлённых за указанный в настройках интервал.
	if sys.argv[1] == "update":
		# Вывод в лог заголовка: обновление.
		logging.info("====== Updating ======")

		# Обновить все локальные файлы.
		if sys.argv[2] == "-local":
			# Получение списка файлов в директории.
			TitlesList = os.listdir("Titles\\")
			# Фильтрация только файлов формата JSON.
			TitlesList = list(filter(lambda x: x.endswith(".json"), TitlesList))
			# Индекс обрабатываемого тайтла.
			CurrentTitleIndex = 0
			# Запись в лог сообщения о количестве локальных тайтлов.
			logging.info("Local titles to update: " + str(len(TitlesList)) + ".")
			# Вывод в лог заголовка: парсинг.
			logging.info("====== Parcing ======")

			# Парсинг обновлённых тайтлов.
			for Slug in TitlesList:
				# Инкремент текущего индекса.
				CurrentTitleIndex += 1
				# Очистка терминала.
				Cls()
				# Вывод в терминал прогресса.
				print("Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(TitlesList)))
				# Генерация сообщения.
				ExternalMessage = InFuncMessage_ForceMode + "Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(TitlesList)) + "\n"
				# Парсинг тайтла.
				LocalTitle = TitleParser(Settings, Slug.replace(".json", ""), ForceMode = IsForceModeActivated, Message = ExternalMessage)
				# Сохранение локальных файлов тайтла.
				LocalTitle.Save()

				# Выжидание указанного интервала, если не все обложки загружены.
				if CurrentTitleIndex < len(TitlesList):
					time.sleep(Settings["delay"])

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
				ExternalMessage = InFuncMessage_ForceMode + "Updating titles: " + str(CurrentTitleIndex) + " / " + str(len(UpdatedTitlesList)) + "\n"
				# Парсинг тайтла.
				LocalTitle = TitleParser(Settings, Slug, ForceMode = IsForceModeActivated, Message = ExternalMessage)
				# Сохранение локальных файлов тайтла.
				LocalTitle.Save()

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