import re

from rest_framework.exceptions import ValidationError


class TitleValidator:
    def __init__(self, field):
        self.field = field

    def __call__(self, value):
        reg = re.compile(r'https?://(www\.)?youtube\.com/.*')
        tmp_val = dict(value).get(self.field)
        if not tmp_val:
            return
        if not bool(reg.match(tmp_val)):
            raise ValidationError('Сторонний ресурс')