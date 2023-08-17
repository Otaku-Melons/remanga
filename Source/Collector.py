from Source.RequestsManager import RequestsManager
from Source.Functions import GetRandomUserAgent
from Source.Functions import Wait
from dublib.Methods import Cls

import logging
import json
import os

# Сборщик списков тайтлов, соответствующих фильтрам каталога.
class Collector:
	
	# Возвращает список тайтлов, подходящих по заданным фильтрам.
	def __CollectTitlesList(self, FilterType: str, FilterID: str, ForceMode: bool) -> list[str]:
		# Состояние: достигнута ли последняя страница католога.
		IsLastPage = False		
		# Список тайтлов.
		TitlesList = list()
		# Номер страницы каталога.
		Page = 1

		# Пока не достигнута последняя страница.
		while IsLastPage == False:
			# URL для запроса к API.
			CollectionAPI = f"https://api.remanga.org/api/search/catalog/?{FilterType}={FilterID}&count=30&ordering=-id&page={Page}"
			# Выполнение запроса.
			Response = self.__RequestsManager.request(CollectionAPI)
			# Очистка консоли.
			Cls()
			# Вывод в консоль состояния режима перезаписи.
			print("Force mode: " + "ON" if ForceMode else "OFF")
			# Вывод в консоль прогресса.
			print(f"Collecting titles slugs on page {Page}...")
			
			# Проверка успешности запроса.
			if Response.status_code == 200:
				# Сохранение форматированного результата.
				PageContent = dict(json.loads(Response.text))["content"]
				
				# Для каждого тайтла найти и записать алиас.
				for TitleDescription in PageContent:
					TitlesList.append(TitleDescription["dir"])
					
				# Если контента нет, то завершить сбор.
				if PageContent == []:
					IsLastPage = True
					
				# Запись в лог сообщения: просканирована страница.
				else:
					logging.info(f"Titles on page {Page} collected.")
					
				# Выжидание указанного интервала.
				Wait(self.__Settings)

			# Обработка ошибки доступа в виду отсутствия токена авторизации.
			elif Response.status_code == 401:
				# Завершение процесса перелистывания.
				IsLastPage = True
				# Запись в лог ошибки: невозможно получить доступ к 18+ фильтру.
				logging.error("Unable to request data. Authorization token required.")

			# Обработка неизвестной ошибки запроса.
			else:
				# Запись в лог критической ошибки: неизвестная ошибка запроса.
				logging.error(f"Unknown request error with status code: {Response.status_code}.")
				# Выброс исключения.
				raise Exception(f"unknown request error (status code: {Response.status_code})")
			
			# Инкремент номера страницы.
			Page += 1

		# Запись в лог сообщения: количество просканированных страниц и найденных тайтлов.
		logging.info("Collected " + str(len(TitlesList)) + " titles slugs on " + str(Page - 2) + " pages.")

		return TitlesList
	
	# Конструктор.
	def __init__(self, Settings: dict):
		# Генерация User-Agent.
		UserAgent = GetRandomUserAgent()
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Менеджер запросов через прокси.
		self.__RequestsManager = RequestsManager(Settings)
		# Глобальные настройки.
		self.__Settings = Settings.copy()
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
		
		# Если токена авторизации нет, то удалить заголовок.
		if self.__RequestHeaders["authorization"] == "":
			del self.__RequestHeaders["authorization"]

	# Сохраняет список алиасов тайтлов в файл.
	def collect(self, FilterType: str, FilterID: str, ForceMode: bool = False) -> list[str]:
		# Запись в лог сообщения: начат сбор списка тайтлов.
		logging.info(f"Starting to collect titles slugs. Filter: \"{FilterType}={FilterID}\".")
		# Список алиасов.
		TitlesList = self.__CollectTitlesList(FilterType, FilterID, ForceMode)
		
		# Если отключён режим перезаписи.
		if ForceMode == False:
			# Локальная коллекция.
			LocalCollection = list()
			
			# Если существует файл коллекции.
			if os.path.exists("Collection.txt"):
				
				# Чтение содржимого файла.
				with open("Collection.txt", "r") as FileReader:
					# Буфер чтения.
					Bufer = FileReader.read().split('\n')
					
					# Поместить алиасы в список на парсинг, если строка не пуста.
					for Slug in Bufer:
						if Slug.strip() != "":
							LocalCollection.append(Slug)
							
			# Слияние списка тайтлов.
			TitlesList = LocalCollection + TitlesList
		
		# Сохранение каждого алиаса в файл.
		with open("Collection.txt", "w") as FileWriter:
			for Slug in TitlesList:
				FileWriter.write(Slug + "\n")


		return TitlesList