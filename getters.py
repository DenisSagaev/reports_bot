import json
import locale
from typing import Any
from datetime import date

from aiogram.types import User
from aiogram_dialog import DialogManager

from lexicon.campaign_message import yes_sheet_message, not_sheet_message
from lexicon.start_messages import start_message
from states import AddSchedule


async def get_start_data(dialog_manager: DialogManager,event_from_user: User, **kwargs) -> dict[str, str]:
    first_name = event_from_user.first_name
    return {
        "first_name": first_name,
        "message": start_message
    }


async def read_active_campaigns(dialog_manager: DialogManager, **kwargs) -> dict[str, list[tuple[Any]]] | list[Any]:
    try:
        with open("campaigns", "r", encoding="utf-8") as file:
            data = json.load(file)

        # Извлекаем данные из ключа 'active_campaigns'
        active_campaigns = data["active_campaigns"]

        # Преобразуем список списков в список кортежей
        active_campaigns = [tuple(campaign) for campaign in active_campaigns]
        id_and_sheet = {k[1]: k[2] for k in active_campaigns}
        dialog_manager.dialog_data["url_sheet"] = id_and_sheet
        return {"active_campaigns": active_campaigns}

    except Exception as e:
        return {"active_campaigns": []}


async def check_sheet(dialog_manager: DialogManager, **kwargs):
    yes_sheet = dialog_manager.dialog_data.get("url_sheet", None)
    if yes_sheet:
        return {"sheet": yes_sheet, "message": yes_sheet_message}
    else:
        return {"no_sheet": True, "message": not_sheet_message}


async def get_button_go_status(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
        if dialog_manager.current_context().state == AddSchedule.select_dates:
            return {"status": dialog_manager.dialog_data.get("date_report")}
        else:
            return {"status": dialog_manager.dialog_data.get("end_date")}


async def get_interval(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
    date_report = dialog_manager.dialog_data.get("date_report", None)
    if isinstance(date_report, date):
        return {"date_report": date_report.strftime("%A")}
    else:
        return {"date_report": None}


async def get_url_sheet(dialog_manager: DialogManager, **kwargs) -> dict[str, Any]:
    return {"url_sheet": dialog_manager.dialog_data.get("url_sheet")}
