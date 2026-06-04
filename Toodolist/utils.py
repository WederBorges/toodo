import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

def validation_number(tel):
    if not tel:
        return {'valid':True, 'number_f': None}
    
    try:
        n = phonenumbers.parse(tel, None)
        if not phonenumbers.is_valid_number(n) or not phonenumbers.is_possible_number(n):
            return False
        return {'valid':True, 'number_f':phonenumbers.format_number(n,PhoneNumberFormat.INTERNATIONAL)}
    except NumberParseException as e:
        return False
