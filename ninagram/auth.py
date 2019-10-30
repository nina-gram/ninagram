"""This module contains all stuffs related to authentication and permission"""
import telegram
from ninagram.states.base import *
from ninagram.response import *
from django.utils.translation import gettext as _

class BaseAccess(AbstractState):
    
    def __init__(self, *args, **kwargs):
        pass
    
    def get_next_error_response(self):
        return (False, NextResponse("START", step=1, force_return=1))
    
    def get_next_success_response(self):
        return (True, None)
    
    def get_menu_error_response(self):
        message = _("Sorry! You are not authorized")
        return (False, MenuResponse(message))
    
    def get_menu_success_response(self):
        return (True, None)
    
    
class UserIsStaff(BaseAccess):
    
    def menu(self, update:telegram.Update):
        if update.db.user.dj.is_staff:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.user.dj.is_staff:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next
    
class UserIsSuper(BaseAccess):
    
    def menu(self, update:telegram.Update):
        if update.db.user.dj.is_superuser:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.user.dj.is_superuser:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next  
    
class ChatIsStaff(BaseAccess):
    
    def menu(self, update:telegram.Update):
        if update.db.chat.is_staff:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.is_staff:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class ChatIsPrivate(BaseAccess):
        
    def menu(self, update:telegram.Update):
        if update.db.chat.type == "private":
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.type == "private":
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class ChatIsGroup(BaseAccess):
    
    def menu(self, update:telegram.Update):
        if update.db.chat.type == "group":
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.type == "group":
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class ChatIsSupergroup(BaseAccess):
    
    def menu(self, update:telegram.Update):
        if update.db.chat.type == "supergroup":
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.type == "supergroup":
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class ChatIsChannel(BaseAccess):
        
    def menu(self, update:telegram.Update):
        if update.db.chat.type == "channel":
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.type == "channel":
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class ChatIsAnyGroup(BaseAccess):
    
    
    def menu(self, update:telegram.Update):
        if update.db.chat.type == "group" or update.db.chat.type == "supergroup":
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.db.chat.type == "group" or update.db.chat.type == "supergroup":
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class UserIdIn(BaseAccess):
    
    def __init__(self, user_ids):
        if isinstance(user_ids, list) or isinstance(user_ids, tuple):
            self.user_ids = user_ids
        else:
            raise TypeError("user_ids must list or tuples")
        
    def menu(self, update:telegram.Update):
        if update.effective_user.id in self.user_ids:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.effective_user.id in self.user_ids:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next    
    
class UserUsernameIn(BaseAccess):
    
    def __init__(self, usernames):
        if isinstance(usernames, list) or isinstance(usernames, tuple):
            self.usernames = usernames
        else:
            raise TypeError("usernames must list or tuples")
        
    def menu(self, update:telegram.Update):
        if update.effective_user.username in self.usernames:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.effective_user.username in self.usernames:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next     
    
class ChatIdIn(BaseAccess):
    
    def __init__(self, chat_ids):
        if isinstance(chat_ids, list) or isinstance(chat_ids, tuple):
            self.chat_ids = chat_ids
        else:
            raise TypeError("user_ids must list or tuples")
            
    def menu(self, update:telegram.Update):
        if update.effective_chat.id in self.chat_ids:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.effective_chat.id in self.chat_ids:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next       
    
class ChatUsernameIn(BaseAccess):
    
    def __init__(self, chatnames):
        if isinstance(chatnames, list) or isinstance(chatnames, tuple):
            self.chatnames = chatnames
        else:
            raise TypeError("user_ids must list or tuples")
            
    def menu(self, update:telegram.Update):
        if uupdate.effective_chat.username in self.chatnames:
            return self.get_menu_success_response()
        else:
            return self.get_menu_error_response()
        
    def next(self, update:telegram.Update):
        if update.effective_chat.username in self.chatnames:
            return self.get_next_success_response()
        else:
            return self.get_next_error_response()
        
    menu_group = menu
    next_group = next       
