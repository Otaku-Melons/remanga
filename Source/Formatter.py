from Source.DUBLIB import MergeDictionaries
from Source.DUBLIB import RenameDictKey
from PIL import Image

import os
import re

# Исключение: не существует подходящего конвертера для указанных форматов.
class UnableToConvert(Exception):

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Сообщение об ошибке.
	__Message = "There isn't suitable converter for these formats:"

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Конструктор: вызывается при обработке исключения.
	def __init__(self, SourceFormat: str, TargetFormat: str): 
		self.__Message += " \"" + SourceFormat + "\" > \"" + TargetFormat + "\"."
		super().__init__(self.__Message) 
			
	# Информатор: вызывается при выводе исключения в консоль.
	def __str__(self):
		return self.__Message

# Исключение: указан неизвестный формат.
class UnknownFormat(Exception):

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Сообщение об ошибке.
	__Message = "Couldn't recognize source or target format:"

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Конструктор: вызывается при обработке исключения.
	def __init__(self, UnknownFormat: str): 
		self.__Message += " \"" +  UnknownFormat + "\"."
		super().__init__(self.__Message) 
			
	# Информатор: вызывается при выводе исключения в консоль.
	def __str__(self):
		return self.__Message

# Форматировщик структур описательных файлов тайтлов.
class Formatter:

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Список известных форматов.
	__FormatsList = ["dmp-v1", "htcrn-v1", "htmp-v1", "rn-v1"]
	# Формат оригинальной структуры тайтла.
	__OriginalFormat = None
	# Оригинальная структура тайтла.
	__OriginalTitle = None
	# Глобальные настройки.
	__Settings = None

	#==========================================================================================#
	# >>>>> КОНВЕРТЕРЫ <<<<< #
	#==========================================================================================#

	# Конвертер: dmp-v1 > rn-v1.
	def __DMP1_to_RN1(self):
		# Перечисление типов тайтла.
		Types = ["Манга", "Манхва", "Маньхуа", "Западный комикс", "Рукомикс", "Индонезийский комикс", "Другое", "Другое"]
		# Перечисление типов тайтла dmp-v1.
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
		FormattedTitle["another_name"] = self.__OriginalTitle["another-names"]
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
		FormattedTitle["genres"] = self.__OriginalTitle["genres"]
		FormattedTitle["categories"] = self.__OriginalTitle["tags"]
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
		BranchList = list(self.__OriginalTitle["content"].keys())
		if len(BranchList) > 0 and len(self.__OriginalTitle["content"][BranchList[0]]) > 0:
			FormattedTitle["first_chapter"]["id"] = self.__OriginalTitle["content"][BranchList[0]][0]["id"]
			FormattedTitle["first_chapter"]["tome"] = self.__OriginalTitle["content"][BranchList[0]][0]["volume"]
			FormattedTitle["first_chapter"]["chapter"] = str(self.__OriginalTitle["content"][BranchList[0]][0]["number"])

		# Определение значений полей is_yaoi и is_erotic.
		for Genre in self.__OriginalTitle["genres"]:
			if Genre["name"] == "Яой":
				FormattedTitle["is_yaoi"] = True
			if Genre["name"] == "Эротика":
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

		return FormattedTitle

	# Конвертер: htmp-v1 > htcrn-v1.
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

	# Конвертер: rn-v1 > dmp-v1.
	def __RN1_to_DMP1(self) -> dict:
		# Перечисление типов тайтла.
		Types = ["MANGA", "MANHWA", "MANHUA", "WESTERN_COMIC", "RUS_COMIC", "INDONESIAN_COMIC", "OEL", "ANOTHER"]
		# Перечисление статусов.
		Statuses = ["ANNOUNCED", "ONGOING", "ABANDONED", "COMPLETED", "ANOTHER"]
		# Буфер обработки возвращаемой структуры.
		FormattedTitle = dict()

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
		FormattedTitle["another-names"] = self.__OriginalTitle["another_name"]
		FormattedTitle["type"] = self.__IdentifyTitleType(self.__OriginalTitle["type"])
		FormattedTitle["age-rating"] = self.__OriginalTitle["age_limit"]
		FormattedTitle["publication-year"] = self.__OriginalTitle["issue_year"]
		FormattedTitle["status"] = self.__IdentifyTitleStatus(self.__OriginalTitle["status"])
		FormattedTitle["description"] = self.__OriginalTitle["description"]
		FormattedTitle["is-licensed"] = self.__OriginalTitle["is_licensed"]
		FormattedTitle["genres"] = self.__OriginalTitle["genres"]
		FormattedTitle["tags"] = self.__OriginalTitle["categories"]
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

				# Перенос номера главы c конвертированием.
				if '.' in Chapter["chapter"]:
					CurrentChapter["number"] = float(re.search(r"\d+(\.\d+)?", str(Chapter["chapter"])).group(0))
				else:
					CurrentChapter["number"] = int(re.search(r"\d+(\.\d+)?", str(Chapter["chapter"])).group(0))

				# Перенос переводчиков.
				for Publisher in Chapter["publishers"]:
					CurrentChapter["translator"] += Publisher["name"] + ", "

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
					CurrentChapter["translator"] = CurrentChapter["translator"][:-2]
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

			# Поиск локальных файлов обложек c ID в названии.
			if self.__Settings["use-id-instead-slug"] is True and os.path.exists(self.__Settings["covers-directory"] + str(FormattedTitle["id"]) + "/" + FormattedTitle["covers"][CoverIndex]["filename"]):
				CoverImage = Image.open(self.__Settings["covers-directory"] + str(FormattedTitle["id"]) + "/" + FormattedTitle["covers"][CoverIndex]["filename"])

			# Поиск локальных файлов обложек c алиасом в названии.
			elif self.__Settings["use-id-instead-slug"] is False and os.path.exists(self.__Settings["covers-directory"] + FormattedTitle["slug"] + "/" + FormattedTitle["covers"][CoverIndex]["filename"]):
				CoverImage = Image.open(self.__Settings["covers-directory"] + FormattedTitle["slug"] + "/" + FormattedTitle["covers"][CoverIndex]["filename"])

			# Получение размеров.
			if CoverImage is not None:
				FormattedTitle["covers"][CoverIndex]["width"], FormattedTitle["covers"][CoverIndex]["height"] = CoverImage.size

		# Сортировка глав по возрастанию.
		for BranchID in FormattedTitle["chapters"].keys():
			FormattedTitle["chapters"][BranchID] = sorted(FormattedTitle["chapters"][BranchID], key = lambda d: d["id"]) 

		return FormattedTitle

	# Конвертер: rn-v1 > htmp-v1.
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

	# Определяет тип тайтла.
	def __IdentifyTitleType(self, TypeDetermination) -> str:
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
	def __IdentifyTitleStatus(self, TitleStatusDetermination) -> str:
		# Тип тайтла.
		Status = None

		# Перебор типов тайтла.
		if type(TitleStatusDetermination) is dict and "name" in TitleStatusDetermination.keys():
			if TitleStatusDetermination["name"] in ["Анонс"]:
				Status = "ANNOUNCED"
			elif TitleStatusDetermination["name"] in ["Закончен"]:
				Status = "COMPLETED"

		else:
			pass

		return Status

	# Конструктор: задаёт описательную структуру тайтла.
	def __init__(self, Settings: dict, Title: dict, Format: str = None):

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__OriginalTitle = Title

		# Определение формата оригинальной структуры.
		if Format is None and "format" in Title.keys() and Title["format"] in self.__FormatsList:
			self.__OriginalFormat = Title["format"]
		elif Format is not None and Format in self.__FormatsList:
			self.__OriginalFormat = Format
		else:
			raise UnknownFormat(Format)

	# Конвертирует оригинальную структуру тайтла в заданный формат.
	def Convert(self, Format: str) -> dict:
		# Буфер возвращаемой структуры.
		FormattedTitle = None

		# Проверка поддержки формата.
		if Format not in self.__FormatsList:
			raise UnknownFormat(Format)

		# Поиск необходимого конвертера.
		else:

			# Конвертирование: htcrn-v1.
			if self.__OriginalFormat == "htcrn-v1":

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "dmp-v1":
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

			# Конвертирование: htmp-v1.
			if self.__OriginalFormat == "htmp-v1":

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "dmp-v1":
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

			# Конвертирование: dmp-v1.
			if self.__OriginalFormat == "dmp-v1":

				# Не конвертировать исходный формат.
				if Format == "dmp-v1":
					FormattedTitle = self.__OriginalTitle

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htmp-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "rn-v1":
					FormattedTitle = self.__DMP1_to_RN1()

			# Конвертирование: rn-v1.
			if self.__OriginalFormat == "rn-v1":

				# Запуск конвертера: rn-v1 > dmp-v1.
				if Format == "dmp-v1":
					FormattedTitle = self.__RN1_to_DMP1()

				# Выброс исключения: не существует подходящего конвертера.
				if Format == "htcrn-v1":
					raise UnableToConvert(self.__OriginalFormat, Format)

				# Запуск конвертера: rn-v1 > htmp-v1.
				if Format == "htmp-v1":
					FormattedTitle = self.__RN1_to_HTMP1()

				# Не конвертировать исходный формат.
				if Format == "rn-v1":
					FormattedTitle = self.__OriginalTitle

		return FormattedTitle