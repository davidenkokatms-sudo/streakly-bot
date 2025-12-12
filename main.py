from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import calendar

app = FastAPI()

class DateList(BaseModel):
    dates: List[str]

# Названия дней недели для шапки
WEEK_DAYS = "Пн Вт Ср Чт Пт Сб Вс"

def create_calendar_view(year: int, month: int, check_days: List[int]) -> str:
    """
    Генерирует календарь, используя логику форматирования из видео-урока.
    """
    cal = calendar.monthcalendar(year, month)
    
    # Шапка месяца
    month_name = f"{year}-{month:02d}"
    result = f"Календарь активностей для {month_name}:\n"
    result += WEEK_DAYS + "\n"
    
    # Проход по неделям
    for week in cal:
        week_str = ""
        for day in week:
            # Если день = 0, это пустая ячейка (дни другого месяца)
            if day == 0:
                week_str += "   " # 3 пробела для отступа
                continue
            
            # --- ЛОГИКА ИЗ СКРИНШОТА ---
            if day in check_days:
                # Эмодзи галочки + пробел
                week_str += "✅ "
            elif day < 10:
                # Пробел + цифра + пробел (чтобы было широко)
                week_str += f" {day} "
            else:
                # Цифра + пробел
                week_str += f"{day} "
            # ---------------------------
            
        result += week_str.rstrip() + "\n" # Убираем лишние пробелы справа и переносим строку
        
    return result

@app.post("/calendar")
async def get_calendar(data: DateList):
    try:
        # 1. Преобразуем строки в объекты дат
        parsed_dates = [datetime.strptime(d, "%d-%m-%Y") for d in data.dates]
        
        if not parsed_dates:
            return {"text": "Список дат пуст"}

        # 2. Группируем даты по месяцам
        # Получаем структуру: { (2025, 3): [14, 20, 27], (2025, 4): [5] }
        grouped = {}
        for dt in parsed_dates:
            key = (dt.year, dt.month)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(dt.day)

        # 3. Генерируем текст
        final_text = ""
        # Сортируем месяцы, чтобы шли по порядку
        for year, month in sorted(grouped.keys()):
            # Передаем список дней (check_days) в функцию
            calendar_str = create_calendar_view(year, month, grouped[(year, month)])
            final_text += calendar_str + "\n"

        # 4. Оборачиваем в тройные кавычки для Телеграма (моноширинный текст)
        tg_message = f"```\n{final_text}```"
        
        return {
            "calendar_response": tg_message, 
            "original_text": final_text
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Ожидается DD-MM-YYYY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
