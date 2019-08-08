Ninagram
===========

Ninagram is a Django app that let you build Telegram bots with the performant python-telegram-bot.

Do you have a Django website and you plan to back a telegram bot to it ? Then This library is for you.
Even if you want to start a telegram bot from scratch you are good to go with Ninagram

Installation

pip install ninagram


Usage

Fresh start

# create a new Django project
django-admin startproject myproject
cd myproject

# create a new app for your project
python manage.py startapp base

Then you can continue like with like an existing project

# create the states.py file that will contain the bot code
touch base/states.py

# add 'ninagram' to your INSTALLED_APPS in settings.py

then add this configuration to your settings.py

NINAGRAM = {
    "TOKENS": ['token_here'],
    "STATES_MODULES": ['base.states'],
    "WORKING_MODE": "polling",
}

then run your development server
python manage.py runserver

Please note that you should be connected to internet for the bot to work correctly
