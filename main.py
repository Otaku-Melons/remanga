from dublib.Methods import CheckPythonMinimalVersion, Cls, MakeRootDirectories, ReadJSON, Shutdown, WriteJSON
from Source.Functions import ManageOtherFormatsFiles, SecondsToTimeString
from dublib.Terminalyzer import ArgumentsTypes, Terminalyzer, Command
from Source.RequestsManager import RequestsManager
from Source.Collector import Collector
from Source.Formatter import Formatter
from Source.Builder import Builder
from Source.Updater import Updater
from Source.Parser import Parser
from time import sleep

import datetime
import logging
import json
import time
import sys
import os

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

# Проверка поддержки используемой версии Python.
CheckPythonMinimalVersion(3, 10)
# Создание папок в корневой директории.
MakeRootDirectories(["Logs"])
# Переключатель: удалять ли лог по завершению работы.
REMOVE_LOGFILE = False
# Код выполнения.
EXIT_CODE = 0

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ ЛОГОВ <<<<< #
#==========================================================================================#

# Получение текущей даты.
CurrentDate = datetime.datetime.now()
# Время запуска скрипта.
StartTime = time.time()
# Формирование пути к файлу лога.
LogFilename = "Logs/" + str(CurrentDate)[:-7] + ".log"
LogFilename = LogFilename.replace(":", "-")
# Установка конфигнурации.
logging.basicConfig(filename = LogFilename, encoding = "utf-8", level = logging.INFO, format = "%(asctime)s %(levelname)s: %(message)s", datefmt = "%Y-%m-%d %H:%M:%S")

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Вывод в лог заголовка: подготовка скрипта к работе.
logging.info("====== Preparing to starting ======")
# Запись в лог используемой версии Python.
logging.info("Starting with Python " + str(sys.version_info.major) + "." + str(sys.version_info.minor) + "." + str(sys.version_info.micro) + " on " + str(sys.platform) + ".")
# Запись команды, использовавшейся для запуска скрипта.
logging.info("Launch command: \"" + " ".join(sys.argv[1:len(sys.argv)]) + "\".")
# Глобальные настройки.
Settings = ReadJSON("Settings.json")

# Форматирование настроек.
if not Settings["token"].startswith("bearer "): Settings["token"] = "bearer " + Settings["token"]
if Settings["covers-directory"] == "": Settings["covers-directory"] = "Covers"
Settings["covers-directory"] = Settings["covers-directory"].replace("\\", "/").rstrip("/")
if Settings["titles-directory"] == "": Settings["titles-directory"] = "Titles"
Settings["titles-directory"] = Settings["titles-directory"].replace("\\", "/").rstrip("/")

# Приведение формата описательного файла к нижнему регистру.
Settings["format"] = Settings["format"].lower()
# Запись в лог сообщения: формат выходного файла.
logging.info("Output file format: \"" + Settings["format"] + "\".")
# Запись в лог сообщения: использование ID вместо алиаса.
logging.info("Using ID instead slug: ON." if Settings["use-id-instead-slug"] == True else "Using ID instead slug: OFF.")
# Запись в лог сообщения: использование менеджера прокси.
logging.info("Proxy manager: ON." if Settings["proxy-manager"] == True else "Proxy manager: OFF.")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

# Список описаний обрабатываемых команд.
CommandsList = list()

# Создание команды: build.
COM_build = Command("build")
COM_build.add_argument(ArgumentsTypes.All, important = True)
COM_build.add_flag_position(["cbz"])
COM_build.add_flag_position(["no-filters"])
COM_build.add_flag_position(["no-delay"])
COM_build.add_key_position(["branch", "chapter", "volume"], ArgumentsTypes.All)
COM_build.add_flag_position(["s"])
CommandsList.append(COM_build)

# Создание команды: collect.
COM_collect = Command("collect")
COM_collect.add_key_position(["filters"], ArgumentsTypes.All, important = True)
COM_collect.add_flag_position(["f"])
COM_collect.add_flag_position(["s"])
CommandsList.append(COM_collect)

# Создание команды: convert.
COM_convert = Command("convert")
COM_convert.add_argument(ArgumentsTypes.All, important = True, layout_index = 1)
COM_convert.add_argument(ArgumentsTypes.All, important = True)
COM_convert.add_argument(ArgumentsTypes.All, important = True)
COM_convert.add_flag_position(["all"], important = True, layout_index = 1)
COM_convert.add_flag_position(["s"])
CommandsList.append(COM_convert)

# Создание команды: get.
COM_get = Command("get")
COM_get.add_argument(ArgumentsTypes.URL, important = True)
COM_get.add_key_position(["dir"], ArgumentsTypes.ValidPath)
COM_get.add_key_position(["name"], ArgumentsTypes.All)
COM_get.add_flag_position(["s"])
CommandsList.append(COM_get)

# Создание команды: getcov.
COM_getcov = Command("getcov")
COM_getcov.add_argument(ArgumentsTypes.All, important = True)
COM_getcov.add_flag_position(["f"])
COM_getcov.add_flag_position(["s"])
CommandsList.append(COM_getcov)

# Создание команды: manage.
COM_manage = Command("manage")
COM_manage.add_argument(ArgumentsTypes.All, important = True)
COM_manage.add_flag_position(["del", "unstub"], important = True, layout_index = 1)
COM_manage.add_key_position(["move"], ArgumentsTypes.ValidPath, important = True, layout_index = 1)
COM_manage.add_flag_position(["s"])
CommandsList.append(COM_manage)

# Создание команды: parse.
COM_parse = Command("parse")
COM_parse.add_argument(ArgumentsTypes.All, important = True, layout_index = 1)
COM_parse.add_flag_position(["collection", "local"], layout_index = 1)
COM_parse.add_flag_position(["onlydesc"])
COM_parse.add_flag_position(["f"])
COM_parse.add_flag_position(["s"])
COM_parse.add_key_position(["from"], ArgumentsTypes.All)
CommandsList.append(COM_parse)

# Создание команды: proxval.
COM_proxval = Command("proxval")
COM_proxval.add_flag_position(["f"])
COM_proxval.add_flag_position(["s"])
CommandsList.append(COM_proxval)

# Создание команды: repair.
COM_repair = Command("repair")
COM_repair.add_argument(ArgumentsTypes.All, important = True)
COM_repair.add_key_position(["chapter"], ArgumentsTypes.Number, important = True)
COM_repair.add_flag_position(["s"])
CommandsList.append(COM_repair)

# Создание команды: unstub.
COM_unstub = Command("unstub")
COM_unstub.add_flag_position(["s"])
CommandsList.append(COM_unstub)

# Создание команды: update.
COM_update = Command("update")
COM_update.add_flag_position(["onlydesc"])
COM_update.add_flag_position(["f"])
COM_update.add_flag_position(["s"])
COM_update.add_key_position(["from"], ArgumentsTypes.All)
CommandsList.append(COM_update)

# Инициализация обработчика консольных аргументов.
CAC = Terminalyzer()
# Получение информации о проверке команд.
CommandDataStruct = CAC.check_commands(CommandsList)

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
# Очистка консоли.
Cls()

# Обработка флага: режим перезаписи.
if "f" in CommandDataStruct.flags and CommandDataStruct.name not in ["build", "convert", "manage", "repair"]:
	# Включение режима перезаписи.
	IsForceModeActivated = True
	# Запись в лог сообщения: включён режим перезаписи.
	logging.info("Force mode: ON.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: ON\n"

elif CommandDataStruct.name not in ["build", "convert", "manage", "repair"]:
	# Запись в лог сообщения об отключённом режиме перезаписи.
	logging.info("Force mode: OFF.")
	# Установка сообщения для внутренних функций.
	InFuncMessage_ForceMode = "Force mode: OFF\n"

# Обработка флага: выключение ПК после завершения работы скрипта.
if "s" in CommandDataStruct.flags:
	# Включение режима.
	IsShutdowAfterEnd = True
	# Запись в лог сообщения о том, что ПК будет выключен после завершения работы.
	logging.info("Computer will be turned off after the script is finished!")
	# Установка сообщения для внутренних функций.
	InFuncMessage_Shutdown = "Computer will be turned off after the script is finished!\n"

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

# Обработка команды: build.
if "build" == CommandDataStruct.name:
	# Запись в лог сообщения: построение тайтла.
	logging.info("====== Building ======")	
	# Инициализация билдера.
	BuilderObject = Builder(Settings, CommandDataStruct.arguments[0], InFuncMessage_Shutdown)
	# Если задан флаг, изменить выходной формат на *.CBZ.
	if "cbz" in CommandDataStruct.flags: BuilderObject.set_output_format("cbz")
	# Если задан флаг, отключить фильтрацию.
	if "no-filters" in CommandDataStruct.flags: BuilderObject.set_filter_status(False)
	# Если задан флаг, отключить интервал.
	if "no-delay" in CommandDataStruct.flags: BuilderObject.set_delay_status(False)
	
	# Если ключом указан ID главы для сборки.
	if "chapter" in CommandDataStruct.keys:
		# Построение главы.
		BuilderObject.build_chapter(int(CommandDataStruct.values["chapter"]))
	
	# Если ключом указан номер тома для сборки.
	elif "volume" in CommandDataStruct.keys:
		# Построение тома.
		BuilderObject.build_volume(None, CommandDataStruct.values["volume"])
	
	# Если ключом указан номер ветви для сборки.
	elif "branch" in CommandDataStruct.keys:
		# Построение ветви.
		BuilderObject.build_branch(CommandDataStruct.values["branch"])
	
	else:
		# Построение всего тайтла.
		BuilderObject.build_branch()

# Обработка команды: collect.
if "collect" == CommandDataStruct.name:
	# Запись в лог сообщения: сбор списка тайтлов.
	logging.info("====== Collecting ======")
	# Инициализация сборщика.
	CollectorObject = Collector(Settings)
	# Название фильтра.
	FilterType = None
	# ID параметра фильтрации.
	FilterID = None
	# Сбор списка алиасов тайтлов, подходящих под фильтр.
	CollectorObject.collect(CommandDataStruct.values["filters"], IsForceModeActivated)
	
# Обработка команды: convert.
if "convert" == CommandDataStruct.name:
	# Запись в лог сообщения: конвертирование.
	logging.info("====== Converting ======")
	# Структура тайтла.
	Title = None
	# Список конвертируемых файлов.
	TitlesSlugs = list()
	# Состояние: конвертировать ли все тайтлы.
	IsConvertAll = False
	
	# Если указано флагом.
	if "all" in CommandDataStruct.flags:
		# Переключение конвертирования на все файлы.
		IsConvertAll = True
		# Получение списка файлов в директории.
		TitlesSlugs = os.listdir(Settings["titles-directory"])
		# Фильтрация только файлов формата JSON.
		TitlesSlugs = list(filter(lambda x: x.endswith(".json"), TitlesSlugs))

	# Добавление расширения к файлу в случае отсутствия такового.
	elif ".json" not in CommandDataStruct.arguments[0]:
		TitlesSlugs.append(CommandDataStruct.arguments[0] + ".json")
	
	# Для каждого тайтла.
	for Index in range(0, len(TitlesSlugs)):
		# Очистка консоли.
		Cls()
		# Вывод в консоль: прогресс.
		print("Progress: " + str(Index + 1) + " / " + str(len(TitlesSlugs)))
		# Чтение описательного файла.
		LocalTitle = ReadJSON(Settings["titles-directory"] + "/" + TitlesSlugs[Index])
		# Исходный формат.
		SourceFormat = None

		# Определение исходного формата.
		if CommandDataStruct.arguments[1] == "-auto":

			# Если формат указан.
			if "format" in LocalTitle.keys():
				SourceFormat = LocalTitle["format"]

		else:
			SourceFormat = CommandDataStruct.arguments[1]

		# Создание объекта форматирования.
		FormatterObject = Formatter(Settings, LocalTitle, Format = SourceFormat)
		# Конвертирование структуры тайтла.
		LocalTitle = FormatterObject.convert(CommandDataStruct.arguments[2])
		
		# Если файл не нуждается в конвертировании.
		if SourceFormat != None and SourceFormat.lower() == CommandDataStruct.arguments[2].lower():
			# Запись в лог сообщения: файл пропущен.
			logging.info("File: \"" + TitlesSlugs[Index].replace(".json", "") + "\". Skipped.")
			
		else:
			# Сохранение переформатированного описательного файла.
			WriteJSON(Settings["titles-directory"] + "/" + TitlesSlugs[Index], LocalTitle)
			# Запись в лог сообщения: файл преобразован.
			logging.info("File: \"" + TitlesSlugs[Index].replace(".json", "") + "\". Converted.")

# Обработка команды: get.
if "get" == CommandDataStruct.name:
	# Запись в лог сообщения: заголовок парсинга.
	logging.info("====== Downloading ======")
	# URL изображения.
	URL = CommandDataStruct.arguments[0]
	# Директория.
	Directory = "" if "dir" not in CommandDataStruct.values else CommandDataStruct.values["dir"]
	# Имя файла.
	Filename = "" if "name" not in CommandDataStruct.values else CommandDataStruct.values["name"]
	# Инициализация менеджера запросов.
	RequestsManagerObject = RequestsManager(Settings)
	# Загрузка изображения.
	Result = RequestsManagerObject.downloadImage(URL, Directory, Filename)

	# Если загрузка изображения не успешна.
	if Result != 200:
		# Изменение кода процесса.
		EXIT_CODE = 1
		# Запись в лог ошибки: не удалось загрузить файл.
		logging.error(f"Unable to download image: \"{URL}\". Response code: {Result}.")
		
	else:
		# Переключение удаление лога.
		REMOVE_LOGFILE = True

# Обработка команды: getcov.
if "getcov" == CommandDataStruct.name:
	# Запись в лог сообщения: заголовок парсинга.
	logging.info("====== Parsing ======")
	# Парсинг тайтла (без глав).
	LocalTitle = Parser(Settings, CommandDataStruct.arguments[0], ForceMode = IsForceModeActivated, Message = InFuncMessage_Shutdown + InFuncMessage_ForceMode, Amending = False)
	# Сохранение локальных файлов тайтла.
	LocalTitle.downloadCovers()

# Обработка команды: manage.
if "manage" == CommandDataStruct.name:
	# Запись в лог сообщения: заголовок менеджмента.
	logging.info("====== Management ======")
	# Вывод в консоль: идёт поиск тайтлов.
	print("Management...", end = "")
	# Менеджмент файлов с другим форматом.
	ManageOtherFormatsFiles(Settings, CommandDataStruct.arguments[0], CommandDataStruct.values["move"] if "move" in CommandDataStruct.keys else None)
	# Вывод в консоль: процесс завершён.
	print("Done.")

# Обработка команды: parse.
if "parse" == CommandDataStruct.name:
	# Запись в лог сообщения: парсинг.
	logging.info("====== Parsing ======")
	# Алиасы обновляемых тайтлов.
	TitlesList = list()
	# Индекс стартового алиаса.
	StartIndex = 0
	# Запись в лог сообщения: режим парсинга.
	logging.info("Parse only description: " + ("ON." if "onlydesc" in CommandDataStruct.flags else "OFF."))
	
	# Если активирован флаг парсинга коллекции.
	if "collection" in CommandDataStruct.flags:
		
		# Если существует файл коллекции.
		if os.path.exists("Collection.txt"):
			# Индекс обрабатываемого тайтла.
			CurrentTitleIndex = 0
			
			# Чтение содржимого файла.
			with open("Collection.txt", "r") as FileReader:
				# Буфер чтения.
				Bufer = FileReader.read().split('\n')
				
				# Поместить алиасы в список на парсинг, если строка не пуста.
				for Slug in Bufer:
					if Slug.strip() != "":
						TitlesList.append(Slug)

			# Запись в лог сообщения: количество тайтлов в коллекции.
			logging.info("Titles count in collection: " + str(len(TitlesList)) + ".")

		else:
			# Запись в лог критической ошибки: отсутствует файл коллекций.
			logging.critical("Unable to find collection file.")
			# Выброс исключения.
			raise FileNotFoundError("Collection.txt")
		
	# Если активирован флаг обновления локальных файлов.
	elif "local" in CommandDataStruct.flags:
		# Вывод в консоль: идёт поиск тайтлов.
		print("Scanning titles...")
		# Получение списка файлов в директории.
		TitlesSlugs = os.listdir(Settings["titles-directory"])
		# Фильтрация только файлов формата JSON.
		TitlesSlugs = list(filter(lambda x: x.endswith(".json"), TitlesSlugs))
			
		# Чтение всех алиасов из локальных файлов.
		for File in TitlesSlugs:
			# Открытие локального описательного файла JSON.
			with open(Settings["titles-directory"] + "/" + File, encoding = "utf-8") as FileRead:
				# JSON файл тайтла.
				LocalTitle = json.load(FileRead)
				# Помещение алиаса в список.
				TitlesList.append(str(LocalTitle["slug"]) if "slug" in LocalTitle.keys() else str(LocalTitle["dir"]))

		# Запись в лог сообщения: количество доступных для парсинга тайтлов.
		logging.info("Local titles to parsing: " + str(len(TitlesList)) + ".")
		
	# Парсинг одного тайтла.
	else:
		# Запись аргумента в качестве цели парсинга.
		TitlesList.append(CommandDataStruct.arguments[0])
		
	# Если указан стартовый тайтл.
	if "from" in CommandDataStruct.keys:
		# Запись в лог сообщения: стартовый тайтл парсинга.
		logging.info("Updating starts from title with slug: \"" + CommandDataStruct.values["from"] + "\".")
				
		# Если стартовый алиас найден.
		if CommandDataStruct.values["from"] in TitlesList:
			# Указать индекс алиаса в качестве стартового.
			StartIndex = TitlesList.index(CommandDataStruct.values["from"])
			
		else:
			# Запись в лог предупреждения: стартовый алиас не найден.
			logging.warning("Unable to find start slug. All titles skipped.")
			# Пропустить все тайтлы.
			StartIndex = len(TitlesList)

	# Парсинг обновлённых тайтлов.
	for Index in range(StartIndex, len(TitlesList)):
		# Очистка терминала.
		Cls()
		# Вывод в терминал прогресса.
		print("Parsing titles: " + str(Index + 1) + " / " + str(len(TitlesList)))
		# Генерация сообщения.
		ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Parsing titles: " + str(Index + 1) + " / " + str(len(TitlesList)) + "\n"
		# Локальный описательный файл.
		LocalTitle = None
			
		# Если включён парсинг только описания.
		if "onlydesc" in CommandDataStruct.flags:
			# Парсинг тайтла (без глав).
			LocalTitle = Parser(Settings, TitlesList[Index], ForceMode = IsForceModeActivated, Message = ExternalMessage, Amending = False)
				
		else:
			# Парсинг тайтла.
			LocalTitle = Parser(Settings, TitlesList[Index], ForceMode = IsForceModeActivated, Message = ExternalMessage)
				
		# Сохранение локальных файлов тайтла.
		LocalTitle.save()
		# Выжидание указанного интервала, если не все тайтлы спаршены.
		if Index < len(TitlesList): sleep(Settings["delay"])

# Обработка команды: proxval.
if "proxval" == CommandDataStruct.name:
	# Запись в лог сообщения: валидация.
	logging.info("====== Validation ======")
	# Инициализация менеджера прокси.
	RequestsManagerObject = RequestsManager(Settings, True)
	# Список всех прокси.
	ProxiesList = RequestsManagerObject.getProxies()
	# Сообщение о валидации прокси.
	Message = "\nProxies.json updated.\n" if IsForceModeActivated == True else ""
	
	# Если указаны прокси.
	if len(ProxiesList) > 0:
		
		# Для каждого прокси провести валидацию.
		for ProxyIndex in range(0, len(ProxiesList)):
			# Вывод результата.
			print(ProxiesList[ProxyIndex], "status code:", RequestsManagerObject.validateProxy(ProxiesList[ProxyIndex], IsForceModeActivated))
			# Выжидание интервала.
			if ProxyIndex < len(ProxiesList) - 1: sleep(Settings["delay"])
		
	else:
		# Вывод в консоль: файл определений не содержит прокси.
		print("Proxies are missing.")
		# Запись в лог предупреждения: файл определений не содержит прокси.
		logging.warning("Proxies are missing.")
		
	# Вывод в терминал сообщения о завершении работы.
	print(f"\nStatus codes:\n200 – valid\n403 – forbidden\nother – invalid\n{Message}")
	# Пауза.
	input("Press ENTER to exit...")
	
# Обработка команды: repair.
if "repair" == CommandDataStruct.name:
	# Запись в лог сообщения: восстановление.
	logging.info("====== Repairing ======")
	# Алиас тайтла.
	TitleSlug = None
	# Название файла тайтла с расширением.
	Filename = (CommandDataStruct.arguments[0] + ".json") if ".json" not in CommandDataStruct.arguments[0] else CommandDataStruct.arguments[0]
	# Чтение тайтла.
	TitleContent = ReadJSON(Settings["titles-directory"] + "/" + Filename)
	# Генерация сообщения.
	ExternalMessage = InFuncMessage_Shutdown
	# Вывод в консоль: идёт процесс восстановления главы.
	print("Repairing chapter...")
	
	# Если ключём алиаса является slug, то получить алиас.
	if "slug" in TitleContent.keys():
		TitleSlug = TitleContent["slug"]
		
	else:
		TitleSlug = TitleContent["dir"]

	# Парсинг тайтла.
	LocalTitle = Parser(Settings, TitleSlug, ForceMode = False, Message = ExternalMessage, Amending = False)
	
	# Если указано, восстановить главу.
	if "chapter" in CommandDataStruct.keys:
		LocalTitle.repairChapter(CommandDataStruct.values["chapter"])
	
	# Сохранение локальных файлов тайтла.
	LocalTitle.save(DownloadCovers = False)
	# Переключение удаление лога.
	REMOVE_LOGFILE = True

# Обработка команды: unstub.
if "unstub" == CommandDataStruct.name:
	# Запись в лог сообщения: заголовок менеджмента.
	logging.info("====== Management ======")
	# Вывод в консоль: идёт поиск тайтлов.
	print("Scanning titles...")
	# Получение списка файлов в директории.
	TitlesSlugs = os.listdir(Settings["titles-directory"])
	# Фильтрация только файлов формата JSON.
	TitlesSlugs = list(filter(lambda x: x.endswith(".json"), TitlesSlugs))
	# Запись в лог сообщения: количество доступных для фильтрации заглушек тайтлов.
	logging.info("Local titles for unstubbing: " + str(len(TitlesSlugs)) + ".")
	# Количество удалённых заглушек.
	FilteredCoversCount = 0
	
	# Для каждого тайтла.
	for Index in range(0, len(TitlesSlugs)):
		# Очистка консоли.
		Cls()
		# Вывод в консоль: прогресс.
		print("Progress: " + str(Index + 1) + " / " + str(len(TitlesSlugs)), "\nStubs removed: " + str(FilteredCoversCount))
		# Инициализация парсера.
		Parser = Parser(Settings, TitlesSlugs[Index], Unstub = True)
		# Если произошла фильтрация, произвести инкремент количества удалённых заглушек.
		if Parser.unstub() == True: FilteredCoversCount += 1
			
	# Запись в лог сообщения: количество удалённых заглушек.
	logging.info("Total stubs removed: " + str(FilteredCoversCount) + ".")

# Обработка команды: update.
if "update" == CommandDataStruct.name:
	# Запись в лог сообщения: получение списка обновлений.
	logging.info("====== Updating ======")
	# Индекс стартового алиаса.
	StartIndex = 0
	# Инициализация проверки обновлений.
	UpdateChecker = Updater(Settings)
	# Получение списка обновлённых тайтлов.
	TitlesList = UpdateChecker.getUpdatesList()
		
	# Если указан стартовый тайтл.
	if "from" in CommandDataStruct.keys:
		# Запись в лог сообщения: стартовый тайтл обновления.
		logging.info("Updating starts from title with slug: \"" + CommandDataStruct.values["from"] + "\".")
				
		# Если стартовый алиас найден.
		if CommandDataStruct.values["from"] in TitlesList:
			# Указать индекс алиаса в качестве стартового.
			StartIndex = TitlesList.index(CommandDataStruct.values["from"])
			
		else:
			# Запись в лог предупреждения: стартовый алиас не найден.
			logging.warning("Unable to find start slug. All titles skipped.")
			# Пропустить все тайтлы.
			StartIndex = len(TitlesList)

	# Парсинг обновлённых тайтлов.
	for Index in range(StartIndex, len(TitlesList)):
		# Очистка терминала.
		Cls()
		# Вывод в терминал прогресса.
		print("Updating titles: " + str(Index + 1) + " / " + str(len(TitlesList)))
		# Генерация сообщения.
		ExternalMessage = InFuncMessage_Shutdown + InFuncMessage_ForceMode + "Updating titles: " + str(Index + 1) + " / " + str(len(TitlesList)) + "\n"
		# Локальный описательный файл.
		LocalTitle = None
			
		# Если включено обновление только описания.
		if "onlydesc" in CommandDataStruct.flags:
			# Парсинг тайтла (без глав).
			LocalTitle = Parser(Settings, TitlesList[Index], ForceMode = IsForceModeActivated, Message = ExternalMessage, Amending = False)
				
		else:
			# Парсинг тайтла.
			LocalTitle = Parser(Settings, TitlesList[Index], ForceMode = IsForceModeActivated, Message = ExternalMessage)
				
		# Сохранение локальных файлов тайтла.
		LocalTitle.save()
		# Выжидание указанного интервала, если не все тайтлы обновлены.
		if Index < len(TitlesList): sleep(Settings["delay"])

#==========================================================================================#
# >>>>> ЗАВЕРШЕНИЕ РАБОТЫ СКРИПТА <<<<< #
#==========================================================================================#

# Запись в лог сообщения: заголовок завершения работы скрипта.
logging.info("====== Exiting ======")
# Очистка консоли.
Cls()
# Время завершения работы скрипта.
EndTime = time.time()
# Запись в лог сообщения: время исполнения скрипта.
logging.info("Script finished. Execution time: " + SecondsToTimeString(EndTime - StartTime) + ".")

# Выключение ПК, если установлен соответствующий флаг.
if IsShutdowAfterEnd == True:
	# Запись в лог сообщения: немедленное выключение ПК.
	logging.info("Turning off the computer.")
	# Выключение ПК.
	Shutdown()

# Выключение логгирования.
logging.shutdown()
# Если указано, удалить файл лога.
if REMOVE_LOGFILE == True and os.path.exists(LogFilename): os.remove(LogFilename)
# Завершение главного процесса.
sys.exit(EXIT_CODE)