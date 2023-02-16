from random_user_agent.params import SoftwareName, OperatingSystem
from random_user_agent.user_agent import UserAgent

# Усекает число до определённого количества знаков после запятой.
def ToFixedFloat(FloatNumber, Digits = 0):
	return float(f"{FloatNumber:.{Digits}f}")

# Проевращает число секунд в строку-дескриптор времени по формату [<x> hours <y> minuts <z> seconds].
def SecondsToTimeString(Seconds):
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

# Возвращает случайное значение заголовка User-Agent.
def GetRandomUserAgent():
	SoftwareNames = [SoftwareName.CHROME.value]
	OperatingSystems = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]   
	UserAgentRotator = UserAgent(software_names = SoftwareNames, operating_systems = OperatingSystems, limit = 100)

	return str(UserAgentRotator.get_random_user_agent()).strip('"')
