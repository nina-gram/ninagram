from django import template
from .actions.sending import *

register = template.Library()


@register.filter(safe=True)
def expand_action(action, argument=None):
    if not isinstance(action, dict):
        raise ValueError("action must be a dict")
    
    if action['type'] == 'send_message':
        return action_send_message(action)
