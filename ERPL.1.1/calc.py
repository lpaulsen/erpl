from operation import *
import sys, traceback

reserved_words_list = ['a', 'add', 'all', 'and', 'any', 'append', 'at', 'be', 'by', 'character', 'characters', 'contains', 'contents', 'decision', 'decisions', 'digit', 'divide', 'each', 'enter', 'entry', 'entries', 'equal', 'exists', 'followed', 'for', 'from', 'greater', 'if', 'in', 'instances', 'is', 'into', 'it', 'item', 'items', 'label', 'labels', 'least', 'length', 'less', 'let', 'letter', 'list', 'lists', 'matches', 'maximum', 'minimum', 'minus', 'modulo', 'most', 'multiply', 'negative', 'no', 'not', 'number', 'numbers', 'of', 'opposite', 'or', 'otherwise', 'over', 'plus', 'product', 'quit', 'range', 'read', 'reading', 'sort', 'space', 'subtract', 'start', 'sum', 'swap', 'table', 'tables', 'text', 'texts', 'than', 'then', 'times', 'through', 'to', 'type', 'under', 'while', 'with', 'words', 'write', 'writing', 'yes']

reserved_words_dict = {} 
for word in reserved_words_list:
    reserved_words_dict[word] = word.upper()
    
functions_dict = {}

tokens = ['NOUN', 'NUM', 'STR', 'WORD', 'FUNC', 'STOP'] + [word.upper() for word in reserved_words_list]

literals = [':', ';', '(', ')', ',']

statement_list = [""]
nesting_level = 0

def t_STR(t):
    r'\[\d+\]'
    t.value = StringRef(int(t.value[1:-1]))
    return t
    
def t_NUM(t):
    r'\d+(\.\d+)?'
    try:
        t.value = float(t.value)
    except:
        print("Did not recognize value: %d", t.value)
        t.value = 0
    return t
    
def t_NOUN(t):
    r'[A-Z][a-z_]*'
    return t
    
def t_WORD(t):
    r'[a-z][a-z_]*'
    if t.value in reserved_words_dict:
        t.type = reserved_words_dict[t.value]
    elif t.value in functions_dict:
        t.type = 'FUNC'
    else:
        t.type = 'WORD'
    return t
    
def t_STOP(t):
    r'\.'
    return t # Shouldn't be used
    
# Ignored characters
t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
    
def t_error(t):
    raise MySyntaxError("Illegal character: '%s'" % t.value[0])
    
# Build the lexer
import ply.lex as lex
lex.lex()

# Precedence rules-- add to this!
precedence = (
    ('nonassoc', 'NOUN'),
    ('left', ','),
    ('nonassoc', 'THEN'),
    ('nonassoc', 'IS'),
    
    ('left', 'FOLLOWED'),
    ('left', 'OR'),
    ('left', 'ANY'),
    
    ('left', 'PLUS','MINUS'),
    ('left', 'TIMES','OVER'),
    ('left', 'MODULO'),
    
    ('right', 'OF'),
    ('left', 'AND'),
    ('nonassoc', 'THROUGH'),    
    ('right', 'NEGATIVE'),
    )
    
# A sentence is the basic unit of execution
start = 'sentence'

def p_sentence_statement(t):
    "sentence : statement STOP"
    t[0] = t[1]
    
def p_quit_statement(t):
    "statement : QUIT"
    t[0] = Operation('quit', [])
    
# Control flow
def p_block_base(t):
    'block : sentence'
    t[0] = t[1]
    
def p_block_extend(t):
    'block : sentence block'
    t[0] = Operation('join', [t[1], t[2]])

def p_if_statement(t):
    '''sentence : IF val ':' block THEN ':' %prec THEN
                | IF val ',' sentence %prec THEN'''
    t[0] = Operation('if', [t[2], t[4]])
    
def p_if_else(t):
    "sentence : IF val ':' block OTHERWISE ':' block THEN ':' %prec THEN"
    t[0] = Operation('if_else', [t[2], t[4], t[7]])
    
def p_while_statement(t):
    '''sentence : WHILE val ':' block THEN ':' %prec THEN
                | WHILE val ',' sentence %prec THEN'''
    t[0] = Operation('while', [t[2], t[4]])
    
def p_for_each_series_var(t):
    '''series : EACH ITEM NOUN IN var
              | EACH ENTRY NOUN IN var'''
    if t[2] == 'item':      op = 'list_series_var'
    elif t[2] == 'entry':   op = 'table_val_series_var'
    else: assert False
    t[0] = (t[3], Operation(op, [t[5]]))
    
def p_for_each_series(t):
    '''series : EACH ITEM NOUN IN val
              | EACH LABEL NOUN IN val
              | EACH ENTRY NOUN IN val'''
    if t[2] == 'item':      op = 'list_series'
    elif t[2] == 'label':   op = 'table_key_series'
    elif t[2] == 'entry':   op = 'table_val_series'
    else: assert False
    t[0] = (t[3], Operation(op, [t[5]]))
    
def p_for_each_structure(t):
    '''sentence : FOR series ':' block THEN ':' %prec THEN
                | FOR series ',' sentence %prec THEN'''
    t[0] = Operation('for', [t[2][0], t[2][1], t[4]])
    
def p_join_statement(t):
    "sentence : statement ';' sentence"
    t[0] = Operation('join', [t[1], t[3]])
    
# Assignment    
def p_statement_assign(t):
    "statement : LET var BE val"
    t[0] = Operation('let', [t[2], t[4]])
    
# Input
def p_statement_read(t):
    "statement : READ var"
    t[0] = Operation('read', [t[2]])
    
def p_read_file(t):
    "statement : START READING FROM val"
    t[0] = Operation('read_file', [t[4]])
    
# Output
def p_statement_write(t):
    "statement : WRITE val"
    t[0] = Operation('write', [t[2]])
    
def p_write_file(t):
    "statement : START WRITING TO val"
    t[0] = Operation('write_file', [t[4]])
    
def p_expr_to_str(t):
    "val : CONTENTS OF val"
    t[0] = Operation('to_str', [t[3]])
    
def p_expr_to_type(t):
    "val : TYPE OF val"
    t[0] = Operation('to_type', [t[3]])
    
def p_expr_exists(t):
    "val : var EXISTS %prec IS"
    t[0] = Operation('exists', [t[1]])
    
# Regex operations
def p_string_concat(t):
    "val : val FOLLOWED BY val %prec FOLLOWED"
    t[0] = Operation('str_concat', [t[1], t[4]])
    
def p_string_or(t):
    "val : val OR val %prec OR"
    t[0] = Operation('str_or', [t[1], t[3]])
    
def p_string_star(t):
    "val : ANY NUMBER OF val %prec ANY"
    t[0] = Operation('str_star', [t[4]])
    
def p_string_match(t):
    "val : val MATCHES val"
    t[0] = Operation('str_match', [t[1], t[3]])
    
def p_string_contains(t):
    "val : val CONTAINS val"
    t[0] = Operation('str_contains', [t[1], t[3]])
   
def p_string_index(t):
    "val : CHARACTERS val THROUGH val OF val"
    t[0] = Operation('str_index', [t[2], t[4], t[6]])
    
def p_string_instances(t):
    "val : INSTANCES OF val IN var"
    t[0] = Operation('str_instances', [t[3], t[5]])
    
def p_string_length(t):
    "val : LENGTH OF val %prec OF"
    t[0] = Operation('str_length', [t[3]])
    
def p_string_words(t):
    "val : WORDS OF val %prec OF"
    t[0] = Operation('str_words', [t[3]])
    
# Everyday math
def p_expr_binop(t):
    '''val : val PLUS val
           | val MINUS val
           | val TIMES val
           | val OVER val
           | val MODULO val'''
    t[0] = Operation(t[2], [t[1], t[3]])
    
def p_assign_binop(t):
    '''statement : ADD val TO var
                 | SUBTRACT val FROM var
                 | MULTIPLY var BY val
                 | DIVIDE var BY val
                 | SWAP var WITH var'''
    t[0] = Operation(t[1], [t[2], t[4]])
    
def p_expr_negative(t):
    "val : NEGATIVE val"
    t[0] = Operation("negative", [t[2]])
    
# Boolean conditions 
def p_cond_op(t):
    '''cond_op : EQUAL TO
               | GREATER THAN
               | LESS THAN
               | AT MOST
               | AT LEAST
               | IN'''
    if t[1] == 'at':
        t[0] = t[2]
    else:
        t[0] = t[1]
    
def p_boolean_cond(t):
    "val : val IS cond_op val %prec IS"
    t[0] = Operation(t[3], [t[1], t[4]])
    
def p_negative_cond(t):
    "val : val IS NOT cond_op val %prec IS"
    t[0] = Operation("not", [Operation(t[4], [t[1], t[5]])])

def p_equality_cond(t):
    "val : val IS val %prec IS"
    t[0] = Operation('equal', [t[1], t[3]])
    
def p_inequality_cond(t):
    "val : val IS NOT val %prec IS"
    t[0] = Operation("not", [Operation('equal', [t[1], t[4]])])
    
def p_boolean_neg(t):
    "val : OPPOSITE OF val"
    t[0] = Operation("not", [t[2]])

# Grouping
def p_val_group(t):
    "val : '(' val ')'"
    t[0] = t[2]
    
def p_var_group(t):
    "var : '(' var ')'"
    t[0] = t[2]
    
# Working with tables
def p_table_enter(t):
    "statement : ENTER val INTO var UNDER val"
    t[0] = Operation('table_enter', [t[2], t[4], t[6]])    
    
def p_table_access(t):
    "val : ENTRY val OF val"
    t[0] = Operation('table_access', [t[2], t[4]])
    
def p_table_access_var(t):
    "var : ENTRY val OF var"
    t[0] = Operation('table_access_var', [t[2], t[4]])
    
def p_table_keys_list(t):
    "val : LABELS OF val"
    t[0] = Operation('table_keys', [t[3]])
    
def p_table_vals_list(t):
    "val : ENTRIES OF val"
    t[0] = Operation('table_vals', [t[3]])
        
def p_table_key_series(t):
    "val : EACH LABEL OF val"
    t[0] = Operation('table_key_series', [t[4]])
    
def p_table_val_series(t):
    "val : EACH ENTRY OF val"
    t[0] = Operation('table_val_series', [t[4]])
    
def p_table_val_series_var(t):
    "var : EACH ENTRY OF var"
    t[0] = Operation('table_val_series_var', [t[4]])
  
# Working with lists
def p_list_access(t):
    "val : ITEM val OF val %prec OF"
    t[0] = Operation('list_access', [t[2], t[4]])
    
def p_list_access_var(t):
    "var : ITEM val OF var %prec OF"
    t[0] = Operation('list_access_var', [t[2], t[4]])
    
def p_list_length(t):
    "val : RANGE OF val"
    t[0] = Operation('list_length', [t[3]])
    
def p_list_slice(t):
    "val : ITEMS val THROUGH val OF val"
    t[0] = Operation('list_slice', [t[2], t[4], t[6]])
    
def p_list_max(t):
    "val : MAXIMUM OF val %prec OF"
    t[0] = Operation('list_max', [t[3]])
    
def p_list_min(t):
    "val : MINIMUM OF val %prec OF"
    t[0] = Operation('list_min', [t[3]])
    
def p_list_append(t):
    "statement : APPEND val TO var"
    t[0] = Operation('list_append', [t[2], t[4]])
    
def p_list_sort(t):
    "statement : SORT var"
    t[0] = Operation('list_sort', [t[2]])
    
# Type-specific list operations
def p_list_sum(t):
    "val : SUM OF val %prec OF"
    t[0] = Operation('list_sum', [t[3]])
    
def p_list_product(t):
    "val : PRODUCT OF val %prec OF"
    t[0] = Operation('list_product', [t[3]])
    
def p_list_all(t):
    "val : ALL OF val %prec OF"
    t[0] = Operation('list_and', [t[3]])
    
def p_list_any(t):
    "val : ANY OF val %prec OF"
    t[0] = Operation('list_or', [t[3]])

# System for constructing lists
def p_list_base_1(t):
    "list : val AND val %prec AND"
    t[0] = Operation('list_base', [t[1], t[3]])
    
def p_list_base_2(t):
    "list : val ',' AND val %prec AND"
    t[0] = Operation('list_base', [t[1], t[4]])
    
def p_list_extend(t):
    "list : val ',' list %prec ','"
    t[0] = Operation('list_ext', [t[1], t[3]])
    
def p_expr_list(t):
    'val : list %prec NOUN'
    t[0] = t[1]
    
def p_series_list(t):
    'val : EACH ITEM OF val %prec OF'
    t[0] = Operation('list_series', [t[4]])
    
def p_series_list_var(t):
    'var : EACH ITEM OF var %prec OF'
    t[0] = Operation('list_series_var', [t[4]])
    
def p_sequence(t):
    'val : val THROUGH val'
    t[0] = Operation('sequence', [t[1], t[3]])
    
def p_it_val(t):
    'var : IT'
    t[0] = Operation('it', [get_it()])
    
def p_func_spec_base(t):
    'func_spec : WORD single_type NOUN'
    t[0] = FunctionSpec(t[1], t[2], t[3])
    
def p_func_spec_extend(t):
    'func_spec : func_spec WITH single_type NOUN'
    t[1].add_argument(t[3], t[4])
    t[0] = t[1]
    
def p_define_func(t):
    "sentence : TO func_spec register_action ':' block THEN ':'"
    t[2].body = t[5]
    t[0] = Operation('func_define', [t[2]])
    
def p_register_func(t):
    "register_action :"
    global functions_dict
    functions_dict[t[-1].name] = t[-1]
    t[0] = True # because why not?
    
def p_func_use_base(t):
    "func_use : FUNC var"
    t[0] = (functions_dict[t[1]], [t[2]])
    
def p_func_use_extend(t):
    "func_use : func_use WITH val"
    t[0] = (t[1][0], t[1][1] + [t[3]])

def p_func_call(t):
    "statement : func_use"
    t[0] = Operation('func_call', t[1][1], func_spec = t[1][0])
    
# System for building empty literals of any type
def p_single_type(t):
    '''single_type : A NUMBER 
                   | A TEXT
                   | A DECISION
                   | A LIST OF plural_type
                   | A TABLE OF plural_type'''
    if t[2] == 'number'     : t[0] = 'num'
    elif t[2] == 'text'     : t[0] = 'str'
    elif t[2] == 'decision' : t[0] = 'bool'
    elif t[2] == 'list'     : t[0] = t[4] + '_list'
    elif t[2] == 'table'    : t[0] = t[4] + '_table'
    else: assert False

def p_plural_type(t):
    '''plural_type : NUMBERS
                   | TEXTS
                   | DECISIONS
                   | LISTS OF plural_type
                   | TABLES OF plural_type'''
    if t[1] == 'numbers'    : t[0] = 'num'
    elif t[1] == 'texts'    : t[0] = 'str'
    elif t[1] == 'decisions': t[0] = 'bool'
    elif t[1] == 'lists'    : t[0] = t[3] + '_list'
    elif t[1] == 'tables'   : t[0] = t[3] + '_table'
  
def p_expr_type(t):
    'val : single_type'
    if t[1].endswith("_list"):
        value = []
    elif t[1].endswith("_table"):
        value = {}
    elif t[1].endswith("str"):
        value = ""
    elif t[1].endswith("num"):
        value = 0
    else:
        value = None
    t[0] = Operation("empty", [], result = Result(value, type_from_string(t[1])))

# Literals of fundamental types    
def p_expr_number(t):
    'val : NUM'
    t[0] = Operation("num", [], result = Result(t[1], Type("num")))
    
def p_expr_boolean_yes(t):
    'val : YES'
    t[0] = Operation("bool", [], result = Result(True, Type("bool")))
    
def p_expr_boolean_no(t):
    'val : NO'
    t[0] = Operation("bool", [], result = Result(False, Type("bool")))
    
def p_expr_string(t):
    'val : STR'
    t[0] = Operation("str", [], result = Result(t[1], Type("str")))
    
def p_regex_wildcard(t):
    '''val : ANY CHARACTER
           | ANY LETTER
           | ANY DIGIT
           | ANY SPACE'''
    if t[2] == 'character': code = '.'
    elif t[2] == 'letter':  code = '[a-zA-Z]'
    elif t[2] == 'digit':   code = '[0-9]'
    elif t[2] == 'space':   code = '\s'
    t[0] = Operation("str", [], result = Result(code, Type("str")))
    
# Names of nouns
def p_expr_name(t):
    'var : NOUN'
    t[0] = Operation("noun", [], result = Result(t[1], Type("noun")))

def p_expr_eval(t):
    'val : NOUN'
    t[0] = Operation('force', [Operation("noun", [], result = Result(t[1], Type("noun")))])
    
def p_error(t):
    global statement_list
    if t:
        error_string = "Couldn't parse this part of the command: \n %s \n " % statement_list[-1]
        error_string += " " * t.lexpos
        error_string += "^" * len(t.value)
        raise MySyntaxError(error_string)
    else:
        raise MySyntaxError("Syntax error: reached end of command without understanding it")

import ply.yacc as yacc
parser = yacc.yacc(debug = 0)

def repl_str(m):
    string_storage.append(m.group(1))
    string_refs.append([])
    return "[" + str(len(string_storage) - 1) + "]"
    
def repl_the(m):
    return m.group(1)

def process_line(s):
    global statement_list, nesting_level, parser
    # Comments
    if re.match("\[.*\]", s):
        return
    # Empty lines
    if len(s) == 0:
        if nesting_level == 0:
            return
        statement_list[-1] += "then: " * nesting_level
        nesting_level = 0
    else:
        s = s + ' '
        # Decapitalize
        s = s[0].lower() + s[1:]
        # Find and preprocess strings
        s = re.sub(r'"([^"]*)"', repl_str, s)
        # Remove 'the's
        s = re.sub(r'([\W])the ', repl_the, s)
        statement_list[-1] += s
        if "then:" in s:
            nesting_level -= 1
        elif s.endswith(": ") and not s.endswith("otherwise: "): # Formalize this!
            nesting_level += 1
    if nesting_level <= 0: # Should be strict =, but let's be careful
        try:
            to_execute = parser.parse(statement_list[-1], debug = 0)
            to_execute.typecheck()
            to_execute.operate()
        except MySyntaxError as e:
            print("")
            print("That looks like a syntax error. If you think it shouldn't be, please tell me.")
            print("Error details:")
            print(e.value)
            print("Code:")
            print(statement_list)
            print("")
        except MyRuntimeError as e:
            print("")
            print("ERPL couldn't execute that command. If you think this is an issue, please tell me.")
            print("Error details: ")
            print(e.value)
            print("Code:")
            print(statement_list)
            print("")
            # TODO: Recover gracefully by saving / restoring n
        except Exception as e:
            print("")
            print("Something bad happened. Please report this!")
            traceback.print_exc()
            print("Code:")
            print(statement_list)
            print("")
            quit()
        statement_list.append("")

def get_nesting_level():
    return nesting_level

# Entry points for anything running ERPL from the command line
def repl(program_file):
    if program_file == "":
        while True:
            try:
                l = input('calc ' + '... ' * calc.get_nesting_level() + '> ')
            except EOFError:
                break
            process_line(l)
    else:
        with open(program_file, "r") as f:
            while True:
                l = f.readline()
                if l.endswith("\n"):
                    process_line(l.strip())
                else:
                    # Getting a line without \n implies EOF
                    process_line(l.strip())
                    break

# Execute as a command line tool
if __name__ == "__main__":
    if len(sys.argv) == 1:
        repl("")
    elif len(sys.argv) == 2:
        repl(sys.argv[1])
    else:
        print("Usage: 'calc.py' OR 'calc.py [filename]'")
