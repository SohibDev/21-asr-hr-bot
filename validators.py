import re

def validate_name(text):
    return len(text.split()) >= 2  # Ism va familiya bo'lishi kerak

def validate_date(text):
    return bool(re.match(r'^\d{1,2}[.\-]\d{1,2}[.\-]\d{4}$', text))

def validate_nonempty(text):
    return len(text.strip()) > 0

def validate_phone(text):
    return bool(re.match(r'^[\d\+\-\(\) ]{7,20}$', text))
