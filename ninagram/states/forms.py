from django.db.models import *
from ninagram.states.base import *
from ninagram.response import *
from django.utils.translation import gettext as _
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import ninagram.fields as nn_fields
from telegram import Update
from telegram.ext import Dispatcher

FIELDS_MAP = {
    'AutoField':nn_fields.IntegerField,
    'BigAutoField':nn_fields.IntegerField,
    'BigIntegerField':nn_fields.IntegerField,
    'BooleanField':BooleanField,
    'CharField':nn_fields.CharField,
    'DateField':nn_fields.CalendarField,
    'FloatField':nn_fields.FloatField,
    'TimeField':nn_fields.TimeField,
    'TextField':nn_fields.TextField,
    'OneToOneField':nn_fields.UniqueSelectField,
    'ForeignKey':nn_fields.UniqueSelectField,
    'ManyToManyField':nn_fields.MultipleSelectField
}


class BaseForm(State):
    
    model:Model = None
    fields = "__all__"
    transitions = {'home':':1'}
    
    def __init__(self, update:Update, dispatcher:Dispatcher, model:Model, instance=None, **kwargs):
        self.position = 0
        self.model = model
        self.instance = None if instance is not None else self.model()
        self.name = "{}_{}".format("FORM", self.model.__class__.__name__.upper())
        
        if self.fields == "__all__":
            self.fields = tuple(field.name for field in self.model._meta.get_fields() \
                           if field.__class__.__name__ != "AutoField")
            
        super(BaseForm, self).__init__(update, dispatcher, **kwargs)
    
    def get_input(self, field:Field)->nn_fields.base.Field:
        field_cls_name = field.__class__.__name__
        return FIELDS_MAP[field_cls_name]
    
    def get_position(self):
        """Return the index in fields on the current form"""
        return self.position
    
    def step_1_menu(self, update):
        pos = self.get_position()
        logger.debug("position {}", pos)
        if pos >= len(self.fields):
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
                    
        fd_name = self.fields[pos]
        field = self.model._meta.get_field(fd_name)
        
        if self.instance:
            initial = getattr(self.instance, fd_name, None)
        else:
            initial = None
                    
        Class_input = self.get_input(field)
        input_instance = Class_input(update, self.dispatcher, label=fd_name, 
                                     initial=initial)
        
        self.install_hook(input_instance)
        return input_instance.menu(update)
    
    def step_1_next(self, update):
        text = self.get_text(update)
        logger.debug("text {}", text)
        
        if text == 'action::save':
            self.instance.save()
            return InputResponse(InputResponse.STOP, value=self.instance)
        elif text == 'action::cancel':
            return InputResponse(InputResponse.ABORT)
        
        fd_name = self.fields[self.get_position()]
        
        hook = self.get_hook()
        if hook:
            res:InputResponse = hook.next(update)
            if res.status == InputResponse.CONTINUE:
                return res
            # if the user aborted the input we set the field to None
            elif res.status == InputResponse.ABORT:
                setattr(self.instance, fd_name, None)
                self.position += 1
                del hook
                self.install_hook(None)                
            elif res.status == InputResponse.STOP:
                setattr(self.instance, fd_name, res.value)
                self.position += 1
                del hook
                self.install_hook(None)                
            else:
                raise ValueError("This response ({}) returned a bad status".format(
                repr(res)))
        
        return InputResponse(InputResponse.CONTINUE)
