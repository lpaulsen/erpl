from typespecs import Type
        
# A robust (?) way to store and refer to strings
string_storage = []
string_refs = []

class StringRef:
    def __init__(self, index, beginning = None, end = None):
        self.index = index
        self.beginning = beginning if beginning else 0
        self.end = end if end else len(string_storage[index])
        string_refs[index].append(self)
        
    def update(self, sr):
        string_storage[self.index] = string_storage[self.index][:self.beginning] + sr.to_str() + string_storage[self.index][self.end:]
        difference = self.end - self.beginning - sr.length()
        for ref in string_refs[self.index]:
            if ref.beginning > self.end:
                ref.beginning -= difference
            if ref.end > self.end:
                ref.end -= difference
        self.end -= difference
                
    def to_str(self):
        return string_storage[self.index][self.beginning:self.end]
        
    def length(self):
        return self.end - self.beginning
        
def new_string(str):
    string_storage.append(str)
    string_refs.append([])
    return StringRef(len(string_storage) - 1)
        
# A wrapper class for expression values
class Result:
    def __init__(self, value, type):
        self.value = value
        self.type = type

class NounRef:
    def __init__(self, name, subref = None):
        self.name = name
        self.subref = subref
    
# A NounList exists to keep track of Nouns. Thin wrapper around a dictionary.
class NounList:
    def __init__(self):
        self.nouns = { }
        
    def is_noun(self, name):
        if self.lookup_noun(NounRef(name)):
            return True
        else:
            return False
        
    def get_ref(self, name):
        return Result(NounRef(name), Type("var", self.nouns[name].type))
       
    def add_noun(self, name, type):
        assert not name in self.nouns
        self.nouns[name] = Result(None, type)
        
    def remove_noun(self, name):
        assert name in self.nouns
        del self.nouns[name]
        
    def update_noun(self, nref, value):
        self.lookup_noun(nref).value = value
        
    def access_noun(self, nref):
        return self.lookup_noun(nref).value
        
    def lookup_noun(self, nref):
        if nref.subref:
            sub_noun = self.lookup_noun(nref.subref)
            if not sub_noun:
                return None
            elif sub_noun.type.top == 'list':
                if nref.name >= len(sub_noun.value) or nref.name < 0:
                    return None
                else:
                    return sub_noun.value[nref.name]
            elif sub_noun.type.top == 'table':
                if not nref.name in sub_noun.value:
                    sub_noun.value[nref.name] = Result(None, sub_noun.type.subtype)
                return sub_noun.value[nref.name]
            else:
                assert False
        else:
            if not nref.name in self.nouns:
                return None
            else:
                return self.nouns[nref.name]