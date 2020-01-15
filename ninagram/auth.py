"""This module contains all stuffs related to authentication and permission"""
import telegram
from ninagram.states.base import *
from ninagram.response import *
from django.utils.translation import gettext as _

class BaseAccess(AbstractState):
    """
    Base class of all authentication classes.
    
    This class doesn't nothing special. It implements methods to be called 
    when the update:``telegram.Update`` is refused or accepted."""
    
    fallback_state = "START"
    """This is the default fallback state when the access is refused."""
    
    error_message = _("Sorry! You are not authorized")
    """This the error message sent when the access is refused."""
    
    def __init__(self, *args, **kwargs):
        pass
    
    def get_next_error_response(self):
        """
        This method is called by next when the access is refused
        
        :return: A tuple with two items, False and a NextResponse to the 
                ``fallback_state``
        :rtype: tuple"""
        return (False, NextResponse("START", step=1, force_return=1))
    
    def get_next_success_response(self):
        """
        This method is called by next when the access is accepted
        
        :return: A tuple with two items, True and None``
        :rtype: tuple"""        
        return (True, None)
    
    def get_menu_error_response(self):
        """
        This method is called by menu when the access is refused
        
        :return: A tuple with two items, False and a MenuResponse to the 
                ``error_message``
        :rtype: tuple"""        
        return (False, MenuResponse(BaseAccess.error_message))
    
    def get_menu_success_response(self):
        """
        This method is called by menu when the access is accepted
        
        :return: A tuple with two items, True and None``
        :rtype: tuple"""                
        return (True, None)
    
    
class UserIsStaff(BaseAccess):
    """
    This class checks whether or not the update comes from a Staff user.
    """
    
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
    """
    This class checks whether or not the update comes from a Super user.
    """    
    
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
    """
    This class checks whether or not the update comes from a Staff chat.
    """    
    
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
    """
    This class checks whether or not the update comes from a private chat.
    """    
        
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
    """
    This class checks whether or not the update comes from a group.
    """    
    
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
    """
    This class checks whether or not the update comes from a supergroup.
    """    
    
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
    """
    This class checks whether or not the update comes from a channel.
    """    
        
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
    """
    This class checks whether or not the update comes from a group or a supergroup.
    """    
    
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
    """
    This class checks whether or not the update comes from a user who is `id` 
    in user_ids.
    
    :param list user_ids: A list telegram user's id.
    """    
    
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
    """
    This class checks whether or not the update comes from a user who is 
    `username` in usernames.
    
    :param list usernames: A list telegram usernames.
    """    
    
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
    """
    This class checks whether or not the update comes from a chat which is `id` 
    in chat_ids.
    
    :param list chat_ids: A list telegram chat's id.
    """    
    
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
    """
    This class checks whether or not the update comes from a chat who is 
    `username` in chatnames.
    
    :param list chatnames: A list telegram chat's username.
    """    
    
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
