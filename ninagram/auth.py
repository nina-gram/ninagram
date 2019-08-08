"""This module contains all stuffs related to authentication and permission"""
import telegram

class BaseAccess:
        
    def check(self, update:telegram.Update):
        return False
    
    
class UserIsStaff(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.user.dj.is_staff
    
class UserIsSuper(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.user.dj.is_superuser    
    
class ChatIsStaff(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.is_staff
    
class ChatIsPrivate(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.type == "private"
    
class ChatIsGroup(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.type == "group"
    
class ChatIsSupergroup(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.type == "supergroup"
    
class ChatIsChannel(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.type == "channel"
    
class ChatIsAnyGroup(BaseAccess):
    
    def check(self, update:telegram.Update):
        return update.db.chat.type == "group" or update.db.chat.type == "supergroup"
    
class UserIdIn(BaseAccess):
    
    def __init__(self, user_ids):
        if isinstance(user_ids, list) or isinstance(user_ids, tuple):
            self.user_ids = user_ids
        else:
            raise TypeError("user_ids must list or tuples")
        
    def check(self, update:telegram.Update):
        return update.effective_user.id in self.user_ids
    
class UserUsernameIn(BaseAccess):
    
    def __init__(self, usernames):
        if isinstance(usernames, list) or isinstance(usernames, tuple):
            self.usernames = usernames
        else:
            raise TypeError("usernames must list or tuples")
        
    def check(self, update:telegram.Update):
        return update.effective_user.username in self.usernames
    
class ChatIdIn(BaseAccess):
    
    def __init__(self, chat_ids):
        if isinstance(chat_ids, list) or isinstance(chat_ids, tuple):
            self.chat_ids = chat_ids
        else:
            raise TypeError("user_ids must list or tuples")
        
    def check(self, update:telegram.Update):
        return update.effective_chat.id in self.chat_ids
    
class ChatUsernameIn(BaseAccess):
    
    def __init__(self, chatnames):
        if isinstance(chatnames, list) or isinstance(chatnames, tuple):
            self.chatnames = chatnames
        else:
            raise TypeError("user_ids must list or tuples")
        
    def check(self, update:telegram.Update):
        return update.effective_chat.username in self.chatnames