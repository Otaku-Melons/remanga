import html
import json
import sys
import os
import re

# Проверяет, имеются ли кирилические символы в строке.
def CheckForCyrillicPresence(Text: str) -> bool:
	# Русский алфавит в нижнем регистре.
	Alphabet = set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя")
	# Состояние: содержит ли строка кирилические символы.
	TextContainsCyrillicCharacters = not Alphabet.isdisjoint(Text.lower())

	return TextContainsCyrillicCharacters

# Очищает консоль.
def Cls():
	os.system("cls" if os.name == "nt" else "clear")

# Объединяет словари без перезаписи.
def MergeDictionaries(FirstDictionary: dict, SecondDictionary: dict) -> dict:

	# Скопировать значения отсутствующих в оригинале ключей.
	for Key in SecondDictionary.keys():
		if Key not in FirstDictionary.keys():
			FirstDictionary[Key] = SecondDictionary[Key]

	return FirstDictionary

# Считывает JSON файл в словарь.
def ReadJSON(Path: str) -> dict:
	# Словарь для преобразования.
	JSON = dict()

	# Открытие и чтение файла JSON.
	with open(Path, encoding = "utf-8") as FileRead:
		JSON = json.load(FileRead)

	return JSON

# Удаляет теги HTML из строки, а также преобразует спецсимволы HTML в Unicode.
def RemoveHTML(TextHTML: str) -> str:
	# Конвертирование спецсимволов HTML в Unicode.
	TextHTML = html.unescape(TextHTML)
	# Регулярное выражение фильтрации тегов HTML.
	TagsHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	# Удаление найденных по регулярному выражению тегов.
	CleanText = re.sub(TagsHTML, '', str(TextHTML))

	return str(CleanText)

# Удаляет из строки подряд идущие повторяющиеся подстроки.
def RemoveRecurringCharacters(String: str, Substring: str) -> str:

	# Пока в строке находятся повторы указанного символа, удалять их.
	while Substring + Substring in String:
		String = String.replace(Substring + Substring, Substring)

	return String

# Удаляет из строки все вхождения подстрок, совпадающие с регулярным выражением.
def RemoveRegexSubstring(String: str, Regex: str) -> str:
	# Поиск всех совпадений.
	RegexSubstrings = re.findall(Regex, String)

	# Удаление каждой подстроки.
	for RegexSubstring in RegexSubstrings:
		String = String.replace(RegexSubstring, "")

	return String

# Переименовывает ключ в словаре, сохраняя исходный порядок.
def RenameDictionaryKey(Dictionary: dict, OldKey: str, NewKey: str) -> dict:
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

# Выключает ПК.
def Shutdown():
	if sys.platform in ["linux", "linux2"]:
		os.system("sudo shutdown now")
	elif sys.platform == "win32":
		os.system("shutdown /s")

# Сохраняет стилизованный JSON файл.
def WriteJSON(Path: str, Dictionary: dict):
	with open(Path, "w", encoding = "utf-8") as FileWrite:
		json.dump(Dictionary, FileWrite, ensure_ascii = False, indent = '\t', separators = (",", ": "))