class Type:
    def __init__(self, top, subtype = None):
        self.top = top
        self.subtype = subtype
        
    def specify(self, type):
        if self.top == 'any':
            self.top = type.top
            self.subtype = type.subtype
        if self.subtype:
            self.subtype.specify(type)
            
    def to_string(self, nested = False):
        s = ""
        if self.top == 'num':
            s += "numbers" if nested else "number"
        elif self.top == 'str':
            s += "texts" if nested else "text"
        elif self.top == 'bool':
            s += "decisions" if nested else "decision"
        elif self.top == 'list':
            s += "lists of " if nested else "list of " 
            s += self.subtype.to_string(nested = True)
        elif self.top == 'table':
            s += "tables of " if nested else "table of " 
            s += self.subtype.to_string(nested = True)
        elif self.top == 'var':
            s += "variable holding a " + self.subtype.to_string(nested = False)
        elif self.top == 'ref':
            s += "reference to a " + self.subtype.to_string(nested = False)
        elif self.top == 'any':
            s += "generic"
        elif self.top == 'statement':
            s += "statement"
        elif self.top == 'noun':
            s += "unresolved variable"
        else:
            s += "unknown type: %s (Bad! Please report!)" % self.top 
        return s
            
    def __repr__(self):
        return self.to_string()