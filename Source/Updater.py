from Functions import GetRandomUserAgent

import requests
import logging
import random
import json
import time

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
			"referer": "https://remanga.org/",
			"User-Agent": UserAgent,
			"authorization": self.__Settings["authorization"]
			}

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
			# Ответ запроса.
			Response = None
			# Формирование адреса для текущего запроса.
			CurrentRequestAPI = LastChaptersAPI.replace("[REPLACEBLE]", str(Page))
			
			# Выполнение запроса с прокси-сервером, если указано, или без него.
			if self.__Settings["use-proxy"] == True:
				Response = requests.get(CurrentRequestAPI, headers = self.__RequestHeaders, proxies = self.__Settings["proxy"][random.randint(0, len(self.__Settings["proxy"]) - 1)])
			else:
				Response = requests.get(CurrentRequestAPI, headers = self.__RequestHeaders)

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