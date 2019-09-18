"""This module contains function for handling sending actions"""
from django.utils.safestring import mark_safe

def action_send_message(action:dict):
    message = action.get('message')
    id = action.get('id')
    
    if isinstance(id, str) or isinstance(id, int):
        if id == 'admins':
            res = """# send message to admins
        for user in User.objects.filter(is_superuser=True):
            self.dispatcher.bot.send_message(user.tg.id, _("{}"))""".format(message)
        elif id == "staff":
            res = """# send message to staff
        for user in User.objects.filter(is_staff=True):
            self.dispatcher.bot.send_message(user.tg.id, _("{}"))""".format(message)
        elif isinstance(id, int) or id.isnumeric():
            res = """# sending message to f{id}
        self.dispatch.bot.send_message({id}, _("{message}"))""".format(id=id, message=message)
            
        return mark_safe(res)
    elif isinstance(id, list):
        res = """# send message to those chat id
        for chat_id in ({chat_ids}):
            self.dispatcher.bot.send_message(chat_id, _("{message}"))"""\
            .format(message=message, chat_ids=', '.join([str(item) for item in id]))
        
        return mark_safe(res)
