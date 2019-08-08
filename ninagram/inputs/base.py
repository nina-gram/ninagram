from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.state import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
import calendar
import datetime


class AbstractInput(State):
    
    transitions = {'init':':1'}
    VALUES_TYPES = ('int', 'float', 'bool', 'string')
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        self.name = kwargs.pop('name', None)
        super(AbstractInput, self).__init__(update, dispatcher, *args, **kwargs)
        
    def menu(self, update:telegram.Update):
        try:
            menu_resp = MenuResponse("Nothing")
            resp = InputResponse(False, menu_resp, None)
            return resp
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            text = self.get_text()
        except Exception as e:
            logger.exception(str(e))
            
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
            
                        
            
