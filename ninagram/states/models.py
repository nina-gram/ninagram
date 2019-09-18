from ninagram.states.base import AbstractState
from django.forms.models import *


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
