from dublib.Methods import Cls, ReadJSON, RemoveFolderContent
from Source.RequestsManager import RequestsManager
from Source.Functions import GetRandomUserAgent
from Source.Functions import MergeListOfLists
from Source.Formatter import Formatter
from Source.Functions import Wait

import logging
import shutil
import json
import os

class TitleParser:

	# Возвращает структуру главы.
	def __GetChapterData(self, ChepterID: str) -> dict:
		# Модификатор для доступа к API глав.
		ChaptersAPI = "https://api.remanga.org/api/titles/chapters/" + str(ChepterID)
		# Описание ветви перевода.
		ChapterData = None
		# Выполнение запроса.
		Response = self.__RequestsManager.request(ChaptersAPI)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Сохранение форматированного результата.
			ChapterData = dict(json.loads(Response.text))["content"]

		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request chapter data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

		# Выжидание указанного интервала.
		Wait(self.__Settings)

		return ChapterData

	# Возвращает количество глав во всех ветвях тайтла.
	def __GetChaptersCountInAllBranches(self) -> int:
		# Количество глав.
		AllBranchesChaptersCount = 0

		# Подсчёт.
		for Branch in self.__Title["chapters"].keys():
			AllBranchesChaptersCount += len(self.__Title["chapters"][str(Branch)])

		return AllBranchesChaptersCount

	# Возвращает описание ветви перевода.
	def __GetBranchData(self, BranchID: str, ChaptersCount: int) -> dict:
		# Описание ветви перевода.
		BranchData = None

		# Получение всех страниц ветви.
		for BranchPage in range(0, int(ChaptersCount / 100) + 1):
			# Модификатор для доступа к API глав.
			ChaptersAPI = "https://api.remanga.org/api/titles/chapters/?branch_id=" + BranchID + "&count=" + str(ChaptersCount) + "&ordering=-index&page=" + str(BranchPage + 1) + "&user_data=1"
			# Выполнение запроса.
			Response = self.__RequestsManager.request(ChaptersAPI)

			# Проверка успешности запроса.
			if Response.status_code == 200:
				# Получение текста с ответом.
				ResponseText = Response.text

				# Сохранение форматированного результата.
				CurrentBranchData = dict(json.loads(ResponseText))["content"]

				# Форматирование переменной (нужно для верной обработки ошибки в логах, когда не удалось выполнить запрос).
				if BranchData is None:
					BranchData = list()

				# Дополнение информации о ветви новой страницей.
				BranchData += CurrentBranchData

			else:
				# Запись в лог сообщения о том, что не удалось выполнить запрос.
				logging.error("Unable to request branch data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

			# Выжидание указанного интервала.
			Wait(self.__Settings)

		# Запись в лог сообщения о завершении получения данных о ветвях тайтла.
		if BranchData is not None:
			logging.info("Title: \"" + self.__TitleHeader + "\". Request title branches... Done.")

		return BranchData

	# Возвращает индекс главы в ветви по её ID.
	def __GetChapterIndex(self, Branch: list, ID: int) -> int:

		# Поиск нужной главы.
		for ChapterIndex in range(0, len(Branch)):
			if Branch[ChapterIndex]["id"] == ID:
				return ChapterIndex

		return None

	# Возвращает словарь описания тайтла.
	def __GetTitleDescription(self) -> dict:
		# Модификатор для доступа к API тайтлов.
		TitlesAPI = "https://api.remanga.org/api/titles/" + self.__Slug
		# Описание тайтла.
		Description = None
		# Выполнение запроса.
		Response = self.__RequestsManager.request(TitlesAPI)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Сохранение форматированного результата.
			Description = dict(json.loads(Response.text))["content"]
			# Запись в лог сообщения о запросе описания тайтла.
			logging.info("Title: \"" + self.__TitleHeader + "\". Request title description... Done.")

		# Обработка ошибки доступа в виду отсутствия токена авторизации.
		elif Response.status_code == 401:
			# Перекючение парсера в неактивное состояние.
			self.__IsActive = False
			# Запись в лог предупреждения: невозможно получить доступ к 18+ тайтлу без токена авторизации.
			logging.warning("Title: \"" + self.__TitleHeader + "\". Authorization token required. Skipped.")

		# Обработка ошибки запроса отсутствующего на сервере тайтла.
		elif Response.status_code == 404:
			# Перекючение парсера в неактивное состояние.
			self.__IsActive = False
			# Запись в лог предупреждения: тайтл не найден.
			logging.warning("Title: \"" + self.__TitleHeader + "\". Not found. Skipped.")

		# Обработка любой другой ошибки запроса.
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request title description: \"" + TitlesAPI + "\". Response code: " + str(Response.status_code) + ".")

		# Выжидание указанного интервала.
		Wait(self.__Settings)

		return Description

	# Выполняет слияние ветвей переводов.
	def __MergeBranches(self, UsedTitleName: str) -> dict:
		# Список ID ветвей локального файла.
		LocalBranchesID = list()
		# Удалённый описательный файл JSON.
		RemangaTitle = self.__Title
		# Локальный описательный файл JSON.
		LocalTitle = None
		# Счётчик перемещённых глав.
		self.__MergedChaptersCount = 0

		# Если включён режим перезаписи.
		if self.__ForceMode == True:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Will be overwritten...")
		else:
			# Запись в лог сообщения: найден локальный описательный файл тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Trying to merge...")
		
		# Открытие локального описательного файла JSON.
		with open(self.__Settings["titles-directory"] + UsedTitleName + ".json", encoding = "utf-8") as FileRead:

			try:
				# Попытка прочитать файл.
				LocalTitle = json.load(FileRead)

			except json.decoder.JSONDecodeError:
				# Запись в лог ошибки: не удалось прочитать существующий файл.
				logging.error("Title: \"" + self.__TitleHeader + "\". Unable to read existing file!")
				# Перевод парсера в неактивное состояние.
				self.__IsActive = False

			# Получение наследуемой ветви и конвертирование в совместимый формат.
			if "branchId" in LocalTitle.keys():
				# Получение наследуемой ветви htmp-v1.
				LocalBranchesID.append(str(LocalTitle["branchId"]))
				# Инициализатора конвертера.
				Converter = Formatter(self.__Settings, LocalTitle, "htmp-v1")
				# Конвертирование формата в htcrn-v1.
				LocalTitle = Converter.convert("htcrn-v1")
				# Список ID всех ветвей.
				AllBranchesID = list()
				
				# Получение списка ID всех ветвей.
				for Branch in self.__Title["branches"]:
					AllBranchesID.append(Branch["id"])

				# Проверка: существует ли наследуемая ветвь на сайте.
				if LocalTitle["branchId"] not in AllBranchesID:
					# Перевод парсера в неактивное состояние.
					self.__IsActive = False
					# Запись в лог сообщения: наследуемая ветвь была удалена на сайте.
					logging.warning("Title: \"" + self.__TitleHeader + "\". Legacy branch was removed from site!")

			# Получение наследуемой ветви и конвертирование в совместимый формат.
			else:
				# Исходный формат.
				OriginalFormat = None
				# Совместимый формат.
				CompatibleFormat = None

				# Определить исходный формат или присвоить нативный.
				if "format" in LocalTitle.keys():
					OriginalFormat = LocalTitle["format"]
				else:
					OriginalFormat = "rn-v1"

				# Определение совместимого формата.
				if OriginalFormat in ["htcrn-v1", "htmp-v1"]:
					CompatibleFormat = "htcrn-v1"
				elif OriginalFormat in ["dmp-v1", "rn-v1"]:
					CompatibleFormat = "rn-v1"

				# Инициализатора конвертера.
				Converter = Formatter(self.__Settings, LocalTitle, OriginalFormat)
				# Конвертирование формата в htcrn-v1.
				LocalTitle = Converter.convert(CompatibleFormat)

				# Получение списка ветвей.
				for Branch in LocalTitle["branches"]:
					LocalBranchesID.append(str(Branch["id"]))

			# Для каждой ветви совершить слияние.
			if self.__IsActive is True:
				for BranchID in LocalBranchesID:
					for ChapterIndex in range(0, len(LocalTitle["chapters"][BranchID])):

						# Проверка главы на платность (первое условие нужно для совместимости со старыми форматами без данных о донатном статусе главы).
						if "is_paid" not in LocalTitle["chapters"][BranchID][ChapterIndex].keys() or LocalTitle["chapters"][BranchID][ChapterIndex]["is_paid"] == False:

							# Поиск индекса главы с таким же ID в структуре, полученной с сервера.
							RemangaTitleChapterIndex = self.__GetChapterIndex(RemangaTitle["chapters"][BranchID], LocalTitle["chapters"][BranchID][ChapterIndex]["id"])

							# Если нашли главу с таким же ID, то переместить в неё информацию о слайдах.
							if RemangaTitleChapterIndex != None:
								# Перемещение данных о слайдах из локального файла в новый, полученный с сервера.
								RemangaTitle["chapters"][BranchID][RemangaTitleChapterIndex]["slides"] = LocalTitle["chapters"][BranchID][ChapterIndex]["slides"]
								# Инкремент счётчика.
								self.__MergedChaptersCount += 1

					#---> Проверка: является ли текущая ветвь самой длинной.
					#==========================================================================================#
					# Копия ветвей тайтла.
					BranchesBufer = RemangaTitle["branches"]
					# Сортировка копии по количеству глав.
					BranchesBufer = sorted(BranchesBufer, key = lambda d: d["count_chapters"])

					# Проверка несоответствия текущей ветви и длиннейшей при обработке форматов с одной активной ветвью.
					if "branchId" in LocalTitle.keys() and LocalTitle["branchId"] != BranchesBufer[0]["id"]:
						# Получение ID ветви с большим количеством глав.
						BranchID = str(BranchesBufer[0]["id"])
						# Запись в лог: доступна ветвь с большим количеством глав.
						logging.warning("Title: \"" + self.__TitleHeader + f"\". Branch with more chapters count (BID: {BranchID}) available!")

				# Запись в лог сообщения: завершение слияния.
				if self.__MergedChaptersCount > 0:
					logging.info("Title: \"" + self.__TitleHeader + "\". Merged chapters: " + str(self.__MergedChaptersCount) + ".")
				else:
					logging.info("Title: \"" + self.__TitleHeader + "\". There are no new chapters.")

		return RemangaTitle

	# Конструктор: строит каркас словаря и проверяет наличие локальных данных.
	def __init__(self, Settings: dict, Slug: str, ForceMode: bool = True, Message: str = "", Amending: bool = True):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Количество скопированных из локального файла глав.
		self.__MergedChaptersCount  = 0
		# Менеджер запросов через прокси.
		self.__RequestsManager = RequestsManager(Settings)
		# Заголовок тайтла для логов и вывода в терминал.
		self.__TitleHeader = Slug
		# Состояние: включена ли перезапись файлов.
		self.__ForceMode = ForceMode
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Состояние: получено ли описание тайтла.
		self.__IsActive = True
		# Словарь описания тайтла.
		self.__Title = dict()
		# Сообщение из внешнего обработчика.
		self.__Message = Message + "Current title: " + self.__TitleHeader + "\n\n"
		# Алиас тайтла.
		self.__Slug = Slug
		# ID тайтла.
		self.__ID = None
		# Заголовки запроса.
		self.__RequestHeaders = {
			"authorization": self.__Settings["authorization-token"],
			"accept": "*/*",
			"accept-language": "ru,en;q=0.9",
			"content-type": "application/json",
			"preference": "0",
			"referer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin",
			"User-Agent": UserAgent
		}

		# Если токена авторизации нет, то удалить заголовок.
		if self.__RequestHeaders["authorization"] == "":
			del self.__RequestHeaders["authorization"]

		# Запись в лог сообщения о начале парсинга.
		logging.info("Title: \"" + self.__TitleHeader + "\". Parcing...")
		# Запись в лог сообщения об использованном User-Agent.
		logging.debug("User-Agent: \"" + UserAgent + "\".")

		#---> Построение каркаса словаря.
		#==========================================================================================#
		# Получение описания тайтла.
		self.__Title = self.__GetTitleDescription()

		# Проверка доступности тайтла.
		if self.__IsActive == True:
			# Получение ID тайтла.
			self.__ID = str(self.__Title["id"])
			# Формирование заголовка тайтла для вывода в консоль.
			self.__TitleHeader = self.__TitleHeader + f" (ID: {self.__ID})"
			# Изменение заголовка тайтла.
			self.__Message = Message + "Current title: " + self.__TitleHeader + "\n\n"

			# Создание ключа для последующего помещения туда глав.
			self.__Title["chapters"] = dict()

			# Генерация ветвей и заполнение их данными о главах.
			for Branch in self.__Title["branches"]:

				# Если в ветви есть главы, то получить её, иначе сформировать искусственно.
				if Branch["count_chapters"] > 0:
					self.__Title["chapters"][str(Branch["id"])] = self.__GetBranchData(str(Branch["id"]), Branch["count_chapters"])
				else:
					self.__Title["chapters"][str(Branch["id"])] = list()

			#---> Дополнение каркаса данными о страницах глав.
			#==========================================================================================#

			# Если отключён режим перезаписи.
			if self.__ForceMode == False:

				# Для каждого варианта имени файла.
				for Filename in [Slug, self.__ID]:

					# Если существует файл с названием таким же, как вариант написания.
					if os.path.exists(self.__Settings["titles-directory"] + Filename + ".json"):
						# Чтение файла.
						File = ReadJSON(self.__Settings["titles-directory"] + Filename + ".json")

						# Если алиас тайтла совпадает с целевым, то выполнить слияние с локальным описательным файлом.
						if "slug" in File.keys() and File["slug"] == Slug or "dir" in File.keys() and File["dir"] == Slug:
							self.__Title = self.__MergeBranches(Filename)

			# Получение недостающих данных о страницах глав.
			if Amending == True:
				self.AmendChapters()

	# Проверяет все главы на наличие описанных страниц и дополняет их, если это необходимо.
	def AmendChapters(self):

		# Если парсер активен.
		if self.__IsActive == True:
			# Список ID ветвей.
			BranchesID = list()
			# Счётчик глав, для которых были получены страницы.
			UpdatedChaptersCounter = 0
			# Количество глав во всех ветвях тайтла.
			AllBranchesChaptersCount = self.__GetChaptersCountInAllBranches()
			# Запись в лог сообщения о старте получения информации о страницах глав.
			logging.info("Title: \"" + self.__TitleHeader + "\". Amending...")

			# Получение списка ID ветвей.
			for Branch in self.__Title["branches"]:
				BranchesID.append(str(Branch["id"]))
			
			# В каждой ветви проверить каждую главу на отсутствие описанных страниц и дополнить.
			for BranchID in BranchesID:

				for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
					# Очистка терминала.
					Cls()

					# Вывод в терминал прогресса.
					if AllBranchesChaptersCount - self.__MergedChaptersCount > 0:
						print(self.__Message + "Amending chapters: " + str(UpdatedChaptersCounter + 1) + " / " + str(AllBranchesChaptersCount - self.__MergedChaptersCount))

					# Проверка отсутствия описанных страниц.
					if "slides" not in self.__Title["chapters"][BranchID][ChapterIndex].keys():

						# Проверка главы на платность.
						if self.__Title["chapters"][BranchID][ChapterIndex]["is_paid"] == False:
							# Получение информации о страницах главы.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = self.__GetChapterData(self.__Title["chapters"][BranchID][ChapterIndex]["id"])["pages"]
							# Форматирование списка слайдов к нужному виду.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = MergeListOfLists(self.__Title["chapters"][BranchID][ChapterIndex]["slides"])
							# Запись в лог сообщения об успешном добавлинии информации о страницах главы.
							logging.info("Title: \"" + self.__TitleHeader + "\". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " amended.")
							# Инкремент счётчика.
							UpdatedChaptersCounter += 1
							# Выжидание указанного интервала.
							Wait(self.__Settings)

						else:
							# Создание пустого списка слайдов.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = list()
							# Запись в лог сообщения о платной главе.
							logging.info("Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " is paid. Skipped.")

			# Запись в лог сообщения о количестве дополненных глав.
			logging.info("Title: \"" + self.__TitleHeader + "\". Amended chapters: " + str(UpdatedChaptersCounter) + ".")

	# Загружает обложки тайтла.
	def DownloadCovers(self):

		# Если парсер активен.
		if self.__IsActive == True:
			# Список URL обложек.
			CoversURL = list()
			# Очистка терминала.
			Cls()
			# Вывод в консоль: сообщение из внешнего обработчика и алиас обрабатываемого тайтла.
			print(self.__Message, end = "")
			# Модифицированные заголовки для получения изображения.
			ImageRequestHeaders = self.__RequestHeaders
			ImageRequestHeaders["content-type"] = "image/jpeg"
			# Ответ запроса.
			Response = None
			# Счётчик загруженных обложек.
			DownloadedCoversCounter = 0
			# Запись URL обложек.
			CoversURL.append("https://remanga.org" + self.__Title["img"]["high"])
			CoversURL.append("https://remanga.org" + self.__Title["img"]["mid"])
			CoversURL.append("https://remanga.org" + self.__Title["img"]["low"])
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = self.__Slug if self.__Settings["use-id-instead-slug"] == False else self.__ID

			# Скачивание обложек.
			for URL in CoversURL:

				# Если включен режим перезаписи, то удалить файлы обложек.
				if self.__ForceMode == True:
					
					# Удалить файл обложки.
					if os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + URL.split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug) 
					elif os.path.exists(self.__Settings["covers-directory"] + self.__ID + "/" + URL.split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__ID) 

				# Для каждого состояния переключателя, указывающего, что использовать для названия файла.
				for State in [True, False]:
					# Установка устаревшего имени папки с обложками в зависимости от статуса.
					Foldername = self.__Settings["covers-directory"] + self.__Slug if State == True else self.__ID

					# Удаление папки для обложек с устаревшим названием.
					if self.__Settings["use-id-instead-slug"] == State and os.path.exists(Foldername + "/" + URL.split('/')[-1]):
						shutil.rmtree(Foldername)

				# Проверка существования файла.
				if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName + "/" + URL.split('/')[-1]) == False:
					# Вывод в терминал URL загружаемой обложки.
					print("Downloading cover: \"" + URL + "\"... ", end = "")

					# Выполнение запроса.
					Response = self.__RequestsManager.request(URL, Headers = ImageRequestHeaders)

					# Проверка успешности запроса.
					if Response.status_code == 200:

						# Создание папки для обложек.
						if not os.path.exists(self.__Settings["covers-directory"]):
							os.makedirs("Covers")

						# Создание папки с алиасом тайтла в качестве названия.
						if not os.path.exists(self.__Settings["covers-directory"] + UsedTitleName):
							os.makedirs(self.__Settings["covers-directory"] + UsedTitleName)

						# Открытие потока записи.
						with open(self.__Settings["covers-directory"] + UsedTitleName + "/" + URL.split('/')[-1], "wb") as FileWrite:
							# Запись изображения.
							FileWrite.write(Response.content)
							# Инкремент счётчика загруженных обложек.
							DownloadedCoversCounter += 1
							# Вывод в терминал сообщения об успешной загрузке.
							print("Done.")

					else:
						# Запись в лог сообщения о неудачной попытке загрузки обложки.
						logging.error("Title: \"" + self.__TitleHeader + "\". Unable download cover: \"" + URL + "\". Response code: " + str(Response.status_code) + ".")
						# Вывод в терминал сообщения об успешной загрузке.
						print("Failure!")
						# Выжидание указанного интервала, если не все обложки загружены.
						if DownloadedCoversCounter < 3:
							Wait(self.__Settings) 

				else:
					# Вывод в терминал URL загружаемой обложки.
					print("Cover already exist: \"" + URL + "\". Skipped.")

				# Выжидание указанного интервала, если не все обложки загружены.
				if DownloadedCoversCounter < 3 and DownloadedCoversCounter > 0:
					Wait(self.__Settings)

			# Запись в лог сообщения: количество загруженных обложек.
			logging.info("Title: \"" + self.__TitleHeader + "\". Covers downloaded: " + str(DownloadedCoversCounter) + ".")

	# Сохраняет локальный JSON файл.
	def Save(self, DownloadCovers: bool = True):
		# Используемое имя тайтла: ID или алиас.
		UsedTitleName = self.__Slug if self.__Settings["use-id-instead-slug"] == False else self.__ID

		# Если парсер активен.
		if self.__IsActive == True:

			# Для каждого состояния переключателя, указывающего, что использовать для названия файла.
			for State in [True, False]:
				# Установка устаревшего имени файла в зависимости от статуса.
				Filename = self.__Settings["titles-directory"] + (self.__Slug if State == True else self.__ID) + ".json" 

				# Если существует файл тайтла с альтернативным названием.
				if self.__Settings["use-id-instead-slug"] == State and os.path.exists(Filename):
					# Чтение файла.
					File = ReadJSON(Filename)

					# Если алиас тайтла совпадает с целевым, то удалить старый файл.
					if "slug" in File.keys() and File["slug"] == self.__Slug or "dir" in File.keys() and File["dir"] == self.__Slug:
						os.remove(Filename)

			# Создание папки для тайтлов.
			if os.path.exists(self.__Settings["titles-directory"]) == False:
				os.makedirs(self.__Settings["titles-directory"])

			# Если указано, скачать обложки.
			if DownloadCovers == True:
				self.DownloadCovers()

			# Инициализация конвертера.
			FormatterObject = Formatter(self.__Settings, self.__Title, "rn-v1")
			FormattedTitle = FormatterObject.convert(self.__Settings["format"])

			# Сохранение локального файла JSON.
			with open(self.__Settings["titles-directory"] + UsedTitleName + ".json", "w", encoding = "utf-8") as FileWrite:
				json.dump(FormattedTitle, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

				# Запись в лог сообщения: создан или обновлён локальный файл.
				if self.__MergedChaptersCount > 0:
					logging.info("Title: \"" + self.__TitleHeader + "\". Updated.")
				else:
					logging.info("Title: \"" + self.__TitleHeader + "\". Parced.")

		# Завершает сеанс запроса.
		self.__RequestsManager.close()