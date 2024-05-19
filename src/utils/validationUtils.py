# String verification.
import re

def is_email_valid(email):
    """
    Check if the given email address is valid.
    """
    email_regex = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def is_telegram_chat_id_valid(chat_id):
    """
    Check if the given telegram chat id is valid.
    """
    chat_id_regex = r'^-?\d+$'  # An optional negative sign followed by one or more digits
    return re.match(chat_id_regex, str(chat_id)) is not None


