from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Column, Button, Start, SwitchTo
from aiogram_dialog.widgets.text import Format, Const

from functions.other_functions import check_valid_url_promo, check_valid_url_sheet
from handlers.report_handlers import correct_url, error_url
from lexicon import report_messages
from states import Report, Campaign, StartMessage

create_report = Dialog(
    Window(
        Const(report_messages.url_campaign_message),
        TextInput(id="url_promo",
                  type_factory=check_valid_url_promo,
                  on_success=correct_url,
                  on_error=error_url),
        Start(Const("Отмена"), state=StartMessage.start, id="cancel"),
        state=Report.start
    ),

    Window(
        Const(report_messages.url_sheet_message),
        TextInput(id="url_sheet",
                  type_factory=check_valid_url_sheet,
                  on_success=correct_url,
                  on_error=error_url),
        Start(Const("Отмена"), state=StartMessage.start, id="cancel"),
        state=Report.sheet
    ),

    Window(
        Const(report_messages.result_message),
        Start(Const("Создать отчет"), state=Report.start, id="new_report"),
        Start(Const("На главную"), state=Campaign.start, id="main"),
        state=Report.final
    )
)