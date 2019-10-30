from django.db.models import *
from ninagram.states.base import *
from ninagram.response import *
from django.utils.translation import gettext as _
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import ninagram.fields as nn_fields


class BaseForm(State):
    
    model:Model = None
    fields = ()
    
    def __init__(self, instance=None, **kwargs):
        self.position = 0
        self.instance = None if instance is None else self.model()
        self.name = "{}_{}".format("FORM", self.model.__class__.__name__.upper())
    
    def get_input(self, field:Field)->nn_fields.base.Field:
        pass
    
    def get_position(self):
        """Return the index in fields on the current form"""
        return self.position
    
    def step_1_menu(self, update):
        pos = self.get_position()
        if pos >= len(fields):
            message = _("Do you want to save these datas ?\n\n")
            for fd_name in self.fields:
                message += _("{}; `{}`\n").format(fd_name, getattr(self.instance, fd_name))
                
            replies = [[InlineKeyboardButton(_("Save"), callback_data='action::save'),
                        InlineKeyboardButton(_("Cancel"), callback_data='action::cancel')]]
            kbd = InlineKeyboardMarkup(replies)
            
            return MenuResponse(message, kbd)
        
        hook = self.get_hook()
        if hook:        
            res:InputResponse = hook.menu(update)
            if res.status == InputResponse.CONTINUE:
                return res.menu_response
            # if the user aborted the input we set the field to None
            elif res.status == InputResponse.ABORT:
                setattr(self.instance, hook.field_name, None)
            elif res.status == InputResponse.STOP:
                setattr(self.instance, hook.field_name, res.value)
                self.position += 1
            else:
                return MenuResponse(_("The Input returns a bad answer."))
                    
        fd_name = fields[pos]
        field = self.model._meta.get_field(fd_name)
        
        Class_input = self.get_input(field)
        input_instance = Class_input(update)
        
        self.install_hook(input_instance)
        return input_instance.menu(update)
    
    def step_1_next(self, update):
        text = self.get_text(update)
        
        if text == 'action::save':
            self.instance.save()
            return InputResponse(InputResponse.STOP, value=self.instance)
        elif text == 'action::cancel':
            return InputResponse(InputResponse.ABORT)
        
        hook = self.get_hook()
        if hook:
            res:InputResponse = hook.menu(update)
            if res.status == InputResponse.CONTINUE:
                return res
            # if the user aborted the input we set the field to None
            elif res.status == InputResponse.ABORT:
                setattr(self.instance, hook.field_name, None)
            elif res.status == InputResponse.STOP:
                setattr(self.instance, hook.field_name, res.value)
                self.position += 1
            else:
                raise ValueError("This response ({}) returned a bad status".format(
                repr(res)))
            
        pos = self.get_position()
        fd_name = self.fields[pos]
        field = self.model._meta.get_field(fd_name)
        
        Class_input = self.get_input(field)
        input_instance = Class_input(update)
        
        self.install_hook(input_instance)
        return InputResponse(InputResponse.CONTINUE)
