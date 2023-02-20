from random_user_agent.params import SoftwareName, OperatingSystem
from random_user_agent.user_agent import UserAgent

import random
import time

# Возвращает случайное значение заголовка User-Agent.
def GetRandomUserAgent() -> str:
	SoftwareNames = [SoftwareName.CHROME.value]
	OperatingSystems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
	UserAgentRotator = UserAgent(software_names = SoftwareNames, operating_systems = OperatingSystems, limit = 100)

	return str(UserAgentRotator.get_random_user_agent()).strip('"')

# Объединяет список списков в один список.
def MergeListOfLists(ListOfLists: list) -> list:
	
	# Если список не пустой и включает списки, то объединить.
	if len(ListOfLists) > 0 and type(ListOfLists[0]) is list:
		# Результат объединения.
		Result = list()

		# Объединить все списки в один список.
		for List in ListOfLists:
			Result.extend(List)

		return Result
	# Если список включет словари, то вернуть без изменений.
	else:
		return ListOfLists

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber: float, Digits: int = 0) -> float:
	return float(f"{FloatNumber:.{Digits}f}")

# Проевращает число секунд в строку-дескриптор времени по формату [<x> hours <y> minuts <z> seconds].
def SecondsToTimeString(Seconds: float) -> str:
	# Количество часов.
	Hours = int(Seconds / 3600.0)
	Seconds -= Hours * 3600
	# Количество минут.
	Minutes = int(Seconds / 60.0)
	Seconds -= Minutes * 60
	# Количество секунд.
	Seconds = ToFixedFloat(Seconds, 2)
	# Строка-дескриптор времени.
	TimeString = ""

	# Генерация строки.
	if Hours > 0:
		TimeString += str(Hours) + " hours "
	if Minutes > 0:
		TimeString += str(Minutes) + " minutes "
	if Seconds > 0:
		TimeString += str(Seconds) + " seconds"

	return TimeString

# Выжидает согласно заданному интервалу.
def Wait(Settings: dict):
	time.sleep(random.randint(Settings["min-delay"], Settings["max-delay"]))