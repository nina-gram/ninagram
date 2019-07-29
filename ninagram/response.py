import telegram
from loguru import logger


class MenuResponse:
    """
    This class represent the response of a menu method of a state.
    """
    
    def __init__(self, message, markup=None, edit=False, force_return=True, parse_mode=None, 
                 edit_inline_callback=True, reply=False):
        self.message = message
        self.markup = markup
        self.edit = edit
        self.parse_mode = parse_mode
        self.edit_inline_callback = edit_inline_callback
        self.force_return = force_return
        self.reply = reply
        
    def apply(self, update:telegram.Update):
        """
        This method apply this response to the update passed in arguments using the Bot instance passed.
        
        Args:
            * update: `telegram.Update` instance
            * bot: `telegram.Bot` object
        """
        try:
            bot = update.effective_message.bot
                        
            # we check if it is a callback_query and we must edit the message
            if update.callback_query != None and self.edit_inline_callback:
                update.callback_query.answer()
                bot.edit_message_text(self.message, chat_id=update.effective_chat.id,
                                      message_id=update.callback_query.message.message_id, 
                                      reply_markup=self.markup, parse_mode=self.parse_mode)
                return [update.callback_query.message]
                        
            if self.edit:
                bot.edit_message_text(self.message, chat_id=update.effective_chat.id,
                                                  message_id=update.message.message_id, 
                                                  reply_markup=self.markup, parse_mode=self.parse_mode)
                return [update.message]
                        
            chatid = update.effective_chat.id
            
            if self.reply:
                reply_to_id = update.effective_message.message_id
            else:
                reply_to_id = None
                
            all_send_msg = []
            while len(self.message) > 4000:
                msg = bot.sendMessage(chatid, self.message[:4000], parse_mode=self.parse_mode, 
                                      reply_markup=self.markup, reply_to_message_id=reply_to_id)
                
                self.message = self.message[4000:]
                all_send_msg.append(msg)
        
            msg = bot.sendMessage(chatid, self.message, parse_mode=self.parse_mode,
                                  reply_markup=self.markup, reply_to_message_id=reply_to_id)
            all_send_msg.append(msg)
            return all_send_msg
        except Exception as e:
            logger.exception(str(e))
            
            
class NextResponse:
    """
    This class represent the response of a next method of a state.
    """
    
    def __init__(self, state, step=None, force_return=False):
        self.state = state
        self.step = step
        self.force_return = force_return
        
        
class InputResponse:
    """
    This class represent the response of an input
    """
    
    CONTINUE = 1
    ABORT = 0
    STOP = -1
    
    def __init__(self, status, menu_response, value):
        self.status = status
        self.value = value
        self.menu_response = menu_response