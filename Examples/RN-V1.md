# RN-V1
**RN-V1** – это нативный формат парсера [Remanga](https://remanga.org/), который практически полностью соответствует сегментам JSON-структур, получаемых при взаимодействии с API сайта.

# Основные принципы
* _**Исходные категории**_ – ID жанров и тегов, как и названия оных, определяются согласно таковым в источнике.
* _**Контейнеры страниц**_ – группы слайдов (страницы) вынесены из списков для упрощения работы со структурой.
* _**Максимальное соответствие**_ – все поля и их типы максимально соответствуют JSON-структурам сайта.
* _**Рудиментарные сведения**_ – формат содержит большое количество устаревших полей и бесполезных данных.
* _**Статусы**_ – статусы и их ID полностью соответствуют таковым на сайте.
* _**Типизация**_ – типы тайтлов и их ID полностью соответствуют таковым на сайте.

# Пример
```json
{
	"id": 123,
	"img": {
		"high": "/media/titles/manga-name/high_cover.jpg",
		"mid": "/media/titles/the-magic-kingdom-of-the-gods/mid_cover.jpg",
		"low": "/media/titles/the-magic-kingdom-of-the-gods/low_cover.jpg"
	},
	"en_name": "Manga name",
	"rus_name": "Название манги",
	"another_name": "漫画名 / Mangamei",
	"dir": "manga-name",
	"description": "<p>Первый абзац описания.</p>\r\n\r\n<p>Второй абзац описания.</p>",
	"issue_year": 1970,
	"avg_rating": "0.0",
	"admin_rating": "0.0",
	"count_rating": 0,
	"age_limit": 0,
	"status": {
		"id": 1,
		"name": "Продолжается"
	},
	"count_bookmarks": 0,
	"total_votes": 0,
	"total_views": 0,
	"type": {
		"id": 1,
		"name": "Манга"
	},
	"genres": [
		{
			"id": 1,
			"name": "Название жанра"
		}
	],
	"categories": [
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
	"can_post_comments": true,
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
	"is_yaoi": false,
	"is_erotic": false,
	"chapters": {
		"456": [
			{
				"id": 10,
				"rated": false,
				"viewed": null,
				"is_bought": false,
				"is_free_today": false,
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
				"index": 0,
				"tome": 1,
				"chapter": "1",
				"name": "",
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
}
























{
	"format": "dmp-v1",
	"site": "remanga.org",
	"id": 0,
	"slug": "",
	"covers": [
		{
			"link": "",
			"filename": "",
			"width": 0,
			"height": 0
		}
	],
	"ru-name": "",
	"en-name": "",
	"another-names": "",
	"type": "",
	"age-rating": 0,
	"publication-year": 0,
	"status": "",
	"description": "",
	"is-licensed": false,
	"genres": [
		{
			"id": 0,
			"name": ""
		}
	],
	"tags": [
		{
			"id": 0,
			"name": ""
		}
	],
	"branches": [
		{
			"id": 0,
			"chapters-count": 0
		}
	],
	"content": {
		"0": [
			{
				"id": 0,
				"number": 0,
				"volume": 0,
				"name": "",
				"is-paid": false,
				"translator": "",
				"slides": [
					{
						"index": 1,
						"link": "",
						"width": 0,
						"height": 0
					}
				]
				
			}
		]
	} 
}
```