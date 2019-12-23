from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
from ninagram.fields.base import TgField
import re


class CharField(TgField):
    """
    This input should be used for short string.
    
    Args:
        - max_length: the max length of the string
        - min_length: the min length of the string
        - null: whether or not the input should allow null value
        - blank: whether or not the input should allow blank value
    """
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        self.max_length = kwargs.pop("max_length", 255)
        self.min_length = kwargs.pop("min_length", 1)
        self.accept_null = kwargs.pop("null", False)
        self.accept_blank = kwargs.pop("blank", False)
        self.value = kwargs.get("value", -1)
        if self.value != -1:
            self.set_run('value', value)
        super(CharField, self).__init__(update, dispatcher, *args, **kwargs)
        
            
    def next(self, update:telegram.Update):
        try:
            text = self.get_text(update)
            logger.debug("text {}", text)
            
            if text == '**ok**':
                value = self.get_run('value', None)
                self.set_run('value', None)
                return InputResponse(InputResponse.STOP, None, value=value)
            elif text == '**cancel**':
                return InputResponse(InputResponse.ABORT)
                
            is_good, value = self.validate_data(text)
            if not is_good:
                self.set_error(value)
            else:                
                self.set_run('value', value)
                
            return InputResponse(InputResponse.CONTINUE, None, value)
        except Exception as e:
            logger.exception(str(e))
            
    def validate_data(self, value:str)-> tuple:
        if self.max_length and len(value) > self.max_length:
            return False, _("The submitted value is greater than the max length allowed")
            
        if self.min_length and len(value) < self.min_length:
            return False, _("The submitted value is lower than the min length allowed")
            
        elif value is None and self.accept_blank is False:
            return False, _("The field can't be blank")
        
        return True, value
            
            
class TextField(CharField):
    """
    This input subclass the CharInput and changes the:
        - null to True
        - blank to True
        - max_length to 4096 (the max length of one telegram message)
    """
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        kwargs['null'] = True
        kwargs['blank'] = True
        kwargs['max_length'] = 4096
        super(TextField, self).__init__(update, dispatcher, *args, **kwargs)
        
        
class EmailField(CharField):
    """
    This input is a subclass of the CharInput that only allows email addresses.
    """
    
    EMAIL_RGX = re.compile("")
    
    def validate_data(self, value:str):
        res = self.EMAIL_RGX.match(self.text)
        if not res:
            return False, _('Email not valid! Retry')
        else:
            return True, res.group(1)
