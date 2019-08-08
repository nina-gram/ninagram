"""This file contains all classes related to state definition and management"""
from ninagram.runtime import *
from ninagram.models import Message, User, Group
from ninagram.cache import save_this
from ninagram.auth import *
from ninagram.response import MenuResponse, NextResponse
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Dispatcher
import telegram
import os
from copy import copy
from pprint import pprint
from loguru import logger
import re
import traceback
from ninagram.exceptions import *
from django.template import Template, Context



class AbstractState:
    """The mother class of others states"""
    
    # Name of the state
    name = 'AbstractState'
    # the message that must be shown in menu
    # TODO support django templates here
    # for now support regex replacement
    menu_message = ""
    # the menu displaying type inline or bottom
    menu_display = "bottom"
    # a table (dictionary) of transitions
    transitions = {}
    # a dict that matchs some text or emoji to add before a menu item
    pre_item = {}
    # a dict that matchs some text or emoji to add after a menu item
    post_item = {}
    # the callback to validate the pass for unlocking
    __unlock_callback = None
    # don't generate buttons for these transitions
    no_buttons = []
    # if you want to restore a state after the current state
    restore_state = None
    # transitions for commands
    inlines = {}
    authorization_instances = {"all":[],
                               1: []}
    
    __runtime = Runtime()
    
    def __init__(self, update: telegram.Update, dispatcher:Dispatcher, *args, **kwargs):
        super(AbstractState, self).__init__()        
        assert len(self.transitions) > 0            
        self.user_id = update.effective_user.id
        self.chat_id = update.effective_chat.id
        self.update = update
        self.dispatcher = dispatcher
        self.text = self.get_text()
            
    def set_run(self, key, value):
        self.__runtime.set(self.user_id, self.chat_id, self.name, key, value)
        
    def get_run(self, key, default, insert=False):
        return self.__runtime.get(self.user_id, self.chat_id, self.name, key, default=default, insert=insert)
    
    def get_error(self, clear=True):
        return self.__runtime.get_error(self.user_id, self.chat_id, self.name, clear=clear)
    
    def clear_error(self):
        self.__runtime.clear_error(self.user_id, self.chat_id, self.name)
        
    def set_error(self, error):
        self.__runtime.set_error(self.user_id, self.chat_id, self.name, error=error)
        
    def get_step(self):
        return self.__runtime.get_step(self.user_id, self.chat_id, self.name, 1)
        
    def reset_step(self):
        self.__runtime.reset_step(self.user_id, self.chat_id, self.name)
        
    def set_step(self, step):
        if isinstance(step, str):
            try:
                if step in self.transitions:
                    step = int(self.transitions[step].split(':')[1])
            except:
                import traceback
                traceback.print_exc()
                return
            
        self.__runtime.set_step(self.user_id, self.chat_id, self.name, step)
        
    def set_return(self, ret):
        self.__runtime.set_return(self.user_id, self.chat_id, self.name, ret)
        
    def get_return(self):
        return self.__runtime.get_return(self.user_id, self.chat_id, self.name, False)
    
    def clear_return(self):
        self.__runtime.clear_return(self.user_id, self.chat_id, self.name)
        
    def install_hook_menu(self, instance):
        if instance is not None and not isinstance(instance, AbstractState):
            raise TypeError("instance argument should be an instance of a State")
        self.set_run('hook_menu', instance)
        
    def install_hook_next(self, instance):
        if instance is not None and not isinstance(instance, AbstractState):
            raise TypeError("instance argument should be an instance of a State")
        self.set_run('hook_next', instance)
        
    def install_hook(self, instance):
        self.install_hook_menu(instance)
        self.install_hook_next(instance)
        
    def get_hook_next(self):
        return self.get_run('hook_next', None)
    
    def get_hook_menu(self):
        return self.get_run('hook_menu', None)
    
    def get_hook(self, default=None):
        hook1 = self.get_hook_menu()
        hook2 = self.get_hook_next()
        
        if hook1 and hook2 and hook1.name == hook2.name:
            return hook1
        elif default == 'menu':
            return hook1
        elif default == "next":
            return hook2
        return None
        
    @classmethod
    def set_unlock_callback(cls, unlocker):
        assert callable(unlocker)
        cls.__unlock_callback = unlocker
        
    def set_lock(self):
        self.set_run("locked", True)
        
    def get_lock(self):
        return self.get_run("locked", False, insert=True)
        
    def unlock(self, password):
        if self.__unlock_callback(self.user_id, self.chat_id, password):
            self.set_run("locked", False)
            
    def set_cache(self, model_name, pkid, instance):
        self.__runtime.set_cache(model_name, pkid, instance)
        
    def get_cache(self, model_name, pkid):
        return self.__runtime.get_cache(model_name, pkid)
        
    def validate_access(self, update:telegram.Update):
        """Validate if the current user and chat are authorized to access this STATE"""
        step = self.get_step()
        
        for auth_instance in self.authorization_instances["all"]:
            res = auth_instance.check(update)
            if res is False:
                return False
            
        if step in self.authorization_instances:
            for auth_instance in self.authorization_instances[step]:
                res = auth_instance.check(update)
                if res is False :
                    return False
        
        return True
    
    def get_text(self, update=None):
        if update is None:
            update = self.update
            
        try:
            text = update.message.text if update.message!= None else update.callback_query.data
            return text
        except:
            pass
        
    def check_next_result(self, res, step):
        if (isinstance(res, str)) and (len(res) > 2): #we must return string # of current State name
            return res
        elif step != self.get_step(): # if step before call # of step after call return
            return self.name
        elif step == self.get_step() and self.get_error(clear=False)==True:
            return self.name
        else:
            return None
        
    def check_menu_result(self, res, update:telegram.Update):
        if isinstance(res, tuple) and len(res) == 2:
            message, kbd = res
        elif isinstance(res, tuple) and len(res) == 3 and res[2] == True:
            message, kbd = (res[0], res[1])
        else:
            return False
        
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            if not isinstance(kbd, telegram.InlineKeyboardMarkup):
                kbd = None
            
        return message, kbd
        
    def next(self, update: telegram.Update):
        """This method is called to find the next State from the current state.
        It chains call like this: 
            - first it searchs a user defined method pre_next for the current step. if found it calls it.
            - if not it calls the default pre_next method.
            - Then it calls the user defined method for the current step.
            
        If the message comes from a group then it reroute the request to next_group.
        In the State-Step pattern, it is responsible in deciding what is the new state or step 
        to get the menu from.
        
        You should not override unless you know what you are doing."""
        
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            return self.next_group(update)
        
        if not self.validate_access(update):
            # we try setting the step in the case we
            try:
                res = self.next_from_class_data(update)
                if res:
                    return res
            except:
                pass
            state = self.restore_state if self.restore_state != None else self.name
            return NextResponse(state, step=1)
        
        step = self.get_step()
            
        try:
            res = self.pre_next(update)
            if res and res.force_return == True:
                return res              
        except Exception as e:
            logger.exception(str(e))
            
        step = self.get_step()
        
        # we call the the pre step method that must perform various operations
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_next" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update)
            if res and res.force_return == True:
                return res
        except StepNotFoundException:
            pass
        except Exception as e:
            logger.exception(str(e))
            
        step = self.get_step()        
            
        try:
            try:
                step_method = getattr(self, "step_%s_next" % step)
            except:
                raise StepNotFoundException
            
            res = step_method(update)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))        
            
        logger.error("No valid NextResponse returned")
            
    def pre_next(self, update: telegram.Update):
        """This method is called before the user defined next method for the current step.
        Use this method typically to short-circuit the user next method.
        If you want to move to another intra-state(step) just call self.set_step(yr_step) 
        and to go to an extern state just return the state name as a string"""
        res = self.next_from_class_data(update)
        logger.trace("res is {}", res)
        if res is not None:
            self.set_run("return", True)
        return res
        
    def next_group(self, update: telegram.Update):
        """This method is called to find the next State of from the current state.
        It chains call like this: first it searchs a user defined method pre_next for 
        the current step. if found it calls it, if not it calls the default pre_next method.
        Then it calls the user defined method for the current step.
        This method is called only if the message come from a group"""
        
        if not self.validate_access(update):
            # we try setting the step in the case we
            try:
                res = self.next_from_class_data(update)
                if res:
                    return res
            except:
                pass
            state = self.restore_state if self.restore_state != None else self.name
            return NextResponse(state, step=1)
        
        step = self.get_step()
        
        # we call the the pre step method that must perform various operations
        try:
            res = self.pre_next_group(update)
            if res and res.force_return == True:
                return res
        except Exception as e:
            logger.exception(str(e))
            
        step = self.get_step()
            
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_next_group" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update)
            if res and res.force_return == True:
                return res            
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))
            
        step = self.get_step()
            
        try:
            try:
                step_method = getattr(self, "step_%s_next_group" % step)
            except:
                raise StepNotFoundException
            
            res = step_method(update)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))   
            
        logger.error("No valid NextResponse returned")
            
    def pre_next_group(self, update: telegram.Update):
        """This method is called before the user defined next method for the current step.
        Use this method typically to short-circuit the user next method.
        If you want to move to another intra-state(step) just call self.set_step(yr_step) 
        and to go to an extern state just return the state name as a string"""
        # don't call the user defined next method
        # self.set_run("return", True)
        # self.set_run("result", "NEXT-STATE")
        
        # change to another step
        # self.set_step(2)
        # self.set_run("return", True)
        res = self.next_from_class_data(update)
        logger.trace("res is {}", res)
        if res is not None:
            self.set_run("return", True)
        return res
        
    def menu(self, update: telegram.Update):
        """This method chain the call to find the correct result.
        For a certain step it call the corresponding pre_menu method.
        If the user has not defined a custom method for the step then it 
        loads the default pre_menu method.
        Then it calls the user implementation of menu method for the current step.
        If the telegram chat type is group or supergroup it reroutes the call to menu_group()"""
        
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            return self.menu_group(update)
        
        if not self.validate_access(update):
            return self.step_X_menu(update)        
        
        step = self.get_step()        
                
        # we call the the pre step method that must perform various operations
        try:
            res = self.pre_menu(update)
            if res and res.force_return == True:
                return res
        except AttributeError:
            pass        
        except Exception as e:
            logger.exception(str(e))
        
        step = self.get_step()
        
        # we call the the pre step method that must perform various operations
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_menu" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update)
            if res and res.force_return == True:
                return res
        except StepNotFoundException:
            pass                
        except Exception as e:
            logger.exception(str(e))
        
        step = self.get_step()        
        
        try:
            try:
                step_method = getattr(self, "step_%s_menu" % step)
            except:
                raise StepNotFoundException
            
            res = step_method(update)
            if res:
                return res        
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))        
        
        logger.error("Can't get a valid MenuResponse")
            
    def pre_menu(self, update: telegram.Update):
        """This method is executed before the call of the user menu step method.
        But this is called if the user has not defined a pre_menu method for a the current step
        The default implementation does nothing"""
        # We return by default the menu based on class data
        pass
        
    def menu_group(self, update: telegram.Update):
        """This method chain the call to find the correct result and it is 
        called only if the telegram chat is group or supergroup.
        For a certain step it call the corresponding pre_menu method.
        If the user has not defined a custom method for the step then it 
        loads the default pre_menu method.
        Then it calls the user implementation of menu method for the current step"""
        
        if not self.validate_access(update):
            return self.step_X_menu_group(update)        
        
        step = self.get_step()
        logger.info("step {}", step)
        
        # we call the the pre step method that must perform various operations
        try:
            res = self.pre_menu_group(update)
            if res and res.force_return == True:
                return res
        except Exception as e:
            logger.exception(str(e))
    
        step = self.get_step()
        logger.info("step {}", step)
    
        # we call the the pre step method that must perform various operations
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_menu_group" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update)
            if res and res.force_return == True:
                return res 
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))
    
        step = self.get_step()  
    
        try:
            try:
                step_method = getattr(self, "step_%s_menu_group" % step)
            except:
                logger.error("not found")
                raise StepNotFoundException
            
            res = step_method(update)
            if res:
                return res
        except StepNotFoundException:
            pass
        except Exception as e:
            logger.exception(str(e))        
    
        logger.error("Can't get the menu")     
            
    def pre_menu_group(self, update: telegram.Update):
        """This method is executed before the call of the user menu step method and 
        only if the telegram chat type is a group or a supergroup.
        But this is called if the user has not defined a pre_menu method for a the current step
        The default implementation does nothing"""
        # we set return to false to ensure that the default call chain goes up
        #self.set_run("return", False) 
        pass
        
    def post(self, update: telegram.Update, tg_message:telegram.Message):
        """This method must be called after the menu has been sent to perfom various actions"""
        
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            return self.post_group(update, tg_message)
        
        step = self.get_step()        
                
        # we call the the pre step method that must perform various operations
        try:
            res = self.pre_post(update, tg_message)
            if res:
                return res                
        except Exception as e:
            logger.exception(str(e))
            
                
        # we call the the pre step method that must perform various operations
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_post" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update, tg_message)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))
                
        try:
            try:
                step_method = getattr(self, "step_%s_post" % step)
            except:
                raise StepNotFoundException
            
            res = step_method(update, tg_message)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))        
        
    def pre_post(self, update: telegram.Update, tg_message:telegram.Message):
        """This method is called before the user defined next method for the current step.
        Use this method typically to short-circuit the user next method.
        If you want to move to another intra-state(step) just call self.set_step(yr_step) 
        and to go to an extern state just return the state name as a string"""
        pass
    
    def post_group(self, update: telegram.Update, tg_message:telegram.Message):
        """This is called by `post_menu` if the current chat is a group"""
        
        step = self.get_step()        
                
        # we call the the pre step method that must perform various operations
        try:
            res = self.pre_post_group(update, tg_message)
            if res:
                return res
        except Exception as e:
            logger.exception(str(e))
        
        # we call the the pre step method that must perform various operations
        try:
            try:
                pre_step_method = getattr(self, "pre_step_%d_post_group" % step)
            except:
                raise StepNotFoundException
            
            res = pre_step_method(update, tg_message)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))
    
        try:
            try:
                step_method = getattr(self, "step_%s_post_group" % step)
            except:
                raise StepNotFoundException
            
            res = step_method(update, tg_message)
            if res:
                return res
        except StepNotFoundException:
            pass        
        except Exception as e:
            logger.exception(str(e))                
        
    def pre_post_group(self, update: telegram.Update, tg_message:telegram.Message):
        """This method is called before the user defined next method for the current step.
        Use this method typically to short-circuit the user next method.
        If you want to move to another intra-state(step) just call self.set_step(yr_step) 
        and to go to an extern state just return the state name as a string"""
        pass    
        
        
    def default_context(self, update: telegram.Update):
        """Return the default context"""
        ctx = {'username':update.effective_user.username, 'first_name':update.effective_user.first_name,
               'last_name':update.effective_user.last_name, 'title':update.effective_chat.title, 'error':self.get_error(clear=False)}
        if update.effective_chat.type == "group" and update.effective_chat.type == "supergroup":
            ctx['group_username'] = update.effective_chat.username
        return ctx
        
    def menu_from_class_data(self, update: telegram.Update, msg=None):
        msg = msg if msg != None else self.menu_message
        tpl = Template(msg)
        ctx = self.default_context(update)
            
        context = Context(ctx)
        message = tpl.render(context)
            
        if update.effective_chat.type == "group" or update.effective_chat.type == "supergroup":
            menu_type = "inline"
        else:
            menu_type = self.menu_display
            
        if menu_type == "inline":
            ClassButton = InlineKeyboardButton
            ClassKeyboard = InlineKeyboardMarkup
        else:
            ClassButton = KeyboardButton
            ClassKeyboard = ReplyKeyboardMarkup
            
        replies = []
        buttons = []
        i = 0
        for state in self.transitions:
            if state in self.no_buttons:
                continue
            
            pre = self.pre_item[state] if state in self.pre_item else ''
            post = self.post_item[state] if state in self.post_item else ''
            state_shown = pre+state+post
            if menu_type == "inline":
                buttons.append(InlineKeyboardButton(state_shown, callback_data=state))
            else:
                buttons.append(KeyboardButton(state_shown))
            i += 1
            
            if i == 2:
                replies.append(copy(buttons))
                buttons.clear()
                i = 0
        if(len(buttons) > 0):
            replies.append(copy(buttons))
        logger.trace("replies :: {}", repr(replies))
                
        if menu_type == "inline":
            kbd = InlineKeyboardMarkup(replies)
        else:
            kbd = ReplyKeyboardMarkup(replies, resize_keyboard=True, one_time_keyboard=True)
            
        logger.debug("{}", message)
        return message, kbd
    
    def next_from_class_data(self, update: telegram.Update):
        
        if getattr(update.message, 'command', None):
            logger.debug("update.message.command {}", update.message.command)
            is_command = True            
        else:
            is_command = False
            
        try:
            if len(update.message.args)>0:
                arg = update.message.args[0]
            else:
                arg = ''
        except:
            arg = ''
            
        if is_command:
            all_trans = copy(self.transitions)
            all_trans.update(self.inlines)
            step = None
            for key, state in all_trans.items():
                if key.upper() == update.message.command.upper() or key.upper() == arg.upper():
                    splitten = state.split(':')
                    nx_state = splitten[0] if len(splitten[0])>0 else self.name
                    if len(splitten)>1:
                        try:
                            step = int(splitten[1])
                        except:
                            step = None
                        
                    logger.debug("I return {} and {}", nx_state, step)
                    return NextResponse(nx_state, step=step, force_return=True)
            else:
                if update.message.command.upper() == self.name:
                    return NextResponse(self.name, force_return=True)                
                
                return None
        else:
            text = self.get_text()
            if text:                    
                step = None
                for key, state in self.transitions.items():
                    if key.upper() == text.upper():
                        splitten = state.split(':')
                        try:
                            nx_state = splitten[0] if splitten[0] else self.name
                            if len(splitten)>1:
                                try:
                                    step = int(splitten[1])
                                except:
                                    step = None
                        except Exception as e:
                            logger.exception(str(e))
                            
                        return NextResponse(nx_state, step=step, force_return=True)
            else:
                return None
            
    def post_save_sent_message(self, update:telegram.Update, tg_message:telegram.Message):
        try:
            message = Message()
            message.id = tg_message.message_id
            message.user = update.db.user
            message.date = tg_message.date
            message.chat = update.db.chat
            message.data = self.name
            save_this(message, force_insert=True)
            return True
        except Exception as e:
            logger.exception(str(e))
            return False
            
    def post_save_recv_message(self, update:telegram.Update, tg_message:telegram.Message):
        try:
            user = self.__runtime.get_cache("User", 0)
            message = Message()
            message.id = update.effective_message.message_id
            message.user = user
            message.date = update.effective_message.date
            message.chat = update.db.chat
            message.data = self.name
            save_this(message, force_insert=True)
            return True
        except Exception as e:
            logger.exception(str(e))
            return False
            
    def post_save_both_message(self, update:telegram.Update, tg_message:telegram.Message):
        res = True
        
        if not self.post_save_sent_message(update, tg_message):
            res = False
            
        if not self.post_save_recv_message(update, tg_message):
            if res:
                res = False
                
        return res
    
    
class AbstractStateModel(AbstractState):
    
    # the model to be used
    Model = None
    # the columns of the Model to be used
    columns = []
    # the columns to be printed on row list
    list_columns = []
    # the input type supported by this state, one or step
    add_input = 'one'
    # the separator of input type when add_input is one
    sep = '\n\n'
    transitions = {'add':':2', 'list':':3', 'show':':4', 'del':':5', 'mod':':6'}
    
    def step_1_menu(self, update: telegram.Update):
        message = "{{first_name}}, you can manage %s here! Choose an option:" % (self.Model()._meta.verbose_name)
        msg, kbd = self.menu_from_class_data(update, msg=message)
        self.set_return(True)
        return msg, kbd
    
    def step_2_menu(self, update: telegram.Update):
        if self.add_input == 'one':
            res = self.add_one(update.message.rest)
        else:
            res = self.add_step(update.message.rest)
            
        if res:
            message = "We created a new %s" % (self.Model()._meta.verbose_name)
        else:
            message = "We failed to create a new %s" % (self.Model()._meta.verbose_name)
        
        msg, kbd = self.menu_from_class_data(update, msg=message)
        self.set_return(True)
        return msg, kbd
    
    def step_3_menu(self, update: telegram.Update):
        fmt_str = "%s - " * len(self.list_columns)
        fmt_str = fmt_str[:-3]
        fmt_str = "#%s. "+fmt_str+"\n"
        message = "List of %s:\n\n" % (self.Model()._meta.verbose_name_plural)
        
        rows = self.get_cache(self.Model.__name__, 'rows')
        if rows is None:            
            rows = self.Model.objects.all()
            self.set_cache(self.Model.__name__, 'rows', rows)
            
        count = len(rows)
        offset = self.get_run('offset', 0, insert=True)
        replies = []
        
        for row in rows[offset:offset+10]:
            param = [getattr(row, col) for col in self.list_columns]
            replies.append[InlineKeyboardButton(fmt_str % tuple(param), callback_data=str(row.id))]
            message += fmt_str % tuple(param)
        
        prev_next_btns = []
        if offset > 0:
            prev_next_btns.append(InlineKeyboardButton('⏪ Prev', callback_data='prev'))
        if offset + 10 < count:
            prev_next_btns.append(InlineKeyboardButton('Next ⏩', callback_data='next'))
            
        if len(prev_next_btns):
            replies.append(prev_next_btns)
            
        replies.append([InlineKeyboardButton('⬅️ Back', callback_data='menu')])
        kbd = InlineKeyboardMarkup(replies)
        
        self.set_return(True)
        return message, kbd
    
    def step_4_menu(self, update: telegram.Update):
        try:
            if len(update.message.tags) < 1:
                self.set_return(True)
                return "Please send an id via a hashtag #id", None
        except Exception as e:
            self.set_return(True)
            return str(e), None
        
        #show_id = int(update.message.tags[0])
        #row = self.Model.objects.get(pk=show_id)
        instance = self.get_run('instance', None)
        if instance:
            message = "Details about this %s\n\n" % (instance._meta.verbose_name)
            for col in self.columns:
                message += "%s: %s\n" % (col, str(getattr(row, col)))
                
            replies = [[InlineKeyboardButton("Del", callback_data='del'), InlineKeyboardButton('Modify', callback_data='mod')]]
            replies.append([InlineKeyboardButton('Home', callback_data='menu'), InlineKeyboardButton('Back to List', callback_data='list')])
            kbd = InlineKeyboardMarkup(replies)
        else:
            message = "No item selected\n"
            kbd = InlineKeyboardMarkup([[InlineKeyboardButton('Back', callback_data='menu')]])
        
        self.set_return(True)
        return msg, kbd    
        
    def step_5_menu(self, update: telegram.Update):
        instance = self.get_run('instance', None)
        if instance:
            instance.delete()
            self.set_run('instance', None)
            message = "I succcessfully deleted the %s" % (self.Model()._meta.verbose_name)
        else:
            message = "No item selected"
            
        kbd = InlineKeyboardMarkup([[InlineKeyboardButton('Back', callback_data='menu')]])
        self.set_return(True)
        return message, kbd
    
    def step_0_menu_group(self, update):
        args = ['/'+arg for arg in self.transitions if ':' in self.transitions[arg]]
        message = "Help: Use the inline command /%s\n" % (self.name.lower())
        message += "Arguments: %s\n\n" % " , ".join(args)
        message += "Example: /%s /list" % (self.name.lower())
        return message    
    
    def step_1_menu_group(self, update):
        msg, kbd = self.step_1_menu(update)
        return msg, None
    
    def step_2_menu_group(self, update):
        msg, kbd = self.step_2_menu(update)
        return msg, None
    
    def step_3_menu_group(self, update):
        msg, kbd = self.step_3_menu(update)
        return msg, kbd
    
    def step_4_menu_group(self, update):
        msg, kbd = self.step_4_menu(update)
        return msg, None
    
    def step_5_menu_group(self, update):
        msg, kbd = self.step_5_menu(update)
        return msg, None
    
    def add_one(self, text):
        values = [line.strip() for line in text.split(self.sep)]
        values[0] = values[0].split('\n')[1]
        logger.debug('values: {}', values)
        row = self.Model()
        for i in range(len(self.columns)):
            col = self.columns[i]
            val = values[i]
            setattr(row, col, val)
        row.save()            
        return True
    
    def add_step(self, value):
        pass
    
    
class State(AbstractState):
    
    def step_1_menu(self, update:telegram.Update):
        pass
    
    def step_1_next(self, update:telegram.Update):
        pass
    
    def step_2_menu(self, update:telegram.Update):
        pass
    
    def step_2_next(self, update:telegram.Update):
        pass
    
    def step_3_menu(self, update:telegram.Update):
        pass
    
    def step_3_next(self, update:telegram.Update):
        pass
    
    def step_4_menu(self, update:telegram.Update):
        pass
    
    def step_4_next(self, update:telegram.Update):
        pass
    
    def step_5_menu(self, update:telegram.Update):
        pass
    
    def step_5_next(self, update:telegram.Update):
        pass
    
    def step_6_menu(self, update:telegram.Update):
        pass
    
    def step_6_next(self, update:telegram.Update):
        pass
    
    def step_7_menu(self, update:telegram.Update):
        pass
    
    def step_7_next(self, update:telegram.Update):
        pass
    
    def step_8_menu(self, update:telegram.Update):
        pass
    
    def step_8_next(self, update:telegram.Update):
        pass
    
    def step_9_menu(self, update:telegram.Update):
        pass
    
    def step_9_next(self, update:telegram.Update):
        pass
    
    
    def step_10_menu(self, update:telegram.Update):
        pass
    
    def step_10_next(self, update:telegram.Update):
        pass
    
    
    def step_11_menu(self, update:telegram.Update):
        pass
    
    def step_11_next(self, update:telegram.Update):
        pass
    
    
    def step_12_menu(self, update:telegram.Update):
        pass
    
    def step_12_next(self, update:telegram.Update):
        pass
    
    def step_13_menu(self, update:telegram.Update):
        pass
    
    def step_13_next(self, update:telegram.Update):
        pass
    
    def step_14_menu(self, update:telegram.Update):
        pass
    
    def step_14_next(self, update:telegram.Update):
        pass
    
    def step_15_menu(self, update:telegram.Update):
        pass
    
    def step_15_next(self, update:telegram.Update):
        pass    
    
    def make_me_super(self):
        if len(User.objects.filter(is_superuser=True)) < 1:
            self.update.db.user.dj.is_superuser = True
            self.update.db.user.dj.is_staff = True
            self.update.db.user.dj.save()
            
    def save_this_message(self, update:telegram.Update, data:str=None):
        message = Message()
        message.id = update.effective_message.message_id
        message.user = update.db.user
        message.date = update.effective_message.date
        message.chat = update.db.chat
        message.data = data
        message.save()
        return message
    
    
class StateFactory:
    
    states_class = {}
    
    fallback_cls = None
    
    @staticmethod
    def set_fallback_class(cls):
        StateFactory.fallback_cls = cls
    
    @staticmethod
    def get_state(name: str, update, dispatcher, *args, **kwargs):
        if name is None:
            return StateFactory.get_state("START", update, dispatcher, *args, **kwargs)
        
        name = name.upper()
        
        if name in StateFactory.states_class:
            cls = StateFactory.states_class[name]
            state = cls(update, dispatcher, *args, **kwargs)            
        else:
            if StateFactory.fallback_cls is not None:
                state = StateFactory.fallback_cls
            else:
                raise StateException("State not found and no fallback State set")
            
        return state
    
    @staticmethod
    def add_state(name: str, cls):
        if isinstance(name, str) and isinstance(cls, type):
            StateFactory.states_class[name] = cls
            logger.debug("{} state registered as {}", name, cls)


def register_state(cls):
    StateFactory.add_state(cls.name, cls)
    
    def wrapper(cls):
        StateFactory.add_state(name, cls)
        return cls
        
    return cls

def get_state(name: str, update, dispatcher, *args, **kwargs):
    return StateFactory.get_state(name, update, dispatcher, *args, **kwargs)



class register_step:
    
    RGX = re.compile(r"step_(\d+)_(.*)_(?:menu|next)")
    
    def __init__(self, fn, *args):
        self.fn = fn

    def __set_name__(self, owner, name):
        res = self.RGX.search(name)
        if res:
            step = res.group(1)
            step_names = res.group(2).split("_")
            for sp_nm  in step_names:
                owner.transitions[sp_nm] = ':{}'.format(step)

        # then replace ourself with the original method
        setattr(owner, 'step_{}_menu'.format(step), self.fn)
        if hasattr(owner, 'SAME_STEP_GROUP') and owner.SAME_STEP_GROUP:
            setattr(owner, 'step_{}_menu_group'.format(step), self.fn)
            
        try:
            setattr(owner, 'step_{}_next'.format(step), 
                    getattr(owner, self.fn.__name__.replace('menu', 'next')))
            
            if hasattr(owner, 'SAME_STEP_GROUP') and owner.SAME_STEP_GROUP:
                setattr(owner, 'step_{}_next_group'.format(step), 
                    getattr(owner, self.fn.__name__.replace('menu', 'next')))            
        except:            
            traceback.print_exc()
             