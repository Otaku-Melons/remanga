# RN-V2
**RN-V2** – это клон [DMP-V1](DMP-V1.md) с расширенной поддержкой данных сайта [Remanga](https://remanga.org/). В дополнение к описанным в базовом формате свойствам и полям модифицированный содержит:

* Время публикации платных глав в бесплатный доступ, если задан таймер (в формате **ISO 8601**: _YYYY-MM-DDTHH:MM:SS_).

# Пример
```json
{
	"format": "rn-v2",
	"site": "remanga.org",
	"id": 123,
	"slug": "123-manga-name",
	"covers": [
		{
			"link": "https://link_to_cover/high_cover.jpg",
			"filename": "high_cover.jpg",
			"width": 480,
			"height": 640
		},
		{
			"link": "https://link_to_cover/mid_cover.jpg",
			"filename": "mid_cover.jpg",
			"width": 360,
			"height": 480
		},
		{
			"link": "https://link_to_cover/low_cover.jpg",
			"filename": "low_cover.jpg",
			"width": 240,
			"height": 360
		}
	],
	"ru-name": "Название манги",
	"en-name": "Manga name",
	"another-names": [
		"漫画名",
		"Mangamei"
	],
	"author": null,
	"publication-year": 2023,
	"age-rating": 0,
	"description": "Первый абзац описания.\nВторой абзац описания.",
	"type": "MANGA",
	"status": "ONGOING",
	"is-licensed": false,
	"series": [],
	"genres": [
		"название жанра"
	],
	"tags": [
		"название тега"
	],
	"branches": [
		{
			"id": 456,
			"chapters-count": 1
		}
	],
	"chapters": {
		"456": [
			{
				"id": 10,
				"number": 1,
				"volume": 1,
				"name": "Название главы",
				"is-paid": false,
				"free-publication-date": "1970-01-01T00:00:00",
				"translator": "Никнейм переводчика",
				"slides": [
					{
						"index": 1,
						"link": "https://link_to_slide/01.jpg",
						"width": 720,
						"height": 1280
					}
				]
				
			}
		]
	} 
}
```