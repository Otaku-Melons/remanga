from dublib.WebRequestor import Protocols, WebRequestor
from dublib.Methods import ReadJSON, WriteJSON
from fake_useragent import UserAgent

import requests
import logging
import json

#==========================================================================================#
# >>>>> ИСКЛЮЧЕНИЯ <<<<< #
#==========================================================================================#

# Исключение: отсутствуют валидные прокси.
class MissingValidProxy(Exception):

	# Конструктор: вызывается при обработке исключения.
	def __init__(self): 
		# Добавление данных в сообщение об ошибке.
		self.__Message = "There are no valid proxies in \"Proxies.json\"."
		# Обеспечение доступа к оригиналу наследованного свойства.
		super().__init__(self.__Message) 

	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return self.__Message

#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

# Менеджер запросов и прокси.
class RequestsManager:
	
	# Перемещает активный прокси в список.
	def __MoveCurrentProxyToList(self, List: str, From: str = "proxies", Initialize: bool = True):
		
		# Если установлен прокси.
		if self.__CurrentProxy != None:
			# Помещение активного прокси в список.
			self.__Proxies[List].append(self.__CurrentProxy)
			# Удаление активного прокси из валидных.
			self.__Proxies[From].remove(self.__CurrentProxy)
			# Сохранение списка прокси.
			WriteJSON("Proxies.json", self.__Proxies)
			# Выбор нового прокси.
			self.__SelectProxy()
			# Если указано, инициализировать запросчик.
			if Initialize == True: self.__Initialize()
	
	# Инициализирует запросчик.
	def __Initialize(self):
		
		# Если запросчик уже инициализирован.
		if self.__Requestor != None:
			# Закрытие старого запросчика.
			self.__Requestor.close()
			# Обнуление старого запросчика.
			self.__Requestor = None
			
		# Запросчик.
		self.__Requestor = WebRequestor()
		
		# Если выбран прокси.
		if self.__CurrentProxy != None:
			# Парсинг данных прокси.
			Data = self.__ParseProxy(self.__CurrentProxy["https"])
			# Добавление прокси.
			self.__Requestor.add_proxy(Protocols.HTTPS, Data["host"], Data["port"], Data["login"], Data["password"])
			
		# Инициализация запросчика.
		self.__Requestor.initialize()
	
	# Парсит прокси.
	def __ParseProxy(self, Proxy: str) -> dict:
		# Результат парсинга.
		Result = {
			"host": None,
			"posrt": None,
			"login": None,
			"password": None
		}
		# Парсинг.
		Auth = None if "@" not in Proxy else Proxy.split("@")[0].split("/")[-1]
		Host = Proxy.split("/")[-1] if "@" not in Proxy else Proxy.split("@")[-1]
		Result["host"] = Host.split(":")[0]
		Result["port"] = int(Host.split(":")[-1])
		
		# Если доступна авторизация.
		if Auth != None:
			# Парсинг данных авторизации.
			Result["login"] = Auth.split(":")[0]
			Result["password"] = Auth.split(":")[-1]
			
		return Result
	
	# Обрабатывает код ответа.
	def __ProcessStatusCode(self, StatusCode: int):
		
		# Если запрос успешен.
		if StatusCode == 200:
			
			# Если прокси был заблокирован.
			if self.__CurrentProxy in self.__Proxies["forbidden-proxies"]:
				# Восстановление прокси.
				self.__MoveCurrentProxyToList("proxies", "forbidden-proxies", False)
				
			# Если прокси недоступен.
			if self.__CurrentProxy in self.__Proxies["invalid-proxies"]:
				# Восстановление прокси.
				self.__MoveCurrentProxyToList("proxies", "invalid-proxies", False)
		
		else:
			
			# Если доступ запрещён.
			if StatusCode in [403]:
				# Перемещение прокси в список заблокированных.
				self.__MoveCurrentProxyToList("forbidden-proxies")
			
			else:
				# Перемещение прокси в список недоступных.
				self.__MoveCurrentProxyToList("invalid-proxies")

	# Выбирает прокси.
	def __SelectProxy(self):
		
		# Если присутствуют валидные прокси.
		if len(self.__Proxies["proxies"]) > 0:
			# Выбор первого прокси.
			self.__CurrentProxy = self.__Proxies["proxies"][0]
		
		else:
			# Выброс исключения.
			raise MissingValidProxy()

	# Конструктор.
	def __init__(self, Settings: dict, LoadProxy: bool = False):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Текущий прокси.
		self.__CurrentProxy = None
		# Словарь прокси.
		self.__Proxies = dict()
		# Заголовки запроса.
		self.__Headers = {
			"Authorization": self.__Settings["authorization-token"],
			"Referer": "https://remanga.org/",
			"User-Agent": UserAgent().chrome
		}
		# Запросчик.
		self.__Requestor = None

		#---> Загрузка и валидация прокси-серверов.
		#==========================================================================================#

		try:
			# Если настройками или аргументом указано использование прокси.
			if Settings["use-proxy"] == True or LoadProxy == True:
				# Чтение прокси.
				self.__Proxies = ReadJSON("Proxies.json")
		
		except FileNotFoundError:
			# Запись в лог критической ошибки: не удалось найти файл 
			logging.critical("Unable to open \"Proxies.json\".")
			# Завершение работы скрипта с кодом ошибки.
			exit(1)

		except json.JSONDecodeError:
			# Запись в лог критической ошибки: не удалось найти файл 
			logging.critical("Error occurred while reading \"Proxies.json\".")
			# Завершение работы скрипта с кодом ошибки.
			exit(1)

		# Если не запущена валидация, выбрать прокси.
		if Settings["use-proxy"] == True and LoadProxy == False: self.__SelectProxy()
		# Инициализация запросчика.
		self.__Initialize()
		
	# Загружает изображение.
	def downloadImage(self, URL: str, Path: str = "", Filename: str = "") -> int:
		# Выполнение запроса.
		Response = self.__Requestor.get(URL, headers = self.__Headers)
		# Получение имени файла.
		Filename = URL.split('/')[-1] if Filename == "" else Filename
		# Конвертирование косых черт.
		Path = Path.replace('\\', '/')
		
		# Если задано название и не указано расширение.
		if Filename.split(".")[-1] not in ["jpeg", "jpg", "webp"]:
			# Добавление расширения к названию файла.
			Filename += "." + URL.split('.')[-1]
	
		# Если путь не зананчивается косой чертой и не пуст.
		if Path.endswith('/') == False and Path.endswith('\\') == False and Path != "":
			# Добавление в конец пути косой черты.
			Path += "/"

		# Проверка успешности запроса.
		if Response.status_code == 200:

			# Открытие потока записи.
			with open(Path + Filename, "wb") as FileWriter:
				# Запись изображения.
				FileWriter.write(Response.content)
		
		return Response.status_code

	# Возвращает список прокси.
	def getProxies(self, ProxiesType: str = "all") -> list[dict]:
		# Возвращаемое значение.
		Proxies = list()
		# Если указаны валидные прокси, преобразовать ключ.
		if ProxiesType == "valid": ProxiesType = "proxies"
		
		# Если запрошены все прокси.
		if ProxiesType == "all":
			# Запись всех прокси.
			Proxies = self.__Proxies["proxies"] + self.__Proxies["forbidden-proxies"] + self.__Proxies["invalid-proxies"]
			
		else:
			# Запись конкретного списка прокси.
			Proxies = self.__Proxies[ProxiesType.replace("-proxies", "")]
			
		return Proxies

	# Проводит запрос к API Remanga и интерпретирует результаты.
	def request(self, URL: str, Headers: dict = None) -> requests.Response:
		# Если не заданы заголовки, использовать стандартные.
		if Headers == None: Headers = self.__Headers
		# Выполнение запроса.
		Response = self.__Requestor.get(URL, headers = Headers, tries = self.__Settings["tries"])
		# Если использовался прокси, обработать код.
		if self.__CurrentProxy != None and self.__Settings["proxy-manager"] == True: self.__ProcessStatusCode(Response.status_code)

		return Response

	# Проверяет валидность прокси сервера.
	def validateProxy(self, Proxy: dict, UpdateFile: bool = False) -> int:
		# Тестовый URL запроса.
		URL = "https://api.remanga.org/api/titles/last-chapters/?page=1&count=20"
		# Установка текущего прокси.
		self.__CurrentProxy = Proxy
		# Инициализация запросчика.
		self.__Initialize()
		# Выполнение запроса.
		Response = self.__Requestor.get(URL, headers = self.__Headers)
		# Если указано флагом, обновить файл определений прокси.
		if UpdateFile == True: self.__ProcessStatusCode(Response.status_code)

		return Response.status_code