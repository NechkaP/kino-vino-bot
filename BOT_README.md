## @cinema_by_NechkaP_bot
### Описание
✨Привет! Я ламповый бот Кино+Вино, который создан, чтобы скрасить твой вечер✨

Вот команды, которые ты можешь мне отправлять:

* /help - чтобы снова увидеть это сообщение

* /vinishko - чтобы я просто посоветовал тебе напиток, без кино

* /history - чтобы посмотреть историю запросов

* /stats - чтобы я напомнил тебе, какие фильмы предлагал

* /popular - чтобы узнать, информацию и ссылки для просмотра каких фильмов чаще всего запрашивали другие


Ну, и самое главное: просто напиши название фильма, о котором хочешь узнать, и я найду для тебя информацию и ссылку на него.
И напиток посоветую, исходя из жанра🍷

Надеюсь, мы подружимся✨

### Реализация
Для поиска фильмов использовалось неофициальное API Кинопоиска, вот оно:
https://kinopoiskapiunofficial.tech/documentation/api/

База данных написана на SQLite, создается прямо внутри программы, состоит из трех таблиц:
* items (query text, user_id) - для хранения запросов пользователей и ответа на команду /history
* stats (film_id text) - для хранения фильмов, информацию про которые запрашивали пользователи, и ответа на команду /popular
* user_stats (film_id text, user_id) - для хранения фильмов, которые советовали пользователю, и ответа на команду /stats

Развернут на AWS из Docker-контейнера.

### "Фишка" бота
Состоит в том, что он советует еще и напитки, и картиночку кидает. 
Случайным образом по команде /vinishko (потому что рифмуется с кинишком), а к фильмам в зависимости от жанра

### Запуск бота
Осуществляется командой 

    `BOT_TOKEN <your_token> KINOPOISK_TOKEN <your_kinopoisk_token> cinemabot.py`
