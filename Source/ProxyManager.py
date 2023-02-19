from Functions import GetRandomUserAgent
from retry import retry

import cloudscraper
import requests
import logging
import json

class MissingValidProxy(Exception):

	# Сообщение об ошибке.
	__Message = ""

	def __init__(self, Message = "There are no valid proxies in the \"Proxies.json\"."): 
		self.__Message = Message 
		super().__init__(self.message) 
			
	def __str__(self):
		return self.__Message

class ProxyManager:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Глобальные настройки.
	__Settings = dict()
	# Заголовки запроса.
	__RequestHeaders = None
	# Хранилище прокси.
	__Proxies = dict()
	# Текущий прокси.
	__CurrentProxy = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Автоматический выбор текущего прокси.
	def __AutoSetCurrentProxy(self):
		
		# Проверка наличия рабочих прокси.
		if len(self.__Proxies["proxies"]) > 0:
			self.__CurrentProxy = self.__Proxies["proxies"][0]
		else:
			# Лог: отсутствуют валидные прокси.
			logging.error("Valid proxies required!")
			# Выброс исключения.
			raise MissingValidProxy

	# Блокирует прокси как невалидный.
	def __BlockProxyAsInvalid(self, Proxy: dict, Status: int):
		# Удаление прокси из списка валидных серверов.
		self.__Proxies["proxies"].remove(Proxy)
		# Добавление кода ошибки в описание прокси.
		Proxy["last-validation-code"] = Status
		# Помещение прокси в новый список.
		self.__Proxies["forbidden-proxies"] = Proxy
		# Сохранение новой структуры прокси в файл.
		self.__SaveProxiesJSON()
		# Выбор нового прокси.
		self.__AutoSetCurrentProxy()

	# Блокирует прокси как запрещённый.
	def __BlockProxyAsForbidden(self, Proxy: dict, Status: int):
		# Удаление прокси из списка валидных серверов.
		self.__Proxies["proxies"].remove(Proxy)
		# Добавление кода ошибки в описание прокси.
		Proxy["last-validation-code"] = Status
		# Помещение прокси в новый список.
		self.__Proxies["invalid-proxies"] = Proxy
		# Сохранение новой структуры прокси в файл.
		self.__SaveProxiesJSON()
		# Выбор нового прокси.
		self.__AutoSetCurrentProxy()

	# Сохраняет JSON с прокси.
	def __SaveProxiesJSON(self):
		with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

	# Непосредственно выполняет запрос к серверу.
	@retry((requests.exceptions.ProxyError, requests.exceptions.HTTPError), delay = 15, tries = 3)
	def __RequestData(self, URL: str, Headers: dict, Proxy: dict = dict()):
		# Сессия с обходом Cloudflare.
		Scraper = cloudscraper.create_scraper()
		# Статус ответа.
		StatusCode = None
		# Ответ сервера.
		Response = None

		try:
			# Попытка выполнения запроса.
			Response = Scraper.get(URL, headers = Headers, proxies = Proxy)

			# Если запрос отклонён сервером.
			if Response.status_code == 403:
				StatusCode = 2
				logging.error("Proxy: " + str(Proxy) + ". Forbidden.")

			# Если запрос прошёл.
			elif Response.status_code == 200:
				StatusCode = 1

			# Проверка других кодов, при которых необходимо повторить запрос.
			elif Response.status_code in [502]:
				raise requests.exceptions.HTTPError

		# Обработка ошибки: прокси недоступен.
		except requests.exceptions.ProxyError:
			logging.error("Proxy: " + str(Proxy) + ". Invalid.")
			StatusCode = 0

		# Обработка ошибки: запрошена капча Cloudflare V2.
		except cloudscraper.exceptions.CloudflareChallengeError:
			logging.error("Proxy: " + str(Proxy) + ". Forbidden.")
			StatusCode = 3

		# Обработка ошибки: ошибка со стороны сервера.
		except requests.exceptions.HTTPError:
			StatusCode = -1

		return Response, StatusCode

	# Конструктор: читает список прокси-серверов.
	def __init__(self, Settings: dict):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
		self.__RequestHeaders = {
			"authorization": self.__Settings["authorization"],
			"accept": "*/*",
			"accept-language": "ru,en;q=0.9",
			"content-type": "application/json",
			"preference": "0",
			"sec-ch-ua": "\"Not?A_Brand\";v=\"8\", \"Chromium\";v=\"108\", \"Yandex\";v=\"23\"",
			"sec-ch-ua-mobile": "?0",
			"sec-ch-ua-platform": "\"Windows\"",
			"sec-fetch-dest": "empty",
			"sec-fetch-mode": "cors",
			"sec-fetch-site": "same-site",
			"referrer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin",
			"body": None,
			"method": "GET",
			"mode": "cors",
			"credentials": "omit",
			"User-Agent": UserAgent
			}

		#---> Загрузка и валидация прокси-серверов.
		#==========================================================================================#
		# Чтение файла определений.
		with open("Proxies.json") as FileRead:
			self.__Proxies = json.load(FileRead)

	# Возвращает список прокси.
	def GetProxies(self, proxies_type = "all"):
		if proxies_type == "invalid":
			return self.__Proxies["invalid-proxies"]
		elif proxies_type == "forbidden":
			return self.__Proxies["forbidden-proxies"]
		elif proxies_type == "valid":
			return self.__Proxies["proxies"]
		elif proxies_type == "all":
			return self.__Proxies["proxies"] + self.__Proxies["forbidden-proxies"] + self.__Proxies["unvalid-proxies"]

	# Проводит запрос к API Remanga и интерпретирует результаты.
	def Request(self, URL: str, Headers: dict = __RequestHeaders):
		# Ответ сервера.
		Response = None
		# Статус ответа.
		Status = None
		
		# Выполнение запроса с прокси или без.
		if self.__Settings["use-proxy"]:
			Response, Status = self.__RequestData(URL, Headers, self.__CurrentProxy)
		else:
			Response, Status = self.__RequestData(URL, Headers)

		# Обработка статусов ответа.
		if Status == -1:
			raise requests.exceptions.HTTPError
		elif Status == 0:
			self.__BlockProxyAsInvalid(self.__CurrentProxy)
		elif Status == 1:
			pass
		elif Status in [2, 3]:
			self.__BlockProxyAsForbidden(self.__CurrentProxy)

		return Response

	# Проверяет валидность прокси сервера.
	def ValidateProxy(self, ProxyIndex: int, RequestHeaders: dict = __RequestHeaders) -> int:
		# Тестовый URL запроса.
		URL = "https://api.remanga.org/api/titles/last-chapters/?page=1&count=20"
		# Сессия с обходом Cloudflare.
		Scraper = cloudscraper.create_scraper()
		# Возвращает код статуса прокси: 0 – недоступен, 1 – валиден, 2 – заблокирован, 3 – запрошена капча Cloudflare V2. 
		StatusCode = None
		
		try:

			# Попытка выполнения запроса.
			Response = Scraper.get(URL, headers = RequestHeaders, proxies = self.__Proxies["proxies"][ProxyIndex])

			# Если запрос отклонён сервером.
			if Response.status_code == 403:
				StatusCode = 2

			# Если запрос прошёл.
			elif Response.status_code == 200:
				StatusCode = 1

			# Проверка других кодов, при которых необходимо повторить запрос.
			elif Response.status_code in [502]:
				raise requests.exceptions.HTTPError

		# Обработка ошибки: прокси недоступен.
		except requests.exceptions.ProxyError:
			StatusCode = 0

		# Обработка ошибки: запрошена капча Cloudflare V2.
		except cloudscraper.exceptions.CloudflareChallengeError:
			StatusCode = 3

		# Обработка ошибки: ошибка со стороны сервера.
		except requests.exceptions.HTTPError:
			StatusCode = -1

		return StatusCode




