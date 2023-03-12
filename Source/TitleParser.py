from Source.RequestsManager import RequestsManager
from Source.Functions import GetRandomUserAgent
from Source.Functions import MergeListOfLists
from Source.DUBLIB import RenameDictKey
from Source.Functions import Wait
from Source.DUBLIB import Cls

import logging
import shutil
import json
import os

class TitleParser:

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Перечисление типов тайтла.
	__Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "ANOTHER"]
	# Перечисление статусов тайтла.
	__Statuses = ["COMPLETED", "ACTIVE", "ABANDONED", "NOT_FOUND", "", "LICENSED"]
	# ID ветви в не нативном форматировании при обновлении тайтла (нужен для сохранения завязки на старую ветвь).
	__NonNativeBranchID = None
	# Менеджер запросов через прокси.
	__RequestsManager = None
	# Заголовки запроса.
	__RequestHeaders = None
	# Заголовок тайтла для логов и вывода в терминал.
	__TitleHeader = None
	# Состояние: включена ли перезапись файлов.
	__ForceMode = True
	# Состояние: проводилось ли слияние с локальным файлом.
	__IsMerged = False
	# Глобальные настройки.
	__Settings = dict()
	# Состояние: получено ли описание тайтла.
	__IsActive = True
	# Словарь описания тайтла.
	__Title = dict()
	# Сообщение из внешнего обработчика.
	__Message = ""
	# Алиас тайтла.
	__Slug = None
	# ID тайтла.
	__ID = None
	
	# Перечисление жанров, обозначающих однополые отношения.
	__HomoGenres = [
			{
				"id": 43,
				"name": "Яой"
			},
			{
				"id": 29,
				"name": "Сёдзё-ай"
			},
			{
				"id": 31,
				"name": "Сёнэн-ай"
			},
			{
				"id": 41,
				"name": "Юри"
			}
		]

	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Форматирует ветвь согласно требованиям обходчика.
	def __FormatBranch(self, Branch: dict) -> dict:
		
		# Пройтись по всем элементам.
		for ChapterIndex in range(0, len(Branch)):
			Branch[ChapterIndex] = RenameDictKey(Branch[ChapterIndex], "tome", "tom")
			Branch[ChapterIndex]["chapter"] = float(Branch[ChapterIndex]["chapter"])

			# Усечение нуля у float.
			if ".0" in str(Branch[ChapterIndex]["chapter"]):
				Branch[ChapterIndex]["chapter"] = int(Branch[ChapterIndex]["chapter"])

		return Branch

	# Форматирует описание согласно требованиям обходчика.
	def __FormatDescription(self, Description: dict) -> dict:
		Description = RenameDictKey(Description, "rus_name", "rusTitle")
		Description = RenameDictKey(Description, "en_name", "engTitle")
		Description = RenameDictKey(Description, "another_name", "alternativeTitle")
		Description = RenameDictKey(Description, "description", "desc")
		Description = RenameDictKey(Description, "dir", "slug")
		Description = RenameDictKey(Description, "categories", "tags")
		Description = RenameDictKey(Description, "is_yaoi", "isYaoi")
		Description = RenameDictKey(Description, "is_erotic", "isHentai")
		Description = RenameDictKey(Description, "can_post_comments", "isHomo")

		Description["status"] = self.__Statuses[Description["status"]["id"]]
		Description["type"] = self.__Types[Description["type"]["id"]]
		Description["isHomo"] = self.__IsHomo(Description)

		return Description

	# Возвращает структуру главы.
	def __GetChapterData(self, ChepterID: str) -> dict:
		# Модификатор для доступа к API глав.
		ChaptersAPI = "https://api.remanga.org/api/titles/chapters/" + str(ChepterID)
		# Описание ветви перевода.
		ChapterData = None
		# Выполнение запроса.
		Response = self.__RequestsManager.Request(ChaptersAPI)

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

	# Возвращает описание ветви перевода.
	def __GetBranchData(self, BranchID: str, ChaptersCount: int) -> dict:
		# Описание ветви перевода.
		BranchData = list()

		# Получение всех страниц ветви.
		for BranchPage in range(0, int(ChaptersCount / 100) + 1):
			# Модификатор для доступа к API глав.
			ChaptersAPI = "https://api.remanga.org/api/titles/chapters/?branch_id=" + BranchID + "&count=" + str(ChaptersCount) + "&ordering=-index&page=" + str(BranchPage + 1) + "&user_data=1"
			# Выполнение запроса.
			Response = self.__RequestsManager.Request(ChaptersAPI)

			# Проверка успешности запроса.
			if Response.status_code == 200:
				# Получение текста с ответом.
				ResponseText = Response.text
				# Запись в лог сообщения о запросе ветвей тайтла.
				logging.info("Title: \"" + self.__TitleHeader + "\". Request title branches... Done.")

				# Сохранение форматированного результата.
				CurrentBranchData = dict(json.loads(ResponseText))["content"]

				# Переименовать ключ тома, если указано настройками.
				if self.__Settings["native-formatting"] == False:
					BranchData += self.__FormatBranch(CurrentBranchData)
				else:
					BranchData += CurrentBranchData

			else:
				# Запись в лог сообщения о том, что не удалось выполнить запрос.
				logging.error("Unable to request branch data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

			# Выжидание указанного интервала.
			Wait(self.__Settings)

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
		Response = self.__RequestsManager.Request(TitlesAPI)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Сохранение форматированного результата.
			Description = dict(json.loads(Response.text))["content"]
			# Форматирование в совместимом режиме.
			if self.__Settings["native-formatting"] == False:
				Description = self.__FormatDescription(Description)
			# Запись в лог сообщения о запросе описания тайтла.
			logging.info("Title: \"" + self.__TitleHeader + "\". Request title description... Done.")

		# Обработка ошибки доступа в виду отсутствия токена авторизации.
		elif Response.status_code == 401:
			self.__IsActive = False

		# Обработка любой другой ошибки запроса.
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request title description: \"" + TitlesAPI + "\". Response code: " + str(Response.status_code) + ".")

		# Выжидание указанного интервала.
		Wait(self.__Settings)

		return Description

	# Проверяет, имеет ли тайтл описание однополых отношений.
	def __IsHomo(self, Description: dict) -> bool:

		# Проверка жанров на представителей однополых отношений.
		for TitleGenre in Description["genres"]:
			for HomoGenre in self.__HomoGenres:
				if HomoGenre == TitleGenre:
					return True

		return False

	# Выполняет слияние ветвей переводов.
	def __MergeBranches(self, UsedTitleName: str) -> dict:
		# Список ID ветвей локального файла.
		LocalBranchesID = list()
		# Удалённый описательный файл JSON.
		RemangaTitle = self.__Title
		# Локальный описательный файл JSON.
		LocalTitle = None
		# Счётчик перемещённых глав.
		MergedChaptersCounter = 0
		# Запись в лог сообщения о том, что найден локальный файл описания тайтла.
		logging.info("Title: \"" + self.__TitleHeader + "\". Local JSON already exists. Trying to merge...")
		# Переключение статуса слияния.
		self.__IsMerged = True
		
		# Открытие локального описательного файла JSON.
		with open(self.__Settings["JSON-directory"] + UsedTitleName + ".json", encoding = "utf-8") as FileRead:
			# JSON файл тайтла.
			LocalTitle = json.load(FileRead)

			# Перемещение информации о слайдах в нативном форматировании.
			if self.__Settings["native-formatting"] is True:

				# Заполнение списка ID ветвей локального JSON.
				for Branch in LocalTitle["branches"]:
					LocalBranchesID.append(str(Branch["id"]))

				# Для каждой ветви совершить слияние.
				for BranchID in LocalBranchesID:
					for ChapterIndex in range(0, len(LocalTitle["chapters"][BranchID])):

						# Проверка главы на платность.
						if LocalTitle["chapters"][BranchID][ChapterIndex]["is_paid"] == False:
							# Поиск индекса главы с таким же ID в структуре, полученной с сервера.
							RemangaTitleChapterIndex = self.__GetChapterIndex(RemangaTitle["chapters"][BranchID], LocalTitle["chapters"][BranchID][ChapterIndex]["id"])

							# Если нашли главу с таким же ID, то переместить в неё информацию о слайдах.
							if RemangaTitleChapterIndex != None:
								# Перемещение данных о слайдах из локального файла в новый, полученный с сервера.
								RemangaTitle["chapters"][BranchID][RemangaTitleChapterIndex]["slides"] = LocalTitle["chapters"][BranchID][ChapterIndex]["slides"]
								# Инкремент счётчика.
								MergedChaptersCounter += 1

			# Перемещение информации о слайдах в не нативном форматировании.
			else:
				# Записать наследуемый ID ветви.
				self.__NonNativeBranchID = str(LocalTitle["branchId"])
				
				# Для каждой главы из локального файла совершить слияние.
				for ChapterIndex in range(0, len(LocalTitle["chapters"])):

					# Проверка главы на платность.
					if "is_paid" in LocalTitle["chapters"][ChapterIndex].keys() and LocalTitle["chapters"][ChapterIndex]["is_paid"] == False:
						# Поиск индекса главы с таким же ID в структуре, полученной с сервера.
						RemangaTitleChapterIndex = self.__GetChapterIndex(RemangaTitle["chapters"][self.__NonNativeBranchID], LocalTitle["chapters"][ChapterIndex]["id"])

						# Если нашли главу с таким же ID, то переместить в неё информацию о слайдах.
						if RemangaTitleChapterIndex != None:
							# Перемещение данных о слайдах из локального файла в новый, полученный с сервера.
							RemangaTitle["chapters"][self.__NonNativeBranchID][RemangaTitleChapterIndex]["slides"] = LocalTitle["chapters"][ChapterIndex]["slides"]
							# Инкремент счётчика.
							MergedChaptersCounter += 1

				#---> Проверка: является ли текущая ветвь самой длинной.
				#==========================================================================================#
				# Копия ветвей тайтла.
				BranchesBufer = RemangaTitle["branches"]
				# Сортировка копии по количеству глав.
				BranchesBufer = sorted(BranchesBufer, key = lambda d: d["count_chapters"])

				# Проверка несоответствия текущей ветви и длиннейшей.
				if self.__NonNativeBranchID != str(BranchesBufer[0]["id"]):
					# Получение ID ветви с большим количеством глав.
					BranchID = str(BranchesBufer[0]["id"])
					# Запись в лог: доступна ветвь с большим количеством глав.
					logging.warning("Title: \"" + self.__TitleHeader + f"\". Branch with more chapters count (BID: {BranchID}) available!")

		# Запись в лог сообщения о завершении объединения локального и удалённого файлов.
		if MergedChaptersCounter > 0:
			logging.info("Title: \"" + self.__TitleHeader + "\". Merged chapters: " + str(MergedChaptersCounter) + ".")
		else:
			logging.info("Title: \"" + self.__TitleHeader + "\". There are no new chapters.")

		return RemangaTitle

	# Конструктор: строит каркас словаря и проверяет наличие локальных данных.
	def __init__(self, Settings: dict, Slug: str, ForceMode: bool = True, Message: str = "", Amending: bool = True):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__Slug = Slug
		self.__ForceMode = ForceMode
		self.__TitleHeader = Slug
		self.__Message = Message + "Current title: " + self.__TitleHeader + "\n\n"
		self.__RequestHeaders = {
			"authorization": self.__Settings["authorization"],
			"accept": "*/*",
			"accept-language": "ru,en;q=0.9",
			"content-type": "application/json",
			"preference": "0",
			"referer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin",
			"User-Agent": UserAgent
			}
		self.__RequestsManager = RequestsManager(Settings)

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
		if self.__IsActive == False:
			# Запись в лог сообщения о невозможности получить доступ к 18+ тайтлу без токена авторизации.
			logging.warning("Title: \"" + self.__TitleHeader + "\". Authorization token required!")

		# Если тайтл доступен, продолжить обработку.
		else:

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

			# Слияние локальной и удалённой ветвей, либо выбор текущей ветви.
			if os.path.exists(self.__Settings["JSON-directory"] + Slug + ".json"):
				self.__Title = self.__MergeBranches(Slug)
			elif os.path.exists(self.__Settings["JSON-directory"] + self.__ID + ".json"):
				self.__Title = self.__MergeBranches(self.__ID)
			elif self.__Settings["native-formatting"] is False:
				self.__NonNativeBranchID = str(self.__Title["branches"][0]["id"])

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
			# Запись в лог сообщения о старте получения информации о страницах глав.
			logging.info("Title: \"" + self.__TitleHeader + "\". Amending...")

			# Заполнение списка ID ветвей в зависимости от выбранного форматирования.
			if self.__Settings["native-formatting"] is True:
				for Branch in self.__Title["branches"]:
					BranchesID.append(str(Branch["id"]))
			else:
				BranchesID.append(self.__NonNativeBranchID)
			
			# В каждой ветви проверить каждую главу на отсутствие описанных страниц и дополнить.
			for BranchID in BranchesID:
				for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
					# Очистка терминала.
					Cls()
					# Вывод в терминал прогресса.
					print(self.__Message + "Amending chapters: " + str(ChapterIndex + 1) + " / " + str(len(self.__Title["chapters"][BranchID])))

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
							# Запись в лог сообщения о платной главе.
							logging.warning("Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " is paid. Skipped.")

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
			# Вывод сообщения из внешнего обработчика и заголовка.
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
			UsedTitleName = None

			# Установка используемого имени тайтла.
			if self.__Settings["use-id-instead-slug"] == False:
				UsedTitleName = self.__Slug
			else:
				UsedTitleName = self.__ID

			# Скачивание обложек.
			for URL in CoversURL:

				# Если включен режим перезаписи, то удалить файлы обложек.
				if self.__ForceMode == True:
					
					# Удалить файл обложки.
					if os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + URL.split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug) 
					elif os.path.exists(self.__Settings["covers-directory"] + self.__ID + "/" + URL.split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__ID) 

				# Удаление папки с алиасом в названии, если используются ID.
				if self.__Settings["use-id-instead-slug"] == True and os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + URL.split('/')[-1]):
					shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug)

				# Проверка существования файла.
				if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName + "/" + URL.split('/')[-1]) == False:
					# Вывод в терминал URL загружаемой обложки.
					print("Downloading cover: \"" + URL + "\"... ", end = "")

					# Выполнение запроса.
					Response = self.__RequestsManager.Request(URL, Headers = ImageRequestHeaders)

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
						logging.error("Title: \"" + self.__TitleHeader + "\". Unable download cover: \"" + URL + "\". Response code: " + str(Response.status_code == 200) + ".")
						# Вывод в терминал сообщения об успешной загрузке.
						print("Failure!")
						# Выжидание указанного интервала, если не все обложки загружены.
						if DownloadedCoversCounter < 3:
							Wait(self.__Settings) 

				else:
					# Вывод в терминал URL загружаемой обложки.
					print("Cover already exist: \"" + URL + "\". Skipped. ")

				# Выжидание указанного интервала, если не все обложки загружены.
				if DownloadedCoversCounter < 3 and DownloadedCoversCounter > 0:
					Wait(self.__Settings)

			# Запись в лог сообщения о количестве загруженных обложек.
			logging.info("Title: \"" + self.__TitleHeader + "\". Covers downloaded: " + str(DownloadedCoversCounter) + ".")

	# Сохраняет локальный JSON файл.
	def Save(self, DownloadCovers: bool = True):

		# Используемое имя тайтла: ID или алиас.
		UsedTitleName = None

		# Установка используемого имени тайтла.
		if self.__Settings["use-id-instead-slug"] == False:
			UsedTitleName = self.__Slug
		else:
			UsedTitleName = self.__ID

		# Если парсер активен.
		if self.__IsActive == True:
			# Список ID ветвей.
			BranchesID = list()

			# Удаление существующего файла, если включен режим перезаписи.
			if self.__ForceMode == True:

				# Удалить файл с алиасом в названии.
				if os.path.exists(self.__Settings["JSON-directory"] + self.__Slug + ".json"):
					# Удаление файла.
					os.remove(self.__Settings["JSON-directory"] + self.__Slug + ".json")
					# Запись в лог сообщения о перезаписи файла.
					logging.info("Title: \"" + self.__TitleHeader + "\". Already exists. Will be overwritten...")

				# Удалить файл с ID в названии.
				elif os.path.exists(self.__Settings["JSON-directory"] + self.__ID + ".json"):
					# Удаление файла.
					os.remove(self.__Settings["JSON-directory"] + self.__ID + ".json")
					# Запись в лог сообщения о перезаписи файла.
					logging.info("Title: \"" + self.__TitleHeader + "\". Already exists. Will be overwritten...")

			# Удаление файла с алиасом в названии, если используются ID.
			if self.__Settings["use-id-instead-slug"] == True and os.path.exists(self.__Settings["JSON-directory"] + self.__Slug + ".json"):
				os.remove(self.__Settings["JSON-directory"] + self.__Slug + ".json")

			# Создание папки для тайтлов.
			if os.path.exists(self.__Settings["JSON-directory"]) == False:
				os.makedirs(self.__Settings["JSON-directory"])

			# Заполнение списка ID ветвей в зависимости от выбранного форматирования.
			if self.__Settings["native-formatting"] is True:
				for Branch in self.__Title["branches"]:
					BranchesID.append(str(Branch["id"]))
			else:
				BranchesID.append(self.__NonNativeBranchID)

			# Инвертирование порядка глав в ветвях.
			for BranchID in BranchesID:
				self.__Title["chapters"][BranchID] = sorted(self.__Title["chapters"][BranchID], key = lambda d: d["id"]) 

			# Если указано, скачать обложки.
			if DownloadCovers == True:
				self.DownloadCovers()

			# Отформатировать URL обложек.
			if self.__Settings["native-formatting"] is False:
				self.__Title["img"]["high"] = self.__ID + "/" + self.__Title["img"]["high"].split('/')[-1]
				self.__Title["img"]["mid"] = self.__ID + "/" + self.__Title["img"]["high"].split('/')[-1]
				self.__Title["img"]["low"] = self.__ID + "/" + self.__Title["img"]["high"].split('/')[-1]

			# Если нативное форматирование отключено, то записать только первую ветвь тайтла.
			if self.__Settings["native-formatting"] is False:
				self.__Title = RenameDictKey(self.__Title, "avg_rating", "branchId")
				self.__Title["branchId"] = self.__Title["branches"][0]["id"]
				self.__Title["chapters"] = self.__Title["chapters"][self.__NonNativeBranchID]

			# Сохранение локального файла JSON.
			with open(self.__Settings["JSON-directory"] + UsedTitleName + ".json", "w", encoding = "utf-8") as FileWrite:
				json.dump(self.__Title, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

				# Запись в лог сообщения о создании или обновлении локального файла.
				if self.__IsMerged == True:
					logging.info("Title: \"" + self.__TitleHeader + "\". Updated.")
				else:
					logging.info("Title: \"" + self.__TitleHeader + "\". Parced.")

		# Завершает сеанс запроса.
		self.__RequestsManager.Close()
