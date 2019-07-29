from django.utils.translation import gettext as _
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninagram.state import State
from ninagram.response import MenuResponse, NextResponse, InputResponse
from loguru import logger
import calendar
import datetime
from ninagram.inputs.base import AbstractInput


class DateInput(AbstractInput):
    
    def menu(self, update:telegram.Update):
        try:
            year = self.get_run('year', None)
            month = self.get_run('month', None)
            day = self.get_run('day', None)
            
            error = self.get_error()
            message = ""
            
            if not year:
                message = _("Please select the year:")
                replies = [[InlineKeyboardButton(_("2015"), callback_data="2015"),
                            InlineKeyboardButton(_("2016"), callback_data="2016"),
                            InlineKeyboardButton(_("2017"), callback_data="2017")]]
                replies.append([InlineKeyboardButton(_("2018"), callback_data="2018"),
                            InlineKeyboardButton(_("2019"), callback_data="2019"),
                            InlineKeyboardButton(_("2020"), callback_data="2020")])
                replies.append([InlineKeyboardButton(_("2021"), callback_data="2021"),
                            InlineKeyboardButton(_("2022"), callback_data="2022"),
                            InlineKeyboardButton(_("2023"), callback_data="2023")])
                kbd = InlineKeyboardMarkup(replies)
                message = self.add_error_to_msg(message)
                return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
            else:
                message = _("{}: --/--/{}").format(self.name, year)
                
            if not month:
                message += _("\n\nPlease select the month:")
                replies = [[InlineKeyboardButton(_("01"), callback_data="1"),
                            InlineKeyboardButton(_("02"), callback_data="2"),
                            InlineKeyboardButton(_("03"), callback_data="3")]]
                replies.append([InlineKeyboardButton(_("04"), callback_data="4"),
                            InlineKeyboardButton(_("05"), callback_data="5"),
                            InlineKeyboardButton(_("06"), callback_data="6")])
                replies.append([InlineKeyboardButton(_("07"), callback_data="7"),
                            InlineKeyboardButton(_("08"), callback_data="8"),
                            InlineKeyboardButton(_("09"), callback_data="9")])
                replies.append([InlineKeyboardButton(_("10"), callback_data="10"),
                            InlineKeyboardButton(_("11"), callback_data="11"),
                            InlineKeyboardButton(_("12"), callback_data="12")])
                replies.append([InlineKeyboardButton(_("Clear"), callback_data="clear")])
                kbd = InlineKeyboardMarkup(replies)
                message = self.add_error_to_msg(message)
                return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
            else:
                message = _("{}: --/{}/{}").format(self.name, month, year)
                
            if not day:
                message += _("\n\nPlease select the day:")
                replies = [[InlineKeyboardButton(_("01"), callback_data="1"),
                            InlineKeyboardButton(_("02"), callback_data="2"),
                            InlineKeyboardButton(_("03"), callback_data="3")]]
                replies.append([InlineKeyboardButton(_("04"), callback_data="4"),
                            InlineKeyboardButton(_("05"), callback_data="5"),
                            InlineKeyboardButton(_("06"), callback_data="6")])
                replies.append([InlineKeyboardButton(_("07"), callback_data="7"),
                            InlineKeyboardButton(_("08"), callback_data="8"),
                            InlineKeyboardButton(_("09"), callback_data="9")])
                replies.append([InlineKeyboardButton(_("10"), callback_data="10"),
                            InlineKeyboardButton(_("11"), callback_data="11"),
                            InlineKeyboardButton(_("12"), callback_data="12")])
                replies.append([InlineKeyboardButton(_("13"), callback_data="13"),
                            InlineKeyboardButton(_("14"), callback_data="14"),
                            InlineKeyboardButton(_("15"), callback_data="15")])
                replies.append([InlineKeyboardButton(_("16"), callback_data="16"),
                            InlineKeyboardButton(_("17"), callback_data="17"),
                            InlineKeyboardButton(_("18"), callback_data="18")])
                replies.append([InlineKeyboardButton(_("19"), callback_data="19"),
                            InlineKeyboardButton(_("20"), callback_data="20"),
                            InlineKeyboardButton(_("21"), callback_data="21")])
                replies.append([InlineKeyboardButton(_("22"), callback_data="22"),
                            InlineKeyboardButton(_("23"), callback_data="23"),
                            InlineKeyboardButton(_("24"), callback_data="24")])
                replies.append([InlineKeyboardButton(_("25"), callback_data="25"),
                            InlineKeyboardButton(_("26"), callback_data="26"),
                            InlineKeyboardButton(_("27"), callback_data="27")])
                replies.append([InlineKeyboardButton(_("28"), callback_data="28"),
                            InlineKeyboardButton(_("29"), callback_data="29"),
                            InlineKeyboardButton(_("30"), callback_data="30")])
                replies.append([InlineKeyboardButton(_("31"), callback_data="31")])                
                replies.append([InlineKeyboardButton(_("Clear"), callback_data="clear")])
                kbd = InlineKeyboardMarkup(replies)
                message = self.add_error_to_msg(message)
                return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
            else:
                message = _("{}: {}/{}/{}").format(self.name, day, month, year)
                
            replies = [[InlineKeyboardButton(_("Clear"), callback_data="clear")],
                       [InlineKeyboardButton(_("OK"), callback_data="ok")]]
            kbd = InlineKeyboardMarkup(replies)
            message = self.add_error_to_msg(message)
            
            return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            self.update = update
            self.text = self.get_text()
            
            year = self.get_run('year', None)
            month = self.get_run('month', None)
            day = self.get_run('day', None)            
                        
            if self.text.lower() == "ok":
                value = {'year':year, 'month':month, 'day':day}
                return InputResponse(InputResponse.STOP, None, value)
            
            if self.text.lower() == "clear":
                self.set_run('year', None)
                self.set_run('month', None)
                self.set_run('day', None)                
                return InputResponse(InputResponse.CONTINUE, None, None)
            
            if not year:
                try:
                    self.set_run('year', int(self.text))
                except:
                    self.set_error("Please enter a valid year")
                return InputResponse(InputResponse.CONTINUE, None, None)
            
            if not month:
                try:
                    self.set_run('month', int(self.text))
                except:
                    self.set_error("Please enter a valid month")
                return InputResponse(InputResponse.CONTINUE, None, None)
            
            if not day:
                try:
                    self.set_run('day', int(self.text))
                except:
                    self.set_error("Please enter a valid day")
                return InputResponse(InputResponse.CONTINUE, None, None)            
        except Exception as e:
            logger.exception(str(e))
            
    def add_error_to_msg(self, message):
        error = self.get_error()
        if error:
            message += _("\n\nError: {}")
        return message
        
        
class CalendarInput(AbstractInput):
    
    weekday_row = [] #Second row - Week Days
    for day in [_("Mo"),_("Tu"), _("We"), _("Th"), _("Fr"), _("Sa") , _("Su")]:
        weekday_row.append(InlineKeyboardButton(day,callback_data="IGNORE::y::m::d"))    
    
    def menu(self, update:telegram.Update):
        try:           
            month = self.get_run('month', None)
            year = self.get_run('year', None)
            now = datetime.datetime.now()
            
            if year is None: year = now.year
            if month is None: month = now.month
            data_ignore = "IGNORE::{}::{}::0".format(year, month)
            keyboard = []
            # First row - Month and Year
            keyboard.append([InlineKeyboardButton(calendar.month_name[month]+" "+str(year),callback_data=data_ignore)])
            keyboard.append(CalendarInput.weekday_row)
            my_calendar = calendar.monthcalendar(year, month)
            for week in my_calendar:
                row=[]
                for day in week:
                    if(day==0):
                        row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
                    else:
                        row.append(InlineKeyboardButton(str(day),callback_data=self.create_callback_data("DAY",year,month,day)))
                keyboard.append(row)
            row=[] #Last row - Buttons
            if month == now.month:
                row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            else:
                row.append(InlineKeyboardButton("<",callback_data=self.create_callback_data("PREV-MONTH",year,month,0)))
            row.append(InlineKeyboardButton(" ",callback_data=data_ignore))
            row.append(InlineKeyboardButton(">",callback_data=self.create_callback_data("NEXT-MONTH",year,month,0)))
        
            keyboard.append(row)
            kbd = InlineKeyboardMarkup(keyboard)
            return InputResponse(InputResponse.CONTINUE, MenuResponse(self.name, markup=kbd), None)
        except Exception as e:
            logger.exception(str(e))
        
    def create_callback_data(self, action, year, month, day):
        return "{}::{}::{}::{}".format(action, year, month, day) 
    
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            (action, year, month, day) = self.text.split("::")
            curr = datetime.datetime(int(year), int(month), 1)
            if action == "IGNORE":
                pass
            elif action == "DAY":
                value = {'year':int(year), 'month':int(month), 'day':int(day)}
                return InputResponse(InputResponse.STOP, None, value)
            elif action == "PREV-MONTH":
                pre = curr - datetime.timedelta(days=1)
                self.set_run('month', pre.month)
                self.set_run('year', pre.year)
            elif action == "NEXT-MONTH":
                ne = curr + datetime.timedelta(days=31)
                self.set_run('month', ne.month)
                self.set_run('year', ne.year)
            else:
                logger.exception("Unexpected entry")
                
            return InputResponse(InputResponse.CONTINUE, None, None)
        except Exception as e:
            logger.exception(str(e))
            
            
class SelectInput(AbstractInput):
    
    def __init__(self, update:telegram.Update, dispatcher:telegram.ext.Dispatcher, *args, **kwargs):
        super(SelectInput, self).__init__(update, dispatcher, *args, **kwargs)
        self.choices = kwargs.get('choices', [])        
        self.multiple = kwargs.get('multiple', False)
        if self.multiple:
            self.selected = kwargs.get('selected', [])
        else:
            self.selected = kwargs.get('selected', None)
        self.offset = kwargs.get('offset', 10)
        self.initial = self.selected
        
    def menu(self, update:telegram.Update):
        try:
            message = _("Please select a {}".format(self.name))
            replies = []
            start = self.get_run('start', 0, insert=True)
            
            real_start = start * self.offset
            real_end = real_start + self.offset
            for row in self.choices[real_start:real_end]:
                if isinstance(row, tuple):
                    text, value = row
                else:
                    text = value = row
                    
                if self.multiple:
                    if value in self.selected:
                        text += " ✅"
                else:
                    if value == self.selected:
                        text += " ✅"
                
                replies.append([InlineKeyboardButton(_(text), callback_data="value::{}".format(value))])
                
            row = []
            if start > 0:
                row.append(InlineKeyboardButton(_("⏪"), callback_data="nav::{}".format(start-1)))
                
            all_pages = len(self.choices) // self.offset
            rest = len(self.choices) % self.offset
            range_max = min([all_pages, start+3])
                        
            inside = []
            for page in range(start+1, range_max+1):
                inside.append(page)
                
            avail = 3 - len(inside)
            if avail:
                for page in range(start-avail, start):
                    if page < 0:
                        continue
                    inside.append(page)
                
            inside = sorted(inside)
            for page in inside:
                row.append(InlineKeyboardButton(_("{}".format(page+1)),
                                                 callback_data='nav::{}'.format(page)))
                
            if start > all_pages:
                pass
            elif start == all_pages and rest!=0:
                pass
            else:
                row.append(InlineKeyboardButton(_("⏩"), callback_data="nav::{}".format(start+1)))
                
            replies.append(row)
            
            replies.append([InlineKeyboardButton(_("OK"), callback_data="ok::ok"),
                            InlineKeyboardButton(_("Cancel"), callback_data="cancel::cancel")])
            kbd = InlineKeyboardMarkup(replies)
            
            return InputResponse(InputResponse.CONTINUE, MenuResponse(message, kbd), None)
        except Exception as e:
            logger.exception(str(e))
            
    def next(self, update:telegram.Update):
        try:
            self.text = self.get_text(update)
            
            action, value = self.text.split("::")
            
            if action.lower() == "nav":
                self.set_run('start', int(value))
            elif action.lower() == "value":
                if self.multiple:
                    self.selected.append(value)
                else:
                    self.selected = value
            elif action.lower() == "ok":
                return InputResponse(InputResponse.STOP, None, self.selected)
            elif action.lower() == "cancel":
                return InputResponse(InputResponse.STOP, None, self.initial)
            
            return InputResponse(InputResponse.CONTINUE, None, None)
        except Exception as e:
            logger.exception(str(e))
