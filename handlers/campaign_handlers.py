import json
from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Select, Button


from functions.other_functions import create_text_report
from getters import read_active_campaigns
from google_sheet import post_data_google_sheet, update_formula_total, create_copy_sheet
from lexicon.campaign_message import template_sheet
from lexicon.report_messages import final_message, error_api_promo, update_formula_message
from promopages import main_promo
from states import Campaign, AddCampaign

router = Router()

async def handler_create_report(callback: CallbackQuery, button: Button, dialog: DialogManager):
    check_file = await read_active_campaigns(dialog_manager=dialog)
    if not check_file["active_campaigns"]:
        await callback.answer("В списке нет активных кампаний. "
                              "Если считаешь, что это неправильно, жми на кнопку "
                              "Добавить кампанию", show_alert=True)
        await dialog.show(show_mode=ShowMode.NO_UPDATE)
    else:
        await dialog.next()



async def select_campaign_handlers(callback: CallbackQuery,
                          widget: Select,
                          dialog_manager: DialogManager,
                          item_id: str):
    dialog_manager.dialog_data.update(id_campaign=item_id)
    await dialog_manager.switch_to(state=Campaign.select_dates, show_mode=ShowMode.EDIT)


async def on_date_selected(callback: CallbackQuery, widget, manager: DialogManager, selected_date: date):
    if not manager.dialog_data.get("start_date"):
        manager.dialog_data["start_date"] = selected_date
        await callback.answer(f"Начало отчета: {selected_date.strftime('%d-%m-%Y')}")

    elif "end_date" not in manager.dialog_data and "start_date" in manager.dialog_data:
        # Если первая дата уже выбрана, сохраняем вторую как конец отчета
        manager.dialog_data["end_date"] = selected_date

        if manager.dialog_data["start_date"] > manager.dialog_data["end_date"]:
            manager.dialog_data["start_date"], manager.dialog_data["end_date"] = (
                manager.dialog_data["end_date"], manager.dialog_data["start_date"])

        await callback.answer(f"Начало отчета: {manager.dialog_data["start_date"].strftime('%d-%m-%Y')}\n\n"
                              f"Конец отчета: {manager.dialog_data["end_date"].strftime('%d-%m-%Y')}\n\n"
                              f"Если всё ок, жми кнопку «Вперед» под календарем. Если не ок, выбери "
                              f"другие даты", show_alert=True)

        await manager.show(show_mode=ShowMode.NO_UPDATE)

    elif "start_date" in manager.dialog_data and "end_date" in manager.dialog_data:
        manager.dialog_data["start_date"] = selected_date
        del manager.dialog_data["end_date"]
        await callback.answer(f"Начало отчета: {selected_date.strftime('%d.%m.%Y')}")
    if manager.start_data and "url_sheet" in manager.start_data:
        manager.dialog_data["url_sheet"] = manager.start_data["url_sheet"]
        manager.dialog_data["id_campaign"] = manager.start_data["id_campaign"]


async def go_report(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await callback.answer()
    await callback.message.answer(final_message)
    report = await main_promo(id_campaign=dialog_manager.dialog_data.get("id_campaign"),
                                  dates=(str(dialog_manager.dialog_data.get("start_date")),
                                     str(dialog_manager.dialog_data.get("end_date"))
                                     )
                              )

    if report is None:
        await callback.message.answer("Похоже ты пытаешься получить отчет за период, "
                                      "когда статьи не откручивались. Я не формирую отчет, "
                                      "если в графе расходы стоят нули")
        await dialog_manager.done()
        return None
    if "Недельные показатели" not in report:
        await callback.message.answer(f"{error_api_promo}:\n\n{report}")
        await dialog_manager.start(state=Campaign.create_report, show_mode=ShowMode.SEND)
    else:
        dialog_manager.dialog_data.update(report=report)
        if isinstance(dialog_manager.dialog_data["url_sheet"], dict):
            dialog_manager.dialog_data["url_sheet"] = dialog_manager.dialog_data["url_sheet"][
                dialog_manager.dialog_data["id_campaign"]]
        message_report = await create_text_report(dialog_manager.dialog_data, dialog_manager)
        await callback.message.answer(message_report)

        flag = await post_data_google_sheet(report,
                                            dialog_manager.dialog_data["url_sheet"],
                                            (dialog_manager.dialog_data["start_date"],
                                             dialog_manager.dialog_data["end_date"]))

        if flag:
            await dialog_manager.switch_to(state=Campaign.result, show_mode=ShowMode.SEND)
        else:
            await callback.message.answer(update_formula_message)
            await update_formula_total(report, dialog_manager.dialog_data["url_sheet"])
            await dialog_manager.switch_to(state=Campaign.result, show_mode=ShowMode.SEND)


async def add_campaign(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    name_client = None
    url_sheet = None
    message_double = False
    id_client = item_id

    for i in dialog_manager.dialog_data["clients"]:
        if i[1] == item_id:
            name_client = i[0]
    del dialog_manager.dialog_data["clients"]
    dialog_manager.dialog_data["title"] = name_client
    dialog_manager.dialog_data["id_campaign"] = id_client


    try:
        # Чтение данных из файла
        with open("campaigns", "r", encoding="utf-8") as file:
            data = json.load(file)

        delete_campaign = data["delete_campaigns"]
        for i in delete_campaign:
            if i[1] == item_id:
                url_sheet = i[2]
                break

        for i in data["active_campaigns"]:
            if i[1] == item_id:
                message_double = True
                break

        if message_double:
            await callback.answer("Эта кампания уже есть в базе бота")
        else:
            new_entry = [name_client, item_id, url_sheet]
            dialog_manager.dialog_data["url_sheet"] = url_sheet
            data.setdefault("active_campaigns", []).append(new_entry)

        # Запись обновленных данных в файл
            with open("campaigns", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)
            await dialog_manager.next()

    except Exception as e:
        await callback.answer(f"Что-то пошло не так. Передай ошибку разработчику: {e}",
                              show_alert=True)


async def create_new_sheet(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await callback.answer("Приступаю к созданию таблицы. Жди...")
    title = dialog_manager.dialog_data["title"]
    try:
        url_sheet = await create_copy_sheet(template_sheet, f"{title} // Статистика кампаний")
        dialog_manager.dialog_data["url_sheet"] = url_sheet
        if url_sheet:
            with open("campaigns", "r", encoding="utf-8") as file:
                data: dict[str, list[list[str, str]]] = json.load(file)
                for i in data["active_campaigns"]:
                    if title in i:
                        if len(i) > 2:
                            i[2] = url_sheet
                        else:
                            i.insert(2, url_sheet)
                        break

            with open("campaigns", "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4)

            await dialog_manager.switch_to(state=AddCampaign.final, show_mode=ShowMode.EDIT)
        else:
            await callback.answer("Не удалось создать таблицу. Обратись к разработчику. "
                                  "А пока можешь попробовать передать ссылку на таблицу вручную",
                                  show_alert=True)
            await dialog_manager.switch_to(state=AddCampaign.sheet_check)
    except Exception as e:
        await callback.message.answer(f"Что-то пошло не так. Передай эту ошибку разработчику "
                                      f"пожалуйста:\n\n{e}", parse_mode=None)
        await dialog_manager.switch_to(state=Campaign.start, show_mode=ShowMode.SEND)


async def handler_start_report(callback: CallbackQuery, widget: Button, dialog_manager: DialogManager):
    await dialog_manager.start(state=Campaign.select_dates, data=dialog_manager.dialog_data)


async def deleted_campaign(callback: CallbackQuery, widget: Select, dialog_manager: DialogManager, item_id: str):
    try:
        with open("campaigns", "r", encoding="utf-8") as file:
            data = json.load(file)
            for i in data["active_campaigns"]:
                if i[1] == item_id:
                    del_campaign = i
                    if del_campaign not in data["delete_campaigns"]:
                        data["delete_campaigns"].append(del_campaign)
                    data["active_campaigns"].remove(i)
                    break

        with open("campaigns", "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        await callback.answer("Кампания успешно удалена")
        await dialog_manager.start(state=Campaign.start)
    except Exception as e:
        await callback.message.answer(f"Что-то пошло не так. Передай эту ошибку "
                                      "разработчику: {e}", parse_mode=None)
        await dialog_manager.switch_to(state=Campaign.start, show_mode=ShowMode.SEND)
