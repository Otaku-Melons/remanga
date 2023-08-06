from dublib.Methods import MergeDictionaries, RenameDictionaryKey, RemoveHTML
from PIL import Image, UnidentifiedImageError

import logging
import os
import re

# Исключение: не существует подходящего конвертера для указанных форматов.
class UnableToConvert(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self, SourceFormat: str, TargetFormat: str): 
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message)
		# Добавление данных в сообщение об ошибке.
		self.__Message = "there isn't suitable converter for these formats: \"" + SourceFormat + "\" > \"" + TargetFormat + "\""
			
	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

# Исключение: указан неизвестный формат.
class UnknownFormat(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self, UnknownFormat: str): 
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message) 
		# Добавление данных в сообщение об ошибке.
		self.__Message = "couldn't recognize source or target format: \"" +  UnknownFormat + "\""
			
	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

# Форматировщик структур описательных файлов тайтлов.
class Formatter:

	#==========================================================================================#
	# >>>>> КОНВЕРТЕРЫ <<<<< #
	#==========================================================================================#

	# Конвертер: DMP-V1 > HCMP-V1.
	def __DMP1_to_HCMP1(self):
		# Перечисление типов тайтла.
		Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "ANOTHER"]
		# Перечисление статусов тайтла.
		Statuses = ["COMPLETED", "ACTIVE", "ABANDONED", "NOT_FOUND", "", "LICENSED"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()
		# Перечисление названий жанров, обозначающих однополые отношения.
		HomoGenres = ["яой", "сёдзё-ай", "сёнэн-ай", "юри"]

		#---> Генерация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "hcmp-v1"
		FormattedTitle["site"] = self.__OriginalTitle["site"]
		FormattedTitle["id"] = self.__OriginalTitle["id"]
		FormattedTitle["slug"] = self.__OriginalTitle["slug"].replace(str(self.__OriginalTitle["id"]) + "-", "")
		FormattedTitle["originalLink"] = "https://hentaichan.live/manga/" + self.__OriginalTitle["slug"] + ".html"
		FormattedTitle["fullTitle"] = None
		FormattedTitle["rusTitle"] = self.__OriginalTitle["ru-name"]
		FormattedTitle["engTitle"] = self.__OriginalTitle["en-name"]
		FormattedTitle["alternativeTitle"] = " / ".join(self.__OriginalTitle["another-names"])
		FormattedTitle["type"] = self.__OriginalTitle["type"]
		FormattedTitle["status"] = self.__OriginalTitle["status"]
		FormattedTitle["isHentai"] = True
		FormattedTitle["isYaoi"] = False
		FormattedTitle["img"] = dict()
		FormattedTitle["series"] = list()
		FormattedTitle["authors"] = list()
		FormattedTitle["translators"] = list()
		FormattedTitle["tags"] = list()
		FormattedTitle["genres"] = list()
		FormattedTitle["chapters"] = list()

		#---> Внесение правок.
		#==========================================================================================#

		# Генерауия ключей обложек.
		FormattedTitle["img"]["high"] = None
		FormattedTitle["img"]["mid"] = None
		FormattedTitle["img"]["low"] = None

		# Конвертирование обложек.
		for CoverIndex in range(0, len(self.__OriginalTitle["covers"])):
			# Используемое наименование тайтла.
			UsetTitleName = None

			# Если используется ID для именования тайтла.
			if self.__Settings["use-id-instead-slug"] == True:
				UsetTitleName = str(self.__OriginalTitle["id"])
			else:
				UsetTitleName = self.__OriginalTitle["slug"]

			if CoverIndex == 0:
				FormattedTitle["img"]["high"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]
			if CoverIndex == 1:
				FormattedTitle["img"]["mid"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]
			if CoverIndex == 2:
				FormattedTitle["img"]["low"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]

		# Проверка наличия статуса.
		if FormattedTitle["status"] == None:
			FormattedTitle["status"] = "NOT_FOUND"

		# Проверка наличия типа.
		if FormattedTitle["type"] == None:
			FormattedTitle["type"] = "MANGA"

		# Определение наличия жанра яой.
		for Genre in FormattedTitle["genres"]:
			if Genre["name"].lower() == "яой":
				FormattedTitle["isYaoi"] = True
		
		# Индекс обрабатываемой главы.
		CurrentChapterIndex = 0

		# Конвертирование глав.
		for OriginalChapter in self.__OriginalTitle["chapters"][list(self.__OriginalTitle["chapters"].keys())[0]]:
			# Буфер текущей главы.
			CurrentChapter = dict()
			# Перенос данных.
			CurrentChapter["id"] = OriginalChapter["id"]
			CurrentChapter["chapter"] = CurrentChapterIndex + 1
			CurrentChapter["originalChapter"] = OriginalChapter["number"]
			CurrentChapter["title"] = OriginalChapter["name"]
			CurrentChapter["tom"] = OriginalChapter["volume"]
			CurrentChapter["index"] = CurrentChapterIndex
			CurrentChapter["slides"] = OriginalChapter["slides"]

			# Проверка отсутствия тома.
			if CurrentChapter["tom"] == None:
				CurrentChapter["tom"] = 1

			# Проверка отсутствия названия.
			if CurrentChapter["title"] == None:
				CurrentChapter["title"] = ""

			# Удаление индексов из слайдов.
			for SlideIndex in range(0, len(CurrentChapter["slides"])):
				del CurrentChapter["slides"][SlideIndex]["index"]

			# Если у главы нет оригинального номера, то присвоить ей оригинальный номер равный индексу плюс один.
			if CurrentChapter["originalChapter"] == None:
				CurrentChapter["originalChapter"] = CurrentChapterIndex + 1

			# Сохранение результата.
			FormattedTitle["chapters"].append(CurrentChapter)
			# Инкремент индекса главы.
			CurrentChapterIndex += 1

		# Конвертирование тегов.
		for TagIndex in range(0, len(self.__OriginalTitle["tags"])):
			FormattedTitle["tags"].append({"id": 0, "name": self.__OriginalTitle["tags"][TagIndex].capitalize()})

		# Конвертирование жанров.
		for GenreIndex in range(0, len(self.__OriginalTitle["genres"])):
			FormattedTitle["genres"].append({"id": 0, "name": self.__OriginalTitle["genres"][GenreIndex].capitalize()})

		# Установка автора.
		if self.__OriginalTitle["author"] != None:
			FormattedTitle["authors"].append({ "id": 0, "name": self.__OriginalTitle["author"] })

		# Установка серии.
		if self.__OriginalTitle["series"] != None:
			FormattedTitle["series"].append({ "id": 0, "name": self.__OriginalTitle["series"] })

		return FormattedTitle

	# Конвертер: DMP-V1 > HTMP-V1.
	def __DMP1_to_HTMP1(self):
		# Перечисление типов тайтла.
		Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "ANOTHER"]
		# Перечисление статусов тайтла.
		Statuses = ["COMPLETED", "ACTIVE", "ABANDONED", "NOT_FOUND", "", "LICENSED"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

		# Перечисление названий жанров, обозначающих однополые отношения.
		HomoGenres = ["яой", "сёдзё-ай", "сёнэн-ай", "юри"]

		#---> Генерация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "htmp-v1"
		FormattedTitle["site"] = self.__OriginalTitle["site"]
		FormattedTitle["id"] = self.__OriginalTitle["id"]
		FormattedTitle["img"] = dict()
		FormattedTitle["engTitle"] = self.__OriginalTitle["en-name"]
		FormattedTitle["rusTitle"] = self.__OriginalTitle["ru-name"]
		FormattedTitle["alternativeTitle"] = " / ".join(self.__OriginalTitle["another-names"])
		FormattedTitle["slug"] = self.__OriginalTitle["slug"]
		FormattedTitle["desc"] = self.__OriginalTitle["description"]
		FormattedTitle["issue_year"] = self.__OriginalTitle["publication-year"]
		FormattedTitle["branchId"] = self.__OriginalTitle["branches"][0]["id"]
		FormattedTitle["admin_rating"] = ""
		FormattedTitle["count_rating"] = 0
		FormattedTitle["age_limit"] = self.__OriginalTitle["age-rating"]
		FormattedTitle["status"] = self.__OriginalTitle["status"]
		FormattedTitle["count_bookmarks"] = 0
		FormattedTitle["total_votes"] = 0
		FormattedTitle["total_views"] = 0
		FormattedTitle["type"] = self.__OriginalTitle["type"]
		FormattedTitle["genres"] = list()
		FormattedTitle["tags"] = list()
		FormattedTitle["bookmark_type"] = None
		FormattedTitle["branches"] = list()
		FormattedTitle["count_chapters"] = self.__OriginalTitle["branches"][0]["chapters-count"]
		FormattedTitle["first_chapter"] = dict()
		FormattedTitle["continue_reading"] = None
		FormattedTitle["is_licensed"] = self.__OriginalTitle["is-licensed"]
		FormattedTitle["newlate_id"] = None
		FormattedTitle["newlate_title"] = None
		FormattedTitle["related"] = None
		FormattedTitle["uploaded"] = 0
		FormattedTitle["isHomo"] = False
		FormattedTitle["adaptation"] = None
		FormattedTitle["publishers"] = list()
		FormattedTitle["isYaoi"] = False
		FormattedTitle["isHentai"] = False
		FormattedTitle["chapters"] = list()

		#---> Внесение правок.
		#==========================================================================================#

		# Генерауия ключей обложек.
		FormattedTitle["img"]["high"] = None
		FormattedTitle["img"]["mid"] = None
		FormattedTitle["img"]["low"] = None

		# Конвертирование обложек.
		for CoverIndex in range(0, len(self.__OriginalTitle["covers"])):
			# Используемое наименование тайтла.
			UsetTitleName = None

			# Если используется ID для именования тайтла.
			if self.__Settings["use-id-instead-slug"] == True:
				UsetTitleName = str(self.__OriginalTitle["id"])
			else:
				UsetTitleName = self.__OriginalTitle["slug"]

			if CoverIndex == 0:
				FormattedTitle["img"]["high"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]
			if CoverIndex == 1:
				FormattedTitle["img"]["mid"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]
			if CoverIndex == 2:
				FormattedTitle["img"]["low"] = UsetTitleName + "/" + self.__OriginalTitle["covers"][CoverIndex]["filename"]

		# Проверка наличия статуса.
		if FormattedTitle["status"] == None:
			FormattedTitle["status"] = "NOT_FOUND"

		# Проверка наличия типа.
		if FormattedTitle["type"] == None:
			FormattedTitle["type"] = "MANGA"

		# Конвертирование ветвей.
		for OriginalBranch in self.__OriginalTitle["branches"]:
			# Буфер текущей ветви.
			CurrentBranch = dict()
			# Перенос данных.
			CurrentBranch["id"] = OriginalBranch["id"]
			CurrentBranch["img"] = ""
			CurrentBranch["subscribed"] = False
			CurrentBranch["total_votes"] = 0
			CurrentBranch["count_chapters"] = OriginalBranch["chapters-count"]
			CurrentBranch["publishers"] = list()
			# Сохранение результата.
			FormattedTitle["branches"].append(CurrentBranch)

		# Конвертирование тегов.
		for TagIndex in range(0, len(self.__OriginalTitle["tags"])):
			FormattedTitle["tags"].append({"id": 0, "name": self.__OriginalTitle["tags"][TagIndex].capitalize()})

		# Конвертирование жанров.
		for GenreIndex in range(0, len(self.__OriginalTitle["genres"])):
			FormattedTitle["genres"].append({"id": 0, "name": self.__OriginalTitle["genres"][GenreIndex].capitalize()})

		# Определение наличия жанра однополых отношений.
		for Genre in FormattedTitle["genres"]:
			if Genre["name"].lower() in HomoGenres:
				FormattedTitle["isHomo"] = True

		# Определение наличия жанра яой.
		for Genre in FormattedTitle["genres"]:
			if Genre["name"].lower() == "яой":
				FormattedTitle["isYaoi"] = True

		# Является ли тайтл хентаем.
		if FormattedTitle["site"] == "hentaichan.live":
				FormattedTitle["isHentai"] = True
		
		# Индекс обрабатываемой главы.
		CurrentChapterIndex = 1

		# Конвертирование глав.
		for OriginalChapter in self.__OriginalTitle["chapters"][list(self.__OriginalTitle["chapters"].keys())[0]]:
			# Буфер текущей главы.
			CurrentChapter = dict()
			# Перенос данных.
			CurrentChapter["id"] = OriginalChapter["id"]
			CurrentChapter["rated"] = None
			CurrentChapter["viewed"] = None
			CurrentChapter["is_bought"] = None
			CurrentChapter["publishers"] = list()
			CurrentChapter["index"] = CurrentChapterIndex
			CurrentChapter["tom"] = OriginalChapter["volume"]
			CurrentChapter["chapter"] = OriginalChapter["number"]
			CurrentChapter["title"] = OriginalChapter["name"]
			CurrentChapter["price"] = None
			CurrentChapter["score"] = 0
			CurrentChapter["upload_date"] = ""
			CurrentChapter["pub_date"] = None
			CurrentChapter["is_paid"] = False
			CurrentChapter["slides"] = OriginalChapter["slides"]

			# Проверка отсутствия тома.
			if CurrentChapter["tom"] == None:
				CurrentChapter["tom"] = 1

			# Проверка отсутствия названия.
			if CurrentChapter["title"] == None:
				CurrentChapter["title"] = ""

			# Генерация структуры переводчиков.
			if OriginalChapter["translator"] != None:
				# Буфер переводчиков.
				Publishers = dict()
				# Перенос данных.
				Publishers["id"] = 0
				Publishers["name"] = OriginalChapter["translator"]
				Publishers["img"] = ""
				Publishers["dir"] = ""
				Publishers["tagline"] = ""
				Publishers["type"] = "Переводчик"
				# Сохранение результата.
				CurrentChapter["publishers"].append(Publishers)

			# Удаление индексов из слайдов.
			for SlideIndex in range(0, len(CurrentChapter["slides"])):
				del CurrentChapter["slides"][SlideIndex]["index"]

			# Если у главы нет номера, то присвоить ей номер равный индексу.
			if CurrentChapter["chapter"] == None:
				CurrentChapter["chapter"] = CurrentChapterIndex

			# Сохранение результата.
			FormattedTitle["chapters"].append(CurrentChapter)
			# Инкремент индекса главы.
			CurrentChapterIndex += 1

		# Формирование структуры первой главы.
		FormattedTitle["first_chapter"]["id"] = FormattedTitle["chapters"][0]["id"]
		FormattedTitle["first_chapter"]["tome"] = FormattedTitle["chapters"][0]["tom"]
		FormattedTitle["first_chapter"]["chapter"] = str(FormattedTitle["chapters"][0]["chapter"])

		# Проставление ID в жанрах.
		for GenreIndex in range(0, len(FormattedTitle["genres"])):
			if FormattedTitle["genres"][GenreIndex]["id"] == None:
				FormattedTitle["genres"][GenreIndex]["id"] = 0

		# Проставление ID в тегах.
		for GenreIndex in range(0, len(FormattedTitle["tags"])):
			if FormattedTitle["tags"][GenreIndex]["id"] == None:
				FormattedTitle["tags"][GenreIndex]["id"] = 0

		return FormattedTitle

	# Конвертер: DMP-V1 > RN-V1.
	def __DMP1_to_RN1(self):
		# Перечисление типов тайтла.
		Types = ["Манга", "Манхва", "Маньхуа", "Западный комикс", "Рукомикс", "Индонезийский комикс", "Другое", "Другое"]
		# Перечисление типов тайтла DMP-V1.
		DMP1_Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "OEL", "ANOTHER"]
		# Перечисление статусов.
		RN1_Statuses = ["Закончен", "Продолжается", "Заморожен", "Нет переводчика", "Анонс", "Лицензировано"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

		#---> Генерация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "rn-v1"
		FormattedTitle["site"] = self.__OriginalTitle["site"]
		FormattedTitle["id"] = self.__OriginalTitle["id"]
		FormattedTitle["img"] = dict()
		FormattedTitle["en_name"] = self.__OriginalTitle["en-name"]
		FormattedTitle["rus_name"] = self.__OriginalTitle["ru-name"]
		FormattedTitle["another_name"] = " / ".join(self.__OriginalTitle["another-names"])
		FormattedTitle["dir"] = self.__OriginalTitle["slug"]
		FormattedTitle["description"] = self.__OriginalTitle["description"]
		FormattedTitle["issue_year"] = self.__OriginalTitle["publication-year"]
		FormattedTitle["avg_rating"] = None
		FormattedTitle["admin_rating"] = None
		FormattedTitle["count_rating"] = None
		FormattedTitle["age_limit"] = self.__OriginalTitle["age-rating"]
		FormattedTitle["status"] = dict()
		FormattedTitle["status"]["id"] = None
		FormattedTitle["status"]["name"] = None
		FormattedTitle["count_bookmarks"] = 0
		FormattedTitle["total_votes"] = 0
		FormattedTitle["total_views"] = 0
		FormattedTitle["type"] = dict()
		FormattedTitle["type"]["id"] = DMP1_Types.index(self.__OriginalTitle["type"])
		FormattedTitle["type"]["name"] = Types[DMP1_Types.index(self.__OriginalTitle["type"])]
		FormattedTitle["genres"] = list()
		FormattedTitle["categories"] = list()
		FormattedTitle["bookmark_type"] = None
		FormattedTitle["branches"] = list()
		FormattedTitle["count_chapters"] = 0
		FormattedTitle["first_chapter"] = dict()
		FormattedTitle["first_chapter"]["id"] = 0
		FormattedTitle["first_chapter"]["tome"] = 0
		FormattedTitle["first_chapter"]["chapter"] = str()
		FormattedTitle["continue_reading"] = None
		FormattedTitle["is_licensed"] = self.__OriginalTitle["is-licensed"]
		FormattedTitle["newlate_id"] = None
		FormattedTitle["newlate_title"] = None
		FormattedTitle["related"] = None
		FormattedTitle["uploaded"] = 0
		FormattedTitle["can_post_comments"] = True
		FormattedTitle["adaptation"] = None
		FormattedTitle["publishers"] = list()
		FormattedTitle["is_yaoi"] = False
		FormattedTitle["is_erotic"] = False
		FormattedTitle["chapters"] = dict()

		#---> Внесение правок.
		#==========================================================================================#

		# Переконвертирование обложек.
		for CoverIndex in range(0, len(self.__OriginalTitle["covers"])):
			# Ключи обложек.
			ImgKeys = ["high", "mid", "low"]

			# Поместить до трёх обложек в новый контейнер.
			if CoverIndex < 3:
				FormattedTitle["img"][ImgKeys[CoverIndex]] = self.__OriginalTitle["covers"][CoverIndex]["link"].replace("https://remanga.org", "")

		# Формирование структуры статуса.
		if self.__OriginalTitle["status"] == "ONGOING":
			FormattedTitle["status"]["id"] = 1
			FormattedTitle["status"]["name"] = RN1_Statuses[1]
		elif self.__OriginalTitle["status"] == "ABANDONED":
			FormattedTitle["status"]["id"] = 2
			FormattedTitle["status"]["name"] = RN1_Statuses[2]
		elif self.__OriginalTitle["status"] == "COMPLETED":
			FormattedTitle["status"]["id"] = 0
			FormattedTitle["status"]["name"] = RN1_Statuses[0]
		else:
			FormattedTitle["status"]["id"] = 6
			FormattedTitle["status"]["name"] = "Неизвестный статус"

		# Конвертирование ветвей и подсчёт количества глав.
		for Branch in self.__OriginalTitle["branches"]:
			BuferBranch = dict()
			BuferBranch["id"] = Branch["id"]
			BuferBranch["img"] = str()
			BuferBranch["subscribed"] = False
			BuferBranch["total_votes"] = 0
			BuferBranch["count_chapters"] = Branch["chapters-count"]
			BuferBranch["publishers"] = list()
			FormattedTitle["branches"].append(BuferBranch)
			FormattedTitle["count_chapters"] += Branch["chapters-count"]

		# Формирование структуры первой главы.
		BranchList = list(self.__OriginalTitle["chapters"].keys())
		if len(BranchList) > 0 and len(self.__OriginalTitle["chapters"][BranchList[0]]) > 0:
			FormattedTitle["first_chapter"]["id"] = self.__OriginalTitle["chapters"][BranchList[0]][0]["id"]
			FormattedTitle["first_chapter"]["tome"] = self.__OriginalTitle["chapters"][BranchList[0]][0]["volume"]
			FormattedTitle["first_chapter"]["chapter"] = str(self.__OriginalTitle["chapters"][BranchList[0]][0]["number"])

		# Определение значений полей is_yaoi и is_erotic.
		if "Яой" in self.__OriginalTitle["genres"]:
			FormattedTitle["is_yaoi"] = True
		if "Эротика" in self.__OriginalTitle["genres"]:
			FormattedTitle["is_erotic"] = True

		# Форматирование ветвей.
		for BranchID in BranchList:
			# Создание списка для глав.
			FormattedTitle["chapters"][BranchID] = list()

			# Форматирование отдельных глав.
			for ChapterIndex in range(0, len(self.__OriginalTitle["chapters"][BranchID])):

				BuferChapter = dict()
				BuferChapter["id"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["id"]
				BuferChapter["rated"] = None
				BuferChapter["viewed"] = None
				BuferChapter["is_bought"] = None
				BuferChapter["publishers"] = list()
				BuferChapter["index"] = ChapterIndex + 1
				BuferChapter["tome"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["volume"]
				BuferChapter["chapter"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["number"]
				BuferChapter["name"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["name"]
				BuferChapter["price"] = None
				BuferChapter["score"] = 0
				BuferChapter["upload_date"] = str()
				BuferChapter["pub_date"] = None
				BuferChapter["is_paid"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["is-paid"]
				BuferChapter["slides"] = list()

				# Переформатирование переводчиков.
				if self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["translator"] is not None:
					BuferPublisher = dict()
					BuferPublisher["name"] = self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["translator"]
					BuferPublisher["dir"] = str()
					BuferPublisher["type"] = 1
					BuferChapter["publishers"].append(BuferPublisher)

				# Переформатирование слайдов.
				for Slide in self.__OriginalTitle["chapters"][BranchID][ChapterIndex]["slides"]:
					BuferSlide = dict()
					BuferSlide["id"] = 0
					BuferSlide["link"] = Slide["link"]
					BuferSlide["page"] = Slide["index"] + 1
					BuferSlide["height"] = Slide["height"]
					BuferSlide["width"] = Slide["width"]
					BuferSlide["count_comments"] = 0
					BuferChapter["slides"].append(BuferSlide)

				# Помещение главы в ветвь.
				FormattedTitle["chapters"][BranchID].append(BuferChapter)

		# Конвертирование тегов.
		for TagIndex in range(0, len(self.__OriginalTitle["tags"])):
			FormattedTitle["categories"].append({"id": 0, "name": self.__OriginalTitle["tags"][TagIndex].capitalize()})

		# Конвертирование жанров.
		for GenreIndex in range(0, len(self.__OriginalTitle["genres"])):
			FormattedTitle["genres"].append({"id": 0, "name": self.__OriginalTitle["genres"][GenreIndex].capitalize()})

		return FormattedTitle

	# Конвертер: HTMP-V1 > HTCRN-V1.
	def __HTMP1_to_HTCRN1(self) -> dict:
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

		#---> Модификация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "htmp-v1"
		FormattedTitle["site"] = "remanga.org"
		FormattedTitle = MergeDictionaries(FormattedTitle, self.__OriginalTitle)
		Chapters = FormattedTitle["chapters"]
		FormattedTitle["chapters"] = dict()
		FormattedTitle["chapters"][str(FormattedTitle["branchId"])] = Chapters

		return FormattedTitle

	# Конвертер: RN-V1 > DMP-V1.
	def __RN1_to_DMP1(self) -> dict:
		# Перечисление типов тайтла.
		Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "OEL", "ANOTHER"]
		# Перечисление статусов.
		Statuses = ["ANNOUNCED", "ONGOING", "ABANDONED", "COMPLETED", "ANOTHER"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

		#---> Вложенные функции.
		#==========================================================================================#

		# Определяет тип тайтла.
		def IdentifyTitleType(TypeDetermination) -> str:
			# Тип тайтла.
			Type = None

			# Перебор типов тайтла.
			if type(TypeDetermination) is dict and "name" in TypeDetermination.keys():
				if TypeDetermination["name"] in ["Манга"]:
					Type = "MANGA"
				elif TypeDetermination["name"] in ["Манхва"]:
					Type = "MANHWA"
				elif TypeDetermination["name"] in ["Маньхуа"]:
					Type = "MANHUA"
				elif TypeDetermination["name"] in ["Западный комикс"]:
					Type = "WESTERN_COMIC"
				elif TypeDetermination["name"] in ["Рукомикс", "Руманга"]:
					Type = "RUS_COMIC"
				elif TypeDetermination["name"] in ["Индонезийский комикс"]:
					Type = "INDONESIAN_COMIC"
				elif TypeDetermination["name"] in ["OEL-манга"]:
					Type = "OEL"
				else:
					Type = "ANOTHER"

			else:
				pass

			return Type

		# Определяет статус тайтла.
		def IdentifyTitleStatus(TitleStatusDetermination) -> str:
			# Тип тайтла.
			Status = None

			# Перебор типов тайтла.
			if type(TitleStatusDetermination) is dict and "name" in TitleStatusDetermination.keys():
				if TitleStatusDetermination["name"] in ["Анонс"]:
					Status = "ANNOUNCED"
				elif TitleStatusDetermination["name"] in ["Продолжается"]:
					Status = "ONGOING"
				elif TitleStatusDetermination["name"] in ["Закончен"]:
					Status = "COMPLETED"
				elif TitleStatusDetermination["name"] in ["Заморожен", "Нет переводчика", "Лицензировано"]:
					Status = "ABANDONED"
				else:
					Status = "ANOTHER"

			else:
				pass

			return Status
		
		#---> Генерация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "dmp-v1"
		FormattedTitle["site"] = "remanga.org"
		FormattedTitle["id"] = self.__OriginalTitle["id"]
		FormattedTitle["slug"] = self.__OriginalTitle["dir"]
		FormattedTitle["covers"] = list()
		FormattedTitle["covers"].append({"link": "https://remanga.org" + self.__OriginalTitle["img"]["high"], "filename": self.__OriginalTitle["img"]["high"].split('/')[-1], "width": None, "height": None})
		FormattedTitle["covers"].append({"link": "https://remanga.org" + self.__OriginalTitle["img"]["mid"], "filename": self.__OriginalTitle["img"]["mid"].split('/')[-1], "width": None, "height": None})
		FormattedTitle["covers"].append({"link": "https://remanga.org" + self.__OriginalTitle["img"]["low"], "filename": self.__OriginalTitle["img"]["low"].split('/')[-1], "width": None, "height": None})
		FormattedTitle["ru-name"] = self.__OriginalTitle["rus_name"]
		FormattedTitle["en-name"] = self.__OriginalTitle["en_name"]
		FormattedTitle["another-names"] = self.__OriginalTitle["another_name"].split(" / ")
		FormattedTitle["type"] = IdentifyTitleType(self.__OriginalTitle["type"])
		FormattedTitle["age-rating"] = self.__OriginalTitle["age_limit"]
		FormattedTitle["publication-year"] = self.__OriginalTitle["issue_year"]
		FormattedTitle["status"] = IdentifyTitleStatus(self.__OriginalTitle["status"])
		FormattedTitle["description"] = RemoveHTML(self.__OriginalTitle["description"]).replace("\r\n\r\n", "\n")
		FormattedTitle["is-licensed"] = self.__OriginalTitle["is_licensed"]
		FormattedTitle["genres"] = list()
		FormattedTitle["tags"] = list()
		FormattedTitle["branches"] = list()
		FormattedTitle["chapters"] = dict()

		#---> Внесение правок.
		#==========================================================================================#

		# Конвертирование ветвей.
		for OriginalBranch in self.__OriginalTitle["branches"]:
			# Буфер текущей ветви.
			CurrentBranch = dict()
			# Перенос данных.
			CurrentBranch["id"] = OriginalBranch["id"]
			CurrentBranch["chapters-count"] = OriginalBranch["count_chapters"]
			# Сохранение результата.
			FormattedTitle["branches"].append(CurrentBranch)

		# Конвертирование глав.
		for CurrentBranchID in self.__OriginalTitle["chapters"].keys():
			# Буфер текущей ветви.
			CurrentBranch = list()

			# Конвертирование глав.
			for Chapter in self.__OriginalTitle["chapters"][CurrentBranchID]:
				# Буфер текущей главы.
				CurrentChapter = dict()
				# Счётчик слайдов.
				SlideIndex = 0
				# Перенос данных.
				CurrentChapter["id"] = Chapter["id"]
				CurrentChapter["number"] = None
				CurrentChapter["volume"] = Chapter["tome"]
				CurrentChapter["name"] = Chapter["name"]
				CurrentChapter["is-paid"] = Chapter["is_paid"]
				CurrentChapter["translator"] = ""
				CurrentChapter["slides"] = list()

				# Если у главы нет названия, то обнулить его.
				if CurrentChapter["name"] == "":
					CurrentChapter["name"] = None

				# Перенос номера главы c конвертированием.
				if '.' in Chapter["chapter"]:
					CurrentChapter["number"] = float(re.search(r"\d+(\.\d+)?", str(Chapter["chapter"])).group(0))
				else:
					CurrentChapter["number"] = int(re.search(r"\d+(\.\d+)?", str(Chapter["chapter"])).group(0))

				# Перенос переводчиков.
				for Publisher in Chapter["publishers"]:
					CurrentChapter["translator"] += Publisher["name"] + " / "

				# Перенос слайдов.
				for Slide in Chapter["slides"]:
					# Инкремент индекса слайда.
					SlideIndex += 1
					# Буфер текущего слайда.
					CurrentSlide = dict()
					# Перенос данных.
					CurrentSlide["index"] = SlideIndex
					CurrentSlide["link"] = Slide["link"]
					CurrentSlide["width"] = Slide["width"]
					CurrentSlide["height"] = Slide["height"]
					# Сохранение результата.
					CurrentChapter["slides"].append(CurrentSlide)

				# Удаление запятой из конца поля переводчика или обнуление поля.
				if CurrentChapter["translator"] != "":
					CurrentChapter["translator"] = CurrentChapter["translator"][:-3]
				else:
					CurrentChapter["translator"] = None

				# Сохранение результата.
				CurrentBranch.append(CurrentChapter)

			# Сохранение результата.
			FormattedTitle["chapters"][CurrentBranchID] = CurrentBranch

		# Вычисление размера локальных обложек.
		for CoverIndex in range(0, len(FormattedTitle["covers"])):
			# Буфер изображения.
			CoverImage = None

			try:

				# Поиск локальных файлов обложек c ID в названии.
				if self.__Settings["use-id-instead-slug"] is True and os.path.exists(self.__Settings["covers-directory"] + str(FormattedTitle["id"]) + "/" + FormattedTitle["covers"][CoverIndex]["filename"]):
					CoverImage = Image.open(self.__Settings["covers-directory"] + str(FormattedTitle["id"]) + "/" + FormattedTitle["covers"][CoverIndex]["filename"])

				# Поиск локальных файлов обложек c алиасом в названии.
				elif self.__Settings["use-id-instead-slug"] is False and os.path.exists(self.__Settings["covers-directory"] + FormattedTitle["slug"] + "/" + FormattedTitle["covers"][CoverIndex]["filename"]):
					CoverImage = Image.open(self.__Settings["covers-directory"] + FormattedTitle["slug"] + "/" + FormattedTitle["covers"][CoverIndex]["filename"])

			except UnidentifiedImageError:
				# Запись в лог ошибки: неизвестная ошибка при чтении изображения.
				logging.error("Resolution of the cover couldn't be determined.")

			# Получение размеров.
			if CoverImage is not None:
				FormattedTitle["covers"][CoverIndex]["width"], FormattedTitle["covers"][CoverIndex]["height"] = CoverImage.size

		# Конвертирование тегов.
		for TagIndex in range(0, len(self.__OriginalTitle["categories"])):
			FormattedTitle["tags"].append(self.__OriginalTitle["categories"][TagIndex]["name"].lower())

		# Конвертирование жанров.
		for GenreIndex in range(0, len(self.__OriginalTitle["genres"])):
			FormattedTitle["genres"].append(self.__OriginalTitle["genres"][GenreIndex]["name"].lower())

		# Сортировка глав по возрастанию.
		for BranchID in FormattedTitle["chapters"].keys():
			FormattedTitle["chapters"][BranchID] = sorted(FormattedTitle["chapters"][BranchID], key = lambda d: d["id"]) 

		return FormattedTitle

	# Конвертер: RN-V1 > HTMP-V1.
	def __RN1_to_HTMP1(self) -> dict:
		# Перечисление типов тайтла.
		Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "ANOTHER"]
		# Перечисление статусов тайтла.
		Statuses = ["COMPLETED", "ACTIVE", "ABANDONED", "NOT_FOUND", "", "LICENSED"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

		# Перечисление жанров, обозначающих однополые отношения.
		HomoGenres = [
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

		#---> Модификация структуры.
		#==========================================================================================#
		FormattedTitle["format"] = "htmp-v1"
		FormattedTitle["site"] = "remanga.org"
		FormattedTitle = MergeDictionaries(FormattedTitle, self.__OriginalTitle)
		FormattedTitle = RenameDictKey(FormattedTitle, "rus_name", "rusTitle")
		FormattedTitle = RenameDictKey(FormattedTitle, "en_name", "engTitle")
		FormattedTitle = RenameDictKey(FormattedTitle, "another_name", "alternativeTitle")
		FormattedTitle = RenameDictKey(FormattedTitle, "description", "desc")
		FormattedTitle = RenameDictKey(FormattedTitle, "dir", "slug")
		FormattedTitle = RenameDictKey(FormattedTitle, "categories", "tags")
		FormattedTitle = RenameDictKey(FormattedTitle, "is_yaoi", "isYaoi")
		FormattedTitle = RenameDictKey(FormattedTitle, "is_erotic", "isHentai")
		FormattedTitle = RenameDictKey(FormattedTitle, "can_post_comments", "isHomo")
		FormattedTitle["status"] = Statuses[FormattedTitle["status"]["id"]]
		FormattedTitle["type"] = Types[FormattedTitle["type"]["id"]]
		FormattedTitle["isHomo"] = False
		FormattedTitle["img"]["high"] = str(FormattedTitle["id"]) + "/" + FormattedTitle["img"]["high"].split('/')[-1]
		FormattedTitle["img"]["mid"] = str(FormattedTitle["id"]) + "/" + FormattedTitle["img"]["high"].split('/')[-1]
		FormattedTitle["img"]["low"] = str(FormattedTitle["id"]) + "/" + FormattedTitle["img"]["high"].split('/')[-1]
		FormattedTitle = RenameDictKey(FormattedTitle, "avg_rating", "branchId")
		FormattedTitle["branchId"] = FormattedTitle["branches"][0]["id"]
		FormattedTitle["chapters"] = FormattedTitle["chapters"][str(FormattedTitle["branches"][0]["id"])]

		#---> Внесение правок.
		#==========================================================================================#

		# Проверка жанров на наличие однополых отношений и выставление параметра isHomo.
		for TitleGenre in FormattedTitle["genres"]:
			for HomoGenre in HomoGenres:
				if HomoGenre == TitleGenre:
					FormattedTitle["isHomo"] = True

		# Переформатирование глав.
		for ChapterIndex in range(0, len(FormattedTitle["chapters"])):
			FormattedTitle["chapters"][ChapterIndex] = RenameDictKey(FormattedTitle["chapters"][ChapterIndex], "tome", "tom")
			FormattedTitle["chapters"][ChapterIndex] = RenameDictKey(FormattedTitle["chapters"][ChapterIndex], "name", "title")
			FormattedTitle["chapters"][ChapterIndex]["chapter"] = float(re.search(r"\d+(\.\d+)?", str(FormattedTitle["chapters"][ChapterIndex]["chapter"])).group(0))

			# Усечение нуля у float.
			if ".0" in str(FormattedTitle["chapters"][ChapterIndex]["chapter"]):
				FormattedTitle["chapters"][ChapterIndex]["chapter"] = int(re.search(r"\d+(\.\d+)?", str(FormattedTitle["chapters"][ChapterIndex]["chapter"]).replace(".0", "")).group(0))

		# Сортировка глав по возрастанию.
		FormattedTitle["chapters"] = sorted(FormattedTitle["chapters"], key = lambda d: d["id"]) 

		return FormattedTitle

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Конструктор: задаёт описательную структуру тайтла.
	def __init__(self, Settings: dict, Title: dict, Format: str = None):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Список известных форматов.
		self.__FormatsList = ["dmp-v1", "hcmp-v1", "htcrn-v1", "htmp-v1", "rn-v1"]
		# Формат оригинальной структуры тайтла.
		self.__OriginalFormat = None
		# Оригинальная структура тайтла.
		self.__OriginalTitle = Title
		# Глобальные настройки.
		self.__Settings = Settings.copy()

		# Определение формата оригинальной структуры.
		if Format is None and "format" in Title.keys() and Title["format"] in self.__FormatsList:
			self.__OriginalFormat = Title["format"]
		elif Format is not None and Format in self.__FormatsList:
			self.__OriginalFormat = Format
		else:
			raise UnknownFormat(Format)

	# Конвертирует оригинальную структуру тайтла в заданный формат.
	def convert(self, Format: str | None) -> dict:
		# Буфер возвращаемой структуры.
		FormattedTitle = None

		# Проверка поддержки формата.
		if Format not in self.__FormatsList:
			raise UnknownFormat(Format)

		# Поиск необходимого конвертера.
		else:

			# Конвертирование: HCMP-V1.
			if self.__OriginalFormat == "hcmp-v1":

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "dmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Не конвертировать исходный формат.
				if Format == "hcmp-v1":
					FormattedTitle = self.__OriginalTitle

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "rn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

			# Конвертирование: HTCRN-V1.
			if self.__OriginalFormat == "htcrn-v1":

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "dmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "hcmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Не конвертировать исходный формат.
				if Format == "htcrn-v1":
					FormattedTitle = self.__OriginalTitle

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "rn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

			# Конвертирование: HTMP-V1.
			if self.__OriginalFormat == "htmp-v1":

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "dmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "hcmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					FormattedTitle = self.__HTMP1_to_HTCRN1()

				# Не конвертировать исходный формат.
				if Format == "htmp-v1":
					FormattedTitle = self.__OriginalTitle

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "rn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

			# Конвертирование: DMP-V1.
			if self.__OriginalFormat == "dmp-v1":

				# Не конвертировать исходный формат.
				if Format == "dmp-v1":
					FormattedTitle = self.__OriginalTitle

				# Запуск конвертера: DMP-V1 > HCMP-V1.
				if Format == "hcmp-v1":
					FormattedTitle = self.__DMP1_to_HCMP1()

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Запуск конвертера: DMP-V1 > HTMP-V1.
				if Format == "htmp-v1":
					FormattedTitle = self.__DMP1_to_HTMP1()
					
				# Выброс исключения: не существует подходящего конвертера.
				if Format == "rn-v1":
					FormattedTitle = self.__DMP1_to_RN1()

			# Конвертирование: RN-V1.
			if self.__OriginalFormat == "rn-v1":

				# Запуск конвертера: RN-V1 > DMP-V1.
				if Format == "dmp-v1":
					FormattedTitle = self.__RN1_to_DMP1()

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "hcmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Запуск конвертера: RN-V1 > HTMP-V1.
				if Format == "htmp-v1":
					FormattedTitle = self.__RN1_to_HTMP1()

				# Не конвертировать исходный формат.
				if Format == "rn-v1":
					FormattedTitle = self.__OriginalTitle

		return FormattedTitle

	# Возвращает автоматически определённый формат.
	def getFormat(self) -> str:
		return self.__OriginalFormat;