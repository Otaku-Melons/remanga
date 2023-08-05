# Обработчик вывода в терминал цветного текста.
class ColoredPrinter:
	
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

	# Выводит в консоль стилизованный текст.
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