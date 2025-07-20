import json
import os
from datetime import datetime, timedelta, timezone
import io
import pstats

from src.utils.logger import logger


def get_date():
    force_date = os.getenv("FORCE_DATE")
    if force_date:
        try:
            a_date = parse_date(force_date)
            return a_date
        except Exception:
            logger.info("Error parse date")

    now_utc = datetime.now(timezone.utc)
    now_peru = now_utc - timedelta(hours=5)
    return now_peru

def get_current_day() -> str:
    today = get_date().strftime("%Y-%m-%d")
    return today

def get_current_day_name():
    # locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    day_name = get_date().strftime("%A %d de %B")
    return day_name

def parse_date(date_string: str) -> datetime:
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%fZ",  # Formato ISO 8601 con milisegundos y zona horaria Z
        "%Y-%m-%dT%H:%M:%S.%f",  # Formato ISO 8601 con milisegundos sin zona horaria
        "%Y-%m-%dT%H:%M:%S",  # Formato ISO 8601 sin milisegundos
        "%Y-%m-%d %H:%M:%S",  # Formato común con espacio en lugar de T
        "%d/%m/%Y %H:%M",  # Formato común en muchos países
        "%Y-%m-%d",  # Solo fecha
        "%d-%m-%Y",
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            continue

    raise ValueError(f"Date string '{date_string}' does not match any known formats")
