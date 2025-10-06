import locale
from datetime import date
import calendar
import re

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.kbd import Select, Button

from apscheduler_functions import schedule_task
from schedule_config import scheduler
from states import AddSchedule, DeleteSchedule, Schedule

router = Router()


async def select_campaign_for_schedule(callback: CallbackQuery,
                          widget: Select,
                          manager: DialogManager,
                          item_id: str):
    manager.dialog_data.update(id_campaign=item_id)
    if item_id in manager.dialog_data["url_sheet"]:
        manager.dialog_data["url_sheet"] = manager.dialog_data["url_sheet"][item_id]

    if callback.message.reply_markup and callback.message.reply_markup.inline_keyboard:
        for row in callback.message.reply_markup.inline_keyboard:
            for button in row:
                if item_id in button.callback_data:
                    manager.dialog_data.update(title=button.text)
                    break
        await manager.switch_to(state=AddSchedule.select_dates)


async def select_dates(callback: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    manager.dialog_data["date_report"] = selected_date
    manager.dialog_data["chat_id"] = callback.message.chat.id
    await callback.answer(f"Следующий отчет: {selected_date.strftime('%d.%m.%Y')}\n\n"
                          f"Если ок, жми на кнопку «Вперед» под календарем. Если "
                          f"не ок, просто выбери другую дату в календаре", show_alert=True)

    await manager.show(show_mode=ShowMode.NO_UPDATE)


async def handler_yes(callback: CallbackQuery, widget: Button, manager: DialogManager):
    try:
        await schedule_task(manager)
        await manager.switch_to(state=AddSchedule.select_interval)
        locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
        await callback.message.answer(f"Отлично! Договорились. Буду присылать отчет каждый: "
                                      f"{manager.dialog_data["date_report"].strftime('%A')}. "
                                      f"В 12:00 по Москве")
        await manager.start(state=Schedule.start, show_mode=ShowMode.SEND)
    except Exception as e:
        await callback.message.answer(f"Что-то пошло не так. Передай "
                                  f"ошибку разработчику:\n\n{e}")


async def start_del_jobs(callback: CallbackQuery, widget: Button, manager: DialogManager):
    jobs = scheduler.get_jobs()
    if not jobs:
        await callback.answer("Нет активных задач")
    else:
        await manager.start(state=DeleteSchedule.delete_schedule, mode=StartMode.RESET_STACK)


async def deleted_jobs(callback: CallbackQuery, widget: Select, manager: DialogManager, item_id: str):
    job_ids = [job.id for job in scheduler.get_jobs() if item_id in job.id]
    for job_id in job_ids:
        scheduler.remove_job(job_id)
    await callback.answer("Задача успешно удалена из расписания")
    await manager.start(state=Schedule.start, mode=StartMode.RESET_STACK)


async def get_jobs_readable(dialog_manager: DialogManager, **kwargs):
    jobs = scheduler.get_jobs()
    readable = ""
    if jobs:
        for job in jobs:
            trigger = str(job.trigger)
            number_day = re.search(r"\d", trigger)
            weekday = calendar.day_name[int(number_day.group()) - 1]
            name = str(job.name)

            readable += f"📌 {name}: каждый — <b>{weekday}</b>\n\n"
        return {"readable": readable, "not_readable": False}
    else:
        return {"readable": False, "not_readable": True}



