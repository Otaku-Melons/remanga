# Remanga Parser
**Remanga Parser** – это кроссплатформенный скрипт для получения данных с сайта [Remanga](https://remanga.org/) в формате JSON. Он позволяет записать всю информацию о конкретной манге, а также её главах и содержании глав.

## Порядок установки и использования
1. Загрузить последний релиз. Распаковать.
2. Установить Python версии не старше 3.10. Рекомендуется добавить в PATH.
3. В среду исполнения установить следующие пакеты: [opencv-python-headless](https://github.com/opencv/opencv-python), [scikit-image](https://github.com/scikit-image/scikit-image), [dublib](https://github.com/DUB1401/dublib), [Pillow](https://github.com/python-pillow/Pillow).
```
pip install opencv-python-headless
pip install scikit-image
pip install dublib
pip install Pillow
```
Либо установить сразу все пакеты при помощи следующей команды, выполненной из директории скрипта.
```
pip install -r requirements.txt
```
4. Настроить скрипт путём редактирования _Settings.json_ и _Proxies.json_.
5. Открыть директорию со скриптом в терминале. Можно использовать метод `cd` и прописать путь к папке, либо запустить терминал из проводника.
6. Указать для выполнения главный файл скрипта `rp.py`, передать ему команду вместе с параметрами, нажать кнопку ввода и дождаться завершения работы.

# Консольные команды
```
collect [FLAGS] [KEYS*]
```
Собирает коллекцию из алиасов тайтлов, соответствующих набору фильтров в каталоге [Remanga](https://remanga.org/). Собранные алиасы добавляются в файл _Collection.txt_ в порядке убывания даты публикации.

> [!IMPORTANT]  
> Такие фильтры, как _**page**_ и _**ordering**_ зарезервированы сборщиком и не могут быть использованы.

**Список специфических флагов:**
* _**-f**_ – удаляет содержимое файла коллекции перед записью.

**Список специфических ключей:**
* _**--filters**_ – задаёт набор фильтров из адресной строки, разделённых амперсантом `&` и заключённых в кавычки `"`.
___
```
convert [TARGET*] [SOURCE_FORMAT*] [OUTPUT_FORMAT*]
```
Преобразует внутреннюю структуру JSON файлов определений тайтлов согласно одному из поддерживаемых форматов: [DMP-V1](Examples/DMP-V1.md), [RN-V1](Examples/RN-V1.md), [RN-V2](Examples/RN-V2.md).

**Описание позиций:**
* **TARGET** – цель для конвертирования. Обязательная позиция.
	* Аргумент – имя файла. Можно указывать как с расширением, так и без него.
	* Флаги:
		* _**-all**_ – указывает, что необходимо конвертировать все локальные файлы JSON.
* **SOURCE_FORMAT** – исходный формат. Обязательная позиция.
	* Аргумент – название формата из [списка](Examples/) в любом регистре.
* **OUTPUT_FORMAT** – целевой формат. Обязательная позиция.
	* Аргумент – название формата из [списка](Examples/) в любом регистре.
	* Флаги:
		* _**-auto**_ – берёт название формата из ключа `format` внутри описательного файла JSON.
___
```
get [URL*] [KEYS]
```
Загружает любое изображение с сайта [Remanga](https://remanga.org/).

**Описание позиций:**
* **URL** – ссылка на загружаемое изображение. Обязательная позиция.
	* Аргумент – ссылка на изображение.

**Список специфических ключей:**
* _**--dir**_ – указывает директорию для сохранения файла;
* _**--name**_ – указывает новое название файла (не меняет расширение).
___
```
getcov [MANGA_SLUG*] [FLAGS]
```
Загружает обложки конкретного тайтла, алиас которого передан в качестве аргумента.

**Список специфических флагов:**
* _**-f**_ – включает перезапись уже загруженных обложек.
___
```
manage [FORMAT*] [RULE*]
```
Удаляет или перемещает файлы JSON, формат которых отличается от заданного.

**Описание позиций:**
* **FORMAT** – целевой формат, которому должны принадлежать файлы, остающиеся в директории тайтлов.
	* Аргумент – название формата из [списка](Examples/) в любом регистре.
* **RULE** – правило обработки файлов, не соответствующих заданному формату.
	* Флаги:
		* _**-del**_ – указывает, что файлы JSON, формат которых отличается от заданного, необходимо удалить.
	* Ключи:
		* _**--move**_ – указывает, что файлы JSON, формат которых отличается от заданного, необходимо переместить в указанную директорию.
___
```
parse [TARGET*] [MODE] [FLAGS] [KEYS]
```
Проводит парсинг тайтла с указанным алиасом в JSON формат и загружает его обложки. В случае, если файл тайтла уже существует, дополнит его новыми данными. 

**Описание позиций:**
* **TARGET** – задаёт цель для парсинга. Обязательная позиция.
	* Аргумент – алиас тайтла для парсинга.
	* Флаги:
		* _**-collection**_ – указывает, что список тайтлов для парсинга необходимо взять из файла _Collection.txt_;
		* _**-local**_ – указывает для парсинга все локальные файлы.
* **MODE** – указывает, какие данные необходимо парсить.
	* Флаги:
		* _**-onlydesc**_ – будет произведено обновление только описательных данных тайтла, не затрагивающее ветви перевода и главы.
		
**Список специфических флагов:**
* _**-f**_ – включает перезапись уже загруженных обложек и существующих JSON файлов.

**Список специфических ключей:**
* _**--from**_ – указывает алиас тайтла, с момента обнаружения которого в коллекции тайтлов необходимо начать парсинг.
___
```
proxval [FLAGS]
```
Выполняет валидацию всех установленных прокси и выводит результат на экран.

**Список специфических флагов:**
* _**-f**_ – дополнительно производит сортировку прокси внутри файла определений согласно их статусам валидации.
___
```
repair [FILENAME*] [CHAPTER_ID*]
```
Обновляет и перезаписывает сведения о слайдах конкретной главы в локальном файле.

**Описание позиций:**
* **FILENAME** – имя локального файла, в котором необходимо исправить слайды. Обязательная позиция.
	* Аргумент – имя файла (с расширением или без него).
* **CHAPTER_ID** – ID главы в локальном файле, слайды которой необходимо заново получить с сервера. Обязательная позиция.
	* Ключи:
		* _**--chapter**_ – указывает ID главы.
___
```
unstub
```
Удаляет из всех локальных файлов заглушки обложек, похожие на [фильтры](Source/Filters/), а также сами файлы заглушек.
___
```
update [MODE] [FLAGS] [KEYS]
```
Проводит парсинг тайтлов, в которые за интервал времени, указанный в _Settings.json_, были добавлены новые главы.

**Описание позиций:**
* **MODE** – указывает, какие данные необходимо обновлять. Может принимать следующие значения:
	* Флаги:
		* _**-onlydesc**_ – будет произведено обновление только описательных данных тайтла, не затрагивающее ветви перевода и главы.

**Список специфических флагов:**
* _**-f**_ – включает перезапись уже загруженных обложек и существующих JSON файлов.

**Список специфических ключей:**
* _**--from**_ – указывает алиас тайтла, с момента обнаружения которого в списке обновляемых тайтлов необходимо начать обработку обновлений.

## Неспецифические флаги
Данный тип флагов работает при добавлении к любой команде и выполняет отдельную от оной функцию.
* _**-s**_ – выключает компьютер после завершения работы скрипта.

# Settings.json
```JSON
"authorization-token": ""
```
Токен авторизации аккаунта [Remanga](https://remanga.org/) для доступа к 18+ произведениям. Получить можно из одноимённого поля заголовка GET-запросов на страницах с контентом для взрослых.
___
```JSON
"format": "rn-v2"
```
Задаёт внутреннюю структуру описательных файлов тайтлов. Поддерживаются следующие форматы: [DMP-V1](Examples/DMP-V1.md), [RN-V1](Examples/RN-V1.md), [RN-V2](Examples/RN-V2.md).
___
```JSON
"use-proxy": false
```
Указывает, следует ли использовать прокси-сервера.
___
```JSON
"ru-links": true
```
Для региона РФ выделены отедльные сервера изображений. Если вы находитесь на территории данной страны или используете её прокси, рекомендуется включить данный параметр для преобразования базовых ссылок в русифицированные.
___
```JSON
"check-updates-period": 60
```
Указывает, обновления за какой период времени до запуска скрипта (в минутах) нужно получить.
___
```JSON
"use-id-instead-slug": false
```
При включении данного параметра файлы JSON и директория обложек тайтла будут названы по ID произведения, а не по алиасу. При этом уже существующие данные можно автоматически обновить командой `rp.py update -local`.
___
```JSON
"titles-directory": ""
```
Указывает, куда сохранять JSON-файлы тайтлов. При пустом значении будет создана папка Titles в исполняемой директории скрипта. Рекомендуется оформлять в соответствии с принципами путей в Linux, описанными [здесь](http://cs.mipt.ru/advanced_python/lessons/lab02.html#cd).
___
```JSON
"covers-directory": ""
```
Указывает, куда сохранять обложки тайтлов. При пустом значении будет создана папка _Covers_ в исполняемой директории скрипта. Рекомендуется оформлять в соответствии с принципами путей в Linux, описанными [здесь](http://cs.mipt.ru/advanced_python/lessons/lab02.html#cd).
___
```JSON
"filter-covers": true
```
Переключает режим фильтрации заглушек для тайтлов, не имеющих собственных обложек. В активном состоянии похожие на [шаблоны](Source/Filters/) обложки не будут сохранены и добавлены в JSON.
___
```JSON
"delay": 1
```
Задаёт интервал в секундах для паузы между GET-запросами к серверу.
___
```JSON
"tries": 1
```
Указывает, сколко раз проводить повторные попытки при ошибке выполнения запроса.

# Proxies.json
```JSON
"example": [
	{
		"https": "http://{USER_NAME}:{PASSWORD}@{IP}:{PORT}"
	},
	{
		"https": "{IP}:{PORT}"
	}
]
```
Указывает два примера настройки для публичного и приватного (требующего логин и пароль) прокси-серверов. Не влияет на работу скрипта.

> [!WARNING]  
> Несмотря на использование протокола HTTPS, в ключе прокси-сервера необходимо прописывать «_http://_». Это связано с особенностями обработки прокси в библиотеке [requests](https://github.com/psf/requests).
___
```JSON
"proxies": []
```
Задаёт указанные пользователем прокси-сервера для использования скриптом. При ошибках валидации, проводящейся перед каждым запросом, записи могут быть перемещены в нижеописанные разделы.
___
```JSON
"forbidden-proxies": []
```
Сюда помещаются прокси, вызывающие ошибку 403 или срабатывание капчи CloudFlare при обращении к серверу [Remanga](https://remanga.org/).
___
```JSON
"invalid-proxies": []
```
Сюда помещаются прокси, по той или иной причине не годящиеся для установления стабильной связи с сервером или отказавшие в доступе при валидации.

_Copyright © DUB1401. 2022-2024._
