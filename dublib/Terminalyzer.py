from dublib.Exceptions.Terminalyzer import *
from urllib.parse import urlparse

import enum
import sys

# Перечисление: типы аргументов.
class ArgumentType(enum.Enum):

	#==========================================================================================#
	# >>>>> СТАТИЧЕСКИЕ СВОЙСТВА <<<<< #
	#==========================================================================================#

	All = "@all"
	Number = "@number"
	Text = "@text"
	URL = "@url"
	Unknown = None
	
# Контейнер команды.
class Command:

	# Подсчитывает максимальное количество аргументов.
	def __CalculateMaxArgc(self):
		# Обнуление значения.
		self.__MaxArgc = 0

		# Подсчёт количества всех возможных позиций.
		self.__MaxArgc = len(self.__FlagsPositions) + len(self.__KeysPositions) * 2

		# Подсчёт аргументов.
		self.__MaxArgc += len(self.__Arguments)

	# Подсчитывает минимальное количество аргументов.
	def __CalculateMinArgc(self):
		# Обнуление значения.
		self.__MinArgc = 0
		
		# Подсчёт важных позиций флагов.
		for FlagPosition in self.__FlagsPositions:
			if FlagPosition["important"] == True:
				self.__MinArgc += 1
				
		# Подсчёт важных позиций ключей.
		for Key in self.__KeysPositions:
			if Key["important"] == True:
				self.__MinArgc += 2
				
		# Подсчёт важных аргументов.
		for Argument in self.__Arguments:
			if Argument["important"] == True:
				self.__MinArgc += 1
				
	# Конструктор: задаёт название команды.
	def __init__(self, Name: str):

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

	# Добавляет аргумент к команде.
	def addArgument(self, Type: ArgumentType = ArgumentType.All, Important: bool = False):
		# Запись аргумента в описание команды.
		self.__Arguments.append({"type": Type, "important": Important})
		# Вычисление максимального и минимального количества аргументов.
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	# Добавляет позицию для флага к команде.
	def addFlagPosition(self, Flags: list, Important: bool = False):
		# Запись позиции ключа в описание команды.
		self.__FlagsPositions.append({"names": Flags, "important": Important})
		# Вычисление максимального и минимального количества аргументов. 
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	# Добавляет позицию для ключа к команде.
	def addKeyPosition(self, Keys: list, Types: list[ArgumentType] | ArgumentType, Important: bool = False):

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
		self.__KeysPositions.append({"names": Keys, "types": Types, "important": Important})
		# Вычисление максимального и минимального количества аргументов. 
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	# Возвращает список аргументов.
	def getArguments(self) -> list:
		return self.__Arguments

	# Возвращает индикатор флага.
	def getFlagIndicator(self) -> str:
		return self.__FlagIndicator

	# Возвращает список позиций флагов.
	def getFlagsPositions(self) -> list:
		return self.__FlagsPositions

	# Возвращает индикатор ключа.
	def getKeyIndicator(self) -> str:
		return self.__KeyIndicator

	# Возвращает список ключей.
	def getKeysPositions(self) -> list:
		return self.__KeysPositions

	# Возвращает максимальное количество аргументов.
	def getMaxArgc(self) -> int:
		return self.__MaxArgc

	# Возвращает минимальное количество аргументов.
	def getMinArgc(self) -> int:
		return self.__MinArgc

	# Возвращает название команды.
	def getName(self) -> str:
		return self.__Name

	# Задаёт индикатор флага.
	def setFlagIndicator(self, FlagIndicator: str):

		# Если новый индикатор флага не повторяет индикатор ключа.
		if FlagIndicator != self.__KeyIndicator:
			self.__FlagIndicator = FlagIndicator

	# Задаёт индикатор ключа.
	def setKeyIndicator(self, KeyIndicator: str):

		# Если новый индикатор ключа не повторяет индикатор флага.
		if KeyIndicator != self.__FlagIndicator:
			self.__KeyIndicator = KeyIndicator

# Контейнер данных проверки команды.
class CommandData:

	# Конструктор: задаёт списки активированных флагов и ключей, значения ключей и аргумента.
	def __init__(self, Name: str, Flags: list[str] = list(), Keys: list[str] = list(), Values: dict[str, str] = dict(), Arguments: list[str] = list()):

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

	# Преобразователь: представляет содержимое класса как строку.
	def __str__(self):
		return str({
			"name": self.Name, 
			"flags": self.Flags, 
			"keys": self.Values, 
			"arguments": self.Arguments
		})

# Обработчик консольных аргументов.
class Terminalyzer():

	# Проверяет соответвтсие количества аргументов.
	def __CheckArgc(self, CommandDescription: Command):

		# Если аргументов слишком много.
		if len(self.__Argv) - 1 > CommandDescription.getMaxArgc():
			raise TooManyArguments(" ".join(self.__Argv))

		# Если аргументов слишком мало.
		if len(self.__Argv) - 1 < CommandDescription.getMinArgc():
			raise NotEnoughArguments(" ".join(self.__Argv))

	# Возвращает список активных флагов.
	def __CheckFlags(self, CommandDescription: Command) -> list:
		# Список позиций флагов.
		FlagsPositions = CommandDescription.getFlagsPositions()
		# Индикатор флага.
		FlagIndicator = CommandDescription.getFlagIndicator()
		# Список активных флагов.
		Flags = list()

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

					else:
						raise MutuallyExclusiveFlags(" ".join(self.__Argv))

		return Flags

	# Возвращает словарь активных ключей и их содержимое.
	def __CheckKeys(self, CommandDescription: Command) -> dict:
		# Список позиций ключей.
		KeysPositions = CommandDescription.getKeysPositions()
		# Индикатор ключа.
		KeyIndicator = CommandDescription.getKeyIndicator()
		# Словарь статусов ключей.
		Keys = dict()

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

					else:
						raise MutuallyExclusiveKeys(" ".join(self.__Argv))

		return Keys

	# Возвращает значение аргумента.
	def __CheckArgument(self, CommandDescription: Command) -> str:
		# Значения аргументов.
		Values = list()
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

			# Если аргумент соответствует типу.
			if self.__CheckArgumentType(FreeArguments[Index], ArgumentsDescription[Index]["type"]) == True:
				Values.append(FreeArguments[Index])

			else:
				raise InvalidArgumentType(FreeArguments[Index], CommandDescription.getArguments()["type"])

		return Values
		
	# Проверяет значение аргумента.
	def __CheckArgumentType(self, Value: str, Type: ArgumentType = ArgumentType.All) -> bool:
		
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

	# Проверяет соответствие названия команды.
	def __CheckName(self, CommandDescription: Command) -> bool:
		if CommandDescription.getName() == self.__Argv[0]:
			return True

		return False

	# Конструктор.
	def __init__(self):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Список задействованных позиций.
		self.__PositionsStatuses = list()
		# Переданные аргументы.
		self.__Argv = sys.argv[1:]
		# Кэшированные данные команды.
		self.__CommandData = None
		
	# Задаёт команду для проверки. Возвращает результат проверки.
	def checkCommand(self, CommandDescription: Command) -> CommandData | None:

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
				Flags = self.__CheckFlags(CommandDescription)
				# Проверка активированных ключей.
				Keys = self.__CheckKeys(CommandDescription)
				# Получение аргументов.
				Arguments = self.__CheckArgument(CommandDescription)
				# Данные проверки команды.
				self.__CommandData = CommandData(Name, Flags, list(Keys.keys()), Keys, Arguments)

			return self.__CommandData

		return None

	# Задаёт команды для проверки. Возвращает результат проверки.
	def checkCommands(self, CommandsDescriptions: list[Command]) -> CommandData | None:

		# Для каждой проверяемой команды.
		for CurrentCommand in CommandsDescriptions:
			
			# Если название команды соответствует.
			if self.__CheckName(CurrentCommand) == True:
				
				# Если данные команды не кэшированы.
				if self.__CommandData == None:
					# Заполнение статусов позиций аргументов.
					self.__PositionsStatuses = [False] * (len(self.__Argv) - 1)
					# Проверка соответствия количества аргументов.
					self.__CheckArgc(CurrentCommand)
					# Получение названия команды.
					Name = CurrentCommand.getName()
					# Проверка активированных флагов.
					Flags = self.__CheckFlags(CurrentCommand)
					# Проверка активированных ключей.
					Keys = self.__CheckKeys(CurrentCommand)
					# Проверка присутствия аргумента.
					Arguments = self.__CheckArgument(CurrentCommand)
					# Данные проверки команды.
					self.__CommandData = CommandData(Name, Flags, list(Keys.keys()), Keys, Arguments)

				return self.__CommandData

		return None