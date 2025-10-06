from aiogram.fsm.state import StatesGroup, State


class StartMessage(StatesGroup):
    start = State()

class Schedule(StatesGroup):
    start = State()

class AddSchedule(StatesGroup):
    select_campaign = State()
    select_dates = State()
    select_interval = State()
    custom_interval = State()

class DeleteSchedule(StatesGroup):
    delete_schedule = State()

class WatchSchedule(StatesGroup):
    watch_schedule = State()

class Campaign(StatesGroup):
    start = State()
    create_report = State()
    select_dates = State()
    formula = State()
    result = State()

class AddCampaign(StatesGroup):
    start = State()
    sheet_check = State()
    text = State()
    final = State()

class DeleteCampaign(StatesGroup):
    start = State()

class GoogleSheet(StatesGroup):
    start = State()

class Report(StatesGroup):
    start = State()
    sheet = State()
    final = State()