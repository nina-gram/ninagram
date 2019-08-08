import re
import telegram
import telegram.ext
from loguru import logger
from .models import Chat, User, Session, Channel, Group
from django.conf import settings
import traceback

cmd_prefixes = getattr(settings, "NINAGRAM_COMMAND_PREFIXES", ["/"])

rgx_tags = re.compile("\W?#(\w+)")
rgx_args = re.compile("\W?/(\w+)")
rgx_users = re.compile("\W?@(\w+)")


class Message:

    type = None
    

class AllMessageHandler(telegram.ext.Handler):
    
    def check_update(self, update):
        return True
    
    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class InlineCommandHandler(telegram.ext.Handler):

    rgx_parts = re.compile("^([%s])([a-zA-Z0-9]+)(@[a-zA-Z0-9_]+)?\s?(.*)?" %
                           (''.join(cmd_prefixes)), re.DOTALL)

    def check_update(self, update):
        logger.debug("checking this update")
        try:
            text = update.message.text if update.message != None else update.callback_query.data
            logger.debug("pattern {}", self.rgx_parts.pattern)
            if text is None:
                return False

            match = self.rgx_parts.search(text)
            if not match:
                return False

            cmd_prefix = match.group(1)
            command = match.group(2)
            rest = match.group(4)
            logger.debug("matched {}", match.groups())

            update.message.rest = rest
            tags = rgx_tags.findall(rest)
            args = rgx_args.findall(rest)
            users = rgx_users.findall(rest)

            update.message.tags = tags
            update.message.args = args
            update.message.users = users

            update.type = "command"
            update.message.command = command

            try:
                update.message.text = '%s%s %s' % (
                    cmd_prefix, command, update.message.rest)
            except:
                update.message.text = command

            return True

        except:
            import traceback
            traceback.print_exc()
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class CommandHandler(telegram.ext.Handler):

    rgx_parts = re.compile("^([%s])([a-zA-Z0-9]+)(@[a-zA-Z0-9_]+)?\s?(.*)?" %
                           (''.join(cmd_prefixes)), re.DOTALL)

    def check_update(self, update: telegram.Update):
        logger.debug("checking this update")
        if update.effective_chat.type != "private":
            return False

        try:
            text = update.message.text if update.message != None else update.callback_query.data
            if text is None:
                return False

            match = self.rgx_parts.search(text)
            if not match:
                return False

            cmd_prefix = match.group(1)
            command = match.group(2)
            rest = match.group(3)

            update.message.rest = rest
            tags = rgx_tags.findall(rest)
            args = rgx_args.findall(rest)
            users = rgx_users.findall(rest)

            update.message.tags = tags
            update.message.args = args
            update.message.users = users

            update.type = "command"
            update.message.command = command

            try:
                update.message.text = '%s%s %s' % (
                    cmd_prefix, command, update.message.rest)
            except:
                update.message.text = command

            return True
        except:
            import traceback
            traceback.print_exc()
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class CallbackQueryHandler(telegram.ext.Handler):

    def check_update(self, update: telegram.Update):
        logger.debug("checking this update")
        if update.callback_query is not None:
            return True

        return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class AddHandler(telegram.ext.Handler):

    def check_update(self, update: telegram.Update):
        logger.debug("checking this update")
        if update.message is None:
            return False

        if update.message.new_chat_members:
            try:
                if update.effective_chat.type == "channel":
                    try:
                        Channel.custom_save(
                            update.effective_chat.id, update.effective_chat.title, update.effective_chat.username)
                    except Exception as e:
                        logger.exception(str(e))

                else:
                    is_supergroup = True if update.effective_chat.type == "supergroup" else False
                    grp = Group.custom_save(update.effective_chat.id, update.effective_chat.title,
                                            update.effective_chat.username, is_supergroup=is_supergroup)

                return True
            except Exception as e:
                logger.exception(str(e))

        return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class NewTitleHandler(telegram.ext.Handler):

    def check_update(self, update: telegram.Update):
        logger.debug("checking this update")
        if update.message is None:
            return False

        if update.message.new_chat_title is not None:
            return True
        else:
            logger.info("{}", update.message.new_chat_title)

        return False

    def handle_update(self, update, dispatcher):
        self.callback(dispatcher.bot, update)


class OffHandler(telegram.ext.Handler):

    def check_update(self, update: telegram.Update):
        logger.debug("checking this update")
        if update.message is None:
            return False

        if update.message.left_chat_member is not None:
            if update.message.left_chat_member.id == 665997630:
                return True

        return False

    def handle_update(self, update, dispatcher):
        self.callback(dispatcher.bot, update)


class ReplyHandler(telegram.ext.Handler):

    def check_update(self, update):
        logger.debug("checking this update")
        if update.message is not None and update.message.reply_to_message is not None:
            return True

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class RegexHandler(telegram.ext.Handler):

    def __init__(self, pattern, command, args, callback, pass_update_queue=False, pass_job_queue=False, pass_user_data=False, pass_chat_data=False):
        super(RegexHandler, self).__init__(callback, pass_update_queue=pass_update_queue, pass_job_queue=pass_job_queue,
                                           pass_chat_data=pass_chat_data, pass_user_data=pass_user_data)
        self.pattern = pattern
        self.command = command
        self.args = args

    def check_update(self, update):
        try:
            if update.message is None and update.callback_query is None:
                return False

            text = update.message.text if update.message != None else update.callback_query.data
            if text is None:
                return False

            if self.pattern.search(text):
                update.type = "command"
                update.message.args = self.args
                update.message.command = self.command
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)


class TextHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.text is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        
        
class PhotoHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.photo is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        

class DocumentHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.document is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        
        
class VideoHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.video is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        
        
class VideoNoteHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.video_note is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        
        
class ContactHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.contact is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
        
        
class LocationHandler(telegram.ext.Handler):

    def check_update(self, update):
        try:
            if update.message is not None and update.message.location is not None:
                return True

            return False
        except Exception as e:
            logger.exception(str(e))
            return False

    def handle_update(self, update, dispatcher):
        self.callback(update, dispatcher)
