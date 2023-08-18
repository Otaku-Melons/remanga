from dublib.Exceptions.Terminalyzer import *
from urllib.parse import urlparse

import enum
import sys

class ArgumentType(enum.Enum):
	"""
	Перечисление типов аргументов.
	"""

	All = "@all"
	Number = "@number"
	Text = "@text"
	URL = "@url"
	Unknown = None
	
class Command:
	"""
	Контейнер для описания команды.
	"""

	def __CalculateMaxArgc(self):
		"""
		Подсчитывает максимальное количество аргументов.
		"""

		# Обнуление значения.
		self.__MaxArgc = 0

		# Подсчитать все позиции флагов, не лежащие на слоях.
		for FlagsPostionIngex in range(0, len(self.__FlagsPositions)):
			if self.__FlagsPositions[FlagsPostionIngex]["layout-index"] == None:
				self.__MaxArgc += 1
				
		# Подсчитать все позиции ключей, не лежащие на слоях.
		for KeysPostionIngex in range(0, len(self.__KeysPositions)):
			if self.__KeysPositions[KeysPostionIngex]["layout-index"] == None:
				self.__MaxArgc += 2

		# Подсчёт аргументов.
		self.__MaxArgc += len(self.__Arguments)

		# Подсчёт слоёв.
		for LayoutIndex in self.__Layouts.keys():
			
			# Если в слое есть ключи.
			if self.__Layouts[LayoutIndex]["keys"] > 0:
				self.__MaxArgc += 2
			else:
				self.__MaxArgc += 1

	def __CalculateMinArgc(self):
		"""
		Подсчитывает минимальное количество аргументов.
		"""

		# Обнуление значения.
		self.__MinArgc = 0
		
		# Подсчитать все важные позиции флагов, не лежащие на слоях.
		for FlagsPostionIngex in range(0, len(self.__FlagsPositions)):
			if self.__FlagsPositions[FlagsPostionIngex]["layout-index"] == None and self.__FlagsPositions[FlagsPostionIngex]["important"] == True:
				self.__MinArgc += 1
				
		# Подсчитать все важные позиции ключей, не лежащие на слоях.
		for KeysPostionIngex in range(0, len(self.__KeysPositions)):
			if self.__KeysPositions[KeysPostionIngex]["layout-index"] == None and self.__KeysPositions[KeysPostionIngex]["important"] == True:
				self.__MinArgc += 2
				
		# Подсчитать все важные аргументы, не лежащие на слоях.
		for Argument in self.__Arguments:
			if Argument["layout-index"] == None and Argument["important"] == True:
				self.__MinArgc += 1
				
		# Подсчёт важных слоёв.
		for LayoutIndex in self.__Layouts.keys():
			
			# Если в важном слое есть ключи.
			if self.__Layouts[LayoutIndex]["important"] == True and self.__Layouts[LayoutIndex]["flags"] > 0 or self.__Layouts[LayoutIndex]["arguments"] > 0 :
				self.__MinArgc += 1
				
	def __InitializeLayout(self, LayoutIndex: int):
		"""
		Инициализирует описательную структуру слоя.
			LayoutIndex – индекс слоя.
		"""
		
		# Преобразование индекса слоя в строку.
		LayoutIndex = str(LayoutIndex)

		# Инициализация описательной структуры слоя.
		if LayoutIndex not in self.__Layouts.keys():
			self.__Layouts[LayoutIndex] = {"arguments": 0, "flags": 0, "keys": 0, "important": False}
				
	def __SetLayoutAsImportant(self, ImportantLayoutIndex: int):
		"""
		Устанавливает для всех параметров одного слоя обязательное наличие.
			ImportantLayoutIndex – индекс слоя для простановки обязательного наличия.
		"""
		
		# Установка важности слоя.
		self.__Layouts[str(ImportantLayoutIndex)]["important"] = True
		
		# Для каждой позиции флага проверить наличие обязательного слоя.
		for FlagPositionIndex in range(len(self.__FlagsPositions)):
			if self.__FlagsPositions[FlagPositionIndex]["layout-index"] == ImportantLayoutIndex and self.__FlagsPositions[FlagPositionIndex]["important"] == False:
				self.__FlagsPositions[FlagPositionIndex]["important"] = True
				
		# Для каждой позиции ключа проверить наличие обязательного слоя.
		for KeyPositionIndex in range(len(self.__KeysPositions)):
			if self.__KeysPositions[KeyPositionIndex]["layout-index"] == ImportantLayoutIndex and self.__KeysPositions[KeyPositionIndex]["important"] == False:
				self.__KeysPositions[KeyPositionIndex]["important"] = True
				
		# Для каждого аргумента проверить наличие обязательного слоя.
		for ArgumentIndex in range(len(self.__Arguments)):
			if self.__Arguments[ArgumentIndex]["layout-index"] == ImportantLayoutIndex and self.__Arguments[ArgumentIndex]["important"] == False:
				self.__Arguments[ArgumentIndex]["important"] = True
	
	def __init__(self, Name: str):
		"""
		Конструктор.
			Name – название команды.
		"""

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Список флагов.
		self.__FlagsPositions = list()
		# Список ключей.
		self.__KeysPositions = list()
		# Индикатор ключа.
		self.__KeyIndicator = "--"
		# Индикатор флага.
		self.__FlagIndicator = "-"
		# Список аргументов.
		self.__Arguments = list()
		# Название команды.
		self.__Name = Name
		# Максимальное количество аргументов.
		self.__MaxArgc = 0
		# Минимальное количество аргументов.
		self.__MinArgc = 0
		# Словарь, предоставляющий список слоёв и количество параметров на них.
		self.__Layouts = dict()

	def addArgument(self, Type: ArgumentType = ArgumentType.All, Important: bool = False, LayoutIndex: int | None = None):
		"""
		Добавляет аргумент к команде.
			Type – тип аргумента;
			Important – является ли аргумент обязательным;
			LayoutIndex – индекс слоя, на который помещается аргумент.
		"""
		
		# Запись аргумента в описание команды.
		self.__Arguments.append({"type": Type, "important": Important, "layout-index": LayoutIndex})

		# Если задан обязательный слой.
		if LayoutIndex != None:
			# Инициализация слоя.
			self.__InitializeLayout(LayoutIndex)
			# Установка обязательного наличия для остальных аргументов на слое.
			self.__SetLayoutAsImportant(LayoutIndex)	
			# Инкремент количества аргументов на слое.
			self.__Layouts[str(LayoutIndex)]["arguments"] += 1

		# Вычисление максимального и минимального количества аргументов.
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	def addFlagPosition(self, Flags: list, Important: bool = False, LayoutIndex: int | None = None):
		"""
		Добавляет позицию для флага к команде.
			Flags – список названий флагов;
			Important – является ли флаг обязательным;
			LayoutIndex – индекс слоя, на который помещается флаг.
		"""
		
		# Запись позиции ключа в описание команды.
		self.__FlagsPositions.append({"names": Flags, "important": Important, "layout-index": LayoutIndex})
		
		# Если задан обязательный слой.
		if LayoutIndex != None:
			# Инициализация слоя.
			self.__InitializeLayout(LayoutIndex)
			# Установка обязательного наличия для остальных позиций на слое.
			self.__SetLayoutAsImportant(LayoutIndex)	
			# Инкремент количества флагов на слое.
			self.__Layouts[str(LayoutIndex)]["flags"] += 1

		# Вычисление максимального и минимального количества аргументов. 
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	def addKeyPosition(self, Keys: list, Types: list[ArgumentType] | ArgumentType, Important: bool = False, LayoutIndex: int | None = None):
		"""
		Добавляет позицию для ключа к команде.
			Keys – список названий ключей;
			Types – список типов значений для конкретных ключей или один тип для всех значений;
			Important – является ли ключ обязательным;
			LayoutIndex – индекс слоя, на который помещается ключ.
		"""
		
		# Если для всех значений установлен один тип аргумента.
		if type(Types) == ArgumentType:
			# Буфер заполнения.
			Bufer = list()

			# На каждый ключ продублировать тип значения.
			for Type in Keys:
				Bufer.append(Types)

			# Замена аргумента буфером.
			Types = Bufer 

		# Запись позиции ключа в описание команды.
		self.__KeysPositions.append({"names": Keys, "types": Types, "important": Important, "layout-index": LayoutIndex})

		# Если задан обязательный слой.
		if LayoutIndex != None:
			# Инициализация слоя.
			self.__InitializeLayout(LayoutIndex)
			# Установка обязательного наличия для остальных позиций на слое.
			self.__SetLayoutAsImportant(LayoutIndex)	
			# Инкремент количества ключей на слое.
			self.__Layouts[str(LayoutIndex)]["keys"] += 1

		# Вычисление максимального и минимального количества аргументов. 
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	def getArguments(self) -> list:
		"""
		Возвращает список аргументов.
		"""

		return self.__Arguments

	def getFlagIndicator(self) -> str:
		"""
		Возвращает индикатор флага.
		"""

		return self.__FlagIndicator

	def getFlagsPositions(self) -> list:
		"""
		Возвращает список позиций флагов.
		"""

		return self.__FlagsPositions

	def getKeyIndicator(self) -> str:
		"""
		Возвращает индикатор ключа.
		"""

		return self.__KeyIndicator

	def getKeysPositions(self) -> list:
		"""
		Возвращает список ключей.
		"""

		return self.__KeysPositions

	def getMaxArgc(self) -> int:
		"""
		Возвращает максимальное количество аргументов.
		"""

		return self.__MaxArgc

	def getMinArgc(self) -> int:
		"""
		Возвращает минимальное количество аргументов.
		"""

		return self.__MinArgc
 
	def getName(self) -> str:
		"""
		Возвращает название команды.
		"""

		return self.__Name

	def setFlagIndicator(self, FlagIndicator: str):
		"""
		Задаёт индикатор флага.
			FlagIndicator – индикатор флага.
		"""

		# Если новый индикатор флага не повторяет индикатор ключа.
		if FlagIndicator != self.__KeyIndicator:
			self.__FlagIndicator = FlagIndicator

	def setKeyIndicator(self, KeyIndicator: str):
		"""
		Задаёт индикатор ключа.
			KeyIndicator – индикатор ключа.
		"""

		# Если новый индикатор ключа не повторяет индикатор флага.
		if KeyIndicator != self.__FlagIndicator:
			self.__KeyIndicator = KeyIndicator

class CommandData:
	"""
	Контейнер для хранения данных используемой команды.
	"""

	def __init__(self, Name: str, Flags: list[str] = list(), Keys: list[str] = list(), Values: dict[str, str] = dict(), Arguments: list[str] = list()):
		"""
		Конструктор.
			Name – название команды;
			Flags – список активированных флагов;
			Keys – список активированных ключей;
			Values – словарь значений активированных ключей;
			Arguments – список аргументов.
		"""

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Значение аргумента.
		self.Arguments = Arguments
		# Словарь значений ключей.
		self.Values = Values
		# Список активированных флагов.
		self.Flags = Flags
		# Список активированных ключей.
		self.Keys = Keys
		# Название команды.
		self.Name = Name

	def __str__(self):
		return str({
			"name": self.Name, 
			"flags": self.Flags, 
			"keys": self.Values, 
			"arguments": self.Arguments
		})

class Terminalyzer:
	"""
	Обработчик консольных аргументов.
	"""

	def __CheckArgc(self, CommandDescription: Command):
		"""
		Проверяет соответвтсие количества аргументов.
			CommandDescription – описательная структура команды.
		"""

		# Если аргументов слишком много.
		if len(self.__Argv) - 1 > CommandDescription.getMaxArgc():
			raise TooManyArguments(" ".join(self.__Argv))

		# Если аргументов слишком мало.
		if len(self.__Argv) - 1 < CommandDescription.getMinArgc():
			raise NotEnoughArguments(" ".join(self.__Argv))
	
	def __CheckArguments(self, CommandDescription: Command) -> list[str] | list[int]:
		"""
		Возвращает значения аргументов.
			CommandDescription – описательная структура команды.
		"""
		
		# Значения аргументов.
		Values = list()
		# Список слоёв аргументов.
		ArgumentsLayouts = list()
		# Список возможных аргументов.
		ArgumentsDescription = CommandDescription.getArguments()
		# Количество важных аргументов.
		ImportantArgumentsCount = 0
		# Список незадействованных позиций.
		FreeArguments = list()
		# Список аргументов без команды.
		ArgumentsList = self.__Argv[1:]
		
		# Подсчитать количество важных аргументов.
		for Argument in ArgumentsDescription:
			if Argument["important"] == True:
				ImportantArgumentsCount += 1

		# Получить не задействованные позиции команды.
		for PositionIndex in range(0, len(ArgumentsList)):
			if self.__PositionsStatuses[PositionIndex] == False:
				FreeArguments.append(ArgumentsList[PositionIndex])

		# Для каждого незадействованного аргумента.
		for Index in range(0, len(FreeArguments)):

			# Если количество свободных аргументов не превышает максимальное.
			if len(FreeArguments) <= len(ArgumentsDescription):
				
				# Если аргумент соответствует типу.
				if self.__CheckArgumentType(FreeArguments[Index], ArgumentsDescription[Index]["type"]) == True:
					# Сохранение значения аргумента.
					Values.append(FreeArguments[Index])
				
					# Если для аргумента задан слой.
					if ArgumentsDescription[Index]["layout-index"] != None:
						ArgumentsLayouts.append(ArgumentsDescription[Index]["layout-index"])

				else:
					raise InvalidArgumentType(FreeArguments[Index], CommandDescription.getArguments()["type"])
				
			else:
				raise TooManyArguments(" ".join(self.__Argv))

		return Values, ArgumentsLayouts
	
	def __CheckArgumentType(self, Value: str, Type: ArgumentType = ArgumentType.All) -> bool:
		"""
		Проверяет значение аргумента.
			Value – значение аргумента;
			Type – тип аргумента.
		"""
		
		# Если требуется проверить специфический тип аргумента.
		if Type != ArgumentType.All:
			
			# Если аргумент должен являться числом.
			if Type == ArgumentType.Number:

				# Если вся строка, без учёта отрицательного знака, не является числом.
				if Value.lstrip('-').isdigit() == False:
					raise InvalidArgumentType(Value, "ArgumentType.Number")

			# Если аргумент должен являться набором букв.
			if Type == ArgumentType.Text:

				# Если строка содержит небуквенные символы.
				if Value.isalpha() == False:
					raise InvalidArgumentType(Value, "ArgumentType.Text")

			# Если аргумент должен являться URL.
			if Type == ArgumentType.URL:

				# Если строка не является URL.
				if bool(urlparse(Value).scheme) == False:
					raise InvalidArgumentType(Value, "ArgumentType.URL")

		return True

	def __CheckFlags(self, CommandDescription: Command) -> list[str] | list[int]:
		"""
		Возвращает список активных флагов.
			CommandDescription – описательная структура команды.
		"""

		# Список позиций флагов.
		FlagsPositions = CommandDescription.getFlagsPositions()
		# Индикатор флага.
		FlagIndicator = CommandDescription.getFlagIndicator()
		# Список активных флагов.
		Flags = list()
		# Список слоёв флагов.
		FlagsLayouts = list()

		# Для каждой позиции флага.
		for PositionIndex in range(0, len(FlagsPositions)):
			# Состояние: активирован ли флаг для позиции.
			IsPositionActivated = False

			# Для каждого названия флага на позиции.
			for FlagName in FlagsPositions[PositionIndex]["names"]:

				# Если индикатор с названием флага присутствует в аргументах.
				if FlagIndicator + FlagName in self.__Argv:
					# Установка активного статуса позициям аргументов команды.
					self.__PositionsStatuses[self.__Argv.index(FlagIndicator + FlagName) - 1] = True

					# Если взаимоисключающий флаг на данной позиции не был активирован.
					if IsPositionActivated == False:
						# Задать для флага активный статус.
						Flags.append(FlagName)
						# Заблокировать позицию для активации.
						IsPositionActivated = True
						
						# Если для флага задан слой.
						if FlagsPositions[PositionIndex]["layout-index"] != None:
							FlagsLayouts.append(FlagsPositions[PositionIndex]["layout-index"])

					else:
						raise MutuallyExclusiveFlags(" ".join(self.__Argv))

		return Flags, FlagsLayouts

	def __CheckKeys(self, CommandDescription: Command) -> dict | list[int]:
		"""
		Возвращает словарь активных ключей и их содержимое.
			CommandDescription – описательная структура команды.
		"""

		# Список позиций ключей.
		KeysPositions = CommandDescription.getKeysPositions()
		# Индикатор ключа.
		KeyIndicator = CommandDescription.getKeyIndicator()
		# Словарь статусов ключей.
		Keys = dict()
		# Список слоёв ключей.
		KeysLayouts = list()
		
		# Для каждой позиции ключа.
		for PositionIndex in range(0, len(KeysPositions)):
			# Состояние: активирован ли ключ для позиции.
			IsPositionActivated = False

			# Для каждого названия ключа на позиции.
			for KeyIndex in range(0, len(KeysPositions[PositionIndex]["names"])):
				# Название ключа.
				KeyName = KeysPositions[PositionIndex]["names"][KeyIndex]

				# Если индикатор с названием ключа присутствует в аргументах.
				if KeyIndicator + KeyName in self.__Argv:
					# Установка активного статуса позициям аргументов команды.
					self.__PositionsStatuses[self.__Argv.index(KeyIndicator + KeyName) - 1] = True
					self.__PositionsStatuses[self.__Argv.index(KeyIndicator + KeyName)] = True

					# Если взаимоисключающий ключ на данной позиции не был активирован.
					if IsPositionActivated == False:
						# Задать для ключа значение.
						Keys[KeyName] = self.__Argv[self.__Argv.index(KeyIndicator + KeyName) + 1]
						# Заблокировать позицию для активации.
						IsPositionActivated = True

						# Проверить тип значения ключа.
						self.__CheckArgumentType(Keys[KeyName], KeysPositions[PositionIndex]["types"][KeyIndex])
						
						# Если для ключа задан слой.
						if KeysPositions[PositionIndex]["layout-index"] != None:
							KeysLayouts.append(KeysPositions[PositionIndex]["layout-index"])

					else:
						raise MutuallyExclusiveKeys(" ".join(self.__Argv))

		return Keys, KeysLayouts
	
	def __CheckLayoutsCollision(self, FlagsLayouts: list[int], KeysLayouts: list[int], ArgumentsLayouts: list[int]):
		"""
		Проверяет коллизию слоёв аргументов.
			FlagsLayouts – список индексов слоёв активированных флагов;
			KeysLayouts – список индексов слоёв активированных ключей;
			ArgumentsLayouts – список индексов слоёв аргументов.
		"""
		
		# Список повторяющихся индексов слоёв.	
		LayeringIndexes = list()
		# Проверка коллизии флагов.
		LayeringIndexes += list(set(FlagsLayouts) & set(KeysLayouts))
		LayeringIndexes += list(set(FlagsLayouts) & set(ArgumentsLayouts))
		# Проверка коллизии ключей.
		LayeringIndexes += list(set(KeysLayouts) & set(FlagsLayouts))
		LayeringIndexes += list(set(KeysLayouts) & set(ArgumentsLayouts))
		# Проверка коллизии флагов.
		LayeringIndexes += list(set(ArgumentsLayouts) & set(FlagsLayouts))
		LayeringIndexes += list(set(ArgumentsLayouts) & set(KeysLayouts))
		
		# Пройтись по результатам всех проверок.
		for Element in LayeringIndexes:
			if Element != []:
				raise MutuallyExclusivePositions(" ".join(self.__Argv))
		
	def __CheckName(self, CommandDescription: Command) -> bool:
		"""
		Проверяет соответствие названия команды.
			CommandDescription – описательная структура команды.
		"""
	
		if CommandDescription.getName() == self.__Argv[0]:
			return True

		return False

	def __init__(self):
		"""
		Конструктор.
		"""

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Список задействованных позиций.
		self.__PositionsStatuses = list()
		# Переданные аргументы.
		self.__Argv = sys.argv[1:]
		# Кэшированные данные команды.
		self.__CommandData = None
		
	def checkCommand(self, CommandDescription: Command) -> CommandData | None:
		"""
		Задаёт команду для проверки. Возвращает результат проверки.
			CommandDescription – описательная структура команды.
		"""

		# Если название команды соответствует.
		if self.__CheckName(CommandDescription) == True:

			# Если данные команды не кэшированы.
			if self.__CommandData == None:
				# Заполнение статусов позиций аргументов.
				self.__PositionsStatuses = [False] * (len(self.__Argv) - 1)
				# Проверка соответствия количества аргументов.
				self.__CheckArgc(CommandDescription)
				# Получение названия команды.
				Name = CommandDescription.getName()
				# Проверка активированных флагов.
				Flags, FlagsLayouts = self.__CheckFlags(CommandDescription)
				# Проверка активированных ключей.
				Keys, KeysLayouts = self.__CheckKeys(CommandDescription)
				# Получение аргументов.
				Arguments, ArgumentsLayouts = self.__CheckArguments(CommandDescription)
				# Проверка коллизии слоёв аргументов.
				self.__CheckLayoutsCollision(FlagsLayouts, KeysLayouts, ArgumentsLayouts)
				# Данные проверки команды.
				self.__CommandData = CommandData(Name, Flags, list(Keys.keys()), Keys, Arguments)

		return self.__CommandData

	def checkCommands(self, CommandsDescriptions: list[Command]) -> CommandData | None:
		"""
		Задаёт список команд для проверки. Возвращает результат проверки.
			CommandDescription – описательная структура команды.
		"""

		# Проверить каждую команду из списка.
		for CurrentCommand in CommandsDescriptions:
			self.checkCommand(CurrentCommand)

		return self.__CommandData