from Functions import GetRandomUserAgent
from retry import retry

import cloudscraper
import requests
import logging
import random
import json
import time
import os

class Updater:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Глобальные настройки.
	__Settings = dict()
	# Заголовки запроса.
	__RequestHeaders = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Выполняет запрос к серверу Remanga.
	@retry(requests.exceptions.ProxyError, delay = 5, tries = 3)
	def __RequestData(self, URL: str, RequestHeaders: dict, UseProxy: bool = False):
		# Список прокси-серверов.
		Proxies = dict()
		# Индекс текущего прокси.
		CurrentProxyIndex = None
		# Текущий прокси.
		CurrentProxy = None
		# Ответ запроса.
		Response = None

		# Чтение списка прокси.
		if UseProxy == True and os.path.exists("Proxies.json"):
			with open("Proxies.json") as FileRead:
				Proxies = json.load(FileRead)

		# Обработка ошибки: нет файла с прокси.
		elif UseProxy == True and os.path.exists("Proxies.json") == False:
			# Запись в лог сообщения о невалидном прокси.
			logging.error("Unable to read \"Proxies.json\": file missing.")
			# Выброс исключения.
			raise Exception("\"Proxies.json\" required")
		
		# Получение текущего прокси.
		if UseProxy == True and len(Proxies["proxies"]) > 0:
			# Генерация индекса текущего прокси.
			CurrentProxyIndex = random.randint(0, len(Proxies["proxies"]) - 1)
			# Выбор прокси для доступа.
			CurrentProxy = Proxies["proxies"][CurrentProxyIndex]

		elif UseProxy == True:
			# Запись в лог сообщения об отсутствующих прокси.
			logging.error("Proxies required!")
			# Выброс исключения.
			raise Exception("List of proxies is empty")

		# Попытка выполнения запроса.
		try:

			# Создание обходчика Cloudflare.
			Scraper = cloudscraper.create_scraper(disableCloudflareV1 = True)

			# Выполнение запроса.
			if UseProxy == True:
				Response = Scraper.get(URL, headers = RequestHeaders, proxies = CurrentProxy)
			else:
				Response = Scraper.get(URL, headers = RequestHeaders)

			# Исключение прокси из разрешённых.
			if Response.status_code == 403:
				# Запись в лог сообщения о невалидном прокси.
				logging.error("Forbidden proxy detected and removed from further requests!")
				# Перемещение невалидного прокси в соответствующий список.
				Proxies["forbidden-proxies"].append(CurrentProxy)
				# Удаление невалидного прокси из изначального списка.
				Proxies["proxies"].pop(CurrentProxyIndex)

				# Сохранение нового файла прокси-серверов.
				with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
					json.dump(Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

				# Выброс исключения.
				raise requests.exceptions.ProxyError

		except requests.exceptions.ProxyError:
			# Запись в лог сообщения о невалидном прокси.
			logging.error("Invalid proxy detected and removed from further requests!")
			# Перемещение невалидного прокси в соответствующий список.
			Proxies["unvalid-proxies"].append(CurrentProxy)
			# Удаление невалидного прокси из изначального списка.
			Proxies["proxies"].pop(CurrentProxyIndex)

			# Сохранение нового файла прокси-серверов.
			with open("Proxies.json", "w", encoding = "utf-8") as FileWrite:
				json.dump(Proxies, FileWrite, ensure_ascii = False, indent = '\t', separators = (',', ': '))

			# Выброс исключения.
			raise requests.exceptions.ProxyError

		return Response

	# Конвертирует секунды в миллисекунды.
	def __SecondsToMilliseconds(self, Seconds: int):
		# Миллисекунды.
		Milliseconds = 0
		# Пересчёт секунд в миллисекунды.
		Milliseconds = Seconds * 60000

		return Milliseconds

	# Конструктор: задаёт глобальные настройки и подготавливает объект к работе.
	def __init__(self, Settings: dict):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()

		#---> Передача аргументов.
		#==========================================================================================#
		self.__Settings = Settings
		self.__RequestHeaders = {
			"authorization": self.__Settings["authorization"],
			"content-type": "application/json",
			"referer": "https://remanga.org/",
			"User-Agent": UserAgent

			}

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

		# Если токена авторизации нет, то удалить заголовок.
		if self.__RequestHeaders["authorization"] == "":
			del self.__RequestHeaders["authorization"]

	# Возвращает список алиасов обновлённых тайтлов.
	def GetUpdatesList(self) -> list:
		# Список алиасов обновлённых тайтлов.
		Updates = list()
		# Промежуток времени для проверки обновлений.
		ElapsedTime = self.__SecondsToMilliseconds(self.__Settings["check-updates-period"])
		# Состояние: достигнут ли конец проверяемого диапазона.
		IsTimeElapse = False
		# Модификатор для доступа к API глав.
		LastChaptersAPI = "https://api.remanga.org/api/titles/last-chapters/?page=[REPLACEBLE]&count=20"
		# Счётчик страницы.
		Page = 1
		# Счётчик обновлённых тайтлов.
		UpdatesCounter = 0

		# Проверка обновлений за указанный промежуток времени.
		while IsTimeElapse == False:
			# Формирование адреса для текущего запроса.
			CurrentRequestAPI = LastChaptersAPI.replace("[REPLACEBLE]", str(Page))
			# Выполнение запроса.
			Response = self.__RequestData(CurrentRequestAPI, self.__RequestHeaders, self.__Settings["use-proxy"])
			
			# Проверка успешности запроса.
			if Response.status_code == 200:
				# Сохранение форматированного результата.
				UpdatesPage = dict(json.loads(Response.text))["content"]

				# Проход по всем записям об обновлениях.
				for UpdateNote in UpdatesPage:

					# Проверка полученных элементов на выход за пределы заданного интервала.
					if UpdateNote["upload_date"] < ElapsedTime:
						# Сохранение алиаса обновлённого тайтла.
						Updates.append(UpdateNote["dir"])
						# Инкремент счётчика.
						UpdatesCounter += 1

					else:
						# Завершение цикла обновления.
						IsTimeElapse = True

			else:
				# Завершение цикла обновления.
				IsTimeElapse = True
				# Запись в лог сообщения о неудачной попытке получить обновления.
				logging.error("Unable to request updates. Response code: " + str(Response.status_code) + ".")

			# Проверка: завершён ли цикл.
			if IsTimeElapse == False:
				# Инкремент страницы.
				Page += 1
				# Выжидание указанного интервала.
				time.sleep(self.__Settings["delay"])

			elif Response.status_code == 200:
				# Запись в лог сообщения о завершении проверки обновлений.
				logging.info("On " + str(Page) + " pages updates notes found: " + str(UpdatesCounter) + ".")

		return Updates