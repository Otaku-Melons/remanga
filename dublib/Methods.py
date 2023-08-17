import shutil
import html
import json
import sys
import os
import re

def CheckForCyrillicPresence(Text: str) -> bool:
	"""
	Проверяет, имеются ли кирилические символы в строке.
		Text – проверяемая строка.
	"""

	# Русский алфавит в нижнем регистре.
	Alphabet = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
	# Состояние: содержит ли строка кирилические символы.
	TextContainsCyrillicCharacters = not Alphabet.isdisjoint(Text.lower())

	return TextContainsCyrillicCharacters

def Cls():
	"""
	Очищает консоль (кроссплатформенная функция).
	"""

	os.system("cls" if os.name == "nt" else "clear")

def MergeDictionaries(FirstDictionary: dict, SecondDictionary: dict) -> dict:
	"""
	Объединяет словари без перезаписи значений уже существующих ключей.
		FirstDictionary – словарь, в который идёт копирование.
		SecondDictionary – словарь, из котрого идёт копирование.
	"""

	# Для каждого ключа, если таковой отсутствует в первом словаре, то скопировать его.
	for Key in SecondDictionary.keys():
		if Key not in FirstDictionary.keys():
			FirstDictionary[Key] = SecondDictionary[Key]

	return FirstDictionary

def ReadJSON(Path: str) -> dict:
	"""
	Считывает JSON файл в словарь.
		Path – путь к файлу JSON.
	"""

	# Словарь для преобразования.
	JSON = dict()

	# Открытие и чтение файла JSON.
	with open(Path, encoding = "utf-8") as FileRead:
		JSON = json.load(FileRead)

	return JSON

def RemoveFolderContent(Path: str):
	"""
	Удаляет все папки и файлы внутри директории.
		Path – путь к директории.
	"""

	# Список содержимого в папке.
	FolderContent = os.listdir(Path)

	# Для каждого элемента.
	for Item in FolderContent:

		# Если элемент является папкой.
		if os.path.isdir(Path + "/" + Item):
			shutil.rmtree(Path + "/" + Item)

		else:
			os.remove(Path + "/" + Item)

def RemoveHTML(TextHTML: str) -> str:
	"""
	Удаляет теги HTML из строки, а также преобразует спецсимволы HTML в Unicode.
		TextHTML – строка, имеющая HTML-разметку.
	"""

	# Конвертирование спецсимволов HTML в Unicode.
	TextHTML = html.unescape(TextHTML)
	# Регулярное выражение фильтрации тегов HTML.
	TagsHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	# Удаление найденных по регулярному выражению тегов.
	CleanText = re.sub(TagsHTML, '', str(TextHTML))

	return str(CleanText)

def RemoveRecurringCharacters(String: str, Substring: str) -> str:
	"""
	Удаляет из строки подряд идущие повторяющиеся подстроки.
		String – строка, из которой удаляются повторы;
		Substring – удаляемая подстрока.
	"""

	# Пока в строке находятся повторы указанного символа, удалять их.
	while Substring + Substring in String:
		String = String.replace(Substring + Substring, Substring)

	return String

def RemoveRegexSubstring(String: str, Regex: str) -> str:
	"""
	Удаляет из строки все вхождения подстрок, совпадающие с регулярным выражением.
		String – обрабатываемая строка;
		Regex – регулярное выражение для поиска подстрок.
	"""

	# Поиск всех совпадений.
	RegexSubstrings = re.findall(Regex, String)

	# Удаление каждой подстроки.
	for RegexSubstring in RegexSubstrings:
		String = String.replace(RegexSubstring, "")

	return String

def RenameDictionaryKey(Dictionary: dict, OldKey: str, NewKey: str) -> dict:
	"""
	Переименовывает ключ в словаре, сохраняя исходный порядок.
		Dictionary – обрабатываемый словарь;
		OldKey – старое название ключа;
		NewKey – новое название ключа.
	"""

	# Результат выполнения.
	Result = dict()

	# Перебор элементов словаря по списку ключей.
	for Key in Dictionary.keys():

		# Если нашли нужный ключ, то переместить значение по новому ключу в результат, иначе просто копировать.
		if Key == OldKey:
			Result[NewKey] = Dictionary[OldKey]
		else:
			Result[Key] = Dictionary[Key]

	return Result

def Shutdown():
	"""
	Выключает питание устройства (кроссплатформенная функция).
	"""

	# Если устройство работает под управлением ОС семейства Linux.
	if sys.platform in ["linux", "linux2"]:
		os.system("sudo shutdown now")

	# Если устройство работает под управлением ОС семейства Windows.
	elif sys.platform == "win32":
		os.system("shutdown /s")

def WriteJSON(Path: str, Dictionary: dict):
	"""
	Сохраняет стилизованный JSON файл. Для отступов используются символы табуляции, новая строка проставляется после запятых, а после двоеточий добавляется пробел.
		Path – путь к существующему или будущему файлу JSON;
		Dictionary – словарь, записываемый в формат JSON.
	"""

	# Запись словаря в JSON файл.
	with open(Path, "w", encoding = "utf-8") as FileWrite:
		json.dump(Dictionary, FileWrite, ensure_ascii = False, indent = '\t', separators = (",", ": "))