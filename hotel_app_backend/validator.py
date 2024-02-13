from django.core.validators import RegexValidator
PhoneNumberRegex = RegexValidator(regex=r"^\+?1?\d{10}$")
