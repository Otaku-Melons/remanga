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

		# Подсчёт количества всех возможных позиций.
		self.__MaxArgc = len(self.__FlagsPositions) + len(self.__KeysPositions) * 2

		# Подсчёт аргументов.
		self.__MaxArgc += len(self.__Arguments)

	def __CalculateMinArgc(self):
		"""
		Подсчитывает минимальное количество аргументов.
		"""

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

	def addArgument(self, Type: ArgumentType = ArgumentType.All, Important: bool = False):
		"""
		Добавляет аргумент к команде.
			Type – тип аргумента;
			Important – является ли аргумент обязательным.
		"""

		# Запись аргумента в описание команды.
		self.__Arguments.append({"type": Type, "important": Important})
		# Вычисление максимального и минимального количества аргументов.
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	def addFlagPosition(self, Flags: list, Important: bool = False):
		"""
		Добавляет позицию для флага к команде.
			Flags – список названий флагов;
			Important – является ли флаг обязательным.
		"""

		# Запись позиции ключа в описание команды.
		self.__FlagsPositions.append({"names": Flags, "important": Important})
		# Вычисление максимального и минимального количества аргументов. 
		self.__CalculateMaxArgc()
		self.__CalculateMinArgc()

	def addKeyPosition(self, Keys: list, Types: list[ArgumentType] | ArgumentType, Important: bool = False):
		"""
		Добавляет позицию для ключа к команде.
			Keys – список названий ключей;
			Types – список типов значений для конкретных ключей или один тип для всех значений;
			Important – является ли ключ обязательным.
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
		self.__KeysPositions.append({"names": Keys, "types": Types, "important": Important})
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

	def __CheckFlags(self, CommandDescription: Command) -> list:
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

	def __CheckKeys(self, CommandDescription: Command) -> dict:
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

	def __CheckArgument(self, CommandDescription: Command) -> str:
		"""
		Возвращает значение аргумента.
			CommandDescription – описательная структура команды.
		"""

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
				Flags = self.__CheckFlags(CommandDescription)
				# Проверка активированных ключей.
				Keys = self.__CheckKeys(CommandDescription)
				# Получение аргументов.
				Arguments = self.__CheckArgument(CommandDescription)
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