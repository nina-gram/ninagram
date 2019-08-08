"""
This module contains classes for handling with Select/Choice inputs
"""
from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.state import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
from ninagram.inputs.base import AbstractInput


class SelectInput(AbstractInput):
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        super(SelectInput, self).__init__(update, dispatcher, *args, **kwargs)
        self.choices = kwargs.get('choices', [])        
        self.multiple = kwargs.get('multiple', False)
        if self.multiple:
            self.selected = kwargs.get('selected', [])
        else:
            self.selected = kwargs.get('selected', None)
        self.offset = kwargs.get('offset', 10)
        self.initial = self.selected
        
    def menu(self, update:telegram.Update):
        try:
            message = _("Please select a {}".format(self.name))
            replies = []
            start = self.get_run('start', 0, insert=True)
            
            real_start = start * self.offset
            real_end = real_start + self.offset
            for row in self.choices[real_start:real_end]:
                if isinstance(row, tuple):
                    text, value = row
                else:
                    text = value = row
                    
                if self.multiple:
                    if value in self.selected:
                        text += " ✅"
                else:
                    if value == self.selected:
                        text += " ✅"
                
                replies.append([InlineKeyboardButton(_(text), callback_data="value::{}".format(value))])
                
            row = []
            if start > 0:
                row.append(InlineKeyboardButton(_("⏪"), callback_data="nav::{}".format(start-1)))
                
            all_pages = len(self.choices) // self.offset
            rest = len(self.choices) % self.offset
            range_max = min([all_pages, start+3])
                        
            inside = []
            for page in range(start+1, range_max+1):
                inside.append(page)
                
            avail = 3 - len(inside)
            if avail:
                for page in range(start-avail, start):
                    if page < 0:
                        continue
                    inside.append(page)
                
            inside = sorted(inside)
            for page in inside:
                row.append(InlineKeyboardButton(_("{}".format(page+1)),
                                                 callback_data='nav::{}'.format(page)))
                
            if start > all_pages:
                pass
            elif start == all_pages and rest!=0:
                pass
            else:
                row.append(InlineKeyboardButton(_("⏩"), callback_data="nav::{}".format(start+1)))
                
            replies.append(row)
            
            replies.append([InlineKeyboardButton(_("OK"), callback_data="ok::ok"),
                            InlineKeyboardButton(_("Cancel"), callback_data="cancel::cancel")])
            kbd = InlineKeyboardMarkup(replies)
            
            return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            
            action, value = self.text.split("::")
            
            if action.lower() == "nav":
                self.set_run('start', int(value))
            elif action.lower() == "value":
                if self.multiple:
                    self.selected.append(value)
                else:
                    self.selected = value
            elif action.lower() == "ok":
                return InputResponse(InputResponse.STOP, None, self.selected)
            elif action.lower() == "cancel":
                return InputResponse(InputResponse.STOP, None, self.initial)
            
            return InputResponse(InputResponse.CONTINUE, None, None)
        except Exception as e:
            logger.exception(str(e))
            
            
class UniqueSelectInput(SelectInput):
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        super().__init__(update, dispatcher, *args, multiple=False, **kwargs)
        
        
class MultipleSelectInput(SelectInput):
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        super().__init__(update, dispatcher, *args, multiple=True, **kwargs)
        self.multiple = True