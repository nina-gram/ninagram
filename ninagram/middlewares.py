import re
import telegram
import telegram.ext
from loguru import logger
from .models import Chat, User, Session, Channel, Group, TgUser
import traceback


class Database:

    session = None
    user = None
    chat = None


class SessionMiddleware(telegram.ext.Handler):
    """
    This class implement a Session Middleware that ensure that every request that is handled is linked to a 
    database user, chat and session.
    If the user and/or chat is new then it creates the objects and save them in the database.
    Here are all the steps performed by the SessionMiddleware:
        1. Checks if the update is from a channel, if yes then save the channel and return
        2. Check if the user exist in the database, else create it. There are 2 type of users as per
        our models. TgUser represent a telegram User and User is the django User model
        3. Check if the chat exists in the database, else created it. Determine the type of 
        the chat. If it is a group then create a group object and saved it to the database.
        4. Check if there is an existing session if no then create the corresponding one and save it.
        5. Attache new attribute .db.user, .db.chat and .db.session to the update received
    
    Also note that this class (that is a handler) never return True to not stop the Update that was 
    just augmented.
    """

    def check_update(self, update: telegram.Update):
        logger.debug("SessionMiddleware in action")
        try:
            if update.effective_chat.type == "channel":
                try:
                    Channel.custom_save(
                        update.effective_chat.id, update.effective_chat.title, update.effective_chat.username)
                except Exception as e:
                    logger.exception(str(e))
                return False

            try:
                # Try to load the TgUser from the cache
                db_user = TgUser.cache_get(update.effective_user.id)
                assert db_user != None
                
                # TODO: decide whether or not to check for any changes
            except:
                first_name = update.effective_user.first_name if update.effective_user.first_name != None else ""
                last_name = update.effective_user.last_name if update.effective_user.last_name != None else ""
                username = update.effective_user.username if update.effective_user.username != None else str(
                    update.effective_user.id)
                lang = update.effective_user.language_code
                
                dj_user = User.objects.create(
                    id=update.effective_user.id, first_name=first_name, last_name=last_name, username=username)
                
                db_user = TgUser.objects.create(id=update.effective_user.id, dj=dj_user)
                
                if lang:
                    db_user.chat.lang = lang
                    db_user.chat.save()

            try:
                db_chat = Chat.cache_get(update.effective_chat.id)
                assert db_chat != None
            except:
                is_supergroup = True if update.effective_chat.type == "supergroup" else False
                grp = Group.custom_save(update.effective_chat.id, update.effective_chat.title,
                                        update.effective_chat.username, is_supergroup=is_supergroup)
                db_chat = grp.chat

            try:
                db_session = Session.cache_get(chat=db_chat, user=db_user)
                assert db_session is not None
            except:
                db_session = Session.objects.create(
                    chat=db_chat, user=db_user, state="START")

            # we augment the Update instance.
            update.db = Database
            update.db.session = db_session
            update.db.chat = db_chat
            update.db.user = db_user
            logger.debug("update.db.session {}", update.db.session)
            logger.debug("update.db.chat {}", update.db.chat)
            logger.debug("update.db.user {}", update.db.user)
        except Exception as e:
            logger.exception(str(e))

        return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
