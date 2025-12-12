from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import calendar

app = FastAPI(title="Telegram Calendar Generator")

# Модель входящих данных
class DateList(BaseModel):
    dates: List[str]

# Словари для русификации (чтобы не зависеть от локали сервера Railway)
MONTH_NAMES = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
}

WEEK_DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

def generate_month_string(year: int, month: int, active_days: set) -> str:
    """Генерирует строковое представление одного месяца."""
    
    # Инициализация календаря (0 - понедельник)
    cal = calendar.TextCalendar(firstweekday=0)
    month_matrix = cal.monthdayscalendar(year, month)
    
    # Заголовок месяца
    month_key = f"{year}-{month:02d}"
    output = [f"Календарь активностей для {month_key}:"]
    
    # Заголовок дней недели
    # Используем 2 символа на день + 1 пробел разделитель = ширина 3
    header_days = " ".join(WEEK_DAYS)
    output.append(header_days)
    
    # Формирование сетки
    for week in month_matrix:
        week_str = []
        for day in week:
            if day == 0:
                # Пустой день (из другого месяца)
                week_str.append("  ") # 2 пробела
            elif day in active_days:
                # Активный день - эмодзи
                # Эмодзи ✅ визуально занимает место как 2 цифры, но технически это 1 символ.
                # В моноширинном шрифте телеграма это часто выглядит лучше без лишних пробелов,
                # или наоборот требует подгонки. Стандартно делаем так:
                week_str.append("✅")
            else:
                # Обычный день, выравнивание вправо (ширина 2)
                week_str.append(f"{day:>2}")
        
        # Собираем неделю в строку с пробелами между днями
        output.append(" ".join(week_str))
        
    return "\n".join(output)

@app.post("/calendar")
async def get_calendar(data: DateList):
    try:
        # 1. Парсим даты
        parsed_dates = []
        for d in data.dates:
            # Парсим формат DD-MM-YYYY
            dt = datetime.strptime(d, "%d-%m-%Y")
            parsed_dates.append(dt)
        
        if not parsed_dates:
            return {"text": "Нет дат для отображения."}

        # 2. Группируем даты по (год, месяц)
        # Словарь вида: {(2025, 3): {14, 20, 27}, (2025, 4): {1}}
        grouped_dates = {}
        for dt in parsed_dates:
            key = (dt.year, dt.month)
            if key not in grouped_dates:
                grouped_dates[key] = set()
            grouped_dates[key].add(dt.day)

        # 3. Генерируем календари для каждого месяца
        # Сортируем ключи, чтобы месяцы шли по порядку
        sorted_keys = sorted(grouped_dates.keys())
        
        final_parts = []
        for year, month in sorted_keys:
            month_cal = generate_month_string(year, month, grouped_dates[(year, month)])
            final_parts.append(month_cal)
            
        # Объединяем всё, добавляя разделитель между месяцами
        full_text = "\n\n".join(final_parts)
        
        # Оборачиваем в тройные кавычки для моноширинного блока в Telegram
        telegram_ready_text = f"```\n{full_text}\n```"
        
        return {
            "calendar_text": telegram_ready_text,
            "raw_text": full_text
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка формата даты. Используйте DD-MM-YYYY. Детали: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Calendar Service is running. Send POST to /calendar"}
