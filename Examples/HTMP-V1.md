# HTMP-V1
**HTMP-V1** – это формат для частичной совместимости с нативным форматом парсера сайта [Remanga](https://remanga.org/).

# Основные принципы
* _**Единая ветвь**_ – формат нацелен на обновление конкретной ветви перевода и не хранит содержимое других ветвей.
* _**Исходные жанры и теги**_ – ID жанров и тегов, как и названия оных, определяются согласно таковым в источнике.
* _**Номер страницы**_ – на [Remanga](https://remanga.org/) некоторыен слайды группируются, потому имеют одинаковые номера страницы.
* _**Рудиментарные сведения**_ – формат содержит большое количество устаревших полей и бесполезных данных.
* _**Статусы**_ – имеются следующие типы статусов: _COMPLETED_, _ACTIVE_, _ABANDONED_, _NOT_FOUND_, _LICENSED_.
* _**Типизация**_ – имеются следующие типы тайтлов: _MANGA_, _MANHWA_, _MANHUA_, _WESTERN_COMIC_, _RUS_COMIC_, _INDONESIAN_COMIC_, _ANOTHER_.

# Пример
```json
{
	"format": "htmp-v1",
	"site": "remanga.org",
	"id": 123,
	"img": {
		"high": "covers_folder/high_cover.jpg",
		"mid": "covers_folder/mid_cover.jpg",
		"low": "covers_folder/low_cover.jpg"
	},
	"engTitle": "Manga name",
	"rusTitle": "Название манги",
	"alternativeTitle": "漫画名 / Mangamei",
	"slug": "manga-slug",
	"desc": "<p>Первый абзац описания.</p>\r\n\r\n<p>Второй абзац описания.</p>",
	"issue_year": 1970,
	"branchId": 456,
	"admin_rating": "0.0",
	"count_rating": 0,
	"age_limit": 0,
	"status": "ACTIVE",
	"count_bookmarks": 0,
	"total_votes": 0,
	"total_views": 0,
	"type": "MANGA",
	"genres": [
		{
			"id": 1,
			"name": "Название жанра"
		}
	],
	"tags": [
		{
			"id": 1,
			"name": "Название тега"
		}
	],
	"bookmark_type": null,
	"branches": [
		{
			"id": 456,
			"img": "/media/publishers/1/low_cover.jpg",
			"subscribed": false,
			"total_votes": 0,
			"count_chapters": 1,
			"publishers": [
				{
					"id": 1,
					"name": "Название команды переводчиков",
					"img": "/media/publishers/1/low_cover.jpg",
					"dir": "1",
					"tagline": "Описание команды.",
					"type": "Переводчик"
				}
			]
		}
	],
	"count_chapters": 1,
	"first_chapter": {
		"id": 10,
		"tome": 1,
		"chapter": "1"
	},
	"continue_reading": null,
	"is_licensed": false,
	"newlate_id": null,
	"newlate_title": null,
	"related": null,
	"uploaded": 0,
	"isHomo": false,
	"adaptation": null,
	"publishers": [
		{
			"id": 1,
			"name": "Название команды переводчиков",
			"img": "/media/publishers/1/low_cover.jpg",
			"dir": "1",
			"tagline": "Описание команды.",
			"type": "Переводчик"
		}
	],
	"chapters": [
		{
			"id": 10,
			"rated": null,
			"viewed": null,
			"is_bought": null,
			"publishers": [],
			"index": 1,
			"tom": 1,
			"chapter": 1,
			"title": "",
			"price": null,
			"score": 0,
			"upload_date": "1970-01-01T00:00:00.000000",
			"pub_date": null,
			"is_paid": false,
			"slides": [
				{
					"id": 1,
					"link": "https://link_to_slide/01.jpg",
					"page": 1,
					"height": 720,
					"width": 1280,
					"count_comments": 0
				}
			]
		}
	]
}
```

# Примечания
1. Другие названия тайтла отделяются сочетанием символов ` / ` (пробел-слеш-пробел).