# !/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'imajeason'

import sys
from threading import Thread,Lock
import threading
from Queue import Queue

#signal超时处理
def handler(signum, frame):
    raise AssertionError
class Timeout(Exception):
    """function run timeout"""
class KThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.killed = False
    def start(self):
        """Start the thread."""
        self.__run_backup = self.run
        # Force the Thread to install our trace.
        self.run = self.__run
        threading.Thread.start(self)
    def __run(self):
        """Hacked run function, which installs the trace."""
        sys.settrace(self.globaltrace)
        self.__run_backup()
        self.run = self.__run_backup
    def globaltrace(self, frame, why, arg):
        if why == 'call':
            return self.localtrace
        else:
            return None
    def localtrace(self, frame, why, arg):
        if self.killed:
            if why == 'line':
                raise SystemExit()
        return self.localtrace
    def kill(self):
        self.killed = True

def timeout(timeout, default=None, try_except=False):
    """Timeout decorator, parameter in timeout."""
    def timeout_decorator(func):
        def new_func(oldfunc, result, oldfunc_args, oldfunc_kwargs):
            result.append(oldfunc(*oldfunc_args, **oldfunc_kwargs))
        """Wrap the original function."""
        def func_wrapper(*args, **kwargs):
            result = []
            # create new args for _new_func, because we want to get the func
            # return val to result list
            new_kwargs = {
                'oldfunc': func,
                'result': result,
                'oldfunc_args': args,
                'oldfunc_kwargs': kwargs
            }
            thd = KThread(target=new_func, args=(), kwargs=new_kwargs)
            thd.start()
            thd.join(timeout)
            # timeout or finished?
            isAlive = thd.isAlive()
            thd.kill()
            if isAlive:
                if try_except is True:
                    raise Timeout("{} Timeout: {} seconds.".format(func, timeout))
                return default
            else:
                return result[0]
        func_wrapper.__name__ = func.__name__
        func_wrapper.__doc__ = func.__doc__
        return func_wrapper
    return timeout_decorator


