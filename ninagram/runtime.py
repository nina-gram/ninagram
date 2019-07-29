try:
    from loguru import logger
except:
    pass
import time


class Runtime:

    __data = {}
    __instance = None
    __cache = {}  # we use this for cache

    def __new__(cls, *args, **kwargs):
        if Runtime.__instance is None:
            Runtime.__instance = object.__new__(cls)

        return Runtime.__instance

    def __init__(self, *args, **kwargs):
        pass

    def set(self, user_id, chat_id, state_name, key, value):
        """This method set a value for a key for a certain state
        state_name: name of a State
        key: a string
        value: any value to set to the key"""
        if user_id not in self.__data:
            self.__data[user_id] = {}

        if chat_id not in self.__data[user_id]:
            self.__data[user_id][chat_id] = {}

        if state_name not in self.__data[user_id][chat_id]:
            self.__data[user_id][chat_id][state_name] = {}

        self.__data[user_id][chat_id][state_name][key] = value
        logger.trace("set ::{}::{}::{}::{}::{}", user_id, chat_id,
                     state_name, key, self.__data[user_id][chat_id][state_name][key])

    def get(self, user_id, chat_id, state_name, key, default, insert=False):
        """This method get a value of a key for a certain state
        state_name: name of a state
        key: a string
        default: the value to return if key not found
        insert: if true, if the key is not found, the key with default as value"""
        logger.trace("get ::{}::{}", user_id, chat_id, repr(self.__data))
        #print("%s::get"%self.__class__, user_id, chat_id, repr(self.__data))
        if (user_id not in self.__data) or (chat_id not in self.__data[user_id]) or (state_name not in self.__data[user_id][chat_id]) or (key not in self.__data[user_id][chat_id][state_name]):
            if insert == True:
                self.set(user_id, chat_id, state_name, key, default)
            return default

        logger.trace("get ::{}::{}::{}::{}::{}", user_id, chat_id,
                     state_name, key, self.__data[user_id][chat_id][state_name][key])
        return self.__data[user_id][chat_id][state_name][key]

    def set_error(self, user_id, chat_id, state_name, error):
        """This method set the last error for a state
        state_name: name of a state
        error: the error to set"""
        self.set(user_id, chat_id, state_name, 'error', error)

    def clear_error(self, user_id, chat_id, state_name):
        """This method clear the error setted
        state_name: the name of a state"""
        self.set(user_id, chat_id, state_name, 'error', None)

    def get_error(self, user_id, chat_id, state_name, clear=True):
        """This method get the last error
        state_name: the name of a state
        clear: if True the error is cleared after getted (Default)"""
        res = self.get(user_id, chat_id, state_name,
                       'error', None, insert=True)
        if clear:
            self.clear_error(user_id, chat_id, state_name)
        return res

    def set_step(self, user_id, chat_id, state_name, step):
        """This method set the next step for a state
        state_name: name of a state
        step: the next step number (or anything if you want to manage it yourself)"""
        self.set(user_id, chat_id, state_name, 'step', step)

    def reset_step(self, user_id, chat_id, state_name):
        """This method reset the step of the state to the step 1
        state_name: the name of the state"""
        self.set(user_id, chat_id, state_name, 'step', 1)

    def get_step(self, user_id, chat_id, state_name, default):
        """This method get the current step of a state
        if the step is not found, set it to default and return default
        state_name: name of a state
        default: the value of the step to set if not found"""
        return self.get(user_id, chat_id, state_name, 'step', default)

    def set_return(self, user_id, chat_id, state_name, ret):
        """This method set if we must return from the previous method without any further call.
        If ret is True"""
        self.set(user_id, chat_id, state_name, "return", ret)

    def get_return(self, user_id, chat_id, state_name, default):
        return self.get(user_id, chat_id, state_name, 'return', default)

    def clear_return(self, user_id, chat_id, state_name):
        self.set(user_id, chat_id, state_name, 'return', False)

    def get_cache(self, model_name, pkid):
        """This method get a model instance from cache/memory. If the cache is (id not found) then it return None."""
        if model_name not in self.__cache:
            self.__cache[model_name] = {}
            return None

        try:
            instance = self.__cache[model_name][pkid]['instance']
            self.__cache[model_name][pkid]['last'] = time.time()
            return instance
        except Exception as e:
            #logger.exception(str(e))
            return None

    def set_cache(self, model_name, pkid, instance):
        """This method add a model instance in cache/memory."""
        if model_name not in self.__cache:
            self.__cache[model_name] = {}

        self.__cache[model_name][pkid] = {
            'instance': instance, 'last': time.time()}
        return True


if __name__ == "__main__":
    run1 = Runtime()
    run2 = Runtime()
    run3 = Runtime()

    print(repr(run1))
    print(repr(run2))
    print(repr(run3))
