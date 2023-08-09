#!/usr/bin/python

from dublib.Methods import Shutdown, Cls, WriteJSON
from Source.RequestsManager import RequestsManager
from Source.Functions import SecondsToTimeString
from Source.TitleParser import TitleParser
from Source.Formatter import Formatter
from dublib.Terminalyzer import *
from Source.Functions import Wait
from Source.Updater import Updater

import datetime
import logging
import json
import time
import sys
import os

#==========================================================================================#
# >>>>> ПРОВЕРКА ВЕРСИИ PYTHON <<<<< #
#==========================================================================================#

# Минимальная требуемая версия Python.
PythonMinimalVersion = (3, 10)
# Проверка соответствия.
if sys.version_info < PythonMinimalVersion:
	sys.exit("Python %s.%s or later is required.\n" % PythonMinimalVersion)

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Создать директорию для логов, если такая отсутствует.
if os.path.exists("Logs") is False:
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
# Расположении папки установки веб-драйвера в директории скрипта.
os.environ["WDM_LOCAL"] = "1"
# Отключение логов WebDriver.
os.environ["WDM_LOG"] = str(logging.NOTSET)
# Глобальные настройки.
Settings = {
	"authorization-token": "",
	"format": "dmp-v1",
	"min-delay": 1,
	"max-delay": 5,
	"use-proxy": False,
	"selenium-mode": False,
	"check-updates-period": 60,
	"use-id-instead-slug": False,
	"covers-directory": "",
	"titles-directory": "",
	"retry-tries": 3,
	"retry-delay": 15,
	"debug": False
}

# Проверка доступности файла.
if os.path.exists("Settings.json"):

	# Открытие файла настроек.
	with open("Settings.json", encoding = "utf-8") as FileRead:
		# Чтение настроек.
		Settings = json.load(FileRead)
		# Запись в лог сообщения об успешном чтении файла настроек.
		logging.info("Settings file was found.")

		# Интерпретация выходной директории обложек и коррекция пути.
		if Settings["covers-directory"] == "":
			Settings["covers-directory"] = "Covers/"
		elif Settings["covers-directory"][-1] != '/':
			Settings["covers-directory"] += "/"

		# Интерпретация выходной директории обложек и коррекция пути.
		if Settings["titles-directory"] == "":
			Settings["titles-directory"] = "Titles/"
		elif Settings["titles-directory"][-1] != '/':
			Settings["titles-directory"] += "/"

		# Запись в шапку лога выбранного режима запросов.
		if Settings["selenium-mode"] is True:
			logging.info("Requests type: Selenium (JavaScript interpreter in Google Chrome).")
		else:
			logging.info("Requests type: requests (Python library).")

		# Приведение формата описательного файла к нижнему регистру.
		Settings["format"] = Settings["format"].lower()

		# Запись в лог сообщения: формат выходного файла.
		logging.info("Output file format: \"" + Settings["format"] + "\".")

		# Запись в лог сообщения: использование ID вместо алиаса.
		if Settings["use-id-instead-slug"] == True:
			logging.info("Using ID instead slug: ON.")
		else:
			logging.info("Using ID instead slug: OFF.")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

# Список описания обрабатываемых команд.
CommandsList = list()

# Создание команды: convert.
COM_convert = Command("convert")
COM_convert.addArgument(ArgumentType.All, Important = True)
COM_convert.addArgument(ArgumentType.All, Important = True)
COM_convert.addArgument(ArgumentType.All, Important = True)
COM_convert.addFlagPosition(["s"])
CommandsList.append(COM_convert)

# Создание команды: getcov.
COM_getcov = Command("getcov")
COM_getcov.addArgument(ArgumentType.All, Important = True)
COM_getcov.addFlagPosition(["f"])
COM_getcov.addFlagPosition(["s"])
CommandsList.append(COM_getcov)

# Создание команды: parce.
COM_parce = Command("parce")
COM_parce.addArgument(ArgumentType.All, Important = True)
COM_parce.addFlagPosition(["f"])
COM_parce.addFlagPosition(["s"])
CommandsList.append(COM_parce)

# Создание команды: proxval.
COM_proxval = Command("proxval")
COM_proxval.addFlagPosition(["s"])
CommandsList.append(COM_proxval)

# Создание команды: update.
COM_update = Command("update")
COM_update.addArgument(ArgumentType.All, Important = True)
COM_update.addFlagPosition(["s"])
COM_update.addKeyPosition(["from"], ArgumentType.All)
CommandsList.append(COM_update)

# Инициализация обработчика консольных аргументов.
CAC = Terminalyzer()
# Получение информации о проверке команд.
CommandDataStruct = CAC.checkCommands(CommandsList)

# Если не удалось определить команду.
if CommandDataStruct == None:
	# Запись в лог критической ошибки: неверная команда.
	logging.critical("Unknown command.")
	# Завершение работы скрипта с кодом ошибки.
	exit(1)

#==========================================================================================#
# >>>>> ОБРАБОТКА ФЛАГОВ <<<<< #
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
if "f" in CommandDataStruct.Flags and "proxval" != CommandDataStruct.Name:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения: включён режим перезаписи.
	logging.info("Force mode: ON.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"

else:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "s" in CommandDataStruct.Flags:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the parser is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the parser is finished!\n"

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

# Обработка команды: convert.
if "convert" == CommandDataStruct.Name:
	# Запись в лог сообщения: конвертирование.
	logging.info("====== Converting ======")
	# Структура тайтла.
	Title = None
	# Имя файла тайтла.
	Filename = None	

	# Добавление расширения к файлу в случае отсутствия такового.
	if ".json" not in CommandDataStruct.Arguments[0]:
		Filename = CommandDataStruct.Arguments[0] + ".json"

	# Чтение тайтла.
	with open(Settings["titles-directory"] + Filename, encoding = "utf-8") as FileRead:
		# Декодирование файла.
		Title = json.load(FileRead)
		# Исходный формат.
		SourceFormat = None

		# Определение исходного формата.
		if CommandDataStruct.Arguments[1] == "-auto":

			# Если формат указан.
			if "format" in Title.keys():
				SourceFormat = Title["format"]

		else:
			SourceFormat = CommandDataStruct.Arguments[1]

		# Создание объекта форматирования.
		FormatterObject = Formatter(Settings, Title, Format = SourceFormat)
		# Конвертирование структуры тайтла.
		Title = FormatterObject.convert(CommandDataStruct.Arguments[2])

	# Сохранение переформатированного описательного файла.
	WriteJSON(Settings["titles-directory"] + Filename, Title)

# Обработка команды: getcov.
if "getcov" == CommandDataStruct.Name:
	# Запись в лог сообщения: заголовок парсинга.
	logging.info("====== Parcing ======")
	# Парсинг тайтла.
	LocalTitle = TitleParser(Settings, CommandDataStruct.Arguments[0], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode, Amending = False)
	# Сохранение локальных файлов тайтла.
	LocalTitle.DownloadCovers()

# Обработка команды: parce.
if "parce" == CommandDataStruct.Name:
	# Запись в лог сообщения: парсинг.
	logging.info("====== Parcing ======")
	# Парсинг тайтла.
	LocalTitle = TitleParser(Settings, CommandDataStruct.Arguments[0], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode)
	# Сохранение локальных файлов тайтла.
	LocalTitle.Save()

# Обработка команды: proxval.
if "proxval" == CommandDataStruct.Name:
	# Запись в лог сообщения: валидация.
	logging.info("====== Validation ======")
	# Очистка консоли.
	Cls()
	# Инициализация менеджера прокси.
	RequestsManagerObject = RequestsManager(Settings, True)
	# Список всех прокси.
	ProxiesList = RequestsManagerObject.GetProxies()
	# Переключатель: обновлять ли файл определений прокси.
	IsUpdateProxiesFile = False

	# Проверка флага для обновления файла определений прокси.
	if "f" in CommandDataStruct.Flags:
		IsUpdateProxiesFile = True

	# Проверка каждого прокси.
	if len(ProxiesList) > 0:
		for ProxyIndex in range(0, len(ProxiesList)):
			# Вывод результата.
			print(ProxiesList[ProxyIndex], "status code:", RequestsManagerObject.ValidateProxy(ProxiesList[ProxyIndex], IsUpdateProxiesFile))

			# Выжидание интервала.
			if ProxyIndex < len(ProxiesList) - 1:
				Wait(Settings)
		
	else:
		# Вывод в консоль: файл определений не содержит прокси.
		print("Proxies are missing.")
		# Запись в лог предупреждения: файл определений не содержит прокси.
		logging.warning("Proxies are missing.")

	# Вывод в терминал сообщения о завершении работы.
	print("\nStatus codes:\n0 – valid\n1 – invalid\n2 – forbidden\n3 – server error (502 Bad Gateway for example)\n\nPress ENTER to exit...")
	# Закрытие менеджера.
	RequestsManagerObject.Close()
	# Пауза.
	input()

# Обработка команды: update.
if "update" == CommandDataStruct.Name:
	# Запись в лог сообщения: получение списка обновлений.
	logging.info("====== Updating ======")

	# Обновить все локальные файлы.
	if "-local" in CommandDataStruct.Arguments:
		# Очистка консоли.
		Cls()
		# Вывод в консоль: идёт поиск тайтлов.
		print("Scanning titles...")
		# Получение списка файлов в директории.
		TitlesList = os.listdir(Settings["titles-directory"])
		# Фильтрация только файлов формата JSON.
		TitlesList = list(filter(lambda x: x.endswith(".json"), TitlesList))
		# Алиас стартового тайтла.
		FromTitle = None
		# Индекс обрабатываемого тайтла.
		CurrentTitleIndex = 0
		# Алиасы тайтлов.
		TitlesSlugs = list()

		# Если активирован ключ, указывающий стартовый тайтл.
		if "from" in CommandDataStruct.Keys:
			FromTitle = CommandDataStruct.Values["from"]
			
		# Чтение всех алиасов из локальных файлов.
		for File in TitlesList:
			# Открытие локального описательного файла JSON.
			with open(Settings["titles-directory"] + File, encoding = "utf-8") as FileRead:
				# JSON файл тайтла.
				LocalTitle = json.load(FileRead)

				# Помещение алиаса в список.
				if "slug" in LocalTitle.keys():
					TitlesSlugs.append(str(LocalTitle["slug"]))
				elif "dir" in LocalTitle.keys():
					TitlesSlugs.append(str(LocalTitle["dir"]))

		# Запись в лог сообщения: количество доступных для обновления тайтлов.
		logging.info("Local titles to update: " + str(len(TitlesList)) + ".")

		# Старт с указанного тайтла.
		if FromTitle is not None:
			# Запись в лог сообщения: стартовый тайтл обновления.
			logging.info("Updating starts from title with slug: \"" + FromTitle + "\".")
			# Буферный список тайтлов.
			BuferTitleSlugs = list()
			# Состояние: записывать ли тайтлы.
			IsWriteSlugs = False
				
			# Перебор тайтлов.
			for Slug in TitlesSlugs:
					
				# Если обнаружен стартовый тайтл, то включить запись тайтлов в новый список обновлений.
				if Slug == FromTitle:
					IsWriteSlugs = True
						
				# Добавить алиас в список обновляемых тайтлов.
				if IsWriteSlugs is True:
					BuferTitleSlugs.append(Slug)

			# Перезапись списка обновляемых тайтлов.
			TitlesSlugs = BuferTitleSlugs
				
		# Запись в лог сообщения: заголовок парсинга.
		logging.info("====== Parcing ======")

		# Парсинг обновлённых тайтлов.
		for Slug in TitlesSlugs:
			# Инкремент текущего индекса.
			CurrentTitleIndex += 1
			# Очистка терминала.
			Cls()
			# Вывод в терминал прогресса.
			print("Updating titles: " + str(len(TitlesList) - len(TitlesSlugs) + CurrentTitleIndex) + " / " + str(len(TitlesList)))
			# Генерация сообщения.
			ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(len(TitlesList) - len(TitlesSlugs) + CurrentTitleIndex) + " / " + str(len(TitlesList)) + "\n"
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
		# Запись в лог сообщения: заголовог парсинга.
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

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок завершения работы скрипта.
logging.info("====== Exiting ======")
# Очистка консоли.
Cls()
# Время завершения работы скрипта.
EndTime = time.time()
# Запись времени завершения работы скрипта.
logging.info("Script finished at " + str(datetime.datetime.now())[:-7] + ". Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")

# Удаление остаточных файлов.
if os.path.exists("ProxyExtension.zip"):
	os.remove("ProxyExtension.zip")

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения о немедленном выключении ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()

# Выключение логгирования.
logging.shutdown()