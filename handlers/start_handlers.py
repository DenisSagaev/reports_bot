from aiogram import Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, BotCommand, BotCommandScopeChat
from aiogram_dialog import DialogManager, StartMode, ShowMode

from states import StartMessage, Report

router = Router()


# Хэндлер для /start
@router.message(CommandStart())
async def start_handler(message: Message, dialog_manager: DialogManager, **kwargs):
    await dialog_manager.start(
                                state=StartMessage.start,
                                show_mode=ShowMode.AUTO,
                                mode=StartMode.RESET_STACK
    )

