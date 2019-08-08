from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.state import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
from ninagram.inputs.base import AbstractInput
import re


class CharInput(AbstractInput):
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
        self.value = kwargs.value("value", -1)
        if self.value != -1:
            self.set_run('value', value)
        super(CharInput, self).__init__(update, dispatcher, *args, **kwargs)
        
    def menu(self, update:telegram.Update):
        try:
            message += _("Send the value of {}\n\n").format(self.name)
            
            error = self.get_error()
            if error:
                message += _("Error: {}\n\n").format(error)
                
            man_set = self.get_run('man_set', False)
            value = self.get_run('value', None)
            
            if value:
                message += _("Current value: {}\n\n").format(value)
            elif (not value) and man_set:
                message += _("Current value: {}\n\n").format(value)
                
            replies = [[InlineKeyboardButton(_("OK"), callback_data="**ok**")],
                       [InlineKeyboardButton(_("Pass"), callback_data='**pass**'),
                        InlineKeyboardButton(_("Cancel"), callback_data="**cancel**")]]
            kbd = InlineKeyboardMarkup(replies)
            
            menu_resp = MenuResponse(message, markup=kbd)
            resp = InputResponse(InputResponse.CONTINUE, menu_resp, value)
            return resp
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            text = self.get_text()
            if text.lower() == "**ok**" or text.lower() == "**pass**" \
               or text.lower() == "**cancel**":
                pass
            else:
                value = text
                
            if self.max_length and len(value) > self.max_length:
                self.set_error(_("The submitted value is greater than the max length allowed"))
                
            if self.min_length and len(value) < self.min_length:
                self.set_error(_("The submitted value is lower than the min length allowed"))
                
            elif value is None and self.accept_blank is False:
                self.set_error(_("The field can't be blank"))
                
            self.set_run('value', value)
            return InputResponse(InputResponse.CONTINUE, None, value)
        except Exception as e:
            logger.exception(str(e))
            
            
class TextInput(CharInput):
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
        
        
class EmailInput(CharInput):
    """
    This input is a subclass of the CharInput that only allows email addresses.
    """
    
    EMAIL_RGX = re.compile("")
    
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            
            if self.EMAIL_RGX.match(self.text):
                self.set_error(_('Email not valid! Retry'))
                return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
            
            self.set_run('value', self.text)
            return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
        except Exception as e:
            logger.exception(str(e))