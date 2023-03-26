from selenium.common import exceptions as SeleniumExceptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from Source.Functions import GetRandomUserAgent
from Source.Extension import ProxiesExtension
from selenium import webdriver

import cloudscraper
import requests
import logging
import base64
import json
import time
import sys

# Исключение: отсутствуют валидные прокси.
class MissingValidProxy(Exception):

	# Сообщение об ошибке.
	__Message = ""

	def __init__(self, Message = "There are no valid proxies in the \"Proxies.json\"."): 
		self.__Message = Message 
		super().__init__(self.__Message) 
			
	def __str__(self):
		return self.__Message

# Эмулятор структуры ответа библиотеки requests.
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

# Менеджер запросов и регулирования работы прокси.
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
	# Состояние: идёт ли верификация.
	__IsProxval = False

	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Автоматический выбор текущего прокси.
	def __AutoSetCurrentProxy(self):
		
		# Проверка наличия рабочих прокси.
		if self.__Settings["use-proxy"] == True and len(self.__Proxies["proxies"]) > 0:
			self.__CurrentProxy = self.__Proxies["proxies"][0]
		elif self.__Settings["use-proxy"] == True and len(self.__Proxies["proxies"]) == 0:
			# Лог: отсутствуют валидные прокси.
			logging.critical("Valid proxies required!")
			# Выброс исключения.
			raise MissingValidProxy

	# Блокирует прокси как невалидный.
	def __BlockProxyAsInvalid(self, Proxy: dict):
		# Удаление прокси из списка валидных серверов.
		self.__Proxies["proxies"].remove(Proxy)
		# Помещение прокси в новый список.
		self.__Proxies["invalid-proxies"].append(Proxy)
		# Сохранение новой структуры прокси в файл.
		self.__SaveProxiesJSON()
		# Запись в лог предупреждения: прокси заблокирован как невалидный.
		logging.warning("Proxy: " + str(Proxy) + ". Blocked as invalid.")
		# Выбор нового прокси.
		self.__AutoSetCurrentProxy()

	# Блокирует прокси как запрещённый.
	def __BlockProxyAsForbidden(self, Proxy: dict):
		# Удаление прокси из списка валидных серверов.
		self.__Proxies["proxies"].remove(Proxy)
		# Помещение прокси в новый список.
		self.__Proxies["forbidden-proxies"].append(Proxy)
		# Сохранение новой структуры прокси в файл.
		self.__SaveProxiesJSON()
		# Запись в лог предупреждения: прокси заблокирован как заблокированный.
		logging.warning("Proxy: " + str(Proxy) + ". Blocked as forbidden.")
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
		ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])

		# При отключённом режиме отладки скрыть окно браузера.
		if self.__Settings["debug"] is False:
			ChromeOptions.add_argument("--headless=new")

		# Инициализация веб-драйвера.
		try:
			self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), options = ChromeOptions)

		except FileNotFoundError:
			logging.critical("Unable to locate webdriver! Try to remove \".wdm\" folder in script directory.")

	# Обработать статусы ответов.
	def __ProcessStatusCode(self, StatusCode: int, Proxy: dict):

		# Обработка статусов ответа в режиме Selenium.
		if self.__Settings["selenium-mode"] is True:
			if StatusCode == 1 and self.__Settings["use-proxy"] is True:
				self.__BlockProxyAsInvalid(Proxy, StatusCode)
				self.__InitializeWebDriver()
			elif StatusCode == 1 and self.__IsProxval is True:
				self.__BlockProxyAsInvalid(Proxy, StatusCode)
				self.__InitializeWebDriver()
			elif StatusCode == 0:
				self.__RestoreProxyAsValid(Proxy)

		# Обработка статусов ответа в режиме requests.
		else: 
			if StatusCode == 1 and self.__Settings["use-proxy"] is True:
				self.__BlockProxyAsInvalid(Proxy, StatusCode)
			elif StatusCode == 1 and self.__IsProxval is True:
				self.__BlockProxyAsInvalid(Proxy, StatusCode)
			elif StatusCode == 0:
				self.__RestoreProxyAsValid(Proxy)
			elif StatusCode == 2 and self.__Settings["use-proxy"] is True:
				self.__BlockProxyAsForbidden(Proxy, StatusCode)
			elif StatusCode == 3:
				raise requests.exceptions.HTTPError

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

	# Непосредственно выполняет запрос к серверу через библиотеку requests.
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

			# Если запрос прошёл.
			elif Response.status_code == 200:
				StatusCode = 0

			# Проверка других кодов, при которых необходимо повторить запрос.
			elif Response.status_code in [502]:
				raise requests.exceptions.HTTPError

		# Обработка ошибки: прокси недоступен.
		except requests.exceptions.ProxyError:
			StatusCode = 0

		# Обработка ошибки: запрошена капча Cloudflare V2.
		except cloudscraper.exceptions.CloudflareChallengeError:
			StatusCode = 2

		# Обработка ошибки: ошибка со стороны сервера.
		except requests.exceptions.HTTPError:
			StatusCode = 3

		return Response, StatusCode

	# Непосредственно выполняет запрос к серверу через JavaScript в браузере Google Chrome.
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
				StatusCode = 2
			elif Response.text != None and dict(json.loads(Response.text))["msg"] == "Для просмотра нужно авторизироваться":
				Response.status_code = 401
				StatusCode = 0
			elif Response.text != None and dict(json.loads(Response.text))["msg"] == "Тайтл не найден":
				Response.status_code = 404
				StatusCode = 0
			else:
				Response.status_code = 200
				StatusCode = 0

		# Обработка ошибки: не удалось выполнить JavaScript или нерабочий прокси.
		except (SeleniumExceptions.JavascriptException, SeleniumExceptions.WebDriverException):
			Response = None
			StatusCode = 1

		# Обнуление эмулируемого контейнера ответа при ошибке запроса.
		if StatusCode in [1, 2]:
			Response = None

		return Response, StatusCode

	# Проверяет, находится ли активный прокси в валидном списке, и восстанавливает его.
	def __RestoreProxyAsValid(self, Proxy: dict):

		# Проверка наличия прокси в валидном списке.
		if self.__Proxies != dict() and Proxy not in self.__Proxies["proxies"]:

			# Удаление прокси из списка недоступных.
			if Proxy in self.__Proxies["forbidden-proxies"]:
				self.__Proxies["forbidden-proxies"].remove(Proxy)
			else:
				self.__Proxies["invalid-proxies"].remove(Proxy)

			# Помещение прокси в новый список.
			self.__Proxies["proxies"].append(Proxy)
			# Сохранение новой структуры прокси в файл.
			self.__SaveProxiesJSON()
			# Запись в лог сообщения: прокси помечен как недоступный.
			logging.info("Proxy: " + str(Proxy) + " marked as valid.")

	# Сохраняет JSON с прокси.
	def __SaveProxiesJSON(self):
		with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

	# Конструктор: читает список прокси и нициализирует менеджер.
	def __init__(self, Settings: dict, LoadProxy: bool = False):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Генерация свойств.
		#==========================================================================================#
		self.__Settings = Settings
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

		#---> Загрузка и валидация прокси-серверов.
		#==========================================================================================#
		# Чтение файла определений прокси, если необходимо.
		try:
			if Settings["use-proxy"] is True or LoadProxy is True:
				with open("Proxies.json") as FileRead:
					self.__Proxies = json.load(FileRead)
		
		except FileNotFoundError:
			# Запись в лог критической ошибки: не удалось найти файл 
			logging.critical("Unable to open \"Proxies.json\" file!")
			# Прерывание выполнения.
			sys.exit()

		except json.JSONDecodeError:
			# Запись в лог критической ошибки: не удалось найти файл 
			logging.critical("Error occurred while reading \"Proxies.json\" file!")
			# Прерывание выполнения.
			sys.exit()

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
		# Текущий индекс попытки.
		CurrentTry = 0

		# Установка заголовков по умолчанию.
		if Headers is None:
			Headers = self.__RequestHeaders
		
		# Повторять пока не будут получены данные или не сработает исключение.
		while Status != 0:
			print("MAX")
			# Повторять пока не закончатся попытки.
			while Status != 0 and CurrentTry <= self.__Settings["retry-tries"]:
				print("min")
				# Выжидание интервала при повторе.
				if CurrentTry > 0:
					# Запись в лог ошибки: не удалось выполнить запрос.
					logging.error("Unable to request data. Retrying... ")
					# Выжидание интервала.
					time.sleep(self.__Settings["retry-delay"])

				# Выполнение запроса в указанном режиме.
				if self.__Settings["selenium-mode"] is True:
					Response, Status = self.__RequestDataWith_ChromeJavaScript(URL, Headers, self.__CurrentProxy)
				else:
					Response, Status = self.__RequestDataWith_requests(URL, Headers, self.__CurrentProxy)

				# Инкремент попыток повтора.
				CurrentTry += 1

			# Обработка кода статуса запроса.
			self.__ProcessStatusCode(Status, self.__CurrentProxy)

		return Response

	# Проверяет валидность прокси сервера.
	def ValidateProxy(self, Proxy: dict, UpdateFile: bool = False) -> int:
		# Тестовый URL запроса.
		URL = "https://api.remanga.org/api/titles/last-chapters/?page=1&count=20"
		# Возвращает код статуса прокси: 0 – валиден, 1 – недоступен, 2 – заблокирован, 3 – ошибка сервера. 
		StatusCode = None
		# Изменение состояния валидации.
		self.__IsProxval = True
		# Заголовки запроса.
		Headers = {
			"accept": "*/*",
			"accept-language": "ru,en;q=0.9",
			"content-type": "application/json",
			"preference": "0",
			"referer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin"
			}
		
		# Выполнение запроса с прокси или без.
		if self.__Settings["selenium-mode"] is True:
			# Удаление ненужных заголовков.
			del Headers["referer"]
			del Headers["referrerPolicy"]
			# Выполнение запроса через интерпретатор JavaScript в Google Chrome.
			Response, StatusCode = self.__RequestDataWith_ChromeJavaScript(URL, Headers, Proxy)

		else:
			# Генерация User-Agent.
			Headers["User-Agent"] = GetRandomUserAgent()
			# Выполнение запроса через библиотеку Python.
			Response, StatusCode = self.__RequestDataWith_requests(URL, Headers, Proxy)

		# Если указано флагом, обновить файл определений прокси.
		if UpdateFile is True:
			self.__ProcessStatusCode(StatusCode, Proxy)

		return StatusCode