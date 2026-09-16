# -*- coding: utf-8 -*-
"""
Телеграм-бот: приветствие → 4 сообщения → плейлист → 5 вопросов →
финальный выбор → видео → финальное сообщение.

Все тексты и медиа лежат в content.py — правь их там, этот файл трогать не надо.
Запуск:  python bot.py   (нужен BOT_TOKEN в переменных окружения или в .env)
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError, TelegramUnauthorizedError
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.utils.media_group import MediaGroupBuilder

import content as c

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
log = logging.getLogger("bot")

BASE_DIR = Path(__file__).resolve().parent


# ────────────────────────────── состояния ──────────────────────────────

class Flow(StatesGroup):
    greeting = State()        # ждём нажатия «Да»
    story = State()           # 4 сообщения с кнопкой «Далее»
    playlist = State()        # плейлист отправлен, ждём «Далее»
    question = State()        # ждём выбор варианта ответа
    custom_answer = State()   # ждём текст «своего варианта»
    final_choice = State()    # ждём выбор в финальном блоке
    video = State()           # ждём нажатия кнопки под финальным сообщением
    after_video = State()     # видео отправлено, ждём кнопку под ним
    done = State()            # всё пройдено


# ────────────────────────────── хелперы ──────────────────────────────

def kb(*rows: list[InlineKeyboardButton]) -> InlineKeyboardMarkup:
    """Инлайн-клавиатура: каждый аргумент — это ряд кнопок."""
    return InlineKeyboardMarkup(inline_keyboard=[row for row in rows if row])


def btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def resolve_media(value: str | None):
    """
    Превращает значение из content.py в то, что понимает aiogram.

    Возвращает None, если это заглушка (PUT_...) или пустая строка —
    тогда бот вместо файла пришлёт текстовую подсказку.
    """
    if not value:
        return None
    if value.startswith("PUT_"):
        return None
    path = Path(value)
    if not path.is_absolute():
        path = BASE_DIR / value
    if path.exists():
        return FSInputFile(path)
    return value  # file_id или прямая ссылка


async def drop_keyboard(message: Message | None, note: str | None = None) -> None:
    """Убирает кнопки у уже отправленного сообщения, чтобы их не нажали дважды."""
    if message is None:
        return
    try:
        if note:
            await message.edit_text(f"{message.html_text}\n\n<i>{note}</i>")
        else:
            await message.edit_reply_markup(reply_markup=None)
    except Exception:  # сообщение слишком старое / уже изменено — не страшно
        pass


def question_keyboard(index: int) -> InlineKeyboardMarkup:
    """Кнопки вопроса: варианты ответа + «свой вариант»."""
    q = c.QUESTIONS[index]
    rows = [[btn(opt, f"q:{index}:{i}")] for i, opt in enumerate(q["options"])]
    rows.append([btn(q["custom_button"], f"q:{index}:own")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def save_answer(state: FSMContext, key: str, answer: str) -> None:
    """Сохраняет ответ в состояние и пишет в лог (сюда же можно добавить БД/таблицу)."""
    data = await state.get_data()
    answers = dict(data.get("answers", {}))
    answers[key] = answer
    await state.update_data(answers=answers)
    log.info("Ответ (%s): %s", key, answer)


# ────────────────────────────── шаги сценария ──────────────────────────────

async def send_greeting(message: Message, state: FSMContext) -> None:
    await state.set_state(Flow.greeting)
    await state.update_data(answers={})
    await message.answer(
        c.GREETING,
        reply_markup=kb([btn(c.START_BUTTON, "start")]),
    )


async def send_story(message: Message, state: FSMContext, index: int) -> None:
    """Одно из 4 сообщений с кнопкой «Далее»."""
    await state.set_state(Flow.story)
    await state.update_data(story_index=index)

    is_last = index == len(c.STORY_MESSAGES) - 1
    next_data = "playlist" if is_last else f"story:{index + 1}"

    await message.answer(
        c.STORY_MESSAGES[index],
        reply_markup=kb([btn(c.NEXT_BUTTON, next_data)]),
    )


async def send_playlist(message: Message, state: FSMContext) -> None:
    """Отправляет плейлист альбомами (до 10 треков в одном сообщении)."""
    await state.set_state(Flow.playlist)

    # оставляем только песни, у которых указан реальный файл
    songs = [s for s in c.PLAYLIST if resolve_media(s.get("file")) is not None]

    for i in range(0, len(songs), 10):
        chunk = songs[i:i + 10]

        # альбом требует минимум 2 элемента — одиночный трек шлём обычным аудио
        if len(chunk) == 1:
            song = chunk[0]
            try:
                await message.answer_audio(
                    resolve_media(song["file"]),
                    title=song.get("title"),
                    performer=song.get("performer"),
                )
            except Exception as e:
                log.warning("Не удалось отправить песню %s: %s", song.get("title"), e)
            continue

        media = MediaGroupBuilder()
        for song in chunk:
            media.add_audio(
                media=resolve_media(song["file"]),
                title=song.get("title"),
                performer=song.get("performer"),
            )

        try:
            await message.answer_media_group(media=media.build())
        except Exception as e:
            log.warning("Ошибка отправки плейлиста: %s", e)

    await message.answer(
        c.PLAYLIST_CAPTION,
        reply_markup=kb([btn(c.PLAYLIST_NEXT_BUTTON, "q:0:show")]),
    )


async def send_question(message: Message, state: FSMContext, index: int) -> None:
    await state.set_state(Flow.question)
    await state.update_data(question_index=index)
    await message.answer(
        c.QUESTIONS[index]["text"],
        reply_markup=question_keyboard(index),
    )


async def after_question(message: Message, state: FSMContext, index: int) -> None:
    """Сообщение после ответа (если задано) и переход к следующему шагу."""
    after_text = c.QUESTIONS[index].get("after")
    if after_text:
        await message.answer(after_text)

    if index + 1 < len(c.QUESTIONS):
        await send_question(message, state, index + 1)
    else:
        await send_final_choice(message, state)


async def send_final_choice(message: Message, state: FSMContext) -> None:
    """Финальный блок с вариантами ответов."""
    await state.set_state(Flow.final_choice)
    rows = [
        [btn(opt["button"], f"fin:{i}")]
        for i, opt in enumerate(c.FINAL_CHOICE_OPTIONS)
    ]
    await message.answer(
        c.FINAL_CHOICE_TEXT,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows),
    )


async def send_video(message: Message, state: FSMContext) -> None:
    """Видео с кнопкой под ним — финальное сообщение придёт только по нажатию."""
    await state.set_state(Flow.after_video)
    markup = kb([btn(c.AFTER_VIDEO_BUTTON, "after_video")])

    video = resolve_media(c.VIDEO_FILE)
    if video is None:
        await message.answer(
            f"🎬 <i>(заглушка видео: подставь file_id или путь в content.py)</i>\n\n"
            f"{c.VIDEO_CAPTION}",
            reply_markup=markup,
        )
        return

    try:
        await message.answer_video(video, caption=c.VIDEO_CAPTION, reply_markup=markup)
    except Exception as e:
        log.warning("Не удалось отправить видео: %s", e)
        await message.answer(
            f"🎬 Видео не отправилось ({e})\n\n{c.VIDEO_CAPTION}",
            reply_markup=markup,
        )


# ────────────────────────────── хендлеры ──────────────────────────────

dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_greeting(message, state)


@dp.message(Command("restart"))
async def cmd_restart(message: Message, state: FSMContext) -> None:
    await state.clear()
    await send_greeting(message, state)


@dp.callback_query(F.data == "start")
async def on_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await drop_keyboard(call.message)
    await send_story(call.message, state, 0)


@dp.callback_query(F.data.startswith("story:"))
async def on_story(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await drop_keyboard(call.message)
    index = int(call.data.split(":")[1])
    await send_story(call.message, state, index)


@dp.callback_query(F.data == "playlist")
async def on_playlist(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await drop_keyboard(call.message)
    await send_playlist(call.message, state)


@dp.callback_query(F.data == "q:0:show")
async def on_questions_start(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await drop_keyboard(call.message)
    await send_question(call.message, state, 0)


@dp.callback_query(F.data.startswith("q:"))
async def on_question_answer(call: CallbackQuery, state: FSMContext) -> None:
    _, raw_index, choice = call.data.split(":")
    index = int(raw_index)

    if choice == "own":
        # пользователь хочет написать свой вариант
        await call.answer()
        await drop_keyboard(call.message)
        await state.set_state(Flow.custom_answer)
        await state.update_data(question_index=index)
        await call.message.answer(c.CUSTOM_ANSWER_PROMPT)
        return

    option_index = int(choice)
    answer = c.QUESTIONS[index]["options"][option_index]

    await call.answer()
    await drop_keyboard(call.message, note=f"Твой ответ: {answer}")
    await save_answer(state, f"вопрос {index + 1}", answer)
    await after_question(call.message, state, index)


@dp.message(Flow.custom_answer, F.text)
async def on_custom_answer(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    index = int(data.get("question_index", 0))
    await save_answer(state, f"вопрос {index + 1}", message.text)
    await after_question(message, state, index)


@dp.callback_query(F.data.startswith("fin:"))
async def on_final_choice(call: CallbackQuery, state: FSMContext) -> None:
    index = int(call.data.split(":")[1])
    option = c.FINAL_CHOICE_OPTIONS[index]

    await call.answer()
    await drop_keyboard(call.message, note=f"Твой ответ: {option['button']}")
    await save_answer(state, "финальный выбор", option["button"])

    await state.set_state(Flow.video)
    await call.message.answer(
        option["reply"],
        reply_markup=kb([btn(c.FINAL_CHOICE_BUTTON, "video")]),
    )


@dp.callback_query(F.data == "video")
async def on_video(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    await drop_keyboard(call.message)
    await send_video(call.message, state)


@dp.callback_query(F.data == "after_video")
async def on_after_video(call: CallbackQuery, state: FSMContext) -> None:
    """Кнопка под видео: только теперь отправляем финальное сообщение."""
    await call.answer()
    await drop_keyboard(call.message)
    await state.set_state(Flow.done)
    await call.message.answer(c.AFTER_VIDEO_MESSAGE)


def extract_file_id(message: Message) -> tuple[str, str] | tuple[None, None]:
    """Возвращает (тип файла, file_id) для присланного медиа."""
    for kind in ("audio", "video", "voice", "video_note", "animation",
                 "document", "photo", "sticker"):
        obj = getattr(message, kind, None)
        if obj:
            if kind == "photo":
                obj = obj[-1]  # самое большое из превью
            return kind, obj.file_id
    return None, None


async def on_media_sent(message: Message) -> None:
    """Режим SHOW_FILE_ID: присылаешь боту файл — он отвечает его file_id."""
    kind, file_id = extract_file_id(message)
    if not file_id:
        return
    await message.answer(
        f"Тип: <b>{kind}</b>\n"
        f"file_id (нажми, чтобы скопировать):\n\n"
        f"<code>{file_id}</code>\n\n"
        f"<i>Вставь его в content.py. Когда всё вставишь — "
        f"поставь SHOW_FILE_ID = False.</i>"
    )


if c.SHOW_FILE_ID:
    dp.message.register(
        on_media_sent,
        F.audio | F.video | F.voice | F.video_note | F.animation
        | F.document | F.photo | F.sticker,
    )


@dp.message(Flow.done)
async def on_after_done(message: Message, state: FSMContext) -> None:
    await message.answer(c.RESTART_HINT)


@dp.message()
async def on_any_other(message: Message, state: FSMContext) -> None:
    """Пользователь пишет текст там, где ждём нажатия кнопки."""
    current = await state.get_state()
    if current is None:
        await send_greeting(message, state)
    else:
        await message.answer(c.WAIT_FOR_BUTTON)


# ────────────────────────────── запуск ──────────────────────────────

def read_token_from_file(path: Path) -> str:
    """Достаёт BOT_TOKEN из .env-файла (терпим к пробелам, кавычкам и BOM)."""
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().upper() == "BOT_TOKEN":
            return value.strip().strip('"').strip("'")
    return ""


def get_token() -> str:
    """Токен из переменной окружения BOT_TOKEN или из файла .env рядом с bot.py."""
    token = os.getenv("BOT_TOKEN", "").strip()
    source = "переменной окружения BOT_TOKEN"

    if not token:
        # .env.txt — частый случай на Windows, где расширения файлов скрыты
        for name in (".env", ".env.txt"):
            env_file = BASE_DIR / name
            if env_file.exists():
                token = read_token_from_file(env_file)
                source = f"файла {env_file}"
                if token:
                    break

    if not token:
        print(
            "\n"
            "  ❌ НЕ НАЙДЕН ТОКЕН БОТА\n"
            "\n"
            f"  Нужен файл .env вот здесь:\n"
            f"      {BASE_DIR / '.env'}\n"
            "\n"
            "  Внутри одна строка (токен берётся у @BotFather):\n"
            "      BOT_TOKEN=123456789:AAH...\n"
            "\n"
            "  Проверь, что файл называется именно .env, а не .env.txt —\n"
            "  Windows по умолчанию скрывает расширения файлов.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    if ":" not in token or not token.split(":", 1)[0].isdigit():
        print(
            f"\n  ❌ Токен из {source} выглядит неправильно: {token[:12]}...\n"
            "  Он должен быть вида 123456789:AAH... — скопируй его из @BotFather целиком.\n",
            file=sys.stderr,
        )
        sys.exit(1)

    log.info("Токен взят из %s", source)
    return token


async def main() -> None:
    bot = Bot(
        token=get_token(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        me = await bot.get_me()
        log.info(
            "Бот запущен: @%s — открой https://t.me/%s и нажми Start",
            me.username, me.username,
        )
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("Бот остановлен")
    except TelegramNetworkError:
        print(
            "\n  ❌ Не получается достучаться до Telegram (сеть).\n"
            "  Проверь интернет; если Telegram у провайдера заблокирован — нужен VPN.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    except TelegramUnauthorizedError:
        print(
            "\n  ❌ Telegram отклонил токен (Unauthorized).\n"
            "  Скорее всего он скопирован с ошибкой или бот удалён в @BotFather.\n"
            "  Возьми токен заново: @BotFather → /mybots → твой бот → API Token.\n",
            file=sys.stderr,
        )
        sys.exit(1)
