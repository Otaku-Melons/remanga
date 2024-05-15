from Source.RequestsManager import RequestsManager
from time import sleep

import logging
import json

class Updater:

	# Конвертирует секунды в миллисекунды.
	def __SecondsToMilliseconds(self, Seconds: int):
		# Миллисекунды.
		Milliseconds = 0
		# Пересчёт секунд в миллисекунды.
		Milliseconds = Seconds * 60000

		return Milliseconds

	# Конструктор: задаёт глобальные настройки и инициализирует объект.
	def __init__(self, Settings: dict):

		#---> Генерация динамичкских свойств.
		#==========================================================================================#
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Менеджер запросов через прокси.
		self.__RequestsManager = RequestsManager(Settings)
		# Заголовки запроса.
		self.__RequestHeaders = {
			"Authorization": self.__Settings["token"],
			"Referer": "https://remanga.org/"
		}
		
		# Если токена авторизации нет, то удалить заголовок.
		if self.__RequestHeaders["Authorization"] == "":
			del self.__RequestHeaders["Authorization"]

	# Возвращает список алиасов обновлённых тайтлов.
	def getUpdatesList(self) -> list:
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
			Response = self.__RequestsManager.request(CurrentRequestAPI)
			
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
				sleep(self.__Settings["delay"])

			elif Response.status_code == 200:
				# Запись в лог сообщения о завершении проверки обновлений.
				logging.info("On " + str(Page) + " pages updates notes found: " + str(UpdatesCounter) + ".")

		return Updates