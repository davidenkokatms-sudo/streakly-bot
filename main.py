import uvicorn
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
import calendar

app = FastAPI()

class DateList(BaseModel):
    dates: List[str]

# Названия дней недели
WEEK_DAYS = "Пн Вт Ср Чт Пт Сб Вс"

def create_calendar_view(year: int, month: int, check_days: List[int]) -> str:
    cal = calendar.monthcalendar(year, month)
    month_name = f"{year}-{month:02d}"
    
    result = f"Календарь активностей для {month_name}:\n"
    result += WEEK_DAYS + "\n"
    
    for week in cal:
        week_str = ""
        for day in week:
            if day == 0:
                week_str += "   " 
                continue
            
            # Логика с видео
            if day in check_days:
                week_str += "✅ "
            elif day < 10:
                week_str += f" {day} "
            else:
                week_str += f"{day} "
            
        result += week_str.rstrip() + "\n"
        
    return result

@app.post("/calendar")
async def get_calendar(data: DateList):
    try:
        parsed_dates = [datetime.strptime(d, "%d-%m-%Y") for d in data.dates]
        
        if not parsed_dates:
            return {"text": "Список дат пуст"}

        grouped = {}
        for dt in parsed_dates:
            key = (dt.year, dt.month)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(dt.day)

        final_text = ""
        for year, month in sorted(grouped.keys()):
            calendar_str = create_calendar_view(year, month, grouped[(year, month)])
            final_text += calendar_str + "\n"

        tg_message = f"```\n{final_text}```"
        
        return {
            "calendar_response": tg_message, 
            "original_text": final_text
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный формат даты. Ожидается DD-MM-YYYY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ВОТ ЭТО БЫЛО ДОБАВЛЕНО, ЧТОБЫ УБРАТЬ Procfile ---
if __name__ == "__main__":
    # Получаем порт от Railway или ставим 8000 по умолчанию
    port = int(os.environ.get("PORT", 8000))
    # Запускаем сервер
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
