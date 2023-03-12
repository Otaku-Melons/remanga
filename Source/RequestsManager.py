from selenium.common import exceptions as SeleniumExceptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from Source.Functions import GetRandomUserAgent
from Source.Extension import ProxiesExtension
from selenium import webdriver
from retry import retry

import cloudscraper
import requests
import logging
import base64
import json

class MissingValidProxy(Exception):

	# Сообщение об ошибке.
	__Message = ""

	def __init__(self, Message = "There are no valid proxies in the \"Proxies.json\"."): 
		self.__Message = Message 
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message

class RequestsManager:
	
	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Заголовки запроса.
	__RequestHeaders = None
	# Текущий прокси.
	__CurrentProxy = None
	# Глобальные настройки.
	__Settings = dict()
	# Хранилище прокси.
	__Proxies = dict()
	# Эземпляр браузера, управляемого Selenium.
	__Browser = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Автоматический выбор текущего прокси.
	def __AutoSetCurrentProxy(self):
		
		# Проверка наличия рабочих прокси.
		if self.__Settings["use-proxy"] == True and len(self.__Proxies["proxies"]) > 0:
			self.__CurrentProxy = self.__Proxies["proxies"][0]
		elif self.__Settings["use-proxy"] == True and len(self.__Proxies["proxies"]) == 0:
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
		self.__Proxies["forbidden-proxies"].append(Proxy)
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
		self.__Proxies["invalid-proxies"].append(Proxy)
		# Сохранение новой структуры прокси в файл.
		self.__SaveProxiesJSON()
		# Выбор нового прокси.
		self.__AutoSetCurrentProxy()

	# Строит JavaScript XHR запрос.
	def __BuildXHR(self, URL: str, Headers: dict, ResponseType: str) -> str:
		# Скрипт XHR запроса.
		Script = None

		# Построение запроса для JSON-файла.
		if ResponseType == "application/json":
			Script = "var XHR = new XMLHttpRequest();\n"
			Script += "XHR.open(\"GET\", \"" + URL + "\", false);\n"
			for HeaderName in Headers.keys():
				if HeaderName == "authorization" and Headers[HeaderName] != "":
					Script += "XHR.setRequestHeader(\"" + HeaderName + "\", \"" + Headers[HeaderName] + "\");\n"
				elif HeaderName == "User-Agent" and self.__Settings["selenium-mode"] is True:
					pass
				elif HeaderName == "referer" or HeaderName == "referrerPolicy":
					pass
				else:
					Script += "XHR.setRequestHeader(\"" + HeaderName + "\", \"" + Headers[HeaderName] + "\");\n"
			Script += "XHR.send();\n"
			Script += "return XHR.response"

		# Построение запроса для изображения в формате Base64.
		elif ResponseType == "image/jpeg":
			# Заголовки для встраивания в XHR запрос.
			HeadersInXHR = ""

			# Заполнение заголовков XHR.
			for HeaderName in Headers.keys():
				if HeaderName == "authorization" and Headers[HeaderName] != "":
					HeadersInXHR += "XHR.setRequestHeader(\"" + HeaderName + "\", \"" + Headers[HeaderName] + "\");\n"
				elif HeaderName == "User-Agent" and self.__Settings["selenium-mode"] is True:
					pass
				elif HeaderName == "referer" or HeaderName == "referrerPolicy":
					pass
				else:
					HeadersInXHR += "XHR.setRequestHeader(\"" + HeaderName + "\", \"" + Headers[HeaderName] + "\");\n"

			# Формирование скрипта методом форматированной строки.
			Script = f'''
				var Done = arguments[0];
				function toDataURL(url, callback) {{
					var XHR = new XMLHttpRequest();
					XHR.onload = function() {{
						var Reader = new FileReader();
						Reader.onloadend = function() {{
							callback(Reader.result);
						}}
						Reader.readAsDataURL(XHR.response);
					}};
					XHR.open("GET", url);
					{HeadersInXHR}
					XHR.responseType = "blob";
					XHR.send();
				}}

				toDataURL("{URL}", function(dataUrl) {{ Done(dataUrl); }})
			'''

		return Script

	# Форматирует прокси в формат дополнения..
	def __ProxyToExtensionFormat(self, Proxy: dict):
		# Данные прокси.
		UserName = None
		Password = None
		IP = None
		Port = None
		# Строка описания прокси.
		ProxyDescription = Proxy["https"].split('/')[-1]
		
		# Если для прокси нужна авторизация.
		if "@" in ProxyDescription:
			UserName = ProxyDescription.split('@')[0].split(':')[0]
			Password = ProxyDescription.split('@')[0].split(':')[1]
			IP = ProxyDescription.split('@')[1].split(':')[0]
			Port = ProxyDescription.split('@')[1].split(':')[1]

		# Если прокси без авторизации.
		else:
			UserName = ""
			Password = ""
			IP = ProxyDescription.split(':')[0]
			Port = ProxyDescription.split(':')[1]

		return UserName, Password, IP, Port

	# Инициализирует веб-драйвер.
	def __InitializeWebDriver(self):

		# Попытка закрыть браузер.
		try:
			self.__Browser.close()
		except Exception:
			pass

		# Опции веб-драйвера.
		ChromeOptions = webdriver.ChromeOptions()
		
		# При включённом прокси создать и установить дополнение.
		if self.__Settings["use-proxy"] is True:
			UserName, Password, IP, Port = self.__ProxyToExtensionFormat(self.__CurrentProxy)
			ProxiesExtensionObject = ProxiesExtension(UserName, Password, IP, Port)
			ChromeOptions.add_extension(ProxiesExtensionObject)

		# Установка опций.
		ChromeOptions.add_argument("--no-sandbox")
		ChromeOptions.add_argument("--disable-dev-shm-usage")

		# При отключённом режиме отладки скрыть окно браузера.
		if self.__Settings["debug"] is False:
			ChromeOptions.add_argument("--headless=new")

		# Инициализация веб-драйвера.
		self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)

	# Непосредственно выполняет запрос к серверу через библиотеку requests.
	@retry((SeleniumExceptions.JavascriptException, requests.exceptions.HTTPError), delay = 15, tries = 3)
	def __RequestDataWith_requests(self, URL: str, Headers: dict, Proxy: dict):
		# Сессия с обходом Cloudflare.
		Scraper = cloudscraper.create_scraper()
		# Статус ответа.
		StatusCode = None
		# Ответ сервера.
		Response = None

		# Интерпретация прокси.
		if Proxy is None:
			Proxy = dict()

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
			StatusCode = 4

		return Response, StatusCode

	# Непосредственно выполняет запрос к серверу через JavaScript в браузере Google Chrome.
	@retry((requests.exceptions.ProxyError, SeleniumExceptions.WebDriverException), delay = 15, tries = 3)
	def __RequestDataWith_ChromeJavaScript(self, URL: str, Headers: dict, Proxy: dict):
		# Статус ответа.
		StatusCode = None
		# Ответ сервера.
		Response = ResponseEmulation()
		# Скрипт XHR запроса.
		Script = self.__BuildXHR(URL, Headers, Headers["content-type"])

		# Интерпретация прокси.
		if Proxy is None:
			Proxy = dict()

		try:

			# Переход на главную страницу.
			if self.__Browser.current_url != "https://remanga.org/":
				self.__Browser.get("https://remanga.org/")

			# Попытка выполнения запроса изображения.
			if Headers["content-type"] == "image/jpeg":
				Response.text = self.__Browser.execute_async_script(Script)

				# Проверка получения изображения в формате Base64.
				if "base64" in Response.text:
					# Удаление определяющей части blob.
					Response.content = base64.b64decode(Response.text.split(',')[1])
					# Обнуление текста ответа.
					Response.text = None
					# Выставление статуса кода.
					Response.status_code = 200

			# Попытка выполнения запроса JSON.
			else:
				Response.text = self.__Browser.execute_script(Script)
			
			# Обработка пустого запроса.
			if Response.text == "":
				logging.error("Proxy: " + str(Proxy) + ". Forbidden.")
				StatusCode = 3
			elif Response.text != None and dict(json.loads(Response.text))["msg"] == "Для просмотра нужно авторизироваться":
				Response.status_code = 401
			else:
				Response.status_code = 200

		# Обработка ошибки: не удалось выполнить JavaScript или нерабочий прокси.
		except (SeleniumExceptions.JavascriptException, SeleniumExceptions.WebDriverException):

			# Запись в лог описания ошибки.
			if self.__Settings["use-proxy"] is True:
				logging.error("Proxy: " + str(Proxy) + ". Invalid.")
			else:
				logging.error("Unable to request data!")

			Response = None
			StatusCode = 0

		# Обнуление эмулируемого контейнера ответа при ошибке запроса.
		if StatusCode in [0, 3]:
			Response = None

		return Response, StatusCode

	# Сохраняет JSON с прокси.
	def __SaveProxiesJSON(self):
		with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

	# Конструктор: читает список прокси и нициализирует менеджер.
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
			"referer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin",
			"User-Agent": UserAgent
			}

		#---> Загрузка и валидация прокси-серверов.
		#==========================================================================================#
		# Чтение файла определений.
		if Settings["use-proxy"] is True:
			with open("Proxies.json") as FileRead:
				self.__Proxies = json.load(FileRead)

		# Выбор текущего прокси.
		self.__AutoSetCurrentProxy()
		# Инициализация и настройка веб-драйвера.
		if self.__Settings["selenium-mode"]:
			self.__InitializeWebDriver()

	# Закрывает экземпляр браузера.
	def Close(self):
		try:
			self.__Browser.close()
		except Exception:
			pass

	# Возвращает список прокси.
	def GetProxies(self, ProxiesType: str = "all"):
		if ProxiesType == "invalid":
			return self.__Proxies["invalid-proxies"]
		elif ProxiesType == "forbidden":
			return self.__Proxies["forbidden-proxies"]
		elif ProxiesType == "valid":
			return self.__Proxies["proxies"]
		elif ProxiesType == "all":
			return self.__Proxies["proxies"] + self.__Proxies["forbidden-proxies"] + self.__Proxies["invalid-proxies"]

	# Проводит запрос к API Remanga и интерпретирует результаты.
	def Request(self, URL: str, Headers: dict = None):
		# Ответ сервера.
		Response = None
		# Статус ответа.
		Status = None

		# Установка заголовков по умолчанию.
		if Headers is None:
			Headers = self.__RequestHeaders
		
		# Повторять пока не будет получен ответ или не выбросится исключение.
		while Response == None:

			# Выполнение запроса с прокси или без.
			if self.__Settings["selenium-mode"] is True:
				Response, Status = self.__RequestDataWith_ChromeJavaScript(URL, Headers, self.__CurrentProxy)
			else:
				Response, Status = self.__RequestDataWith_requests(URL, Headers, self.__CurrentProxy)

			# Обработка статусов ответа в режиме Selenium.
			if self.__Settings["selenium-mode"] is True:
				if Status == 0:
					self.__BlockProxyAsInvalid(self.__CurrentProxy, Status)
					self.__InitializeWebDriver()

			# Обработка статусов ответа в режиме requests.
			else: 
				if Status == 0 and self.__Settings["use-proxy"] is True:
					self.__BlockProxyAsInvalid(self.__CurrentProxy, Status)
				elif Status == 1:
					pass
				elif Status in [2, 3] and self.__Settings["use-proxy"] is True:
					self.__BlockProxyAsForbidden(self.__CurrentProxy, Status)
				elif Status == 4:
					raise requests.exceptions.HTTPError

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
			StatusCode = 4

		return StatusCode

class ResponseEmulation():

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#
	# Код ответа.
	status_code = 0
	# Бинарный вариант ответа.
	content = None
	# Текст ответа.
	text = ""
	
