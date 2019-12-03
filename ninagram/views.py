"""
This module defines views to handle telegram update via webhook
"""
from django.views.decorators.csrf import csrf_exempt
from ninagram.bot import Bot
from telegram import Update
import json
from django.conf import settings
from django.http import HttpResponse
from loguru import logger

@csrf_exempt
def handle_webhook(request, token):
    if token not in settings.NINAGRAM["TOKENS"]:
        return
    
    try:
        try:
            data = json.loads(request.body)
        except:
            data = json.loads(request.body.decode())
                    
        ninabot = Bot(settings.NINAGRAM["TOKENS"])
        bot = ninabot.tokens[token]['bot']
        dispatcher = ninabot.tokens[token]['dispatcher']
        update = Update.de_json(data, bot)            
        
        dispatcher.process_update(update)
    except Exception as e:
        logger.exception(str(e))
        
    return HttpResponse("OK")
