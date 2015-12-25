#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ###############################################################################
#
# Copyright (c) 2015 XXX.com, Inc. All Rights Reserved
#
# ###############################################################################

# @Compiler :2.7.10
# @Author  : HuiDong ()
# @Date    : 2015-10-29 11:45:45
# @Link    : http://example.org
# @Version : $Id$
# @Todo: nothing $2015-10-29


"""SYS LIBS
"""
import os
import sys
import time


# Good behaviors. It means refusing called like from xxx import *
# When `__all__` is []
__all__ = []

reload(sys)
sys.setdefaultencoding('utf-8')


# ********************************************************
# * Global defines start.                                *
# ********************************************************

ERROR_LEVEL = {
    0: "EMAIL",
    1: "PHONE",
    -1: "LOG",
    -1: "TERRIBLE ERROR",
    2: "CURRENT POSITON AND FILE SIZE",
}

# ********************************************************
# * Global defines end.                                  *
# ********************************************************


class Tail(object):

    """
    Python-Tail - Unix tail follow implementation in Python.

    python-tail can be used to monitor changes to a file.

    Example:
        import tail

        # Create a tail instance
        t = tail.Tail('file-to-be-followed')

        # Register a callback function to be called when a new line is found in the followed file.
        # If no callback function is registerd, new lines would be printed to standard out.
        t.register_callback(callback_function)

        # Follow the file with 5 seconds as sleep time between iterations.
        # If sleep time is not provided 1 second is used as the default time.
        t.follow(s=5)
    """

    ''' Represents a tail command. '''

    def __init__(self, tailed_file, last_pos=0, err_callback=None):
        ''' Initiate a Tail instance.
            Check for file validity, assigns callback function to standard out.

            Arguments:
                tailed_file - File to be followed.
                last_pos - 程序上一次停止时读取的最后位置，主要用于重启时恢复上次读取的位置，
                           防止数据丢失
        '''

        self.check_file_validity(tailed_file)
        self.tailed_file = tailed_file
        self.callback = sys.stdout.write
        self.err_callback = err_callback
        self.last_pos = int(last_pos)

        self.try_count = 0
        self.read_try = 0

        try:
            self.file_ = open(self.tailed_file, "r")
            self.size = os.path.getsize(self.tailed_file)

            if self.last_pos == 0:
                # Go to the end of file
                self.file_.seek(0, 2)
            else:
                # Go to the last position
                self.file_.seek(self.last_pos, 0)
        except Exception as e:
            raise TailError(str(e))

    def reload_tailed_file(self):
        """ Reload tailed file when it be empty be `echo "" > tailed file`, or
            segmentated by logrotate.
        """
        try:
            self.file_ = open(self.tailed_file, "r")
            self.size = os.path.getsize(self.tailed_file)

            # Go to the head of file
            self.file_.seek(0)

            return True
        except Exception as e:
            if self.err_callback:
                err_msg = {"type": -1,
                           "msg": "Error when reload file, detail: %s" % e}
                self.err_callback(err_msg)
            return False

    def follow(self, s=0.0001):
        """ Do a tail follow. If a callback function is registered it is called with every new line.
        Else printed to standard out.

        Arguments:
            s - Number of seconds to wait between each iteration; Defaults to 1. """

        while True:
            try:
                _size = os.path.getsize(self.tailed_file)
            except Exception as e:
                if self.err_callback:
                    err_msg = {"type": -1,
                               "msg": "Error when get size of '%s', detail: %s" % (self.tailed_file, e)}
                    self.err_callback(err_msg)
                self.try_count += 1

                if self.try_count == 10:
                    if self.err_callback:
                        msg = "Fuck, try open '%s' failed after '%d' times" % (self.tailed_file,
                                                                               self.try_count)
                        err_msg = {"type": -2,
                                   "msg": msg}
                        self.err_callback(err_msg)
                    break
                else:
                    time.sleep(0.2)
                    continue
            else:
                self.try_count = 0

            if _size >= self.size:
                self.size = _size
            else:
                if self.err_callback:
                    msg = "File '%s' is changed" % self.tailed_file
                    err_msg = {"type": -1,
                               "msg": msg}
                    self.err_callback(err_msg)

                while self.try_count < 10:
                    if not self.reload_tailed_file():
                        self.try_count += 1
                    else:
                        self.try_count = 0
                        try:
                            self.size = os.path.getsize(self.tailed_file)
                        except Exception as e:
                            raise TailError(str(e))
                        break
                    time.sleep(0.2)

                if self.try_count == 10:
                    msg = "Open %s failed after try 10 times" % self.tailed_file
                    err_msg = {"type": -2,
                               "msg": msg}
                    self.err_callback(err_msg)
                    break

            try:
                curr_position = self.file_.tell()
                line = self.file_.readline()

                if not line:
                    self.file_.seek(curr_position)
                elif not line.endswith("\n"):
                    self.file_.seek(curr_position)
                else:
                    if self.err_callback:
                        err_msg = {"type": 2, "msg": (self.file_.tell(), self.size)}
                        self.err_callback(err_msg)
                    self.callback(line)

                self.read_try = 0
            except Exception as e:
                self.read_try += 1

                if self.read_try == 1000:
                    if self.err_callback:
                        msg = "Fuck, read data failed, detail:%s" % e
                        err_msg = {"type": -2,
                                   "msg": msg}
                        self.err_callback(err_msg)
                    raise TailError(str(e))
            time.sleep(s)

    def register_callback(self, func):
        """ Overrides default callback function to provided function. """
        self.callback = func

    def check_file_validity(self, file_):
        """ Check whether the a given file exists, readable and is a file """
        if not os.access(file_, os.F_OK):
            raise TailError("File '%s' does not exist" % (file_))
        if not os.access(file_, os.R_OK):
            raise TailError("File '%s' not readable" % (file_))
        if os.path.isdir(file_):
            raise TailError("File '%s' is a directory" % (file_))


class TailError(Exception):

    """ Custom error type.
    """

    def __init__(self, msg):
        """ Init.
        """
        self.message = msg

    def __str__(self):
        """ str.
        """
        return self.message


if __name__ == '__main__':
    t = Tail("/home/syslog/switch.log")

    def print_msg(msg):
        pass

    t.register_callback(print_msg)

    t.follow()

""" vim: set ts=4 sw=4 sts=4 tw=100 et: """
