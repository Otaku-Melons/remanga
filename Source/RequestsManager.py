from selenium.common import exceptions as SeleniumExceptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from Source.Functions import GetRandomUserAgent
from seleniumwire import webdriver
from bs4 import BeautifulSoup

import cloudscraper
import requests
import logging
import base64
import json
import time
import sys

# Исключение: отсутствуют валидные прокси.
class MissingValidProxy(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self): 
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message) 
		# Добавление данных в сообщение об ошибке.
		self.__Message = "There are no valid proxies in the \"Proxies.json\"."

	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

# Эмулятор структуры ответа библиотеки requests.
class ResponseEmulation():


	# Конструктор.
	def __init__(self):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Код ответа.
		self.status_code = 0
		# Бинарный вариант ответа.
		self.content = None
		# Текст ответа.
		self.text = ""

# Менеджер запросов и регулирования работы прокси.
class RequestsManager:

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
		self.close()
		# Опции веб-драйвера.
		ChromeOptions = webdriver.ChromeOptions()
		# Настройка прокси.
		SeleniumWireOptions = None
		
		# При включённом прокси создать и установить дополнение.
		if self.__Settings["use-proxy"] is True:
			# Получение данных текущего прокси.
			UserName, Password, IP, Port = self.__GetProxyData(self.__CurrentProxy)
			# Формирование настроек.
			SeleniumWireOptions = {
				"disable_capture": True,
				"proxy": {
					"http": f"http://{UserName}:{Password}@{IP}:{Port}", 
					"https": f"http://{UserName}:{Password}@{IP}:{Port}"
				}
			}

		# Установка опций.
		ChromeOptions.add_argument("--no-sandbox")
		ChromeOptions.add_argument("--disable-dev-shm-usage")
		ChromeOptions.add_experimental_option("excludeSwitches", ["enable-logging"])

		# При отключённом режиме отладки скрыть окно браузера.
		if self.__Settings["debug"] is False:
			ChromeOptions.add_argument("--headless=new")

		# Инициализация веб-драйвера.
		try:
			self.__Browser = webdriver.Chrome(service = Service(ChromeDriverManager().install()), seleniumwire_options = SeleniumWireOptions, options = ChromeOptions)

		except FileNotFoundError:
			logging.critical("Unable to locate webdriver! Try to remove \".wdm\" folder in script directory.")

	# Обработать статусы ответов.
	def __ProcessStatusCode(self, Status: int, Proxy: dict):

		# Обработка статусов ответа в режиме Selenium.
		if self.__Settings["selenium-mode"] is True and self.__Settings["use-proxy"] is True:
			if Status == 1:
				self.__BlockProxyAsInvalid(Proxy)
				self.__InitializeWebDriver()
			elif Status == 2:
				self.__BlockProxyAsForbidden(Proxy)
				self.__InitializeWebDriver()
			elif Status == 3:
				raise requests.exceptions.HTTPError
			elif Status == 0:
				self.__RestoreProxyAsValid(Proxy)

		# Обработка статусов ответа в режиме requests.
		elif self.__Settings["use-proxy"] is True: 
			if Status == 1:
				self.__BlockProxyAsInvalid(Proxy)
			elif Status == 2:
				self.__BlockProxyAsForbidden(Proxy)
			elif Status == 3:
				raise requests.exceptions.HTTPError
			elif Status == 0:
				self.__RestoreProxyAsValid(Proxy)

	# Форматирует прокси в формат дополнения..
	def __GetProxyData(self, Proxy: dict):
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
		# Ответ сервера.
		Response = None
		# Статус ответа.
		Status = None

		# Интерпретация прокси.
		if Proxy is None:
			Proxy = dict()

		try:
			# Попытка выполнения запроса.
			Response = Scraper.get(URL, headers = Headers, proxies = Proxy)

			# Если запрос успешен.
			if Response.status_code in [200, 401, 404]:
				Status = 0

			# Если запрос отклонён сервером.
			elif Response.status_code == 403:
				Status = 2

			# Если возникла ошибка на сервере.
			elif Response.status_code in [502]:
				Status = 3

		# Обработка ошибки: прокси недоступен.
		except requests.exceptions.ProxyError:
			Status = 1

		# Обработка ошибки: запрошена капча Cloudflare V2.
		except cloudscraper.exceptions.CloudflareChallengeError:
			Status = 2

		return Response, Status

	# Непосредственно выполняет запрос к серверу через JavaScript в браузере Google Chrome.
	def __RequestDataWith_ChromeJavaScript(self, URL: str, Headers: dict, Proxy: dict):
		# Скрипт XHR запроса.
		Script = self.__BuildXHR(URL, Headers, Headers["content-type"])
		# Ответ сервера.
		Response = ResponseEmulation()
		# Статус ответа.
		Status = None

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
			
			# Обработка ответа для выяснения успешности.
			if Response.text == "":
				Response.status_code = 403
				Status = 2

			elif Response.text != None and dict(json.loads(Response.text))["msg"] == "Для просмотра нужно авторизироваться":
				Response.status_code = 401
				Status = 0

			elif Response.text != None and dict(json.loads(Response.text))["msg"] == "Тайтл не найден":
				Response.status_code = 404
				Status = 0

			else:
				Response.status_code = 200
				Status = 0

		# Обработка ошибки: не удалось выполнить JavaScript или нерабочий прокси.
		except (SeleniumExceptions.JavascriptException, SeleniumExceptions.WebDriverException):
			Response.status_code = 403
			Status = 1
		
		return Response, Status

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
			# Запись в лог сообщения: прокси помечен как доступный.
			logging.info("Proxy: " + str(Proxy) + ". Marked as valid.")

	# Сохраняет JSON с прокси.
	def __SaveProxiesJSON(self):
		with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
			json.dump(self.__Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

	# Конструктор: читает список прокси и нициализирует менеджер.
	def __init__(self, Settings: dict, LoadProxy: bool = False):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Текущий прокси.
		self.__CurrentProxy = None
		# Хранилище прокси.
		self.__Proxies = dict()
		# Экземпляр браузера, управляемого Selenium.
		self.__Browser = None
		# Заголовки запроса.
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

	# Закрывает экземпляр браузера.
	def close(self):
		try:
			self.__Browser.quit()
		except Exception:
			pass

	# Возвращает список прокси.
	def getProxies(self, ProxiesType: str = "all"):
		if ProxiesType == "invalid":
			return self.__Proxies["invalid-proxies"]
		elif ProxiesType == "forbidden":
			return self.__Proxies["forbidden-proxies"]
		elif ProxiesType == "valid":
			return self.__Proxies["proxies"]
		elif ProxiesType == "all":
			return self.__Proxies["proxies"] + self.__Proxies["forbidden-proxies"] + self.__Proxies["invalid-proxies"]

	# Проводит запрос к API Remanga и интерпретирует результаты.
	def request(self, URL: str, Headers: dict = None):
		# Ответ сервера.
		Response = None
		# Статус ответа.
		Status = None
		# Текущий индекс повтора.
		CurrentTry = 0
		
		# Инициализация и настройка веб-драйвера.
		if self.__Settings["selenium-mode"] and self.__Browser == None:
			self.__InitializeWebDriver()

		# Установка заголовков по умолчанию.
		if Headers is None:
			Headers = self.__RequestHeaders
		
		# Обработка повторов запроса с использованием прокси.
		if self.__Settings["use-proxy"] is True:

			# Повторять пока не будут получены данные или не сработает исключение.
			while Status != 0:
				# Обнуление индекса повторов прокси.
				CurrentTry = 0
				
				# Повторять пока не закончатся попытки для каждого прокси.
				while Status != 0 and CurrentTry <= self.__Settings["retry-tries"]:
					
					# Выжидание интервала при повторе.
					if CurrentTry > 0:
						# Запись в лог ошибки: не удалось выполнить запрос.
						logging.error("Unable to request data with proxy: " + str(self.__CurrentProxy) + ". Retrying...")
						# Реинициализация браузера.
						self.__InitializeWebDriver()
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
		
		# Обработка повторов запроса без использования прокси.
		else:

			# Повторять пока не закончатся попытки.
			while Status != 0 and CurrentTry <= self.__Settings["retry-tries"]:
				
				# Выжидание интервала при повторе.
				if CurrentTry > 0:
					# Запись в лог ошибки: не удалось выполнить запрос.
					logging.error("Unable to request data. Retrying...")
					# Реинициализация браузера.
					self.__InitializeWebDriver()
					# Выжидание интервала.
					time.sleep(self.__Settings["retry-delay"])

				# Выполнение запроса в указанном режиме.
				if self.__Settings["selenium-mode"] is True:
					Response, Status = self.__RequestDataWith_ChromeJavaScript(URL, Headers, self.__CurrentProxy)
				else:
					Response, Status = self.__RequestDataWith_requests(URL, Headers, self.__CurrentProxy)

				# Инкремент попыток повтора.
				CurrentTry += 1

		return Response

	# Проверяет валидность прокси сервера.
	def validateProxy(self, Proxy: dict, UpdateFile: bool = False) -> int:
		# Тестовый URL запроса.
		URL = "https://api.remanga.org/api/titles/last-chapters/?page=1&count=20"
		# Возвращает код статуса прокси: 0 – валиден, 1 – недоступен, 2 – заблокирован, 3 – ошибка сервера. 
		StatusCode = None
		# Заголовки запроса.
		Headers = {
			"accept": "*/*",
			"accept-language": "ru,en;q=0.9",
			"content-type": "application/json",
			"preference": "0",
			"referer": "https://remanga.org/",
			"referrerPolicy": "strict-origin-when-cross-origin"
			}
		
		# Инициализация и настройка веб-драйвера.
		if self.__Settings["selenium-mode"] and self.__Browser == None:
			self.__InitializeWebDriver()
		
		# Выполнение запроса с прокси или без.
		if self.__Settings["selenium-mode"] is True:

			try:
				# Переход на указанную страницу валидации.
				self.__Browser.get(self.__Proxies["selenium-validator"]["url"])
				# HTML код тела страницы после полной загрузки.
				BodyHTML = str(self.__Browser.execute_script("return document.body.innerHTML;"))
				# Получение текущего IP согласно настройкам.
				CurrentIP = BeautifulSoup(BodyHTML, "html.parser").find(self.__Proxies["selenium-validator"]["tag"], self.__Proxies["selenium-validator"]["properties"]).get_text().strip()

				# Если текущий IP такой же, как у прокси.
				if CurrentIP == Proxy["https"].split('@')[1].split(':')[0]:
					StatusCode = 0

				else:
					StatusCode = 1

			except Exception:
				StatusCode = 1

		else:
			# Генерация User-Agent.
			Headers["User-Agent"] = GetRandomUserAgent()
			# Выполнение запроса через библиотеку Python.
			Response, StatusCode = self.__RequestDataWith_requests(URL, Headers, Proxy)

		# Если указано флагом, обновить файл определений прокси.
		if UpdateFile is True:
			self.__ProcessStatusCode(StatusCode, Proxy)

		return StatusCode