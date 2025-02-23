from abc import ABC, abstractmethod
from typing import List
from enum import Enum, auto
import atexit

class LogLevel(Enum):
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class LogHandler(ABC):

    @abstractmethod
    def log(self, message, level: LogLevel = LogLevel.INFO):
        pass

class ConsoleLogHandler(LogHandler):
    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level 
    def log(self, message, level: LogLevel = LogLevel.INFO):
        if level.value < self.level.value:
            return
        print(message)

class FileLogHandler(LogHandler):
    def __init__(self, file_path, level: LogLevel = LogLevel.INFO):
        self.level = level
        self.file_path = file_path
        self.file = open(file_path, 'a')
        atexit.register(self.file.close)

    def log(self, message, level: LogLevel = LogLevel.INFO):
        if level.value < self.level.value:
            return
        self.file.write(str(message) + '\n')
        self.file.flush()
    
    def close(self):
        if self.file and not self.file.closed:
            self.file.close()
            self.file = None



class Logger:
    def __init__(self):
        self.log_handlers:List[LogHandler] = []

    def add_handler(self, handler:LogHandler):
        self.log_handlers.append(handler)

    def log(self, message, level: LogLevel = LogLevel.INFO):
        for handler in self.log_handlers:
            handler.log(str(message), level)

if __name__ == '__main__':
    logger = Logger()
    logger.add_handler(ConsoleLogHandler(LogLevel.INFO))
    logger.add_handler(FileLogHandler('log.txt', LogLevel.DEBUG))

    logger.log('Hello, world!', LogLevel.INFO)
    logger.log('Goodbye, world!', LogLevel.DEBUG)
