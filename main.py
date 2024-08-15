from Source.Core.Formats.Manga import BaseStructs, Manga, Statuses, Types
from Source.Core.ParserSettings import ParserSettings
from Source.Core.Downloader import Downloader
from Source.Core.Objects import Objects
from Source.Core.Exceptions import *
from Source.CLI.Templates import *

from dublib.WebRequestor import Protocols, WebConfig, WebLibs, WebRequestor
from dublib.Methods.Data import RemoveRecurringSubstrings, Zerotify
from skimage.metrics import structural_similarity
from dublib.Polyglot import HTML
from skimage import io
from time import sleep

import cv2
import os

#==========================================================================================#
# >>>>> ОПРЕДЕЛЕНИЯ <<<<< #
#==========================================================================================#

VERSION = "2.0.0"
NAME = "remanga"
SITE = "remanga.org"
STRUCT = Manga()

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Parser:
	"""Модульный парсер."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def site(self) -> str:
		"""Домен целевого сайта."""

		return self.__Title["site"]

	@property
	def id(self) -> int:
		"""Целочисленный идентификатор."""

		return self.__Title["id"]

	@property
	def slug(self) -> str:
		"""Алиас."""

		return self.__Title["slug"]

	@property
	def content_language(self) -> str | None:
		"""Код языка контента по стандарту ISO 639-3."""

		return self.__Title["content_language"]

	@property
	def localized_name(self) -> str | None:
		"""Локализованное название."""

		return self.__Title["localized_name"]

	@property
	def en_name(self) -> str | None:
		"""Название на английском."""

		return self.__Title["en_name"]

	@property
	def another_names(self) -> list[str]:
		"""Список альтернативных названий."""

		return self.__Title["another_names"]

	@property
	def covers(self) -> list[dict]:
		"""Список описаний обложки."""

		return self.__Title["covers"]

	@property
	def authors(self) -> list[str]:
		"""Список авторов."""

		return self.__Title["authors"]

	@property
	def publication_year(self) -> int | None:
		"""Год публикации."""

		return self.__Title["publication_year"]

	@property
	def description(self) -> str | None:
		"""Описание."""

		return self.__Title["description"]

	@property
	def age_limit(self) -> int | None:
		"""Возрастное ограничение."""

		return self.__Title["age_limit"]

	@property
	def genres(self) -> list[str]:
		"""Список жанров."""

		return self.__Title["genres"]

	@property
	def tags(self) -> list[str]:
		"""Список тегов."""

		return self.__Title["tags"]

	@property
	def franchises(self) -> list[str]:
		"""Список франшиз."""

		return self.__Title["franchises"]

	@property
	def type(self) -> Types | None:
		"""Тип тайтла."""

		return self.__Title["type"]

	@property
	def status(self) -> Statuses | None:
		"""Статус тайтла."""

		return self.__Title["status"]

	@property
	def is_licensed(self) -> bool | None:
		"""Состояние: лицензирован ли тайтл на данном ресурсе."""

		return self.__Title["is_licensed"]

	@property
	def content(self) -> dict:
		"""Содержимое тайтла."""

		return self.__Title["content"]

	#==========================================================================================#
	# >>>>> СТАНДАРТНЫЕ ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CalculateEmptyChapters(self, content: dict) -> int:
		"""Подсчитывает количество глав без слайдов."""

		ChaptersCount = 0

		for BranchID in content.keys():

			for Chapter in content[BranchID]:
				if not Chapter["slides"]: ChaptersCount += 1

		return ChaptersCount

	def __InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self.__Settings.common.retries)
		Config.add_header("Authorization", self.__Settings.custom["token"])
		WebRequestorObject = WebRequestor(Config)

		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTPS,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		return WebRequestorObject
	
	def __InitializeCoversRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов обложек."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self.__Settings.common.retries)
		Config.requests.enable_proxy_protocol_switching(True)
		Config.add_header("Referer", f"https://{SITE}/")
		WebRequestorObject = WebRequestor(Config)

		if self.__Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTP,
			host = self.__Settings.proxy.host,
			port = self.__Settings.proxy.port,
			login = self.__Settings.proxy.login,
			password = self.__Settings.proxy.password
		)

		return WebRequestorObject

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __CheckForStubs(self, url: str) -> bool:
		"""
		Проверяет, является ли обложка заглушкой.
			url – ссылка на обложку.
		"""

		FiltersDirectories = os.listdir(f"Parsers/{NAME}/Filters")

		for FilterIndex in FiltersDirectories:
			Patterns = os.listdir(f"Parsers/{NAME}/Filters/{FilterIndex}")
			
			for Pattern in Patterns:
				Result = self.__CompareImages(f"Parsers/{NAME}/Filters/{FilterIndex}/{Pattern}")
				if Result != None and Result < 50.0: return True
		
		return False

	def __Collect(self, filters: str | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список тайтлов по заданным параметрам.
			filters – строка из URI каталога, описывающая параметры запроса;\n
			pages – количество запрашиваемых страниц.
		"""

		Slugs = list()
		IsCollected = False
		Page = 1
		
		while not IsCollected:
			Response = self.__Requestor.get(f"https://remanga.org/api/search/catalog/?page={Page}&count=30&ordering=-id&{filters}")
			
			if Response.status_code == 200:
				PrintCollectingStatus(Page)
				PageContent = Response.json["content"]
				for Note in PageContent: Slugs.append(Note["dir"])
				if not PageContent or pages and Page == pages: IsCollected = True
				if IsCollected: self.__SystemObjects.logger.titles_collected(len(Slugs))
				Page += 1
				sleep(self.__Settings.common.delay)

			else:
				self.__SystemObjects.logger.request_error(Response, "Unable to request catalog.")
				raise Exception("Unable to request catalog.")

		return Slugs
	
	def __CollectUpdates(self, period: int | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список обновлений тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			pages – количество запрашиваемых страниц.
		"""

		Slugs = list()
		period *= 3600000
		IsCollected = False
		Page = 1
		
		while not IsCollected:
			Response = self.__Requestor.get(f"https://remanga.org/api/titles/last-chapters/?page={Page}&count=30")
			
			if Response.status_code == 200:
				PrintCollectingStatus(Page)
				PageContent = Response.json["content"]

				for Note in PageContent:

					if not period or Note["upload_date"] <= period:
						Slugs.append(Note["dir"])

					else:
						IsCollected = True
						break
					
				if not PageContent or pages and Page == pages: IsCollected = True
				if IsCollected: self.__SystemObjects.logger.titles_collected(len(Slugs))
				Page += 1
				sleep(self.__Settings.common.delay)

			else:
				self.__SystemObjects.logger.request_error(Response, "Unable to request catalog.")
				raise Exception("Unable to request catalog.")

		return Slugs

	def __CompareImages(self, pattern_path: str) -> float | None:
		"""
		Сравнивает изображение с фильтром.
			url – ссылка на обложку;\n
			pattern_path – путь к шаблону.
		"""

		Differences = None

		try:
			Temp = self.__SystemObjects.temper.get_parser_temp(NAME)
			Pattern = io.imread(f"{Temp}cover")
			Image = cv2.imread(pattern_path)
			Pattern = cv2.cvtColor(Pattern, cv2.COLOR_BGR2GRAY)
			Image = cv2.cvtColor(Image, cv2.COLOR_BGR2GRAY)
			PatternHeight, PatternWidth = Pattern.shape
			ImageHeight, ImageWidth = Image.shape
		
			if PatternHeight == ImageHeight and PatternWidth == ImageWidth:
				(Similarity, Differences) = structural_similarity(Pattern, Image, full = True)
				Differences = 100.0 - (float(Similarity) * 100.0)

		except Exception as ExceptionData:
			self.__SystemObjects.logger.error("Problem occurred during filtering stubs: \"" + str(ExceptionData) + "\".")		
			Differences = None

		return Differences

	def __GetAgeLimit(self, data: dict) -> int:
		"""
		Получает возрастной рейтинг.
			data – словарь данных тайтла.
		"""

		Ratings = {
			0: 0,
			1: 16,
			2: 18
		}
		Rating = Ratings[data["age_limit"]]

		return Rating 

	def __GetContent(self, data: str) -> dict:
		"""Получает содержимое тайтла."""

		Content = dict()

		for Branch in data["branches"]:
			BranchID = Branch["id"]
			ChaptersCount = Branch["count_chapters"]

			for BranchPage in range(0, int(ChaptersCount / 100) + 1):
				Response = self.__Requestor.get(f"https://remanga.org/api/titles/chapters/?branch_id={BranchID}&count=100&ordering=-index&page=" + str(BranchPage + 1) + "&user_data=1")

				if Response.status_code == 200:
					Data = Response.json["content"]
					
					for Chapter in Data:
						if str(BranchID) not in Content.keys(): Content[str(BranchID)] = list()
						Translators = [sub["name"] for sub in Chapter["publishers"]]
						Buffer = {
							"id": Chapter["id"],
							"volume": str(Chapter["tome"]),
							"number": Chapter["chapter"],
							"name": Zerotify(Chapter["name"]),
							"is_paid": Chapter["is_paid"],
							"free-publication-date": None,
							"translators": Translators,
							"slides": []	
						}

						if self.__Settings.custom["add_free_publication_date"]:
							if Buffer["is_paid"]: Buffer["free-publication-date"] = Chapter["pub_date"]

						else:
							del Buffer["free-publication-date"]

						Content[str(BranchID)].append(Buffer)

				else:
					self.__SystemObjects.logger.request_error(Response, "Unable to request chapter.")

		return Content			

	def __GetCovers(self, data: dict) -> list[str]:
		"""Получает список обложек."""

		Covers = list()

		for CoverURI in data["img"].values():

			if CoverURI not in ["/media/None"]:
				Buffer = {
					"link": f"https://{SITE}{CoverURI}",
					"filename": CoverURI.split("/")[-1]
				}

				if self.__Settings.common.sizing_images:
					Buffer["width"] = None
					Buffer["height"] = None

				Covers.append(Buffer)

				if self.__Settings.custom["unstub"]:
					Downloader(self.__SystemObjects, self.__CoversRequestor).image(
						url = Buffer["link"],
						directory = self.__SystemObjects.temper.get_parser_temp(NAME),
						filename = "cover",
						is_full_filename = True,
						referer = SITE
					)
					
					if self.__CheckForStubs(Buffer["link"]):
						Covers = list()
						self.__SystemObjects.logger.covers_unstubbed(self.__Slug, self.__Title["id"])
						break

		return Covers

	def __GetDescription(self, data: dict) -> str | None:
		"""
		Получает описание.
			data – словарь данных тайтла.
		"""

		Description = None
		Description = HTML(data["description"]).plain_text
		Description = Description.replace("\r", "").replace("\xa0", " ").strip()
		Description = RemoveRecurringSubstrings(Description, "\n")
		Description = Zerotify(Description)

		return Description

	def __GetGenres(self, data: dict) -> list[str]:
		"""
		Получает список жанров.
			data – словарь данных тайтла.
		"""

		Genres = list()
		for Genre in data["genres"]: Genres.append(Genre["name"])

		return Genres

	def __GetSlides(self, chapter_id: int) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			chapter_id – идентификатор главы.
		"""

		Slides = list()
		Response = self.__Requestor.get(f"https://remanga.org/api/titles/chapters/{chapter_id}")

		if Response.status_code == 200:
			Data = Response.json["content"]
			Data["pages"] = self.__MergeListOfLists(Data["pages"])

			for SlideIndex in range(len(Data["pages"])):
				Buffer = {
					"index": SlideIndex + 1,
					"link": Data["pages"][SlideIndex]["link"]
				}
				IsFiltered = False
				if self.__Settings.custom["ru_links"]: Buffer["link"] = self.__RusificateLink(Buffer["link"])

				if self.__Settings.common.sizing_images:
					Buffer["width"] = Data["pages"][SlideIndex]["width"]
					Buffer["height"] = Data["pages"][SlideIndex]["height"]

				if self.__Settings.custom["min_height"] and Data["pages"][SlideIndex]["height"] <= self.__Settings.custom["min_height"]: IsFiltered = True
				if not IsFiltered: Slides.append(Buffer)

		elif Response.status_code in [401, 423]:
			self.__SystemObjects.logger.chapter_skipped(self.__Slug, self.__Title["id"], chapter_id, True)

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request chapter content.")

		return Slides

	def __GetStatus(self, data: dict) -> str:
		"""
		Получает статус.
			data – словарь данных тайтла.
		"""

		Status = None
		StatusesDetermination = {
			"Продолжается": Statuses.ongoing,
			"Закончен": Statuses.completed,
			"Анонс": Statuses.announced,
			"Заморожен": Statuses.dropped,
			"Нет переводчика": Statuses.dropped,
			"Не переводится (лицензировано)": Statuses.dropped
		}
		SiteStatusIndex = data["status"]["name"]
		if SiteStatusIndex in StatusesDetermination.keys(): Status = StatusesDetermination[SiteStatusIndex]

		return Status

	def __GetTags(self, data: dict) -> list[str]:
		"""
		Получает список тегов.
			data – словарь данных тайтла.
		"""

		Tags = list()
		for Tag in data["categories"]: Tags.append(Tag["name"])

		return Tags

	def __GetTitleData(self) -> dict | None:
		"""
		Получает данные тайтла.
			slug – алиас.
		"""

		Response = self.__Requestor.get(f"https://remanga.org/api/titles/{self.__Slug}/")

		if Response.status_code == 200:
			Response = Response.json["content"]
			self.__SystemObjects.logger.parsing_start(self.__Slug, Response["id"])

		elif Response.status_code == 404:
			raise TitleNotFound(self.__Slug)

		else:
			self.__SystemObjects.logger.request_error(Response, "Unable to request title data.")
			Response = None

		return Response

	def __GetType(self, data: dict) -> str:
		"""
		Получает тип тайтла.
			data – словарь данных тайтла.
		"""

		Type = None
		TypesDeterminations = {
			"Манга": Types.manga,
			"Манхва": Types.manhwa,
			"Маньхуа": Types.manhua,
			"Рукомикс": Types.russian_comic,
			"Западный комикс": Types.western_comic,
			"Индонезийский комикс": Types.indonesian_comic
		}
		SiteType = data["type"]["name"]
		if SiteType in TypesDeterminations.keys(): Type = TypesDeterminations[SiteType]

		return Type

	def __MergeListOfLists(self, list_of_lists: list) -> list:
		"""
		Объединяет список списков в один список.
			list_of_lists – список списоков.
		"""
		
		if len(list_of_lists) > 0 and type(list_of_lists[0]) is list:
			Result = list()
			for List in list_of_lists: Result.extend(List)

			return Result

		else: return list_of_lists

	def __RusificateLink(self, link: str) -> str:
		"""
		Задаёт домен российского сервера для ссылки на слайд.
			link – ссылка на слайд.
		"""

		if link.startswith("https://img5.reimg.org"): link = link.replace("https://img5.reimg.org", "https://reimg2.org")
		link = link.replace("reimg.org", "reimg2.org")

		return link

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, system_objects: Objects, settings: ParserSettings):
		"""
		Модульный парсер.
			system_objects – коллекция системных объектов;\n
			settings – настройки парсера.
		"""

		system_objects.logger.select_parser(NAME)

		#---> Генерация динамических свойств.
		#==========================================================================================#
		self.__Settings = settings
		self.__Requestor = self.__InitializeRequestor()
		self.__CoversRequestor = self.__InitializeCoversRequestor()
		self.__Title = None
		self.__Slug = None
		self.__SystemObjects = system_objects

	def amend(self, content: dict | None = None, message: str = "") -> dict:
		"""
		Дополняет каждую главу в кажой ветви информацией о содержимом.
			content – содержимое тайтла для дополнения;\n
			message – сообщение для портов CLI.
		"""

		if content == None: content = self.content
		ChaptersToAmendCount = self.__CalculateEmptyChapters(content)
		AmendedChaptersCount = 0
		ProgressIndex = 0

		for BranchID in content.keys():
			
			for ChapterIndex in range(0, len(content[BranchID])):
				
				if content[BranchID][ChapterIndex]["slides"] == []:
					ProgressIndex += 1
					Slides = self.__GetSlides(content[BranchID][ChapterIndex]["id"])

					if Slides:
						AmendedChaptersCount += 1
						content[BranchID][ChapterIndex]["slides"] = Slides
						self.__SystemObjects.logger.chapter_amended(self.__Slug, self.__Title["id"], content[BranchID][ChapterIndex]["id"], content[BranchID][ChapterIndex]["is_paid"])

					PrintAmendingProgress(message, ProgressIndex, ChaptersToAmendCount)
					sleep(self.__Settings.common.delay)

		self.__SystemObjects.logger.amending_end(self.__Slug, self.__Title["id"], AmendedChaptersCount)

		return content

	def collect(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			filters – строка из URI каталога, описывающая параметры запроса;\n
			pages – количество запрашиваемых страниц.
		"""

		if filters and not period:
			self.__SystemObjects.logger.collect_filters(filters)

		elif filters and period:
			self.__SystemObjects.logger.collect_filters_ignored()
			self.__SystemObjects.logger.collect_period(period)

		if pages:
			self.__SystemObjects.logger.collect_pages(period)

		Slugs: list[str] = self.__Collect(filters, pages) if not period else self.__CollectUpdates(period, pages)

		return Slugs

	def parse(self, slug: str, message: str | None = None):
		"""
		Получает основные данные тайтла.
			slug – алиас тайтла, использующийся для идентификации оного в адресе;\n
			message – сообщение для портов CLI.
		"""

		message = message or ""
		self.__Title = BaseStructs().manga
		self.__Slug = slug
		PrintParsingStatus(message)
		Data = self.__GetTitleData()
		self.__Title["site"] = SITE
		self.__Title["id"] = Data["id"]
		self.__Title["slug"] = slug
		self.__Title["content_language"] = "rus"
		self.__Title["localized_name"] = Data["main_name"]
		self.__Title["en_name"] = Data["secondary_name"]
		self.__Title["another_names"] = Data["another_name"].split(" / ")
		self.__Title["covers"] = self.__GetCovers(Data)
		self.__Title["authors"] = []
		self.__Title["publication_year"] = Data["issue_year"]
		self.__Title["description"] = self.__GetDescription(Data)
		self.__Title["age_limit"] = self.__GetAgeLimit(Data)
		self.__Title["type"] = self.__GetType(Data)
		self.__Title["status"] = self.__GetStatus(Data)
		self.__Title["is_licensed"] = Data["is_licensed"]
		self.__Title["genres"] = self.__GetGenres(Data)
		self.__Title["tags"] = self.__GetTags(Data)
		self.__Title["franchises"] = []
		self.__Title["content"] = self.__GetContent(Data)

	def repair(self, content: dict, chapter_id: int) -> dict:
		"""
		Заново получает данные слайдов главы главы.
			content – содержимое тайтла;\n
			chapter_id – идентификатор главы.
		"""

		for BranchID in content.keys():
			
			for ChapterIndex in range(len(content[BranchID])):
				
				if content[BranchID][ChapterIndex]["id"] == chapter_id:
					Slides = self.__GetSlides(content[BranchID][ChapterIndex]["id"])
					self.__SystemObjects.logger.chapter_repaired(self.__Slug, self.__Title["id"], chapter_id, content[BranchID][ChapterIndex]["is_paid"])
					content[BranchID][ChapterIndex]["slides"] = Slides

		return content