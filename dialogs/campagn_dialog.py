import operator

from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Column, Button, Start, SwitchTo, Select, Group, Calendar, Back
from aiogram_dialog.widgets.text import Format, Const

from functions.other_functions import check_valid_url_sheet
from getters import read_active_campaigns, check_sheet, get_button_go_status, get_url_sheet
from handlers.campaign_handlers import select_campaign_handlers, on_date_selected, \
    handler_create_report, go_report, add_campaign, create_new_sheet, deleted_campaign, handler_start_report
from handlers.report_handlers import correct_url, error_url
from lexicon.campaign_message import start_campaign_message, select_campaign_message, select_dates_message, \
    select_clients_message, done_ad_sheet, text_url_message, delete_start_message
from lexicon.report_messages import result_message, update_formula_message
from promopages import get_clients
from states import Campaign, AddCampaign, DeleteCampaign, StartMessage

campaign_dialog = Dialog(
    Window(
        Const(start_campaign_message),
        Column(
            Button(Const("Создать отчет"), on_click=handler_create_report, id="create_report"),
            Start(Const("Добавить кампанию"), state=AddCampaign.start, id="add_campaign"),
            Start(Const("Удалить кампанию"), state=DeleteCampaign.start, id="delete_campaign"),
            Start(Const("◀️ Назад"), id="back", state=StartMessage.start)
        ),
        state=Campaign.start
    ),

    Window(
        Const(select_campaign_message),
        Group(
            Select(
                Format("{item[0]}"),
                id="list_active_campaign",
                item_id_getter=operator.itemgetter(1),
                items="active_campaigns",
                on_click=select_campaign_handlers
            ),
            width=2
        ),
        Start(Const("Добавить кампанию"), state=AddCampaign.start, id="add_campaign"),
        Back(Const("◀️ Назад")),
        getter=read_active_campaigns,
        state=Campaign.create_report
    ),

    Window(
        Const(select_dates_message),
        Calendar(id="calendar", on_click=on_date_selected),
        Button(Const("Вперед"), id="go_report", on_click=go_report, when="status"),
        Back(Const("◀️ Назад"), when="status"),
        state=Campaign.select_dates,
        getter=get_button_go_status
    ),

    Window(
        Const(result_message),
        Start(Const("Создать отчет"), state=Campaign.create_report, id="create_report", mode=StartMode.RESET_STACK),
        Start(Const("На главную"), state=Campaign.start, id="start", mode=StartMode.RESET_STACK),
        Back(Const("◀️ Назад"), when="status"),
        state=Campaign.result
    )
)


add_campaign_dialog = Dialog(Window(
        Const(select_clients_message),
        Group(
            Select(
                Format("{item[0]}"),
                id="list_clients",
                item_id_getter=operator.itemgetter(1),
                items="clients",
                on_click=add_campaign,
            ),
            width=2
        ),
        Start(Const("Отмена"), state=Campaign.start, id="cancel", mode=StartMode.RESET_STACK),
        getter=get_clients,
        state=AddCampaign.start
    ),

    Window(
        Format("{message}", when="no_sheet"),
        Format("{message}", when="sheet"),
        Column(
            Start(Const("Оставь текущую таблицу"), id="yes_sheet", when="sheet", state=Campaign.start, mode=StartMode.RESET_STACK),
            Button(Const("Создать отчет"), id="create_report", on_click=handler_start_report, when="sheet"),
            Button(Const("Создай новую таблицу"), id="create_sheet", on_click=create_new_sheet),
            SwitchTo(Const("Дам ссылку на свою таблицу"), id="post_url_sheet", state=AddCampaign.text)
        ),
        state=AddCampaign.sheet_check,
        getter=check_sheet
    ),

    Window(
        Format("Вот ссылка на новую таблицу: {url_sheet}\n\n"
               "Можно прямо сейчас создать отчет. Если не надо, жми на "
               "Готово"),
        Button(Const("Создать отчет"), id="create_report", on_click=handler_start_report),
        Start(Const("Готово"), state=Campaign.start, id="start", mode=StartMode.RESET_STACK),
        state=AddCampaign.final,
        getter=get_url_sheet
    ),

    Window(
        Const(text_url_message),
        TextInput(
            id="text_url_sheet",
            type_factory=check_valid_url_sheet,
            on_success=correct_url,
            on_error=error_url
        ),
        Start(Const("Отмена"), state=Campaign.start, id="cancel", mode=StartMode.RESET_STACK),
        state=AddCampaign.text
    )
)


delete_campaign_dialog = Dialog(
    Window(
        Const(delete_start_message),
        Group(
            Select(
                Format("{item[0]}"),
                id="list_clients",
                item_id_getter=operator.itemgetter(1),
                items="active_campaigns",
                on_click=deleted_campaign,
            ),
            width=2
        ),
        Start(Const("Отмена"), state=Campaign.create_report, id="cancel", mode=StartMode.RESET_STACK),
        getter=read_active_campaigns,
        state=DeleteCampaign.start
        )
)

