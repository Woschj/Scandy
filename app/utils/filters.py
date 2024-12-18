from datetime import datetime

def format_datetime(value):
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return value
    return value.strftime('%d.%m.%Y %H:%M')

def register_filters(app):
    app.jinja_env.filters['format_datetime'] = format_datetime 