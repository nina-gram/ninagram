from django.apps import AppConfig
from django.conf import settings


class NinagramConfig(AppConfig):
    name = 'ninagram'
    
    def ready(self):
        return True
    
        try:
            from ninagram.bot import Bot
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
                    print("Working mode not recognised. We ignored it.")
        except Exception as e:
            import traceback
            traceback.print_exc()
