from dublib.Exceptions.StyledPrinter import DuplicatedStyles

import enum

class Styles:
	"""
	Содержит два контейнера: для декораций и стилей.
	"""

	class Color(enum.Enum):
		"""
		Контейнер цветов.
		"""

		Black = "0"
		Red = "1"
		Green = "2"
		Yellow = "3"
		Blue = "4"
		Purple = "5"
		Cyan = "6"
		White = "7"

	class Decoration(enum.Enum):
		"""
		Контейнер декораций.
		"""

		Bold = "1"
		Faded = "2"
		Italic = "3"
		Underlined = "4"
		Flashing = "5"
		Throughline = "9"
		DoubleUnderlined = "21"
		Framed = "51"
		Surrounded = "52"
		Upperlined = "53"

class StylesGroup:
	"""
	Предоставляет возможность комбинировать стили для их однократной инициализации и повторного использования.
	При интерпретации в str() предоставляет строковый маркер стилей.
	"""

	def __init__(self, Decorations: list[Styles.Decoration] = list(), TextColor: Styles.Color | None = None, BackgroundColor: Styles.Color | None = None):
		"""
		Конструктор: строит маркер стилей.
			Decorations – список декораций;
			TextColor – цвет текста;
			BackgroundColor – цвет фона.
		"""

		# Маркер стилей строки.
		self.StyleMarkers = "\033["

		# Добавить каждую декорацию.
		for Decoration in Decorations:
			self.StyleMarkers += Decoration + ";"

		# Если передан цвет для текста, то создать соответствующий литерал.
		if TextColor != None:
			self.StyleMarkers += "3" + TextColor.value + ";"

		# Если передан цвет для фона, то создать соответствующий литерал.
		if BackgroundColor != None:
			self.StyleMarkers += "4" + BackgroundColor.value + ";"

		# Постановка завершающего символа маркировки и добавление строки.
		self.StyleMarkers = self.StyleMarkers.rstrip(';') + "m"

	def __str__(self):
		return self.StyleMarkers

def StyledPrinter(Text: str, Styles: StylesGroup | None = None, Decorations: list[Styles.Decoration] = list(), TextColor: Styles.Color | None = None, BackgroundColor: Styles.Color | None = None, Autoreset: bool = True, Newline: bool = True):
	"""
	Выводит в терминал цветной и стилизованный текст с возможностью отключения автоматического сброса стилей к стандартным и перехода на новую строку.
		Text – обрабатываемая строка;
		Styles – контейнер стилей;
		Decorations – список декораций;
		TextColor – цвет текста;
		BackgroundColor – цвет фона;
		Autoreset – сбрасывать ли стили к стандартным после завершения вывода;
		Newline – переходить ли на новую строку после завершения вывода.

		Примечание: не используйте одновременно группу стилей и отдельные стили, так как это приводит к ошибке переопределения.
	"""
		
	# Указатель новой строки.
	End = "\n" if Newline == True else ""

	# Генерация форматированного текста.
	Text = TextStyler(Text, Styles, Decorations, TextColor, BackgroundColor, Autoreset)

	# Если указано, добавить модификатор сброса стилей после вывода.
	if Autoreset == True:
		Text += "\033[0m"

	# Вывод в консоль: стилизованный текст.
	print(Text, end = End)

def TextStyler(Text: str, Styles: StylesGroup | None = None, Decorations: list[Styles.Decoration] = list(), TextColor: Styles.Color | None = None, BackgroundColor: Styles.Color | None = None, Autoreset: bool = True) -> str:
	"""
	Возвращает стилизованный текст.
		Text – обрабатываемая строка;
		Styles – контейнер стилей;
		Decorations – список декораций;
		TextColor – цвет текста;
		BackgroundColor – цвет фона;
		Autoreset – сбрасывать ли стили к стандартным после завершения вывода.

		Примечание: не используйте одновременно группу стилей и отдельные стили, так как это приводит к ошибке переопределения.
	"""
		
	# Маркер стилей строки.
	StyleMarkers = None

	# Если не указана группа стилей.
	if Styles == None:
		# Инициализация маркера стилей строки.
		StyleMarkers = "\033["

		# Добавить каждую декорацию.
		for Decoration in Decorations:
			StyleMarkers += Decoration + ";"

		# Если передан цвет для текста, то создать соответствующий литерал.
		if TextColor != None:
			StyleMarkers += "3" + TextColor.value + ";"

		# Если передан цвет для фона, то создать соответствующий литерал.
		if BackgroundColor != None:
			StyleMarkers += "4" + BackgroundColor.value + ";"

		# Постановка завершающего символа маркировки и добавление строки.
		StyleMarkers = StyleMarkers.rstrip(';') + "m"

	# Если указана и группа стилей, и стили по отдельности.
	elif Styles != None and Decorations != list() or TextColor != None or BackgroundColor != None:
		raise DuplicatedStyles()

	# Если указана группа стилей.
	else:
		# Запись маркера стилей строки.
		StyleMarkers = str(Styles)

	# Добавление стилей к строке.
	Text = StyleMarkers + Text

	# Если указано, добавить модификатор сброса стилей после вывода.
	if Autoreset == True:
		Text += "\033[0m"

	return Text

