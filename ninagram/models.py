from django.db import models
from timezone_field import TimeZoneField
from django.contrib.auth import get_user_model
from django.contrib.admin import site
from django.conf import settings
from datetime import datetime
from .cache import SimpleCache
from .runtime import Runtime
try:
    from loguru import logger
except:
    pass

LANG = getattr(settings,"LANGUAGE_CODE", 'en')
    
AVAIL_LANGS = getattr(settings, "AVAIL_LANGS", ['en'])

User = get_user_model()

# Create your models here.


class Chat(models.Model, SimpleCache):
    """
    This model help us represent the telegram Chat object in database.
    But it adds also various field that help in dealing telegram Chat.
    
    id: the telegram Chat id
    join_date: the date when the Chat is created in database (in fact 
        when the bot is added in the chat)
    username: the telegram Username
    is_staff: is this chat a staff group for the bot
    type: the telegram Chat.TYPE
    timezone: the timezone of this group
    lang: the language of this group"""

    id = models.IntegerField(unique=True, primary_key=True)
    join_date = models.DateTimeField(auto_now=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=100, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    type = models.CharField(max_length=20)
    timezone = TimeZoneField(null=True)
    lang = models.CharField(max_length=10, default=LANG)

    def __str__(self):
        return "%s - %s" % (self.id, self.title)


class Group(models.Model, SimpleCache):
    """
    This model help just to match a chat.
    
    chat: the corresponding Chat"""

    chat = models.OneToOneField(Chat, models.SET_NULL, null=True)
    
    @property
    def username(self):
        return self.chat.username
    
    @username.setter
    def set_username(self, username):
        self.chat.username = username
    
    @property
    def title(self):
        return self.chat.title
    
    @title.setter
    def set_title(self, title):
        self.chat.title = title

    def __str__(self):
        return self.title

    @classmethod
    def custom_save(cls, chat_id, title, username, is_staff=False, is_supergroup=False):
        if is_supergroup:
            cat = "supergroup"
        else:
            cat = "group"

        try:
            chat = Chat.objects.get(pk=chat_id)
            if chat.title != title:
                chat.title = title
                chat.save()
        except:
            chat = Chat.objects.create(id=chat_id, title=title, type=cat, username=username)

        try:
            grp = Group.objects.get(chat=chat)
        except:
            grp = Group.objects.create(chat=chat)

        return grp


class TgUser(models.Model, SimpleCache):
    """
    This User model help us work with telegram User and Django user in 
    a simple fashion.
    
    id: the telegram ID, unique identifier
    dj: the correspondant Django user
    is_bot: whether or not the user is a bot
    chat: the private chat of the user"""

    id = models.IntegerField(primary_key=True)
    dj = models.OneToOneField(User, models.DO_NOTHING, related_name='tg')
    is_bot = models.BooleanField(default=False)
    chat = models.OneToOneField(Chat, models.SET_NULL, null=True)

    def __str__(self):
        return "%s - %s" % (self.id, self.dj.username)

    def save(self, *args, **kwargs):
        """
        We re-implement this method to ensure that a telegram user always 
        has chat attached to him.
        """
        if self.chat is None:
            self.chat = Chat.objects.get_or_create(id=self.id, title=self.dj.username, 
                        username=self.dj.username, type='private')[0]
        super().save(*args, **kwargs)


class Channel(models.Model, SimpleCache):
    """
    Channel model is used to save channel.
    
    chat: the chat as Chat, that is a channel"""

    chat = models.OneToOneField(Chat, models.SET_NULL, null=True)
    
    @property
    def username(self):
        return self.chat.username
    
    @property
    def title(self):
        return self.chat.title

    def __str__(self):
        return self.title

    @classmethod
    def custom_save(cls, chat_id, title, username):
        try:
            chat = Chat.objects.get(pk=chat_id)
            if chat.title != title:
                chat.title = title
                chat.save()
        except:
            chat = Chat.objects.create(id=chat_id, title=title, type='channel', username=username)

        try:
            chan = Channel.objects.get(chat=chat)
        except:
            chan = Channel.objects.create(chat=chat)

        return chan


class Session(models.Model, SimpleCache):
    """
    The session Model is used to save user interaction with bot.
    
    state: the last state where the user was
    add_infos: additional infos about this session
    last_activity: the last time the user interacted with the bot
    user: the user as a TgUser instance
    chat: the chat as a Chat instance"""

    state = models.CharField(max_length=100)
    add_infos = models.TextField()
    last_activity = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(TgUser, models.CASCADE)
    chat = models.ForeignKey(Chat, models.SET_NULL, null=True)

    class Meta:
        unique_together = ('user', 'chat')

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.last_activity = datetime.utcnow()
        super(Session, self).save(force_insert=force_insert, force_update=force_update,
                                  using=using, update_fields=update_fields)

    @classmethod
    def cache_get(cls, chat, user):
        # we cache the result by their model
        model_name = cls.__name__
        runtime = Runtime()
        pkid = "%s%s" % (chat.id, user.id)
        logger.trace("pkid {}", pkid)
        instance = runtime.get_cache(model_name, pkid)
        if instance is None:
            # if there is no result we get from database and cache it
            instance = cls.objects.get(chat=chat, user=user)
            runtime.set_cache(model_name, pkid, instance)

        return instance

    def __str__(self):
        return "%s - %s" % (self.user.dj.username, self.chat.title)


class Message(models.Model, SimpleCache):
    """
    This model represent some info about a telegram message.
    Please note that this model doesn't store the message content 
    but rather its metadata.
    
    id: match to message_id
    user: match to a TgUser model instance
    date: match to date
    chat: match to a Chat model instance
    data: a text field to add some extra infos about this message
    forward_from_user: match TgUser model instance
    forward_from_chat: match a Chat model instance
    forward_date: match the date when message was forwarded
    edit_date: match the date when message was lastly edited
    reply_to: match to himself (Message)"""

    id = models.IntegerField(primary_key=True, unique=True)
    user = models.ForeignKey(TgUser, models.DO_NOTHING)
    date = models.DateTimeField()
    chat = models.ForeignKey(Chat, models.DO_NOTHING)
    data = models.TextField(blank=True, null=True)
    forward_from_user = models.ForeignKey(TgUser, models.DO_NOTHING, related_name="user_forwarded", blank=True, null=True)
    forward_from_chat = models.ForeignKey(Chat, models.DO_NOTHING, related_name='chat_forwarded', blank=True, null=True)
    forward_date = models.DateTimeField(blank=True, null=True)
    edit_date = models.DateTimeField(blank=True, null=True)
    reply_to = models.ForeignKey('self', models.DO_NOTHING, null=True, blank=True)
    
    def from_tg_msg(self):
        pass
    

class Media(models.Model, SimpleCache):
    """
    This model represent a telegram Media
    
    id: correspond to telegram File_ID
    intern: correspond to a file in the case the media was downloaded
    type: the type of the media
    desc: a small description about the file. To help you query it
    message: a reference to a Message instance"""
    
    id = models.CharField(max_length=255, primary_key=True)
    intern = models.FileField(upload_to='ninagram')
    type = models.CharField(max_length=20)
    desc = models.CharField(max_length=255, null=True, blank=True)
    message = models.ForeignKey(Message, models.DO_NOTHING, null=True, blank=True)