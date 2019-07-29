import telegram
from ninagram.handlers import *
from telegram.ext import MessageHandler, Filters
from telegram import ParseMode
from loguru import logger
from .state import get_state
from .models import TgUser, User
from .runtime import Runtime
from .middlewares import SessionMiddleware
    
try:
    from django.utils import translation
    CAN_TRANSLATE = True
except:
    CAN_TRANSLATE = False


def generic_processor(update: telegram.Update, dispatcher:telegram.ext.Dispatcher):
    try:
        if CAN_TRANSLATE:
            try:
                lang = update.db.chat.lang
                translation.activate(lang)
                logger.debug("we are setting lang {}", lang)
            except Exception as e:
                logger.exception(str(e))
                
        try:
            sess = update.db.session
            logger.debug("last state is {}", sess.state)
            prev_state = get_state(sess.state, update, dispatcher)
            resp = prev_state.next(update)
            state = get_state(resp.state, update, dispatcher)
            if resp.step:
                state.set_step(resp.step)
            logger.debug("new state is {}", state.name)
        except Exception as e:
            logger.exception(str(e))
            state = get_state("START", update, dispatcher)
            return
        
        sess.state = state.name
        # note that we save the session in the Saver thread to avoid
        # waiting for database writes
        sess.save_after()
        
        try:
            resp = state.menu(update)
            if state.restore_state:
                sess.state = state.restore_state
            else:
                sess.state = state.name
            sess.save_after(force_update=True)
            logger.debug("after state is {}", sess.state)
        except Exception as e:
            logger.exception(str(e))
            state = get_state("START", update, dispatcher)
            resp = state.menu(update)
            sess.state = state.name
            sess.save_after()
            
        all_msg = resp.apply(update)
        
        try:
            for msg in all_msg:
                state.post(update, msg)
        except Exception as e:
            logger.exception(str(e))
    except Exception as e:
            logger.exception(str(e))
        

class Bot:
    """
    This class encapsulates all the bot behavior
    """
    
    REQUEST_KWARGS={
        'proxy_url': 'http://127.0.0.1:8080/',
    }    
    
    def __init__(self, token):
        self.bot = telegram.Bot(token)
        self.updater = telegram.ext.Updater(token, request_kwargs=None)
        self.dispatcher = self.updater.dispatcher
        self.job_queue = self.updater.job_queue
        self.runtime = Runtime()
        
        self.handlers = {'inline': [], 'command': [], 'text': [], 'default':[], 'add-in':[],
                         'reply':[], 'query':[], 'title':[], 'off':[], 'regex':[], 'photo':[],
                         'video':[], 'videonote':[]}
        
        bot_id = token.split(':')[0]
        try:
            bot_user = TgUser.objects.get(pk=int(bot_id))
        except:
            dj_user = User.objects.create(username='self-{}'.format(bot_id),
                            first_name='self')
            bot_user = TgUser.objects.create(id=int(bot_id), dj=dj_user, is_bot=True)
            
        self.runtime.set_cache("TgUser", int(bot_id), bot_user)
        
        cmd = SessionMiddleware(lambda: None)
        self.dispatcher.add_handler(cmd)
        self.handlers['default'].append(cmd)
        
        #we register inline command
        self.install_default_inline_command_handler()
        # we register command
        self.install_default_command_handler()
        # we register callback query
        self.install_default_callback_query_handler()
        
    def install_default_inline_command_handler(self):
        cmd = InlineCommandHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['inline'].append(cmd) 
        
    def install_default_command_handler(self):
        cmd = CommandHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['command'].append(cmd)
        
    def install_default_text_handler(self):
        cmd = TextHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['text'].append(cmd)
        
    def install_default_photo_handler(self):
        cmd = PhotoHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['photo'].append(cmd)
        
    def install_default_video_handler(self):
        cmd = VideoHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['video'].append(cmd)
        
    def install_default_videonote_handler(self):
        cmd = VideoNoteHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['videonote'].append(cmd)    
        
    def install_default_callback_query_handler(self):
        cmd = CallbackQueryHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['query'].append(cmd)
        
    def register_inline_command(self, callback):
        cmd = InlineCommandHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['inline'].append(cmd)
        
    def register_command(self, callback):
        cmd = CommandHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['command'].append(cmd)
        
    def register_text(self, callback):
        cmd = TextHandler(generic_processor)
        self.dispatcher.add_handler(cmd)
        self.handlers['text'].append(cmd)
        
    def register_add_in_group(self, callback):
        cmd = AddHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['add-in'].append(cmd)
        
    def register_off_chat(self, callback):
        cmd = OffHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['off'].append(cmd)    
        
    def register_reply(self, callback):
        cmd = ReplyHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['reply'].append(cmd)
        
    def register_callback_query(self, callback):
        cmd = CallbackQueryHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['query'].append(cmd)        
        
    def register_new_title(self, callback):
        cmd = NewTitleHandler(callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['title'].append(cmd)
        
    def register_regex(self, pattern, command, args, callback):
        cmd = RegexHandler(pattern, command, args, callback)
        self.dispatcher.add_handler(cmd)
        self.handlers['regex'].append(cmd)
