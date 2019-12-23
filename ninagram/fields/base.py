from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.states.base import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from django.forms.forms import Field
from loguru import logger


class TgField(State, Field):
    
    transitions = {'init':':1'}
    VALUES_TYPES = ('int', 'float', 'bool', 'string')
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        self.name = kwargs.pop('name', None)
        self.return_on_click = kwargs.get('return_on_click', False)
        super().__init__(update, dispatcher, *args, **kwargs)
        
    def menu(self, update:telegram.Update):
        try:
            message = self.get_label(update)
            message += "\n\n" + self.get_current_value(update)
            
            error = self.get_error()
            if error:
                message += "\n\n" + error
                
            kbd = self.get_keyboard(update)
            
            menu_resp = MenuResponse(message, markup=kbd)
            resp = InputResponse(InputResponse.CONTINUE, menu_resp, None)
            return resp
        except Exception as e:
            logger.exception(str(e))
            
    def get_label(self, update):
        return _("Send the value of {}").format(self.label)
    
    def get_current_value(self, udpate):
        value = self.get_run('value', None)
        
        if not value:
            if self.initial:
                value = self.initial
            else:
                value = ''
                
        return _("Current value: {}").format(value)
            
    def next(self, update:telegram.Update):
        try:
            text = self.get_text()
        except Exception as e:
            logger.exception(str(e))
            
    def get_keyboard(self, update):
        replies = [[InlineKeyboardButton(_("OK"), callback_data="**ok**"),
                    InlineKeyboardButton(_("Cancel"), callback_data="**cancel**")]]
        kbd = InlineKeyboardMarkup(replies)
        return kbd
            
    def encode_cb_value(self, op_symbol, value_type, value):
        """
        This method create a string from some values to be decoded after.
        
        Params:
            - op_symbol: "+", "-", "/", "*", "=" one of this operator
            - value_type: the type of the value. should be one of the 
            AbstractInput.VALUES_TYPES element
            - value: the value of button
            
        Returns: a string with this format {}::{}::{}
        
        Raise: ValueError
        """
        try:
            if not isinstance(value_type, str):
                raise ValueError(_("value_type should be a string"))
            
            value_type = value_type.lower()
            if value_type not in self.VALUES_TYPES:
                raise ValueError(_("This value_type is not authorised. "
                                   "Please see AbstractInput.VALUES_TYPES"))
            
            return "{}::{}::{}".format(op_symbol, value_type, value)
        except Exception as e:
            logger.exception(str(e))
            
                        
            
