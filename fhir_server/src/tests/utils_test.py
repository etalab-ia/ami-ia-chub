from datetime import datetime


def datetime_fromisoformat(date_str):
    return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')