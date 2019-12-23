from ninagram.states.base import AbstractState, register_step
from django.forms.models import *
from django.db.models import Model
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from ninagram.response import MenuResponse, NextResponse, InputResponse
from ninagram.fields.choice import UniqueSelectField
from django.utils.translation import gettext as _
from ninagram.states.forms import BaseForm


class AbstractStateModel(AbstractState):
    
    # the model to be used
    model:Model = None
    # the columns of the Model to be used
    columns = []
    # the columns to be printed on row list
    list_columns = []
    # the input type supported by this state, one or step
    add_input = 'one'
    # the separator of input type when add_input is one
    
    transitions = {'start':'START'}
    number_items = 9
    
    @register_step
    def step_1_home_menu(self, update: Update):
        message = _("What do you want to do?")
        replies = [[InlineKeyboardButton(_("Add"), callback_data="add"),
                    InlineKeyboardButton(_("List"), callback_data="list")]]
        kbd = InlineKeyboardMarkup(replies)
        return MenuResponse(message, kbd)
    
    @register_step
    def step_2_add_menu(self, update: Update):
        Hook_instance = self.get_hook()
        if not Hook_instance:
            Hook_instance = BaseForm(update, self.dispatcher, self.model,
                                     as_hook=True)
            self.install_hook(Hook_instance)
            
        res = Hook_instance.menu(update)
        if res.status == InputResponse.CONTINUE:
            return res.menu_response
        elif res.status == InputResponse.ABORT:
            replies = [[InlineKeyboardButton(_("Back"), callback_data="home")]]
            kbd = InlineKeyboardMarkup(replies)
            return MenuResponse("Aborted", kbd)
        
    def step_2_add_next(self, update:Update):
        Hook_instance = self.get_hook()
        if not Hook_instance:
            Hook_instance = BaseForm(update, self.dispatcher, self.model,
                                     as_hook=True)
            self.install_hook(Hook_instance)
            
        res = Hook_instance.next(update)
        if res.status == InputResponse.CONTINUE:
            return NextResponse(self.name)
        else:
            return NextResponse(self.name, 'list')
    
    @register_step
    def step_3_list_menu(self, update: Update):
        
        Hook_instance = self.get_hook()
        if not Hook_instance:
            queryset = self.get_queryset(update)
            offset = self.get_number_items(update)
            
            ctx = {'name':self.model.__class__.__name__, 'offset':offset,
                   'choices':queryset, 'return_on_click':True}
            Hook_instance = UniqueSelectField(update, self.dispatcher, **ctx)
            self.install_hook(Hook_instance)
            
        res = Hook_instance.menu(update)
        if res.status == InputResponse.CONTINUE:
            return res.menu_response
        elif res.status == InputResponse.ABORT:
            replies = [[InlineKeyboardButton(_("Back"), callback_data="home")]]
            kbd = InlineKeyboardMarkup(replies)
            return MenuResponse("Aborted", kbd)
        
    def step_3_list_next(self, update:Update):
        Hook_instance = self.get_hook()
        if not Hook_instance:
            queryset = self.get_queryset(update)
            offset = self.get_number_items(update)
            
            ctx = {'name':str(self.model), 'offset':offset,
                   'choices':queryset, 'return_on_click':True}
            Hook_instance = UniqueSelectField(update, self.dispatcher, **ctx)    
            self.install_hook(Hook_instance)
            
        res = Hook_instance.next(update)
        if res.status == InputResponse.CONTINUE:
            return NextResponse(self.name)
        elif res.status == InputResponse.STOP:
            if res.value:
                self.set_run('pk', res.value)
                Hook_instance = None
                del Hook_instance
                self.install_hook(None)
                return NextResponse(self.name, 'detail')
            else:
                return NextResponse(self.name, 'home')
        else:
            Hook_instance = None
            del Hook_instance
            self.install_hook(None)            
            return NextResponse(self.name, 'home')
        
    @register_step
    def step_4_detail_menu(self, update: Update):        
        pk = self.get_run('pk', None)        
        instance = self.model.objects.get(pk=pk)
        if instance:
            message = "%s details\n\n" % (instance._meta.verbose_name)
            fields = [field.name for field in self.model._meta.get_fields()]
            for col in fields:
                message += "%s: %s\n" % (col, str(getattr(instance, col)))
                
            replies = [[InlineKeyboardButton("Del", callback_data='del'), InlineKeyboardButton('Modify', callback_data='mod')]]
            replies.append([InlineKeyboardButton('Home', callback_data='menu'), InlineKeyboardButton('Back to List', callback_data='list')])
            kbd = InlineKeyboardMarkup(replies)
        else:
            message = "No item selected\n"
            kbd = InlineKeyboardMarkup([[InlineKeyboardButton('Back', callback_data='menu')]])
        
        return MenuResponse(message, kbd)
        
    @register_step
    def step_5_del_menu(self, update: Update):
        pk = self.get_run('pk', None)        
        instance = self.model.objects.get(pk=pk)
        deleted = self.get_run('deleted', False)
        if deleted:
            message = _("{} object deleted").format(self.model._meta.verbose_name)
            replies = [[InlineKeyboardButton('Back', callback_data='list')]]
        else:
            error = self.get_error()
            message = _("Do you really want to delete {} ?").format(instance)
            if error:
                message += _("\n\nError: {}").format(error)
            replies = [[InlineKeyboardButton(_("Yes"), callback_data="yes"),
                        InlineKeyboardButton(_("No"), callback_data="detail")]]
        
        kbd = InlineKeyboardMarkup(replies)
        return MenuResponse(message, kbd)
    
    def step_5_del_next(self, update:Update):
        if self.text == "yes":
            pk = self.get_run('pk', None)        
            instance = self.model.objects.get(pk=pk)
            self.set_run('pk', None)
            self.set_run('deleted', True)
            
        return NextResponse(self.name)
    
    
    def get_queryset(self, update:Update):
        return self.model.objects.all()
    
    def get_number_items(self, update:Update):
        return self.number_items
