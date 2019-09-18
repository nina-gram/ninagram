from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from ninagram.bot import Bot


class Command(BaseCommand):
    """Start the bot"""
    
    def handle(self, *args, **options):
        print("Starting the bot...")
        
        try:
            
            tokens = settings.NINAGRAM['TOKENS']
            self.ninabot  = Bot(tokens)
            self.ninabot.init(tokens)
            print("Ninagram is now fully loaded")
            
            if settings.NINAGRAM['WORKING_MODE']:
                if settings.NINAGRAM['WORKING_MODE'].lower() == "polling":
                    self.ninabot.start_polling()
                elif settings.NINAGRAM['WORKING_MODE'].lower() == "webhook":
                    self.ninabot.start_webhook()
                else:
                    raise ValueError("Working mode not recognised. We ignored it.")
                self.ninabot.idle()
        except Exception as e:
            import traceback
            traceback.print_exc()        
            
        print("Successfully renewed all the User's sms")