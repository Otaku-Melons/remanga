from Source.RequestsManager import RequestsManager
from dublib.Methods import Cls
from time import sleep

import logging
import json
import os

# Сборщик списков тайтлов, соответствующих фильтрам каталога.
class Collector:
	
	# Возвращает список тайтлов, подходящих по заданным фильтрам.
	def __CollectTitlesList(self, Filters: str, ForceMode: bool) -> list[str]:
		# Состояние: достигнута ли последняя страница католога.
		IsLastPage = False		
		# Список тайтлов.
		TitlesList = list()
		# Номер страницы каталога.
		Page = 1

		# Пока не достигнута последняя страница.
		while IsLastPage == False:
			# URL для запроса к API.
			CollectionAPI = f"https://api.remanga.org/api/search/catalog/?page={Page}&count=30&ordering=-id&{Filters}"
			# Выполнение запроса.
			Response = self.__RequestsManager.request(CollectionAPI)
			# Очистка консоли.
			Cls()
			# Вывод в консоль состояния режима перезаписи.
			print("Force mode: " + ("ON" if ForceMode else "OFF"))
			
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
					
				
				else:
					# Вывод в консоль прогресса.
					print(f"Collecting titles slugs on page {Page}...")
					# Запись в лог сообщения: просканирована страница.
					logging.info(f"Titles on page {Page} collected.")
					
				# Выжидание указанного интервала.
				sleep(self.__Settings["delay"])

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
		logging.info("Found " + str(len(TitlesList)) + " titles slugs on " + str(Page - 2) + " pages.")

		return TitlesList
	
	# Конструктор.
	def __init__(self, Settings: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Менеджер запросов через прокси.
		self.__RequestsManager = RequestsManager(Settings)
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Заголовки запроса.
		self.__RequestHeaders = {
			"Authorization": self.__Settings["token"],
			"Referer": "https://remanga.org/"
		}
		
		# Если токена авторизации нет, то удалить заголовок.
		if self.__RequestHeaders["Authorization"] == "":
			del self.__RequestHeaders["Authorization"]

	# Сохраняет список алиасов тайтлов в файл.
	def collect(self, Filters: str, ForceMode: bool = False) -> list[str]:
		# Запись в лог сообщения: начат сбор списка тайтлов.
		logging.info(f"Starting to collect titles slugs. Filters: \"{Filters}\".")
		# Список алиасов.
		TitlesList = self.__CollectTitlesList(Filters, ForceMode)
		# Количество полученных алиасов.
		CollectedSlugsCount = len(TitlesList)
		# Количество дубликатов.
		DuplicatesCount = 0
		# Локальная коллекция.
		LocalCollection = list()
		
		# Если отключён режим перезаписи.
		if ForceMode == False:
			
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
					
			# Буфер списка алиасов.
			Bufer = list()
			# Для каждого собранного алиаса.
			for Slug in TitlesList:
					
				# Если такого алиаса нет в коллекции, то добавить его.
				if Slug not in LocalCollection:
					Bufer.append(Slug)
					
				else:
					# Инкремент количества дубликатов.
					DuplicatesCount += 1
			
			# Перемещение содержимого буфера в список алиасов.
			TitlesList = LocalCollection + Bufer
			
		# Сохранение каждого алиаса в файл.
		with open("Collection.txt", "w") as FileWriter:
			for Slug in TitlesList:
				FileWriter.write(Slug + "\n")
		
		# Если были дубликаты.
		if DuplicatesCount > 0:
			# Запись в лог сообщения: количество дубликатов.
			logging.info("Excluded duplicated slugs count: " + str(DuplicatesCount) + ".")
			# Запись в лог сообщения: количество записанных алиасов.
			logging.info(str(CollectedSlugsCount - DuplicatesCount) + " slugs written.")
			
		else:
			# Запись в лог сообщения: все алиасы записаны..
			logging.info("All slugs are written.")

		return TitlesList