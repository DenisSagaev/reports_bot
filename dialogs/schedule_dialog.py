import operator

from aiogram_dialog import Dialog, Window, StartMode
from aiogram_dialog.widgets.kbd import Column, Button, Start, Select, Group, Calendar, Row, SwitchTo
from aiogram_dialog.widgets.text import Format, Const

from apscheduler_functions import get_jobs_for_del
from getters import read_active_campaigns, get_button_go_status, get_interval
from handlers.schedule_handlers import select_campaign_for_schedule, \
    handler_yes, deleted_jobs, start_del_jobs, select_dates, get_jobs_readable
from lexicon.schedule_messages import start_schedule_message, select_campaigns_message, \
    select_dates_schedule, delete_message
from states import Schedule, DeleteSchedule, AddSchedule, WatchSchedule


start_schedule= Dialog(
    Window(
        Const(start_schedule_message),
        Column(
            Start(Const("Создать расписание"), state=AddSchedule.select_campaign, id="add_schedule", mode=StartMode.RESET_STACK),
            Start(Const("Посмотреть все расписания"), id="watch_schedule", state=WatchSchedule.watch_schedule, mode=StartMode.RESET_STACK),
            Button(Const("Удалить расписание"), id="delete_schedule", on_click=start_del_jobs)
        ),
        state=Schedule.start
    ),
)


add_schedule = Dialog(
    Window(
        Const(select_campaigns_message),
                Group(
            Select(
                Format("{item[0]}"),
                id="list_active_campaign",
                item_id_getter=operator.itemgetter(1),
                items="active_campaigns",
                on_click=select_campaign_for_schedule
            ),
            width=2
        ),
        Start(Const("Отмена"), state=Schedule.start, id="cancel"),
        state=AddSchedule.select_campaign,
        getter=read_active_campaigns
    ),

    Window(
        Const(select_dates_schedule),
        Calendar(id="calendar", on_click=select_dates),
        SwitchTo(Const("Вперед"), id="view", when="status", state=AddSchedule.select_interval),
        state=AddSchedule.select_dates,
        getter=get_button_go_status
    ),

    Window(
        Format("Присылать отчет каждый: {date_report}?"),
        Row(
        Button(Const("Да"), id="yes", on_click=handler_yes)
        ),
        Start(Const("Нет, всё отменяется"), id="cancel", state=Schedule.start, mode=StartMode.RESET_STACK),
        state=AddSchedule.select_interval,
        getter=get_interval
    )
)


delete_schedule = Dialog(
    Window(
Const(delete_message),
                Group(
            Select(
                Format("{item[0]}"),
                id="del_schedule",
                item_id_getter=operator.itemgetter(1),
                items="ids",
                on_click=deleted_jobs),
                    width=2
            ),
        Start(Const("Отмена"), id="cancel", state=Schedule.start, mode=StartMode.RESET_STACK),
        state=DeleteSchedule.delete_schedule,
        getter=get_jobs_for_del
    )
)


view_jobs = Dialog(
    Window(
        Format("{readable}", when="readable"),
        Format("Нет задач в расписании", when="not_readable"),
        Start(Const("Понятно"), state=Schedule.start, mode=StartMode.RESET_STACK, id="ok"),
        getter=get_jobs_readable,
        state=WatchSchedule.watch_schedule
    )
)


