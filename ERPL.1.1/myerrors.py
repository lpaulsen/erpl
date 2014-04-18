# A class for reporting various non-fatal issues
class MySyntaxError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
        
class MyRuntimeError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)