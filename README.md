# remanga
**remanga** – это модуль системы управления парсерами [Melon](https://github.com/Otaku-Melons/Melon), включающий поддержку источника: [Remanga](https://remanga.org/).

## Коллекция
Таблица поддерживаемых ключей для `melon collect`.
| Ключ | Поддержка | Описание |
|---|---|---|
| **&#x2011;&#x2011;period** | ✅ | Период, за который нужно получить обновления (в часах). |
| **&#x2011;&#x2011;filters** | ✅ | Строка запроса из URL каталога с параметрами фильтрации. **page** и **ordering** необходимо исключить, поскольку они зарезревированы парсером. |
| **&#x2011;&#x2011;pages** | ✅ | Количество страниц каталога, с которых нужно получить данные. |

# Дополнительные настройки
Данный раздел описывает специфичные для этого парсера настройки.
___
```JSON
"token": ""
```
Токен аккаунта [Remanga](https://remanga.org/).
___
```JSON
"ru_links": false
```
Сайт имеет два типа ссылок на слайды: для РФ и для других стран. Данная настройка позволяет выбрать, какой регион вы будете использовать для доступа к контенту.
___
```JSON
"unstub": false
```
Включает фильтрацию заглушек обложек. Дополнительные фильтры по формату можно добавлять в эту [директорию](Filters/).
___
```JSON
"add_free_publication_date": false
```
Указывает, нужно ли в информацию о главе добавлять дату бесплатной публикации.