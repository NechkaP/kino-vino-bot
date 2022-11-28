import aiohttp
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import typing as tp
import os
import sqlite3
import numpy.random as rnd
from aiogram.types.inline_keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from urllib.parse import quote, quote_plus


WELCOME = "Просто напиши мне название фильма на русском или английском языке"
HELP = """
✨Привет! Я ламповый бот Кино+Вино, который создан, чтобы скрасить твой вечер✨

Вот команды, которые ты можешь мне отправлять:
/help - чтобы снова увидеть это сообщение
/vinishko - чтобы я просто посоветовал тебе напиток, без кино
/history - чтобы посмотреть историю запросов
/stats - чтобы я напомнил тебе, какие фильмы предлагал
/popular - чтобы узнать, информацию и ссылки для просмотра каких фильмов чаще всего запрашивали другие

Ну, и самое главное: просто напиши название фильма, о котором хочешь узнать, и я найду для тебя информацию и ссылку на него.
И напиток посоветую, исходя из жанра🍷

Надеюсь, мы подружимся✨
"""
FOUND = "Что-то из этого, да?"
NOT_FOUND = "Хм... сложновато. Может, лучше выпить? Например... "
CANCEL = "Спасибо за фидбек, записал себе. Попробуем поискать другое?"

genre_map = {'мелодрама': 'А к мелодраме рекомендуем...',
             'комедия': 'К такой комедии прекрасно подойдет...',
             'драма': 'Кстати, как насчет бокальчика...',
             'ужасы': 'Ну, тут поможет только...',
             'семейный': 'О, кажется, вам можно пить только...',
             'приключения': 'Приключенческий фильм прекрасно сочетается с...',
             'фантастика': 'Фантастика и этот напиток сочетаются фантастически: ',
             'мультфильм': 'Сегодня мы пьем...',
             'аниме': 'Такая же классика, как и...',
             'триллер': 'Ну, тут поможет только...',
             'военный': 'Ну, тут поможет только...',
             'документальный': 'Такая же классика, как и...',
             'исторический': 'Такая же классика, как и...',
             'криминал': 'Кстати, как насчет бокальчика...',
             'биография': 'Кстати, как насчет бокальчика...',
             'детектив': 'Детектив прекрасно сочетается с...',
             'фэнтези': 'Сегодня мы пьем...'
             }

vinishko_types = {'мелодрама': 'розовое вино',
                  'комедия': 'певасик',
                  'драма': 'красного?',
                  'ужасы': 'валерьянка',
                  'семейный': 'шампусик',
                  'приключения': 'мартини',
                  'фантастика': 'белое вино',
                  'мультфильм': 'милкшейк',
                  'аниме': 'певасик',
                  'триллер': 'валерьянка',
                  'военный': 'валерьянка',
                  'документальный': 'виски',
                  'исторический': 'коньяк',
                  'криминал': 'красного?',
                  'биография': 'белого?',
                  'детектив': 'коньяк',
                  'фэнтези': 'милкшейк'
                  }

vinishko_map = {'мелодрама': 'https://kubnews.ru/upload/iblock/3df/3df60460fcb6641cf250cb32f75f8ff1.jpg',
                'комедия': 'https://tehcovet.ru/wp-content/uploads/2021/03/scale_1200.jpg',
                'драма': 'https://ispaniainfo.ru/wp-content/uploads/2017/06/ispanskoe-vino.jpg',
                'ужасы': 'https://irecommend.ru/sites/default/files/imagecache/copyright1/user-images/684619/kbJndTeyNXFNbWn9DWR3g.jpg',
                'семейный': 'https://forumsamogon.ru/wp-content/uploads/9/1/1/91149ad5d97353ab569f3aa157f9c3c2.jpg',
                'приключения': 'https://forumsamogon.ru/wp-content/uploads/7/3/4/734b73f3a402048f84e303da1c4bd11e.jpeg',
                'фантастика': 'https://images.luxuryescapes.com/lux-group/image/upload/f_auto,fl_progressive,q_auto:best/55ugan49bi6aeiytuyzi3',
                'мультфильм': 'https://www.culture.ru/storage/images/8f159f230c34aba58ad85ccb5b74518a/5a67027142fea96ef45274e2c1fb7b71.jpeg',
                'аниме': 'https://tehcovet.ru/wp-content/uploads/2021/03/scale_1200.jpg',
                'триллер': 'https://irecommend.ru/sites/default/files/imagecache/copyright1/user-images/684619/kbJndTeyNXFNbWn9DWR3g.jpg',
                'военный': 'https://irecommend.ru/sites/default/files/imagecache/copyright1/user-images/684619/kbJndTeyNXFNbWn9DWR3g.jpg',
                'документальный': 'https://roblawson.com/wp-content/uploads/2015/11/Lifestyle_Dubliner_On_The_Rocks_w2.jpg',
                'исторический': 'https://s00.yaplakal.com/pics/pics_original/3/9/7/10623793.jpg',
                'криминал': 'https://ispaniainfo.ru/wp-content/uploads/2017/06/ispanskoe-vino.jpg',
                'биография': 'https://images.luxuryescapes.com/lux-group/image/upload/f_auto,fl_progressive,q_auto:best/55ugan49bi6aeiytuyzi3',
                'детектив': 'https://s00.yaplakal.com/pics/pics_original/3/9/7/10623793.jpg',
                'фэнтези': 'https://www.culture.ru/storage/images/8f159f230c34aba58ad85ccb5b74518a/5a67027142fea96ef45274e2c1fb7b71.jpeg'
               }


class DBHelper:
    def __init__(self, dbname="cinemabot_database.sqlite"):
        self.dbname = dbname
        self.conn = sqlite3.connect(dbname)

    def setup(self):
        stmt = "CREATE TABLE IF NOT EXISTS items (query text, user_id text)"
        self.conn.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS stats (film_id text)"
        self.conn.execute(stmt)
        self.conn.commit()
        stmt = "CREATE TABLE IF NOT EXISTS user_stats (film_id text, user_id text)"
        self.conn.execute(stmt)
        self.conn.commit()

    def add_query(self, query, user_id):
        stmt = "INSERT INTO items (query, user_id) VALUES (?, ?)"
        args = (query, user_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def increment_film(self, film_id):
        stmt = "INSERT INTO stats (film_id) VALUES (?)"
        args = (film_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def increment_film_for_user(self, film_id, user_id):
        stmt = "INSERT INTO user_stats (film_id, user_id) VALUES (?, ?)"
        args = (film_id, user_id, )
        self.conn.execute(stmt, args)
        self.conn.commit()

    def get_queries(self, user_id):
        stmt = "SELECT query FROM items WHERE user_id = (?)"
        args = (user_id, )
        return [x[0] for x in self.conn.execute(stmt, args)]

    def get_stats(self):
        stmt = "SELECT film_id, COUNT(*) as cnt FROM stats GROUP BY film_id ORDER BY cnt LIMIT 10"
        args = ()
        return [x for x in self.conn.execute(stmt, args)]

    def get_user_stats(self, user_id):
        stmt = "SELECT film_id, COUNT(*) as cnt FROM user_stats WHERE user_id = (?) GROUP BY film_id ORDER BY cnt LIMIT 10"
        args = (user_id, )
        return [x for x in self.conn.execute(stmt, args)]


db = DBHelper()
bot = Bot(
    token=os.environ['BOT_TOKEN']
)
memory_storage = MemoryStorage()
dp = Dispatcher(bot, storage=memory_storage)


class FindFilm(StatesGroup):
    waiting_for_particular_film = State()


@dp.message_handler(commands=['start'], state='*')
async def send_welcome(message: types.Message) -> None:
    await bot.send_message(message.from_user.id, WELCOME)


@dp.message_handler(commands=['help'], state='*')
async def send_help(message: types.Message) -> None:
    await bot.send_message(message.from_user.id, HELP)


def vinishko_advice(film_json: tp.Optional[tp.Dict[str, tp.Any]] = None) -> tp.Tuple[str, str, str]:
    vino = None
    wine_url = None
    if film_json and len(film_json.get('genres', [])):
        k = rnd.randint(0, len(film_json.get('genres', [])))
        tries = 0
        while not (film_json.get('genres', [])[0]['genre'].lower() in genre_map.keys() or tries > 10):
            tries += 1
            k = rnd.randint(0, len(film_json.get('genres', [])))
        if film_json.get('genres', [])[0]['genre'].lower() in genre_map.keys():
            vino1 = genre_map[film_json.get('genres', [])[k]['genre'].lower()]
            vino2 = vinishko_types[film_json.get('genres', [])[k]['genre'].lower()]
            wine_url = vinishko_map[film_json.get('genres', [])[k]['genre'].lower()]
        else:
            k = rnd.randint(0, len(genre_map.keys()))
            random_wine = list(genre_map.keys())[k]
            vino1 = "Сегодня, кстати, хороший день, чтобы выпить"
            vino2 = vinishko_types[random_wine]
            wine_url = vinishko_map[random_wine]
    else:
        k = rnd.randint(0, len(genre_map.keys()))
        random_wine = list(genre_map.keys())[k]
        vino1 = genre_map[random_wine]
        vino2 = vinishko_types[random_wine]
        wine_url = vinishko_map[random_wine]
    return vino1, vino2, wine_url


@dp.message_handler(commands=['vinishko'], state='*')
async def send_vinishko(message: types.Message) -> None:
    vinishko1, vinishko2, pic = vinishko_advice()
    await bot.send_message(message.from_user.id, 'Сегодня я рекомендую тебе выпить...')
    await bot.send_message(message.from_user.id, vinishko2)
    await bot.send_photo(message.from_user.id, pic)


@dp.message_handler(commands=['history'], state='*')
async def send_history(message: types.Message) -> None:
    hist = list(reversed(db.get_queries(user_id=message.from_user.id)))
    response = ''
    cnt = 10
    for item in hist:
        if not cnt:
            break
        response = item + '\n' + response
        cnt -= 1
    await bot.send_message(message.from_user.id, response)


@dp.message_handler(commands=['popular'], state='*')
async def send_stats(message: types.Message) -> None:
    stat = db.get_stats()
    response = ''
    for item in stat:
        response = str(item[0]) + ' - ' + str(item[1]) + ' раз\n' + response
    if len(response):
        response = 'Наши пользователи больше всего интересовались: \n\n' + response
        await bot.send_message(message.from_user.id, response)
    else:
        await bot.send_message(message.from_user.id, 'Кажется, пока нет популярных фильмов')


@dp.message_handler(commands=['stats'], state='*')
async def send_user_stats(message: types.Message) -> None:
    stat = db.get_user_stats(message.from_user.id)
    response = ''
    for item in stat:
        response = str(item[0]) + ' - ' + str(item[1]) + ' раз\n' + response
    if len(response):
        response = 'Я предлагал тебе вот эти фильмы чаще всего, может, уже посмотришь? \n\n' + response
        await bot.send_message(message.from_user.id, response)
    else:
        await bot.send_message(message.from_user.id, 'Кажется, мы пока маловато общались')


def construct_description(film_json: tp.Dict[str, tp.Any]) -> str:
    name_ru = film_json.get('nameRu', '')
    name_en = film_json.get('nameEn', '')
    description = film_json.get('description', '-')
    year = film_json.get('year', '-')
    countries = ', '.join([c['country'] for c in film_json.get('countries', [])])
    length = film_json.get('filmLength', '-')
    genres = ', '.join([g['genre'] for g in film_json.get('genres', '')])
    rating = film_json.get('rating', '-')

    film_encoded = quote(name_ru)

    return f"""{name_ru}, {name_en}

{genres}
{countries}
Год: {year}
Рейтинг Кинопоиска: {rating}/10
Продолжительность: {length}

Описание: {description}
"""


def source_choice(film_name: str) -> InlineKeyboardMarkup:
    film_encoded = quote(film_name)

    kb = InlineKeyboardMarkup(row_width=2)
    rich = InlineKeyboardButton('Посмотрим на ivi!', url=f"https://www.ivi.ru/search/?q={film_encoded}")
    pirate = InlineKeyboardButton('Неа, я пират☠️‍', url=f"http://baskino.me/index.php?do=search&mode=advanced&subaction=search&story={film_encoded}")
    kb.row(rich, pirate)

    return kb


def film_choice(response_json: tp.Dict[str, tp.Any]) -> (InlineKeyboardMarkup, tp.List[tp.Any]):
    kb = InlineKeyboardMarkup(row_width=1)
    films_json = response_json.get('films')
    films = []
    film_names = []
    for i, film_json in enumerate(films_json):
        film = None
        if i >= 3:
            break
        try:
            names = [film_json.get('nameRu', ''), film_json.get('nameEn', ''), film_json.get('year', '')]
            film = ', '.join([name for name in names if name is not None and len(name) > 0])
        except:
            pass
        if film:
            button = InlineKeyboardButton(film, callback_data=f"film {i}")
            kb.add(button)
            films.append(film_json)
            film_names.append(film)

    cancel = InlineKeyboardButton('Неа, все не то :(', callback_data="film cancel")
    kb.add(cancel)

    return kb, films, film_names


@dp.callback_query_handler(state=FindFilm.waiting_for_particular_film)
async def film_choice_callback_handler(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    code = callback_query.data.split()[-1]

    if code == 'cancel':
        await state.finish()
        await bot.send_message(callback_query.from_user.id, CANCEL)
    else:
        try:
            film_id = int(code)
        except ValueError:
            assert False, "invalid film id"

        data = await state.get_data()
        film_json = data['films'][film_id]
        db.increment_film(film_json.get('nameRu', ''))

        await bot.send_photo(callback_query.from_user.id, film_json.get('posterUrl', ''))
        kb = source_choice(film_json.get('nameRu', film_json.get('nameEn', '')))
        await bot.send_message(callback_query.from_user.id, construct_description(film_json), reply_markup=kb)
        vinishko1, vinishko2, pic = vinishko_advice(film_json)
        await bot.send_message(callback_query.from_user.id, vinishko1)
        await bot.send_message(callback_query.from_user.id, vinishko2)
        await bot.send_photo(callback_query.from_user.id, pic)
        await FindFilm.next()

    await callback_query.answer()


async def film2info(film: str) -> tp.Dict[str, tp.Any]:
    film_encoded = quote_plus(film)
    url = f"https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword?keyword={film_encoded}"
    headers = {'accept': 'application/json', 'X-API-KEY': os.environ['KINOPOISK_TOKEN']}

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as r:
            json_body = await r.json()
            return json_body


@dp.message_handler(state='*')
async def find_films_by_name(message: types.Message, state: FSMContext) -> None:
    film: str = message.text.lower().replace(',', '').replace(':', '').replace('?', '').replace('.', '').replace('!', '')
    db.add_query(film, message.from_user.id)
    response_json: tp.Dict[str, tp.Any] = await film2info(film)
    if response_json.get('pagesCount', 0) == 0:
        film_first_word = film.split(' ')[0]
        if film_first_word != film:
            response_json: tp.Dict[str, tp.Any] = await film2info(film_first_word)
            if response_json.get('pagesCount', 0) == 0:
                await bot.send_message(message.from_user.id, NOT_FOUND)
                vinishko1, vinishko2, pic = vinishko_advice()
                await bot.send_message(message.from_user.id, vinishko2)
                await bot.send_photo(message.from_user.id, pic)
                return
        else:
            await bot.send_message(message.from_user.id, NOT_FOUND)
            vinishko1, vinishko2, pic = vinishko_advice()
            await bot.send_message(message.from_user.id, vinishko2)
            await bot.send_photo(message.from_user.id, pic)
            return

    kb, films, film_names = film_choice(response_json)
    for film in film_names:
        db.increment_film_for_user(film, message.from_user.id)
    await FindFilm.waiting_for_particular_film.set()
    await state.update_data(films=films)
    await bot.send_message(message.from_user.id, FOUND, reply_markup=kb)


def main():
    db.setup()
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
