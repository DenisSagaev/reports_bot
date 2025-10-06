from datetime import datetime, timedelta

from aiogram_dialog import DialogManager
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from schedule_config import scheduler
from functions.other_functions import create_text_report
from google_sheet import post_data_google_sheet, update_formula_total
from lexicon.report_messages import error_api_promo, update_formula_message, result_message
from promopages import main_promo


async def schedule_task(dialog_manager: DialogManager):
    id_campaign = dialog_manager.dialog_data.get("id_campaign")
    date_report = dialog_manager.dialog_data.get("date_report")
    url_sheet = dialog_manager.dialog_data.get("url_sheet")
    title = dialog_manager.dialog_data.get("title")
    chat_id = dialog_manager.dialog_data.get("chat_id")

    cron_day = (date_report.weekday() + 1) % 7

    scheduler.add_job(
        go_report_scheduled,
        CronTrigger(day_of_week=cron_day, hour=12, minute=0, second=0),
        kwargs={
            "data": {
                "title": title,
                "id_campaign": id_campaign,
                "date_report": date_report,
                "url_sheet": url_sheet,
                "bot": dialog_manager.event.bot if hasattr(dialog_manager.event, "bot") else None,
                "chat_id": chat_id,
            }
        },
        id=f"{title}_{id_campaign}",
        name=title,
        replace_existing=True,
    )


MAX_RETRIES = 3
RETRY_DELAY_MINUTES = 5

async def go_report_scheduled(data: dict, attempt: int = 1):
    id_campaign = data["id_campaign"]
    url_sheet = data["url_sheet"]
    chat_id = data.get("chat_id")
    bot = data.get("bot")

    today = datetime.now()
    end_date = (today.date() - timedelta(days=1))
    start_date = (today - timedelta(days=7)).date()

    try:
        report = await main_promo(id_campaign=id_campaign, dates=(str(start_date),str(end_date)))
        if report is None:
            bot.send_message(chat_id, "Похоже, ты пытаешься получить отчет в интервале, "
                                      "в котором было ноль расходов. За такой период я "
                                      "отчет не могу сформировать")
    except Exception as e:
        if attempt < MAX_RETRIES:
            retry_id = f"retry_report_{id_campaign}_{attempt + 1}"
            scheduler.add_job(
                go_report_scheduled,
                trigger=DateTrigger(run_date=datetime.now() + timedelta(minutes=RETRY_DELAY_MINUTES)),
                kwargs={"data": data, "attempt": attempt + 1},
                id=retry_id,
                replace_existing=True
            )
            if bot and chat_id:
                await bot.send_message(chat_id, f"⚠️ Ошибка получения отчета. Попытка #{attempt} из {MAX_RETRIES}. "
                                                f"Повтор через {RETRY_DELAY_MINUTES} мин.")
        else:
            if bot and chat_id:
                await bot.send_message(chat_id, f"❌ Все попытки получить отчет провалились. Ошибка: {e}")
        return

    if "Недельные показатели" not in report:
        if bot and chat_id:
            await bot.send_message(chat_id, f"{error_api_promo}:\n\n{report}")
        return

    dialog_data = {
        "id_campaign": id_campaign,
        "start_date": start_date,
        "end_date": end_date,
        "url_sheet": url_sheet,
        "report": report
    }

    try:
        message_report = await create_text_report(dialog_data, None)
        if bot and chat_id:
            await bot.send_message(chat_id, message_report)
    except Exception as e:
        if bot and chat_id:
            await bot.send_message(chat_id, f"⚠️ Не удалось сформировать текст отчета: {e}")

    flag = await post_data_google_sheet(report, url_sheet, (start_date, end_date))

    if not flag:
        if bot and chat_id:
            await bot.send_message(chat_id, update_formula_message)
        await update_formula_total(report, url_sheet)
        await bot.send_message(chat_id, result_message)
    else:
        await bot.send_message(chat_id, result_message)


async def get_jobs_for_del(*args, **kwargs):
    jobs = scheduler.get_jobs()
    ids = [(str(job.id).split("_")[0], str(job.id).split("_")[1]) for job in jobs]
    return {"ids": ids}


