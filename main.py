from Source.Core.Formats.Manga import Branch, Chapter, Manga, Statuses, Types
from Source.Core.Base.MangaParser import MangaParser
from Source.Core.ImagesDownloader import ImagesDownloader
from Source.Core.Exceptions import TitleNotFound

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
TYPE = Manga

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

class Parser(MangaParser):
	"""Парсер."""

	#==========================================================================================#
	# >>>>> ПЕРЕОПРЕДЕЛЯЕМЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def _InitializeRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self._Settings.common.retries)
		Config.add_header("Authorization", self._Settings.custom["token"])
		Config.add_header("Referer", f"https://{SITE}/")
		WebRequestorObject = WebRequestor(Config)

		if self._Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTPS,
			host = self._Settings.proxy.host,
			port = self._Settings.proxy.port,
			login = self._Settings.proxy.login,
			password = self._Settings.proxy.password
		)

		return WebRequestorObject
	
	def _PostInitMethod(self):
		"""Метод, выполняющийся после инициализации объекта."""
	
		self.__CoversRequestor = self.__InitializeCoversRequestor()

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __InitializeCoversRequestor(self) -> WebRequestor:
		"""Инициализирует модуль WEB-запросов обложек."""

		Config = WebConfig()
		Config.select_lib(WebLibs.requests)
		Config.set_retries_count(self._Settings.common.retries)
		Config.requests.enable_proxy_protocol_switching(True)
		Config.add_header("Referer", f"https://{SITE}/")
		WebRequestorObject = WebRequestor(Config)

		if self._Settings.proxy.enable: WebRequestorObject.add_proxy(
			Protocols.HTTPS,
			host = self._Settings.proxy.host,
			port = self._Settings.proxy.port,
			login = self._Settings.proxy.login,
			password = self._Settings.proxy.password
		)

		return WebRequestorObject

	def __CheckForStubs(self) -> bool:
		"""Проверяет, является ли обложка заглушкой."""

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
			Response = self._Requestor.get(f"https://{SITE}/api/search/catalog/?page={Page}&count=30&ordering=-id&{filters}")
			
			if Response.status_code == 200:
				self._PrintCollectingStatus(Page)
				PageContent = Response.json["content"]
				for Note in PageContent: Slugs.append(Note["dir"])
				if not PageContent or pages and Page == pages: IsCollected = True
				Page += 1
				sleep(self._Settings.common.delay)

			else:
				self._SystemObjects.logger.request_error(Response, "Unable to request catalog.")
				raise Exception("Unable to request catalog.")

		return Slugs
	
	def __CollectUpdates(self, period: int | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список обновлений тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			pages – количество запрашиваемых страниц.
		"""

		Slugs = list()
		period *= 3_600_000
		IsCollected = False
		Page = 1
		
		while not IsCollected:
			Response = self._Requestor.get(f"https://{SITE}/api/titles/last-chapters/?page={Page}&count=30")
			
			if Response.status_code == 200:
				self._PrintCollectingStatus(Page)
				PageContent = Response.json["content"]

				for Note in PageContent:

					if not period or Note["upload_date"] <= period:
						Slugs.append(Note["dir"])

					else:
						Slugs = list(set(Slugs))
						IsCollected = True
						break
					
				if not PageContent or pages and Page == pages: IsCollected = True
				if IsCollected: self._SystemObjects.logger.titles_collected(len(Slugs))
				Page += 1
				sleep(self._Settings.common.delay)

			else:
				self._SystemObjects.logger.request_error(Response, "Unable to request catalog.")
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
			Temp = self._SystemObjects.temper.get_parser_temp(NAME)
			Pattern = io.imread(f"{Temp}/cover")
			Image = cv2.imread(pattern_path)
			Pattern = cv2.cvtColor(Pattern, cv2.COLOR_BGR2GRAY)
			Image = cv2.cvtColor(Image, cv2.COLOR_BGR2GRAY)
			PatternHeight, PatternWidth = Pattern.shape
			ImageHeight, ImageWidth = Image.shape
		
			if PatternHeight == ImageHeight and PatternWidth == ImageWidth:
				(Similarity, Differences) = structural_similarity(Pattern, Image, full = True)
				Differences = 100.0 - (float(Similarity) * 100.0)

		except Exception as ExceptionData:
			self._SystemObjects.logger.error("Problem occurred during filtering stubs: \"" + str(ExceptionData) + "\".")		
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

	def __GetBranches(self, data: str):
		"""Получает ветви тайтла."""

		for CurrentBranchData in data["branches"]:
			BranchID = CurrentBranchData["id"]
			ChaptersCount = CurrentBranchData["count_chapters"]
			CurrentBranch = Branch(BranchID)

			for BranchPage in range(0, int(ChaptersCount / 100) + 1):
				Response = self._Requestor.get(f"https://{SITE}/api/titles/chapters/?branch_id={BranchID}&count=100&ordering=-index&page=" + str(BranchPage + 1) + "&user_data=1")

				if Response.status_code == 200:
					Data = Response.json["content"]
					
					for CurrentChapter in Data:
						Translators = [sub["name"] for sub in CurrentChapter["publishers"]]
						Buffer = {
							"id": CurrentChapter["id"],
							"volume": str(CurrentChapter["tome"]),
							"number": CurrentChapter["chapter"],
							"name": Zerotify(CurrentChapter["name"]),
							"is_paid": CurrentChapter["is_paid"],
							"free-publication-date": None,
							"translators": Translators,
							"slides": []	
						}
						
						if self._Settings.custom["add_free_publication_date"]:
							if Buffer["is_paid"]: Buffer["free-publication-date"] = CurrentChapter["pub_date"]

						else:
							del Buffer["free-publication-date"]

						ChapterObject = Chapter(self._SystemObjects)
						ChapterObject.set_dict(Buffer)
						CurrentBranch.add_chapter(ChapterObject)

				else: self._SystemObjects.logger.request_error(Response, "Unable to request chapter.")

			self._Title.add_branch(CurrentBranch)		

	def __GetCovers(self, data: dict) -> list[str]:
		"""Получает список обложек."""

		Covers = list()

		for CoverURI in data["img"].values():

			if CoverURI not in ["/media/None"]:
				Buffer = {
					"link": f"https://{SITE}{CoverURI}",
					"filename": CoverURI.split("/")[-1]
				}

				if self._Settings.common.sizing_images:
					Buffer["width"] = None
					Buffer["height"] = None

				Covers.append(Buffer)

				if self._Settings.custom["unstub"]:
					ImagesDownloader(self._SystemObjects, self.__CoversRequestor).temp_image(
						url = Buffer["link"],
						filename = "cover"
					)
					
					if self.__CheckForStubs():
						Covers = list()
						self._SystemObjects.logger.covers_unstubbed(self._Title.slug, self._Title.id)
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

	def __GetSlides(self, chapter: Chapter) -> list[dict]:
		"""
		Получает данные о слайдах главы.
			chapter – данные главы.
		"""

		Slides = list()
		Response = self._Requestor.get(f"https://{SITE}/api/titles/chapters/{chapter.id}")

		if Response.status_code == 200:
			Data = Response.json["content"]
			Data["pages"] = self.__MergeListOfLists(Data["pages"])

			for SlideIndex in range(len(Data["pages"])):
				Buffer = {
					"index": SlideIndex + 1,
					"link": Data["pages"][SlideIndex]["link"],
					"width": Data["pages"][SlideIndex]["width"],
					"height": Data["pages"][SlideIndex]["height"]
				}
				IsFiltered = False
				if self._Settings.custom["ru_links"]: Buffer["link"] = self.__RusificateLink(Buffer["link"])
				if not IsFiltered: Slides.append(Buffer)

		elif Response.status_code in [401, 423]:
			self._SystemObjects.logger.chapter_skipped(self._Title, chapter)

		else:
			self._SystemObjects.logger.request_error(Response, "Unable to request chapter content.")

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

	def amend(self, branch: Branch, chapter: Chapter):
		"""
		Дополняет главу дайными о слайдах.
			branch – данные ветви;\n
			chapter – данные главы.
		"""

		Slides = self.__GetSlides(chapter)
		for Slide in Slides: chapter.add_slide(Slide["link"], Slide["width"], Slide["height"])

	def collect(self, period: int | None = None, filters: str | None = None, pages: int | None = None) -> list[str]:
		"""
		Собирает список тайтлов по заданным параметрам.
			period – количество часов до текущего момента, составляющее период получения данных;\n
			filters – строка из URI каталога, описывающая параметры запроса;\n
			pages – количество запрашиваемых страниц.
		"""

		if filters and not period:
			self._SystemObjects.logger.collect_filters(filters)

		elif filters and period:
			self._SystemObjects.logger.collect_filters_ignored()
			self._SystemObjects.logger.collect_period(period)

		if pages:
			self._SystemObjects.logger.collect_pages(pages)

		Slugs: list[str] = self.__Collect(filters, pages) if not period else self.__CollectUpdates(period, pages)

		return Slugs
	
	def parse(self):
		"""Получает основные данные тайтла."""

		Response = self._Requestor.get(f"https://{SITE}/api/titles/{self._Title.slug}/")

		if Response.status_code == 200:
			Data = Response.json["content"]
			
			self._Title.set_site(SITE)
			self._Title.set_id(Data["id"])
			self._SystemObjects.logger.parsing_start(self._Title)
			self._Title.set_content_language("rus")
			self._Title.set_localized_name(Data["main_name"])
			self._Title.set_eng_name(Data["secondary_name"])
			self._Title.set_another_names(Data["another_name"].split(" / "))
			self._Title.set_covers(self.__GetCovers(Data))
			self._Title.set_publication_year(Data["issue_year"])
			self._Title.set_description(self.__GetDescription(Data))
			self._Title.set_age_limit(self.__GetAgeLimit(Data))
			self._Title.set_type(self.__GetType(Data))
			self._Title.set_status(self.__GetStatus(Data))
			self._Title.set_is_licensed(Data["is_licensed"])
			self._Title.set_genres(self.__GetGenres(Data))
			self._Title.set_tags(self.__GetTags(Data))
			
			self.__GetBranches(Data)

		elif Response.status_code == 404: raise TitleNotFound(self._Title)
		else: self._SystemObjects.logger.request_error(Response, "Unable to request title data.")