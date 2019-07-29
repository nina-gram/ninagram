from threading import Thread, Lock
from queue import Queue
try:
    from loguru import logger
except:
    pass
import time
from .runtime import Runtime
from django.db.utils import IntegrityError


class Saver(Thread):
    """This thread is just there to save model instance asynchronously.
    This allow others parts of the code to not block while writing in the database.
    It helps for bot that handle many users.
    """

    queue = Queue()

    def run(self):
        while True:
            instance, kwargs = self.queue.get()
            try:
                cached = kwargs.pop('cached', None)
                instance.save(**kwargs)
                
                if cached:
                    Runtime().set_cache(instance.__class__.__name__, instance.id, instance)
            except IntegrityError:
                pass
            except Exception as e:
                logger.exception(str(e))
            self.queue.task_done()


def save_this(instance, **kwargs):
    """
    Use this method to save a model instance in another thread.
    
    Args:
        * instance: the model instance
        * cached(optional): if True the model will be updated in the cache
    """
    Saver.queue.put((instance, kwargs))


saver = Saver()
saver.setDaemon(True)
saver.start()


class SimpleCache:
    """
    This class implements a simple cache. It should be used as a mixing.
    It is based on the simple and useful Runtime class.
    When there is a cache miss then it loads it from Model manager
    """

    @classmethod
    def cache_get(cls, pkid):
        """
        This method fetch and cache model instance. If the model doesn't 
        exist thrown an exception.
        
        Params:
            - cls: the Model class of the instance
            - pkid: the id of the instance
            
        Return:
            - instance of the Model
            
        Raise:
            - cls.DoesNotExist: in case of an id not found
        """
        # we cache the result by their model
        model_name = cls.__name__
        runtime = Runtime()
        instance = runtime.get_cache(model_name, pkid)
        if instance is None:
            # if there is no result we get from database and cache it
            instance = cls.objects.get(pk=pkid)
            runtime.set_cache(model_name, pkid, instance)

        return instance

    def save_after(self, **kwargs):
        """
        This method save the current model instance via the Saver thread.
        In others ways it is asynchronous.
        """
        save_this(self, **kwargs)
