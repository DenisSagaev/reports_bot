import locale
import re
import os
import json
from datetime import datetime, date
from typing import Tuple, List, Any, Dict

from aiogram_dialog import DialogManager


def check_valid_url_promo(url_promo: str) -> tuple[list[Any], list[Any]] or ValueError:
    """Проверяет валидность ссылки на кампанию в ПромоСтраницах"""
    valid_url = re.compile(r'^(https://promopages.yandex.ru/profile/editor/id/)')
    url = re.findall(valid_url, url_promo)
    if not url:
        raise ValueError
    return url_promo


def check_valid_url_sheet(url_sheet: str) -> tuple[list[Any], list[Any]] or ValueError:
    """Проверяет валидность ссылки на Гугл Таблицу"""
    valid_url = re.compile(r'^(https://docs.google.com/spreadsheets/d/)')
    url = re.findall(valid_url, url_sheet)
    if not url:
        raise ValueError
    return url_sheet


def generated_date_for_report(url):
    '''Генерирует интервал отчета, забирая даты прямо из урла ПромоСтраниц'''
    regex = r'\d{10}'
    date = re.findall(regex, url)
    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    start_interval_for_report = datetime.fromtimestamp(int(date[0])).strftime('%d %B').lower()
    end_interval_for_report = datetime.fromtimestamp(int(date[1])).strftime('%d %B').lower()

    return start_interval_for_report, end_interval_for_report


async def create_text_report(report: dict, dialog_manager: DialogManager=None) -> str:
    if "report" in report:
        dict_for_text = report["report"]

    else:
        dict_for_text = {}

    locale.setlocale(locale.LC_ALL, 'ru_RU.UTF-8')

    dates_interval = None
    url_sheet = dialog_manager.dialog_data.get('url_sheet')

    start_date = dialog_manager.dialog_data.get("start_date")
    end_date = dialog_manager.dialog_data.get("end_date")

    if isinstance(start_date, date) and isinstance(end_date, date):
        # Если даты уже являются объектами datetime
        dates_interval = (
            start_date.strftime("%d %B").lower(),
            end_date.strftime("%d %B").lower()
        )

    elif isinstance(start_date, str) and isinstance(end_date, str):
        try:
            # Преобразуем строки в объекты datetime
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")  # Пример формата: "2023-10-05"
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")  # Пример формата: "2023-10-10"
            dates_interval = (
                start_date_obj.strftime("%d %B").lower(),
                end_date_obj.strftime("%d %B").lower()
            )

        except ValueError as e:
            # Обработка ошибки, если формат даты некорректен
            print(f"Ошибка при парсинге дат: {e}")
            return "Ошибка: Некорректный формат даты."

    try:
        report_text = (f"Добрый день! Несу отчет по рекламным кампаниям в ПромоСтраницах.\n\n"
                       f"За период c {dates_interval[0]} по {dates_interval[1]} открутили "
                       f"{dict_for_text['Недельные показатели'][1]} ₽ бюджета.\n\nОбщие результаты такие:\n\n"
                       f"- Дочитывания по средней цене за неделю — {dict_for_text['Недельные показатели'][6]} ₽.\n\n"
                       f"- Переходы на сайт по {dict_for_text['Недельные показатели'][3]} ₽.\n\n"
                       f"- Средний CTR — {dict_for_text['Недельные показатели'][-2]}.\n\n"
                       f"Всего было {dict_for_text['Недельные показатели'][0]} показов, "
                       f"{dict_for_text['Недельные показатели'][5]} дочитываний и "
                       f"{dict_for_text['Недельные показатели'][2]} "
                       f"переходов на сайт.\n\n"
                       f"Полный отчет <a href='{url_sheet}'>по ссылке</a>")
        return report_text

    except KeyError:
        return ("Что-то пошло не так, и отчет не сформирован😢\n\n"
                "Попробуй заново")


async def create_json_file(filename: str) -> None:
    """
    Создает JSON-файл с начальной структурой данных, если он не существует.
    Файл содержит переменную "campaigns" с пустым словарем.

    :param filename: Имя файла (с расширением .json)
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(filename):
            # Создаем начальную структуру данных
            campaigns = {
                "active_campaigns": {}  # Пустой словарь для campaigns
            }
            # Записываем данные в файл
            with open(filename, "w", encoding="utf-8") as file:
                json.dump(campaigns, file, ensure_ascii=False, indent=4)
    except Exception as e:
        pass


def check_interval(text):
    if all(ch.isdigit() for ch in text) and 1 > int(text) > 31:
        return text
    raise ValueError

