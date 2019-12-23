from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
from ninagram.fields.base import TgField
from  ninagram.fields.char import CharField
import re


class IntegerField(CharField):
    
    def validate_data(self, value:str)->tuple:
        try:
            return True, int(value)
        except:
            return False, _("This value can't be converted to an integer")
        
        
class FloatField(CharField):
    
    def validate_data(self, value:str)->tuple:
        try:
            return True, float(value)
        except:
            return False, _("This value can't be converted to a float")    
        
        
class BooleanField(CharField):
    
    def validate_data(self, value:str):
        if value.lower() in [_("true"), _("yes"), _("y"), _("1")]:
            return True, True
        elif value.lower() in [_("false"), _("no"), _("n"), _("0")]:
            return True, False
        else:
            return False, _("Unknown answer received")
            
