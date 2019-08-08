"""
This module defines the password inputs
"""
from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.state import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
from ninagram.inputs.base import AbstractInput


class PasswordInput(AbstractInput):
    
    ASK_TWICE = True
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        self.min_length = kwargs.pop('min_length', 6)
        self.max_length = kwargs.pop('max_length', 16)
        super().__init__(update, dispatcher, *args, **args)
        
    def menu(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            
            password1 = self.get_run('password1', None)
            if password1 is None:
                message = _("Please send your password")
                error = self.get_error()
                if error:
                    message += "\n\nError: {}".format(error)          
                    
                replies = [[InlineKeyboardButton(_("Cancel"), callback_data="cancel")]]
                kbd = InlineKeyboardMarkup(replies)
                return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd))
            
            if self.ASK_TWICE:
                password2 = _("Please send again your password")
                error = self.get_error()
                if error:
                    message += "\n\nError: {}".format(error)
                replies = [[InlineKeyboardButton(_("Cancel"), callback_data="cancel")]]
                kbd = InlineKeyboardMarkup(replies)
                return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd))
                    
            message = _("Done!")
            replies = [[InlineKeyboardButton(_("OK"), callback_data="ok")]]
            kbd = InlineKeyboardMarkup(replies)
            
            return InputResponse(InputResponse.STOP, MenuResponse(message, kbd), password1)
        except Exception as e:
            logger.exception(str(e))
        
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            self.dispatcher.bot.delete_message(update.effective_chat.id, 
                                update.effective_message.message_id)
            
            if self.text.lower() == 'ok':
                password1 = self.get_run('password1', None)
                return InputResponse(InputResponse.STOP, NextResponse(self.name), password1)
            elif self.text.lower() == 'cancel':
                return InputResponse(InputResponse.ABORT, NextResponse(self.name))
            
            if len(self.text) < self.min_length or len(self.text) > self.max_length:
                self.set_error(_("The password length should be between {} and {}")\
                               .format(self.min_length, self.max_length))
                return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
            
            password1 = self.get_run('password1', None)
            if password1 is None:
                self.set_run('password1', self.text)
                return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                
            password2 = self.get_run('password2', None)
            if password2 is None:
                if password1 != self.text:
                    self.set_error(_("The two password doesn't match. Retry"))
                    return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                
                self.set_run('password2', self.text)
                return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
        except Exception as e:
            logger.exception(str(e))
            
            
class NumericalPasswordInput(PasswordInput):
    """
    This is a password input that prompt the user with numeric keypad and accept only numeric code as password.
    Its subclass PasswordInput.
    """
    
    def menu(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            password = self.get_run('password', '')
            
            message = _("Tape your numeric password code.\n\nCurrent: {}").format('*'*len(password))
            
            error = self.get_error()
            if error:
                message += _("\n\nError: {}").format(error)
                
            replies = []
            for i in range(1, 4):
                row = []
                for j in range(3):
                    row.append(InlineKeyboardButton(_(str(i+j)), callback_data=_(str(i+j))))
                replies.append(row)
            kbd = InlineKeyboardMarkup(replies)
            
            return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd))
            
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            password = self.get_run('password', '')
            
            if self.text.lower() == "cancel":
                return InputResponse(InputResponse.ABORT, NextResponse(self.name))
            elif self.text.lower() == "ok":
                if len(password) < self.min_length or \
                   len(password) > self.max_length:
                    self.set_error(_("The password length should be betwwen {} and {}")\
                                   .format(self.min_length, self.max_length))
                    return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                else:
                    return InputResponse(InputResponse.STOP, NextResponse(self.name), password)
            elif not self.text.isnumeric():
                self.set_error(_("Only number are allowed"))
                return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
            
            password += self.text
            self.set_run("password", password)
            return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                
        except Exception as e:
            logger.exception(str(e))
            
            
class AlphaPasswordInput(PasswordInput):
    
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            password = self.get_run('password', '')
            
            if self.text.lower() == "cancel":
                return InputResponse(InputResponse.ABORT, NextResponse(self.name))
            elif self.text.lower() == "ok":
                if len(password) < self.min_length or \
                   len(password) > self.max_length:
                    self.set_error(_("The password length should be betwwen {} and {}")\
                                   .format(self.min_length, self.max_length))
                    return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                else:
                    return InputResponse(InputResponse.STOP, NextResponse(self.name), password)
            
            password += self.text
            self.set_run("password", password)
            return InputResponse(InputResponse.CONTINUE, NextResponse(self.name))
                
        except Exception as e:
            logger.exception(str(e))