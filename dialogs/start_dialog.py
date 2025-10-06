from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Button, Start, SwitchTo
from aiogram_dialog.widgets.text import Format, Const

from getters import get_start_data
from states import StartMessage, Report, Campaign, Schedule

start_dialog = Dialog(
    Window(
        Format("Привет, {first_name}!\n\n{message}"),
        Column(
            Start(Const("Кампании"), id="campaigns", state=Campaign.start),
            Start(Const("Расписание"), id="schedule", state=Schedule.start),
    ),
    state=StartMessage.start,
    getter=get_start_data
    )
)