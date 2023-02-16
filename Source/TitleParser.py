from Functions import GetRandomUserAgent
from DUBLIB import Cls

import requests
import logging
import random
import json
import time
import os

class TitleParser:

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Заголовки запроса.
	__RequestHeaders = None
	# Состояние: проводилось ли слияние с локальным файлом.
	__IsMerged = False
	# Глобальные настройки.
	__Settings = dict()
	# Состояние: включена ли перезапись файлов.
	__ForceMode = True
	# Словарь описания тайтла.
	__Title = dict()
	# Алиас тайтла.
	__Slug = None
	# Сообщение из внешнего обработчика.
	__Message = ""
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Возвращает структуру страниц главы.
	def __GetChapterData(self, ChepterID: str) -> dict:
		# Модификатор для доступа к API глав.
		ChaptersAPI = "https://api.remanga.org/api/titles/chapters/" + str(ChepterID)
		# Описание ветви перевода.
		ChapterData = None
		# Ответ запроса.
		Response = None

		# Выполнение запроса с прокси-сервером, если указано, или без него.
		if self.__Settings["use-proxy"] == True:
			Response = requests.get(ChaptersAPI, headers = self.__RequestHeaders, proxies = self.__Settings["proxy"][random.randint(0, len(self.__Settings["proxy"]) - 1)])
		else:
			Response = requests.get(ChaptersAPI, headers = self.__RequestHeaders)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Сохранение форматированного результата.
			ChapterData = dict(json.loads(Response.text))["content"]
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request chater data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

		return ChapterData

	# Возвращает описание ветви перевода.
	def __GetBranchData(self, BranchID: str, ChaptersCount: str) -> dict:
		# Модификатор для доступа к API глав.
		ChaptersAPI = "https://api.remanga.org/api/titles/chapters/?branch_id=" + BranchID + "&count=" + ChaptersCount + "&ordering=-index&page=1&user_data=1"
		# Описание ветви перевода.
		BranchData = None
		# Ответ запроса.
		Response = None

		# Выполнение запроса с прокси-сервером, если указано, или без него.
		if self.__Settings["use-proxy"] == True:
			Response = requests.get(ChaptersAPI, headers = self.__RequestHeaders, proxies = self.__Settings["proxy"][random.randint(0, len(self.__Settings["proxy"]) - 1)])
		else:
			Response = requests.get(ChaptersAPI, headers = self.__RequestHeaders)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Получение текста с ответом.
			ResponseText = Response.text
			# Запись в лог сообщения о запросе ветвей тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Request title branches... Done.")

			# Переименовать ключ тома, если указано настройками.
			if self.__Settings["tome-to-tom"] == True:
				ResponseText = ResponseText.replace("\"tome\":", "\"tom\":")

			# Сохранение форматированного результата.
			BranchData = dict(json.loads(ResponseText))["content"]
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request branch data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

		return BranchData

	# Возвращает словарь описания тайтла.
	def __GetTitleDescription(self) -> dict:
		# Модификатор для доступа к API тайтлов.
		TitlesAPI = "https://api.remanga.org/api/titles/" + self.__Slug
		# Описание тайтла.
		Description = None
		# Ответ запроса.
		Response = None

		# Выполнение запроса с прокси-сервером, если указано, или без него.
		if self.__Settings["use-proxy"] == True:
			Response = requests.get(TitlesAPI, headers = self.__RequestHeaders, proxies = self.__Settings["proxy"][random.randint(0, len(self.__Settings["proxy"]) - 1)])
		else:
			Response = requests.get(TitlesAPI, headers = self.__RequestHeaders)

		# Проверка успешности запроса.
		if Response.status_code == 200:
			# Сохранение форматированного результата.
			Description = dict(json.loads(Response.text))["content"]
			# Запись в лог сообщения о запросе описания тайтла.
			logging.info("Title: \"" + self.__Slug + "\". Request title description... Done.")
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request title description: \"" + TitlesAPI + "\". Response code: " + str(Response.status_code) + ".")

		return Description

	# Выполняет слияние ветвей переводов.
	def __MergeBranches(self) -> dict:
		# Список ID ветвей локального файла.
		LocalBranchesID = list()
		# Удалённый описательный файл JSON.
		RemangaTitle = self.__Title
		# Локальный описательный файл JSON.
		LocalTitle = None
		# Счётчик перемещённых глав.
		MergedChaptersCounter = 0
		# Запись в лог сообщения о том, что найден локальный файл описания тайтла.
		logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Trying to merge...")
		# Переключение статуса слияния.
		self.__IsMerged = True

		# Открытие локального описательного файла JSON.
		with open("Titles\\" + self.__Slug + ".json", encoding = "utf-8") as FileRead:
			# JSON файл тайтла.
			LocalTitle = json.load(FileRead)

			# Проверка файла на пустоту.
			if LocalTitle == None:
				pass
			else:

				# Заполнение списка ID ветвей удалённого JSON.
				for Branch in LocalTitle["branches"]:
					LocalBranchesID.append(str(Branch["id"]))

				# Перемещение информации о слайдах.
				for BranchID in LocalBranchesID:
					for ChapterIndex in range(0, len(LocalTitle["chapters"][BranchID])):
						# Проверка главы на платность.
						if LocalTitle["chapters"][BranchID][ChapterIndex]["is_paid"] == False:
							# Перемещение данных о слайдах из локального файла в новый, полученный с сервера.
							RemangaTitle["chapters"][BranchID][ChapterIndex]["slides"] = LocalTitle["chapters"][BranchID][ChapterIndex]["slides"]
							# Инкремент счётчика.
							MergedChaptersCounter += 1

		# Запись в лог сообщения о завершении объединения локального и удалённого файлов.
		if MergedChaptersCounter > 0:
			logging.info("Title: \"" + self.__Slug + "\". Merged chapters: " + str(MergedChaptersCounter) + ".")
		else:
			logging.info("Title: \"" + self.__Slug + "\". There are no new chapters.")

		return RemangaTitle

	# Конструктор: строит каркас словаря и проверяет наличие локальных данных.
	def __init__(self, Settings: dict, Slug: str, ForceMode: bool = True, Message: str = "", Amending: bool = True):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Передача аргументов.
		#==========================================================================================#
		self.__Settings = Settings
		self.__Slug = Slug
		self.__ForceMode = ForceMode
		self.__Message = Message + "Current title: " + Slug + "\n\n"
		self.__RequestHeaders = {
			"referer": "https://remanga.org/",
			"User-Agent": UserAgent,
			"authorization": self.__Settings["authorization"]
			}

		# Удаление существующего файла, если указано.
		if ForceMode == True and os.path.exists("Titles\\" + Slug + ".json"):
			os.remove("Titles\\" + Slug + ".json")
			# Запись в лог сообщения о перезаписи файла.
			logging.info("Title: \"" + self.__Slug + "\". Already exists. Will be overwritten...")

		# Запись в лог сообщения о начале парсинга.
		logging.info("Title: \"" + self.__Slug + "\". Parcing...")
		# Запись в лог сообщения об использованном User-Agent.
		logging.debug("User-Agent: \"" + UserAgent + "\".")

		#---> Построение каркаса словаря.
		#==========================================================================================#
		# Получение описания тайтла.
		self.__Title = self.__GetTitleDescription()
		# Создание ключа для последующего помещения туда глав.
		self.__Title["chapters"] = dict()

		# Генерация ветвей и заполнение их данными о главах.
		for Branch in self.__Title["branches"]:
			self.__Title["chapters"][str(Branch["id"])] = self.__GetBranchData(str(Branch["id"]), str(Branch["count_chapters"]))

		#---> Дополнение каркаса данными о страницах глав.
		#==========================================================================================#

		# Слияние локальной и удалённой ветвей.
		if os.path.exists("Titles\\" + self.__Slug + ".json"):
			self.__Title = self.__MergeBranches()

		# Получение недостающих данных о страницах глав.
		if Amending == True:
			self.AmendChapters()

	# Проверяет все главы на наличие описанных страниц и дополняет их, если это необходимо.
	def AmendChapters(self):
		# Список ID ветвей.
		BranchesID = list()
		# Счётчик глав, для которых были получены страницы.
		UpdatedChaptersCounter = 0
		# Запись в лог сообщения о старте получения информации о страницах глав.
		logging.info("Title: \"" + self.__Slug + "\". Amending...")

		# Заполнение списка ID ветвей.
		for Branch in self.__Title["branches"]:
			BranchesID.append(str(Branch["id"]))

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
						# Запись в лог сообщения об успешном добавлинии информации о страницах главы.
						logging.info("Title: \"" + self.__Slug + "\". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " amended.")
						# Инкремент счётчика.
						UpdatedChaptersCounter += 1
						# Выжидание указанного интервала.
						time.sleep(self.__Settings["delay"])
					else:
						# Запись в лог сообщения о платной главе.
						logging.warning("Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " is paid. Skipped.")

		# Запись в лог сообщения о количестве дополненных глав.
		logging.info("Title: \"" + self.__Slug + "\". Amended chapters: " + str(UpdatedChaptersCounter) + ".")

	# Загружает обложки тайтла.
	def DownloadCovers(self):
		# Список URL обложек.
		CoversURL = list()
		# Очистка терминала.
		Cls()
		# Вывод сообщения из внешнего обработчика и заголовка.
		print(self.__Message, end = "")
		# Ответ запроса.
		Response = None
		# Счётчик загруженных обложек.
		DownloadedCoversCounter = 0
		# Запись URL обложек.
		CoversURL.append("https://remanga.org" + self.__Title["img"]["high"])
		CoversURL.append("https://remanga.org" + self.__Title["img"]["mid"])
		CoversURL.append("https://remanga.org" + self.__Title["img"]["low"])

		# Скачивание обложек.
		for URL in CoversURL:

			# Проверка существования файлов.
			if os.path.exists("Covers\\" + self.__Slug + "\\" + URL.split('/')[-1]) == False or os.path.exists("Covers\\" + self.__Slug + "\\" + URL.split('/')[-1]) == True and self.__ForceMode == True:
				# Вывод в терминал URL загружаемой обложки.
				print("Downloading cover: \"" + URL + "\"... ", end = "")

				# Выполнение запроса с прокси-сервером, если указано, или без него.
				if self.__Settings["use-proxy"] == True:
					Response = requests.get(URL, headers = self.__RequestHeaders, proxies = self.__Settings["proxy"][random.randint(0, len(self.__Settings["proxy"]) - 1)])
				else:
					Response = requests.get(URL, headers = self.__RequestHeaders)

				# Проверка успешности запроса.
				if Response.status_code == 200:

					# Создание папки для обложек.
					if not os.path.exists("Covers"):
						os.makedirs("Covers")

					# Создание папки с алиасом тайтла в качестве названия.
					if not os.path.exists("Covers\\" + self.__Slug):
						os.makedirs("Covers\\" + self.__Slug)

					# Открытие потока записи.
					with open("Covers\\" + self.__Slug + "\\" + URL.split('/')[-1], "wb") as FileWrite:
						# Запись изображения.
						FileWrite.write(Response.content)
						# Инкремент счётчика загруженных обложек.
						DownloadedCoversCounter += 1
						# Вывод в терминал сообщения об успешной загрузке.
						print("Done.")

				else:
					# Запись в лог сообщения о неудачной попытке загрузки обложки.
					logging.error("Title: \"" + self.__Slug + "\". Unable download cover: \"" + URL + "\". Response code: " + str(Response.status_code == 200) + ".")
					# Вывод в терминал сообщения об успешной загрузке.
					print("Failure!")

			else:
				# Вывод в терминал URL загружаемой обложки.
				print("Cover already exist: \"" + URL + "\". Skipped. ")

			# Выжидание указанного интервала, если не все обложки загружены.
			if DownloadedCoversCounter < 3:
				time.sleep(self.__Settings["delay"])

		# Запись в лог сообщения о количестве загруженных обложек.
		logging.info("Title: \"" + self.__Slug + "\". Covers downloaded: " + str(DownloadedCoversCounter) + ".")

	# Сохраняет локальный JSON файл.
	def Save(self, DownloadCovers: bool = True):
		# Список ID ветвей.
		BranchesID = list()

		# Создание папки для тайтлов.
		if os.path.exists("Titles") == False:
			os.makedirs("Titles")

		# Заполнение списка ID ветвей.
		for Branch in self.__Title["branches"]:
			BranchesID.append(str(Branch["id"]))

		# Инвертирование порядка глав в ветвях.
		for BranchID in BranchesID:
			self.__Title["chapters"][BranchID].reverse()

		# Если указано, скачать обложки.
		if DownloadCovers == True:
			self.DownloadCovers()

		# Сохранение локального файла JSON.
		with open("Titles\\" + self.__Slug + ".json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Title, FileWrite, ensure_ascii = False, indent = 2, separators = (',', ': '))

			# Запись в лог сообщения о создании или обновлении локального файла.
			if self.__IsMerged == True:
				logging.info("Title: \"" + self.__Slug + "\". Updated.")
			else:
				logging.info("Title: \"" + self.__Slug + "\". Parced.")
