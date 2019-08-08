"""
This module defines views to handle telegram update via webhook
"""
from django.views.decorators.csrf import csrf_exempt
from ninagram.bot import Bot
from telegram import Update
import json

@csrf_exempt
def handle_webhook(request, token):
    try:
        try:
            data = json.loads(request.body)
        except:
            data = json.loads(request.body.decode())
        
        ninabot = Bot(None)
        update = Update.de_json(data, ninabot.bot)            
        
        bot.dispatcher.process_update(update)