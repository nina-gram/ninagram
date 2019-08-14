import telegram
from ninagram.handlers import *
from telegram.ext import MessageHandler, Filters
from telegram import ParseMode
from loguru import logger
from .state import get_state
from .models import TgUser, User
from .runtime import Runtime
from .middlewares import SessionMiddleware
import importlib
    
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
    It is a singleton.
    """
    
    REQUEST_KWARGS={
        'proxy_url': 'http://127.0.0.1:8080/',
    }
    
    instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super(Bot, cls).__new__(cls)
            cls.instance.__init__(*args, **kwargs)
        return cls.instance
    
    def __init__(self, tokens):
        self.init(tokens)
        
    def init(self, tokens):
        """We get a list of tokens"""
        if len(tokens) < 1:
            return
        
        self.runtime = Runtime()
        
        self.handlers = {'inline': [], 'command': [], 'text': [], 'default':[], 'add-in':[],
                         'reply':[], 'query':[], 'title':[], 'off':[], 'regex':[], 'photo':[],
                         'video':[], 'videonote':[]}        
        
        if not hasattr(self, 'token'):
            self.tokens = {}
        
        for token in tokens:
            if not isinstance(token, str):
                logger.warning("token is not a string. Ignoring")
                continue
            
            bot = telegram.Bot(token)
            updater = telegram.ext.Updater(token, request_kwargs=None)
            dispatcher = updater.dispatcher
            job_queue = updater.job_queue
            self.tokens[token] = {'bot':bot, 'updater':updater,
                        'dispatcher':dispatcher, 'job_queue':job_queue}
            
            bot_id = token.split(':')[0]
            try:
                bot_user = TgUser.objects.get(pk=int(bot_id))
            except:
                dj_user = User.objects.create(username='self-{}'.format(bot_id),
                                first_name='self')
                bot_user = TgUser.objects.create(id=int(bot_id), dj=dj_user, is_bot=True)
                
            self.runtime.set_cache("TgUser", int(bot_id), bot_user)      
            
        cmd = SessionMiddleware(lambda: None)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['default'].append(cmd)            
        
        self.install_default_command_handler()
        self.install_default_inline_command_handler()
        self.install_default_callback_query_handler()
        #self.install_accept_all()
        self.install_default_text_handler()
        self.install_default_document_handler()
        self.install_default_photo_handler()
        self.install_default_contact_handler()
        self.install_default_location_handler()
        
        self.started = False
        logger.info("self.started {}", self.started)
        
    def start_polling(self):
        if  not hasattr(self, 'started'):
            logger.info("Can't initialize")
            return
            
        if not self.started:
            logger.info("{}", settings.NINAGRAM['STATES_MODULES'])
            for module in settings.NINAGRAM['STATES_MODULES']:
                logger.info("Importing {}", module)
                importlib.import_module(module)
                
            for token in self.tokens.values():
                try:
                    token['updater'].start_polling()
                except Exception as e:
                    logger.exception(str(e))
        else:
            logger.info("Already started")
            
    def idle(self):
        try:
            for token in self.tokens.values():
                try:
                    token['updater'].idle()
                    break
                except Exception as e:
                    logger.exception(str(e))
        except Exception as e:
            logger.exception(str(e))
            
    def install_accept_all(self):
        cmd = AllMessageHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['inline'].append(cmd)        
        
        
    def install_default_inline_command_handler(self):
        cmd = InlineCommandHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['inline'].append(cmd) 
        
    def install_default_command_handler(self):
        cmd = CommandHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd) 
        
    def install_default_text_handler(self):
        cmd = TextHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd) 
        
    def install_default_photo_handler(self):
        cmd = PhotoHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd)
            
    def install_default_document_handler(self):
        cmd = DocumentHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd)    
            
    def install_default_contact_handler(self):
        cmd = ContactHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd)    
            
    def install_default_location_handler(self):
        cmd = LocationHandler(generic_processor)
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
            self.handlers['command'].append(cmd)        
        
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
        for token in self.tokens.values():
            dispatcher = token['dispatcher']
            dispatcher.add_handler(cmd)
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
