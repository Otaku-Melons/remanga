from RequestsManager import RequestsManager
from Functions import GetRandomUserAgent
from Functions import Wait

import logging
import json

class Updater:
    
    #==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	# Глобальные настройки.
	__Settings = dict()
	# Заголовки запроса.
	__RequestHeaders = None
	# Менеджер запросов через прокси.
	__RequestsManager = None

	#==========================================================================================#
	# >>>>> МЕТОДЫ РАБОТЫ <<<<< #
	#==========================================================================================#

	# Конвертирует секунды в миллисекунды.
	def __SecondsToMilliseconds(self, Seconds: int):
		# Миллисекунды.
		Milliseconds = 0
		# Пересчёт секунд в миллисекунды.
		Milliseconds = Seconds * 60000

		return Milliseconds

	# Конструктор: задаёт глобальные настройки и инициализирует объект.
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
		self.__RequestsManager = RequestsManager(Settings)

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
			Response = self.__RequestsManager.Request(CurrentRequestAPI)
			
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
				Wait(self.__Settings)

			elif Response.status_code == 200:
				# Запись в лог сообщения о завершении проверки обновлений.
				logging.info("On " + str(Page) + " pages updates notes found: " + str(UpdatesCounter) + ".")

		return Updates