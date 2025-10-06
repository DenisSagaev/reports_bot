from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram_dialog import DialogManager, ShowMode, StartMode
from aiogram_dialog.widgets.input import ManagedTextInput

from functions.other_functions import create_text_report
from google_sheet import post_data_google_sheet, update_formula_total
from lexicon.report_messages import error_url_message, final_message, update_formula_message, error_api_promo
from promopages import main_promo, get_date_from_url
from states import Report, AddCampaign

router = Router()


@router.message(Command(commands="report"))
async def process_generating_command(message: Message, dialog_manager: DialogManager, **kwargs):
    await dialog_manager.start(state=Report.start, mode=StartMode.RESET_STACK)


async def correct_url(message: Message,
                         widget: ManagedTextInput,
                         dialog_manager: DialogManager,
                         text: str):
    if text.startswith("https://promopages.yandex.ru/"):
        dialog_manager.dialog_data["url_promo"] = text.lower().strip()
        dates = get_date_from_url(dialog_manager.dialog_data["url_promo"])
        dialog_manager.dialog_data["start_date"] = dates[0]
        dialog_manager.dialog_data["end_date"] = dates[1]
        await dialog_manager.switch_to(state=Report.sheet)

    elif text.startswith("https://docs.google"):
        dialog_manager.dialog_data["url_sheet"] = text
        if dialog_manager.current_context().state == AddCampaign.text:
            await dialog_manager.switch_to(state=AddCampaign.final, show_mode=ShowMode.SEND)
        else:
            await message.answer(final_message)
            report = await main_promo(url=dialog_manager.dialog_data["url_promo"])
            if 'Недельные показатели' not in report:
                await message.answer(error_api_promo)
                await dialog_manager.start(state=Report.start, show_mode=ShowMode.SEND)
            dialog_manager.dialog_data.update(report=report)
            message_report = await create_text_report(dialog_manager.dialog_data, dialog_manager)
            await message.answer(message_report)
            flag = await post_data_google_sheet(data_Promo=report,
                                                dates=(dialog_manager.dialog_data["start_date"], dialog_manager.dialog_data["end_date"]),
                                                url_Google=dialog_manager.dialog_data["url_sheet"])
            if flag:
                await dialog_manager.next()

            else:
                await message.answer(update_formula_message)
                await update_formula_total(report, dialog_manager.dialog_data["url_sheet"])
                await dialog_manager.next()


async def error_url(message: Message,
                          widget: ManagedTextInput,
                          dialog_manager: DialogManager,
                          error: ValueError):
    await message.answer(error_url_message)
    await dialog_manager.show(show_mode= ShowMode.NO_UPDATE)