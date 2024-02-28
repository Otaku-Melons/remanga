from dublib.Methods import Cls, ReadJSON, RemoveFolderContent, WriteJSON
from Source.Functions import CompareImages, MergeListOfLists
from Source.RequestsManager import RequestsManager
from Source.Formatter import Formatter
from time import sleep

import logging
import shutil
import json
import os

# Обработчик взаимодействий парсера и сайта.
class TitleParser:
	
	# Фильтрует заглушки для тайтлов без собственной обложки.
	def __FilterCovers(self, CoverPath: str, CoverIndex: int) -> bool:
		# Состояние: отвильтрована ли обложка.
		IsFiltered = False
		# Список названий файлов фильтров.
		FiltersFilenames = ["high", "mid", "low"]
		
		# Для каждого фильтра.
		for Filter in os.listdir("Source/Filters"):
			# Сравнение изображений.
			Result = CompareImages(f"Source/Filters/{Filter}/" + FiltersFilenames[CoverIndex] + ".jpg", CoverPath)
		
			# Если разница между обложкой и шаблоном составляет менее 50%.
			if Result != None and Result < 50.0:
				# Удалить файл обложки.
				os.remove(CoverPath)
				# Удалить запись об обложке.
				self.__Title["img"][FiltersFilenames[CoverIndex]] = ""
				# Переключить статус фильтрации.
				IsFiltered = True
		
		return IsFiltered
		
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
			# Объединение групп слайдов.
			ChapterData["slides"] = MergeListOfLists(ChapterData["pages"])
			# Удаление старого ключа.
			del ChapterData["pages"]
			
		else:
			# Запись в лог предупреждения: не удалось запросить данные главы.
			logging.error("Unable to request chapter data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

		# Выжидание указанного интервала.
		sleep(self.__Settings["delay"])

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
				if BranchData == None:
					BranchData = list()

				# Дополнение информации о ветви новой страницей.
				BranchData += CurrentBranchData

			else:
				# Запись в лог сообщения о том, что не удалось выполнить запрос.
				logging.error("Unable to request branch data: \"" + ChaptersAPI + "\". Response code: " + str(Response.status_code) + ".")

			# Выжидание указанного интервала.
			sleep(self.__Settings["delay"])

		# Если ветвь не пустая.
		if BranchData != None:
			
			# Для каждой главы создать ключ для слайдов.
			for Index in range(0, len(BranchData)):
				BranchData[Index]["slides"] = list()
				
			# Запись в лог сообщения: завершено получение данных о ветвях.
			logging.info("Title: " + self.__TitleHeader + ". Request title branches... Done.")

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
			logging.info("Title: " + self.__TitleHeader + ". Request title description... Done.")

		# Обработка ошибки доступа в виду отсутствия токена авторизации.
		elif Response.status_code == 401:
			# Перекючение парсера в неактивное состояние.
			self.__IsActive = False
			# Запись в лог предупреждения: невозможно получить доступ к 18+ тайтлу без токена авторизации.
			logging.warning("Title: " + self.__TitleHeader + ". Authorization token required. Skipped.")

		# Обработка ошибки запроса отсутствующего на сервере тайтла.
		elif Response.status_code == 404:
			# Перекючение парсера в неактивное состояние.
			self.__IsActive = False
			# Запись в лог предупреждения: тайтл не найден.
			logging.warning("Title: " + self.__TitleHeader + ". Not found. Skipped.")

		# Обработка любой другой ошибки запроса.
		else:
			# Запись в лог сообщения о том, что не удалось выполнить запрос.
			logging.error("Unable to request title description: \"" + TitlesAPI + "\". Response code: " + str(Response.status_code) + ".")

		# Выжидание указанного интервала.
		sleep(self.__Settings["delay"])

		return Description

	# Выполняет слияние ветвей переводов.
	def __MergeBranches(self, UsedTitleName: str) -> dict:
		# Список ID ветвей локального файла.
		LocalBranchesID = list()
		# Список ID ветвей на сайте.
		RemangaBranchesID = list()
		# Удалённый описательный файл JSON.
		RemangaTitle = self.__Title.copy()
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
			logging.info("Title: \"" + self.__Slug + "\". Local JSON already exists. Merging...")
			# Чтение локального описательного файла JSON.
			LocalTitle = ReadJSON(self.__Settings["titles-directory"] + UsedTitleName + ".json")

			# Для каждой ветви на сайте записать ID.
			for Branch in RemangaTitle["branches"]:
				RemangaBranchesID.append(str(Branch["id"]))

			# Если формат HTMP-V1.
			if LocalTitle["format"].upper() == "HTMP-V1":
				# Инициализатора конвертера.
				Converter = Formatter(self.__Settings, LocalTitle, "htmp-v1")
				# Конвертирование формата в HTCRN-V1.
				LocalTitle = Converter.convert("htcrn-v1")
				# Список ID всех ветвей.
				AllBranchesID = list()
				
				# Получение списка ID локальных ветвей.
				for Branch in LocalTitle["branches"]:
					LocalBranchesID.append(str(Branch["id"]))
				
				# Получение списка ID всех ветвей.
				for Branch in self.__Title["branches"]:
					AllBranchesID.append(Branch["id"])

				# Проверка: существует ли наследуемая ветвь на сайте.
				if LocalTitle["branchId"] not in AllBranchesID:
					# Перевод парсера в неактивное состояние.
					self.__IsActive = False
					# Запись в лог сообщения: наследуемая ветвь была удалена на сайте.
					logging.warning("Title: " + self.__TitleHeader + ". Legacy branch was removed from site!")

			# Если формат не HTMP-V1.
			else:
				# Исходный формат.
				OriginalFormat = LocalTitle["format"] if "format" in LocalTitle.keys() else "rn-v1"
				# Инициализатора конвертера.
				Converter = Formatter(self.__Settings, LocalTitle, OriginalFormat)
				# Конвертирование формата в совместимый.
				LocalTitle = Converter.convert("rn-v1")

				# Получение списка ветвей.
				for Branch in LocalTitle["branches"]:
					LocalBranchesID.append(str(Branch["id"]))

			# Если тайтл активен.
			if self.__IsActive == True:
				
				# Для каждой локальной ветви.
				for BranchID in LocalBranchesID:
					
					# Если локальная ветвь присутствует на сайте.
					if BranchID in RemangaBranchesID:
					
						# Для каждой главы в локальной ветви.
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
									
							#---> Проверка: является ли текущая ветвь HTMP-V1 самой длинной.
							#==========================================================================================#

							# Если формат HTMP-V1.
							if LocalTitle["format"].upper() == "HTMP-V1":
								# Копия ветвей тайтла.
								BranchesBufer = RemangaTitle["branches"]
								# Сортировка копии по количеству глав.
								BranchesBufer = sorted(BranchesBufer, key = lambda d: d["count_chapters"])

								# Проверка несоответствия текущей ветви и длиннейшей при обработке форматов с одной активной ветвью.
								if LocalTitle["branchId"] != BranchesBufer[0]["id"]:
									# Получение ID ветви с большим количеством глав.
									BranchID = str(BranchesBufer[0]["id"])
									# Запись в лог: доступна ветвь с большим количеством глав.
									logging.warning("Title: " + self.__TitleHeader + f". Branch with more chapters count (BID: {BranchID}) available!")
									
					else:
						# Запись в лог предупреждения: ветвь была удалена.
						logging.warning("Title: " + self.__TitleHeader + f". Branch with ID {BranchID} was removed on site.")
						
						# Если есть определение контента в локальном файле, то скопировать его.
						if BranchID in LocalTitle["chapters"].keys():
							RemangaTitle["chapters"][BranchID] = LocalTitle["chapters"][BranchID]
							RemangaTitle["branches"].append(
							{
								"id": int(BranchID),
								"img": "",
								"subscribed": False,
								"total_votes": 0,
								"count_chapters": len(LocalTitle["chapters"][BranchID]),
								"publishers": [
									{
										"id": 0,
										"name": "",
										"img": "",
										"dir": "",
										"tagline": "",
										"type": ""
									}
									]
							})
						
				# Запись в лог сообщения: завершение слияния.
				logging.info("Title: " + self.__TitleHeader + ". Merged chapters: " + str(self.__MergedChaptersCount) + ".")

		return RemangaTitle

	# Конструктор: строит каркас словаря и проверяет наличие локальных данных.
	def __init__(self, Settings: dict, Slug: str, ForceMode: bool = True, Message: str = "", Amending: bool = True, Unstub: bool = False):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Количество скопированных из локального файла глав.
		self.__MergedChaptersCount  = 0
		# Менеджер запросов через прокси.
		self.__RequestsManager = RequestsManager(Settings)
		# Заголовок тайтла для логов и вывода в терминал.
		self.__TitleHeader = f"\"{Slug}\""
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
			"Authorization": self.__Settings["authorization-token"],
			"Referer": "https://remanga.org/",
		}

		# Если токена авторизации нет, удалить заголовок.
		if self.__RequestHeaders["Authorization"] == "": del self.__RequestHeaders["Authorization"]
		# Запись в лог сообщения о начале парсинга.
		logging.info("Title: " + self.__TitleHeader + ". Parsing...")

		#---> Построение каркаса словаря.
		#==========================================================================================#
		# Если не запущен режим фильтрации заглушек, запросить данные тайтла.
		if Unstub == False: self.__Title = self.__GetTitleDescription()

		# Если не запущен режим фильтрации заглушек и тайтл активен.
		if Unstub == False and self.__IsActive == True:
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
				self.amendChapters()

	# Проверяет все главы на наличие описанных страниц и дополняет их, если это необходимо.
	def amendChapters(self):

		# Если парсер активен.
		if self.__IsActive == True:
			# Список ID ветвей.
			BranchesID = list()
			# Счётчик глав, для которых были получены страницы.
			UpdatedChaptersCounter = 0
			# Количество глав во всех ветвях тайтла.
			AllBranchesChaptersCount = self.__GetChaptersCountInAllBranches()
			# Запись в лог сообщения о старте получения информации о страницах глав.
			logging.info("Title: " + self.__TitleHeader + ". Amending...")

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
					if self.__Title["chapters"][BranchID][ChapterIndex]["slides"] == list():

						# Проверка главы на платность.
						if self.__Title["chapters"][BranchID][ChapterIndex]["is_paid"] == False:
							# Получение информации о страницах главы.
							self.__Title["chapters"][BranchID][ChapterIndex]["slides"] = self.__GetChapterData(self.__Title["chapters"][BranchID][ChapterIndex]["id"])["slides"]
							# Запись в лог сообщения об успешном добавлинии информации о страницах главы.
							logging.info("Title: " + self.__TitleHeader + ". Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " amended.")
							# Инкремент счётчика.
							UpdatedChaptersCounter += 1
							# Выжидание указанного интервала.
							sleep(self.__Settings["delay"])

						else:
							# Запись в лог сообщения: глава платная.
							logging.info("Chapter " + str(self.__Title["chapters"][BranchID][ChapterIndex]["id"]) + " is paid. Skipped.")

			# Запись в лог сообщения о количестве дополненных глав.
			logging.info("Title: " + self.__TitleHeader + ". Amended chapters: " + str(UpdatedChaptersCounter) + ".")

	# Загружает обложки тайтла.
	def downloadCovers(self):

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
			# Количество загруженных обложек.
			DownloadedCoversCount = 0
			# Состояние: отфильтрованы ли обложки.
			IsCoversFiltered = False
			# Используемое имя тайтла: ID или алиас.
			UsedTitleName = self.__Slug if self.__Settings["use-id-instead-slug"] == False else self.__ID
			# Типы обложек.
			CoversTypes = ["high", "mid", "low"]
			
			# Для каждого типа обложки.
			for Type in CoversTypes:
				
				# Если указан URL обложки.
				if self.__Title["img"]["high"] not in ["/media/None", None]:
					# Запись URL обложки.
					CoversURL.append("https://remanga.org" + self.__Title["img"][Type])
					
				else:
					# Запись в лог предупреждения: отсутствует URL обложки.
					logging.warning("Title: " + self.__TitleHeader + f". Missing \"{Type}\" cover URL.")
					# Вывод в терминал данных обложки.
					print(f"Missing \"{Type}\" cover URL. Skipped.")

			# Скачивание обложек.
			for Index in range(0, len(CoversURL)):
				# Имя файла обложки.
				CoverFilename = self.__Settings["covers-directory"] + UsedTitleName + "/" + CoversURL[Index].split('/')[-1]
				
				# Если включен режим перезаписи, то удалить файлы обложек.
				if self.__ForceMode == True:
					
					# Удалить файл обложки.
					if os.path.exists(self.__Settings["covers-directory"] + self.__Slug + "/" + CoversURL[Index].split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__Slug) 
						
					elif os.path.exists(self.__Settings["covers-directory"] + self.__ID + "/" + CoversURL[Index].split('/')[-1]):
						shutil.rmtree(self.__Settings["covers-directory"] + self.__ID) 

				# Для каждого состояния переключателя, указывающего, что использовать для названия файла.
				for State in [True, False]:
					# Установка устаревшего имени папки с обложками в зависимости от статуса.
					Foldername = self.__Settings["covers-directory"] + self.__Slug if State == True else self.__ID

					# Удаление папки для обложек с устаревшим названием.
					if self.__Settings["use-id-instead-slug"] == State and os.path.exists(Foldername + "/" + CoversURL[Index].split('/')[-1]):
						shutil.rmtree(Foldername)

				# Проверка существования файла.
				if os.path.exists(CoverFilename) == False:
					# Вывод в терминал URL загружаемой обложки.
					print("Downloading cover: \"" + CoversURL[Index] + "\"... ", end = "")

					# Выполнение запроса.
					Response = self.__RequestsManager.request(CoversURL[Index], Headers = ImageRequestHeaders)

					# Проверка успешности запроса.
					if Response.status_code == 200:

						# Создание папки для обложек.
						if os.path.exists(self.__Settings["covers-directory"]) == False:
							os.makedirs("Covers")

						# Создание папки с алиасом тайтла в качестве названия.
						if os.path.exists(self.__Settings["covers-directory"] + UsedTitleName) == False:
							os.makedirs(self.__Settings["covers-directory"] + UsedTitleName)

						# Открытие потока записи.
						with open(CoverFilename, "wb") as FileWrite:
							# Запись изображения.
							FileWrite.write(Response.content)
							# Инкремент счётчика загруженных обложек.
							DownloadedCoversCount += 1
							# Вывод в терминал: успешная загрузка.
							print("Done.")

					else:
						# Запись в лог ошибки: не удалось загрузить обложку.
						logging.error("Title: " + self.__TitleHeader + ". Unable download cover: \"" + CoversURL[Index] + "\". Response code: " + str(Response.status_code) + ".")
						# Вывод в терминал: ошибка загрузки.
						print("Failure!")

				else:
					# Вывод в терминал URL загружаемой обложки.
					print("Cover already exist: \"" + CoversURL[Index] + "\". Skipped.")
					
				# Если включена фильтрация заглушек и обложка отфильтрована.
				if self.__Settings["filter-covers"] == True and self.__FilterCovers(CoverFilename, Index) == True:
					# Переключение статуса фильтрации.
					IsCoversFiltered = True
					# Удаление файлов обложек.
					RemoveFolderContent(self.__Settings["covers-directory"] + UsedTitleName)
					# Очистка записей об обложках.
					self.__Title["img"]["high"] = ""
					self.__Title["img"]["mid"] = ""
					self.__Title["img"]["low"] = ""
					# Остановка цикла.
					break
						
				# Выжидание указанного интервала, если не все обложки загружены.
				if DownloadedCoversCount < 3: sleep(self.__Settings["delay"])
			
			if IsCoversFiltered == True:
				# Вывод в терминал: обложки отфильтрованы.
				print(f"\nAll covers filtered as stubs!")
				# Запись в лог сообщения: обложки отфильтрованы.
				logging.info("Title: " + self.__TitleHeader + ". Covers filtered as stubs.")
				
			else:
				# Запись в лог сообщения: количество загруженных обложек.
				logging.info("Title: " + self.__TitleHeader + ". Covers downloaded: " + str(DownloadedCoversCount) + ".")
			
	# Заменяет главу свежей версией с сервера.
	def repairChapter(self, ChapterID: str):
		# Состояние: восстановлена ли глава.
		IsRepaired = False
		
		# Для каждой главы в каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				
				# Если ID главы совпадает с целевым.
				if self.__Title["chapters"][BranchID][ChapterIndex]["id"] == int(ChapterID):
					# Переключить состояние в успешное.
					IsRepaired = True
					
					# Если глава бесплатная.
					if self.__Title["chapters"][BranchID][ChapterIndex]["is_paid"] == False:
						# Запрос данных главы и переименование ключа со слайдами.
						self.__Title["chapters"][BranchID][ChapterIndex] = self.__GetChapterData(ChapterID)
						# Запись в лог сообщения: глава восстановлена.
						logging.info(f"Chapter {ChapterID} repaired.")
						
					else:
						# Запись в лог сообщения: глава платная.
						logging.info(f"Chapter {ChapterID} is paid. Skipped.")
		
		# Если глава не найдена.
		if IsRepaired == False:
			# Запись в лог критической ошибки: не найдена глава с указанным ID.
			logging.critical(f"Unable to find chapter with ID: {ChapterID}.")
			# Выброс исключения.
			raise Exception(f"unable to find chapter in local file")

	# Русифицирует ссылки на слайды.
	def rusificateLinks(self):
		
		# Для каждой ветви.
		for BranchID in self.__Title["chapters"].keys():
			
			# Для каждой главы.
			for ChapterIndex in range(0, len(self.__Title["chapters"][BranchID])):
				
				# Для каждого слайда.
				for SlideIndex in range(0, len(self.__Title["chapters"][BranchID][ChapterIndex]["slides"])):
					# Ссылка на слайд.
					Link = self.__Title["chapters"][BranchID][ChapterIndex]["slides"][SlideIndex]["link"]
					# Если слайд на пятом международном сервере, заменить его.
					if Link.startswith("https://img5.reimg.org"): Link = Link.replace("https://img5.reimg.org", "https://reimg2.org")
					# Замена других серверов.
					Link = Link.replace("reimg.org", "reimg2.org")
					# Сохранение результата.
					self.__Title["chapters"][BranchID][ChapterIndex]["slides"][SlideIndex]["link"] = Link

	# Сохраняет локальный JSON файл.
	def save(self, DownloadCovers: bool = True):
		# Используемое имя тайтла: ID или алиас.
		UsedTitleName = self.__Slug if self.__Settings["use-id-instead-slug"] == False else self.__ID
		
		# Если парсер активен.
		if self.__IsActive == True:
			
			# Если указано, русифицировать ссылки на слайды.
			if self.__Settings["ru-links"] == True: self.rusificateLinks()

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
				self.downloadCovers()

			# Инициализация конвертера.
			FormatterObject = Formatter(self.__Settings, self.__Title, "rn-v1")
			FormattedTitle = FormatterObject.convert(self.__Settings["format"])

			# Сохранение локального файла JSON.
			with open(self.__Settings["titles-directory"] + UsedTitleName + ".json", "w", encoding = "utf-8") as FileWrite:
				json.dump(FormattedTitle, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

				# Запись в лог сообщения: создан или обновлён локальный файл.
				if self.__MergedChaptersCount > 0:
					logging.info("Title: " + self.__TitleHeader + ". Updated.")
				else:
					logging.info("Title: " + self.__TitleHeader + ". Parsed.")
					
	# Фильтрует заглушки обложек.
	def unstub(self) -> bool:
		# Используемое имя тайтла.
		UsedTitleName = self.__Slug.replace(".json", "")
		# Чтение тайтла.
		self.__Title = ReadJSON(self.__Settings["titles-directory"] + self.__Slug)
		# Инициализатора конвертера.
		Converter = Formatter(self.__Settings, self.__Title)
		# Конвертирование формата в совместимый.
		self.__Title = Converter.convert("rn-v1")
		# Список URL обложек.
		CoversURL = list()
		# Состояние: отфильтрованы ли обложки.
		IsFiltered = False
		# Запись URL обложек.
		if self.__Title["img"]["high"] != "": CoversURL.append("https://remanga.org" + self.__Title["img"]["high"])
		if self.__Title["img"]["mid"] != "": CoversURL.append("https://remanga.org" + self.__Title["img"]["mid"])
		if self.__Title["img"]["low"] != "": CoversURL.append("https://remanga.org" + self.__Title["img"]["low"])
		
		# Скачивание обложек.
		for Index in range(0, len(CoversURL)):
			# Имя файла обложки.
			CoverFilename = self.__Settings["covers-directory"] + UsedTitleName + "/" + CoversURL[Index].split('/')[-1]
			
			# Если обложка отфильтрована.
			if self.__FilterCovers(CoverFilename, Index) == True:
				# Переключение состояния.
				IsFiltered = True
				# Удаление файлов обложек.
				RemoveFolderContent(self.__Settings["covers-directory"] + UsedTitleName)
				# Очистка записей об обложках.
				self.__Title["img"]["high"] = ""
				self.__Title["img"]["mid"] = ""
				self.__Title["img"]["low"] = ""
				# Запись в лог сообщения: количество удалённых заглушек.
				logging.info("Title: \"" + self.__Slug + "\". Covers filtered as stubs.")
				# Остановка цикла.
				break
			
		# Инициализатора конвертера.
		Converter = Formatter(self.__Settings, self.__Title)
		# Конвертирование формата в совместимый.
		self.__Title = Converter.convert(self.__Settings["format"])
		# Сохранение файла.
		WriteJSON(self.__Settings["titles-directory"] + self.__Slug, self.__Title)
		# Если обложки не были отфильтрованы, записать сообщение в лог.
		if IsFiltered == False: logging.info("Title: \"" + self.__Slug + "\". Filtering done.")

		return IsFiltered		