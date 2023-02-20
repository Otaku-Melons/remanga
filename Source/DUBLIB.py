import sys
import os
import re

#==========================================================================================#
# >>>>> КЛАССЫ <<<<< #
#==========================================================================================#

# Вывод в консоль цветного текста.
class ColoredPrinter(object):
	
	# Конструктор.
	def __init__(self):
		# Базовые цвета.
		self.BLACK = "0"
		self.RED = "1"
		self.GREEN = "2"
		self.YELLOW = "3"
		self.BLUE = "4"
		self.PURPLE = "5"
		self.CYAN = "6"
		self.WHITE = "7"
		# Переключатель: возвращать ли стандартные настройки после каждого вывода.
		self.ResetStylesAfterPrint = True
		# Переключатель: переход на новую строку после вывода.
		self.NewLineAfterPrint = False

	# Вывод в консоль.
	def Print(self, Text: str, TextColor: str, BackgroundColor: str = ""):
		# Если передан цвет для фота, то создать соответствующий модификатор.
		if BackgroundColor != "":
			BackgroundColor = "\033[4" + BackgroundColor + "m"
		# Генерация модификатора цвета текста.
		TextColor = "\033[3" + TextColor + "m"
		# Создание результирующей строки со стилями: цветового модификатора, модификатора фона, текста.
		StyledText = TextColor + BackgroundColor + Text
		# Если указано, добавить модификатор сброса стилей после вывода.
		if self.ResetStylesAfterPrint == True:
			StyledText = StyledText + "\033[0m"
		# Вывод в консоль и установка параметра перехода на норвую строку.
		if self.NewLineAfterPrint == True:
			print(StyledText, end = "")
		else:
			print(StyledText)

#==========================================================================================#
# >>>>> ФУНКЦИИ <<<<< #
#==========================================================================================#

# Очищает консоль.
def Cls():
	os.system('cls' if os.name == 'nt' else 'clear')

# Переименовывает ключ в словаре, сохраняя исходный порядок.
def RenameDictKey(Dictionary: dict, OldKey: str, NewKey: str) -> dict:
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

# Удаляет теги HTML из строки.
def RemoveHTML(TextHTML: str) -> str:
	# Регулярное выражение фильтрации тегов HTML.
	TagsHTML = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	# Удаление найденных по регулярному выражению тегов.
	CleanText = re.sub(TagsHTML, '', str(TextHTML))

	return str(CleanText)

# Выключает ПК: работает на Windows и Linux.
def Shutdown():
	if sys.platform == "linux" or sys.platform == "linux2":
		os.system("sudo shutdown now")
	elif sys.platform == "win32":
		os.system("shutdown /s")
