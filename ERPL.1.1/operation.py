import re
from nouns import *
from copy import deepcopy
from myerrors import *
        
class FunctionSpec:
    def __init__(self, name, base_arg_type, base_arg):
        self.name = name
        self.args = [base_arg]
        self.types = [type_from_string(base_arg_type + "_var")]
        self.body = None
        self.context = None
        
    def add_argument(self, new_arg_type, new_arg):
        assert new_arg not in self.args
        self.args.append(new_arg)
        self.types.append(type_from_string(new_arg_type))

class Operation:
    # An Operation is a tree. 
    # @param operator: a string identifying the operator
    # @param operands: a list of Operations
    # @param result: value for a cell, if any
    # @param func_spec: function spec for call, if any
    def __init__(self, operator, operands, result = None, func_spec = None):
        self.operator = operator
        self.operands = operands
        self.result = result
        self.func_spec = func_spec
        spec = op_list[operator]
        self.function = spec[0]
        self.out_type = deepcopy(spec[1])
        if func_spec:
            self.in_types = deepcopy(func_spec.types)
        else:
            self.in_types = deepcopy(spec[2])
        
    def __repr__(self):
        return "[" + self.operator + "]-< "  + " | ".join([repr(operand) for operand in self.operands]) + " >"
            
    # First pass: Checks types; registers variables; modifies structure to account for generics
    def typecheck(self):
        global n
        # Terminal case
        if self.result:
            if self.operator in ['num', 'bool', 'str']:
                pass
            elif self.operator == 'noun':
                # If we have an unfamiliar noun, leave the ref to get filled in. Otherwise, get the ref.
                if n.is_noun(self.result.value):
                    self.result = n.get_ref(self.result.value)
                    self.out_type = self.result.type
            elif self.operator == 'empty':
                self.out_type = self.result.type
            else:
                # Shouldn't get any other types
                assert False
            return self.result.type         
        
        # Special case for a for-loop
        elif self.operator == 'for':
            # Get the type of the thing being iterated over
            iterated_type = self.operands[1].typecheck()
            # Make sure we treat the loop var as a variable
            loop_var_type = iterated_type.subtype if iterated_type.top == 'var' else iterated_type
            # Register the variable
            n.add_noun(self.operands[0], loop_var_type)
            # Typecheck the loop body
            assert self.operands[2].typecheck().top == 'statement'
            # Clean up
            n.remove_noun(self.operands[0])
            return Type('statement')
            
        # Special case for functions
        elif self.operator == 'func_define':
            func_spec = self.operands[0]
            # Save and clear context
            old_n = n
            n = NounList()
            # Set up context according to typespecs
            n.add_noun(func_spec.args[0], func_spec.types[0].subtype)
            for arg, type in zip(func_spec.args[1:], func_spec.types[1:]):
                n.add_noun(arg, type)
            assert func_spec.body.typecheck().top == 'statement'
            # Restore context
            func_spec.context = n
            n = old_n
            return Type('statement')
                    
        # Non-terminal case
        else:
            # Indicator variable to trigger our special case below
            new_noun = False
            # Make sure our structure is fine
            if len(self.operands) != len(self.in_types):
                raise MySyntaxError("Issue: '%s' requires %s arguments, but got %s." % (self.func_spec.name, len(self.in_types), len(self.operands)))
            # Recursively typecheck our operands
            for i in range(len(self.operands)):
                # Testing framework
                # print "*************************************"
                # print self.operator
                # print self.operands[i].out_type
                # print self.in_types[i]
                # print i
                # Make copies to ensure everything works correctly
                sub_out_type = self.operands[i].typecheck()
                in_type_copy = self.in_types[i]
                
                # Check for unfamiliar nouns
                if sub_out_type.top == 'noun':
                    if self.operator == 'let' and i == 0:
                        new_noun = True
                        continue
                    else:
                        raise MySyntaxError("Didn't recognize noun name: %s" % self.operands[i].result.value)
                    
                # Strip higher-order types one by one
                while in_type_copy.subtype and sub_out_type.subtype:
                    if sub_out_type.top != in_type_copy.top:    
                        raise MySyntaxError("Data type mismatch: %s expected, %s received. In argument %s of operator %s." % (in_type_copy, sub_out_type, i, self.operator))
                    sub_out_type = sub_out_type.subtype
                    in_type_copy = in_type_copy.subtype

                # Handle generic markers
                if in_type_copy.top == 'any':
                    for type in self.in_types:
                        type.specify(sub_out_type)
                    self.out_type.specify(sub_out_type)                             
                # Compare base types
                elif sub_out_type.top != in_type_copy.top:
                    raise MySyntaxError("Base type mismatch: %s expected, %s received" % (in_type_copy, sub_out_type))
            
            # Special case for variable assignment
            if new_noun:
                noun = self.operands[0].result.value
                # Register the new noun
                n.add_noun(noun, self.in_types[1])
                # Update so we can use it correctly in the operate phase
                self.operands[0].result = n.get_ref(noun)
                self.operands[0].out_type = self.operands[0].result.type
            return self.out_type
        
    # Second pass: Evaluates
    def operate(self):
        global it_value, n
        # Case for literals
        if self.result:
            return [self.result]
        # Case for control structures
        elif self.operator in ['if', 'if_else', 'while', 'for', 'func_define']:
            inputs = []
            for operand in self.operands:
                inputs.append(operand)
            return [Result(self.function(*inputs), self.out_type)]          
        # Otherwise, do the operation right away and check values
        else:
            # If we have a toplevel statement, set 'it' to the first variable argument
            if self.out_type.top == 'statement':
                for i, in_type in enumerate(self.in_types):
                    if in_type.top == 'var':
                        it_value = deepcopy(self.operands[i])
                        break
            # Placeholder so we have something to start with
            input_combos = [[None]]
            # Iterate over the arguments
            for operand in self.operands:
                new_combos = []
                in_results = operand.operate()
                # Iterate over the results for each argument (1 usually, any number with series computation)
                for in_result in in_results:
                    if in_result.value is None:
                        raise MyRuntimeError("You tried to use a value that doesn't seem to exist! In operation: %s" % operand.operator)
                    else:
                        # Compile lists giving all possible combinations of results
                        new_combos.extend([combo + [in_result] for combo in input_combos])
                # Keep building up (potentially exponential, but intentionally so)
                input_combos = new_combos

            outputs = []
            for combo in input_combos:
                combo = combo[1:]
                # Special case: re-format input for functions
                if self.operator == 'func_call':
                    outputs.append(Result(self.function(self.func_spec, *combo), self.out_type))
                elif self.operator in ['list_series', 'table_key_series', 'table_val_series', 'list_series_var', 'table_val_series_var']:
                    outputs.extend([Result(value, self.out_type) for value in self.function(*combo)])
                else:
                    outputs.append(Result(self.function(*combo), self.out_type))
            return outputs
        
#################################################################################################
        
    
# Helper function for list indexing (from 1!)
def to_ind(n):
    i = int(n.value)
    if i == 0:
        raise MyRuntimeError("List numbering starts at 1. There is no item 0.")
    elif i > 0:
        return i - 1
    else:
        return i
    
# Helper function for deep copies. Recursive. Returns a new Result.
def copy_helper(result):
    if result.type.top == 'list':
        return Result([copy_helper(subresult) for subresult in result.value], result.type)
    elif result.type.top == 'table':
        result_dict = {}
        for key, value in result.value.items():
            result_dict[key] = copy_helper(value)
        return Result(result_dict, result.type)
    else:
        return Result(result.value, result.type)
        
# Helper function for comparing two results of the same time. Recursive. Returns -1 / 0 / 1.
def compare_helper(result1, result2):
    if result1.type.top == 'list':
        # Lexical-esque ordering
        for i in range(min(len(result1.value), len(result2.value))):
            b = compare_helper(result1.value[i], result2.value[i])
            if not b == 0:
                return b
        return cmp(len(result1.value), len(result2.value))
    elif result1.type.top == 'table':
        keys1 = result1.value.keys()
        keys2 = result2.value.keys()
        b = cmp(keys1, keys2)
        if not b == 0:
            return b
        # Key arrays are equal
        for key in keys1:
            b = compare_helper(result1.value[key], result2.value[key])
            if not b == 0:
                return b
        return 0
    elif result1.type.top == 'str':
        return cmp(result1.value.to_str(), result2.value.to_str())
    else:
        return cmp(result1.value, result2.value)
        
# Helper function for print_op. Recursive. Returns the string to be printed.
def print_helper(result):
    if result.value is None:
        return "[nothing]"
    elif result.type.top == 'list':
        if len(result.value) > 0:
            return ", ".join([print_helper(subresult) for subresult in result.value])
        else:
            return "[empty list]"
    elif result.type.top == 'table':
        if len(result.value) > 0:
            return ", ".join([key + ": " + print_helper(subresult) for (key, subresult) in result.value.items()])
        else:
            return "[empty table]"
    elif result.type.top == 'bool':
        return "yes" if result.value else "no"
    elif result.type.top == 'str':
        return result.value.to_str()
        #raw_str = result.value.to_str()
        #if len(raw_str) > 0:
        #    return raw_str
        #else:
        #    return "[empty text]"
    elif result.type.top == 'num':
        if float(int(result.value)) == result.value:
            return str(int(result.value))
        else:
            return str(result.value)
    else:
        assert False
    
# Helper function for capturing data    
def read_helper(str, type):
    result = None
    if type.top == 'var':
        return read_helper(str, type.subtype)
    elif type.top == 'str':
        result = new_string(str)
    elif type.top == 'num':
        try:
            result = float(str)
        except ValueError:
            raise MyRuntimeError("Could not read the number '%s'." % str)
    elif type.top == 'bool':
        if re.match("\s*(yes|Yes|YES)\s*", str):
            result = True
        elif re.match("\s*(no|No|NO)\s*", str):
            result = False
        else:
            raise MyRuntimeError("Could not read the decision '%s'." % str)
    elif type.top == 'list':
        result = [read_helper(substr, type.subtype) for substr in str.split(",")]
    elif type.top == 'table':
        result = {}
        for substr in str.split(","):
            keyval = substr.split(":")
            if len(keyval) == 2:
                result[keyval[0]] = read_helper(keyval[1], type.subtype)
            else:
                raise MyRuntimeError("Could not read the table entry '%s' in '%s'." % (substr, str))
    else:
        raise Exception("Unfamiliar type: %s. Please report this issue!" % type.top)
    return Result(result, type)
    
    
# Generic, effectful operations.
def print_op(a1):
    global out_file
    l = print_helper(a1)
    if out_file:
        out_file.write(l + "\n")
    else:
        print(l)
    return True
    
def write_file_op(s1):
    global out_file
    if out_file:
        out_file.close()
    if s1.value.to_str() == "default":
        out_file = None
    else:
        try:
            out_file = open(s1.value.to_str(), "w")
        except:
            raise MyRuntimeError("Could not open that file.")
    return True
    
def read_op(av1):
    global in_file
    try:
        if in_file:
            l = in_file.readline()
        else:
            l = raw_input('READ > ')
    except EOFError:
        l = ""
    n.update_noun(av1.value, read_helper(l, av1.type).value)
    return True

def read_file_op(s1):
    global in_file
    if in_file:
        in_file.close()
    if s1.value.to_str() == "default":
        in_file = None
    else:
        try:
            in_file = open(s1.value.to_str(), "r")
        except:
            raise MyRuntimeError("Could not open that file.")
    return True
        
def let_op(av1, a1):
    if a1.type.top == 'str' and n.access_noun(av1.value):
        n.access_noun(av1.value).update(a1.value)
    else:
        n.update_noun(av1.value, a1.value)
    return True
    
def swap_op(av1, av2):
    av1_result = n.access_noun(av1.value)
    av2_result = n.access_noun(av2.value)
    n.update_noun(av1.value, av2_result)
    n.update_noun(av2.value, av1_result)
    
def exists_op(av1):
    if n.lookup_noun(av1.value):
        if n.access_noun(av1.value):
            return True
    return False
    
# Control flow
def if_op(b1, s1):
    for b1_result in b1.operate():
        if b1_result.value is None:
            raise MySyntaxError("Tried to use a variable without a value.")
        if b1_result.value is False:
            return True # used to break out of loop, doesn't execute inner statement
    for s1_result in s1.operate():
        if not s1_result.value:
            return False
    return True
    
def if_else_op(b1, s1, s2):
    branch = True
    for b1_result in b1.operate():
        if b1_result.value is None:
            raise MySyntaxError("Tried to use a variable without a value.")
        if b1_result.value is False:
            branch = False
    if branch:
        for s1_result in s1.operate():
            if not s1_result.value:
                return False
    else:
        for s2_result in s2.operate():
            if not s2_result.value:
                return False
    return True
    
def while_op(b1, s1):
    while True:
        for b1_result in b1.operate():
            if b1_result.value is None:
                raise MySyntaxError("Tried to use a variable without a value.")
            if b1_result.value is False:
                return True # used to break out of loop, doesn't execute inner statement
        for s1_result in s1.operate():
            if not s1_result.value:
                return False
    return True
    
def join_op(s1, s2):
    return s1.value and s2.value
    
def for_op(rs1, a1, s1):
    for a1_result in a1.operate():
        if a1_result.value is None:
            raise MySyntaxError("Tried to use a variable without a value.")
        if a1_result.type.top == 'var':
            # Set up the loop variable
            n.add_noun(rs1, a1_result.type.subtype)
            loop_var_ref = n.get_ref(rs1).value
            n.update_noun(loop_var_ref, n.access_noun(a1_result.value))
            # Run the loop
            for s1_result in s1.operate():
                if not s1_result.value:
                    return False
            # Clean up
            n.update_noun(a1_result.value, n.access_noun(loop_var_ref))
            n.remove_noun(rs1)
        else:
            # Set up the loop variable
            n.add_noun(rs1, a1_result.type)
            loop_var_ref = n.get_ref(rs1).value
            n.update_noun(loop_var_ref, a1_result.value)
            # Run the loop
            for s1_result in s1.operate():
                if not s1_result.value:
                    return False
            # Clean up
            n.remove_noun(rs1)
    return True
    
# Operations on numbers, effectless
def plus_op(n1, n2):
    return n1.value + n2.value

def minus_op(n1, n2):
    return n1.value - n2.value
    
def times_op(n1, n2):
    return n1.value * n2.value
    
def over_op(n1, n2):
    return n1.value / n2.value
    
def modulo_op(n1, n2):
    return n1.value % n2.value
    
def neg_op(n1):
    return 0 - n1.value
    
# Operations on numbers, effectful
def add_op(n1, nv1):
    nv1_result = n.access_noun(nv1.value)
    n.update_noun(nv1.value, n1.value + nv1_result)
    return True
    
def sub_op(n1, nv1):
    nv1_result = n.access_noun(nv1.value)
    n.update_noun(nv1.value, nv1_result - n1.value)
    return True    
    
def mul_op(nv1, n1):
    nv1_result = n.access_noun(nv1.value)
    n.update_noun(nv1.value, n1.value * nv1_result)
    return True
    
def div_op(nv1, n1):
    nv1_result = n.access_noun(nv1.value)
    # Check for division by 0!
    n.update_noun(nv1.value, nv1_result / n1.value)
    return True

# Boolean conditions  
def equal_op(a1, a2):
    return compare_helper(a1, a2) == 0
    
def greater_op(a1, a2):
    return compare_helper(a1, a2) == 1
    
def less_op(a1, a2):
    return compare_helper(a1, a2) == -1
    
def most_op(a1, a2):
    return compare_helper(a1, a2) < 1
    
def least_op(a1, a2):
    return compare_helper(a1, a2) > -1
    
def not_op(b1):
    return not b1.value
    
def in_op(a1, al1):
    for item in al1.value:
        if compare_helper(a1, item) == 0:
            return True
    return False
    
# List operations 
def list_b_op(a1, a2):
    return [a1, a2]
    
def list_e_op(a1, al1):
    return [a1] + al1.value
    
def list_a_op(n1, al1):
    if al1.type.top == 'var':
        return NounRef(to_ind(n1), subref = al1.value)
    else:
        return al1.value[to_ind(n1)].value 
        # Make this work with negatives! Catch out-of-bounds! Catch non-integer?!
        
def list_len_op(al1):
    return len(al1.value)
    
def sequence_op(n1, n2):
    if n1.value > n2.value:
        raise MySyntaxError("'Through' only counts up at this time. Sorry!")
    sequence = []
    while n1.value <= n2.value:
        sequence.append(Result(n1.value, Type("num")))
        n1.value += 1.0
    return sequence
    
def list_s_op(n1, n2, al1):
    return al1.value[to_ind(n1):to_ind(n2)+1]
    
def list_max_op(al1):
    # Handle case of an empty list!
    max_index = 0
    for i in range(len(al1.value)):
        if compare_helper(al1.value[i], al1.value[max_index]) == 1:
            max_index = i
    return al1.value[max_index].value
    
def list_min_op(al1):
    # Handle case of an empty list!
    min_index = 0
    for i in range(len(al1.value)):
        if compare_helper(al1.value[i], al1.value[min_index]) == -1:
            min_index = i
    return al1.value[min_index].value
    
def list_sort_op(alv1):
    current_list = n.access_noun(alv1.value)
    n.update_noun(alv1.value, sorted(current_list, cmp = compare_helper))
    return True
    
def list_append_op(a1, alv1):
    current_list = n.access_noun(alv1.value)
    current_list.append(a1)
    n.update_noun(alv1.value, current_list)
    return True
  
def list_sum_op(nl1):
    acc = 0
    for subresult in nl1.value:
        acc += subresult.value
    return acc
    
def list_product_op(nl1):
    acc = 1
    for subresult in nl1.value:
        acc *= subresult.value
    return acc

def list_and_op(bl1):
    acc = True
    for subresult in bl1.value:
        acc = acc and subresult.value
    return acc
  
def list_or_op(bl1):
    acc = False
    for subresult in bl1.value:
        acc = acc or subresult.value
    return acc

# Operations on tables  
def table_enter_op(a1, atv1, s1):
    current_table = n.access_noun(atv1.value)
    current_table[s1.value.to_str()] = copy_helper(a1)
    n.update_noun(atv1.value, current_table)
    return True
    
def table_access_op(s1, at1):
    if at1.type.top == 'var':
        return NounRef(s1.value.to_str(), subref = at1.value)
    else:
        return at1.value[s1.value.to_str()].value 
        # Catch corner cases!
        
def table_keys_op(at1):
    return [Result(new_string(key), Type("str")) for key in at1.value.keys()]
    
def table_vals_op(at1):
    return [copy_helper(val) for val in at1.value.values()]

def table_key_series_op(at1):
    return [new_string(key) for key in at1.value.keys()]
    
def table_val_series_op(at1):
    if at1.type.top == 'var':
        return [NounRef(k, subref = at1.value) for k in n.access_noun(at1.value).keys()]
    else:
        return [at1.value[k].value for k in at1.value.keys()]
    
def list_series_op(al1):
    if al1.type.top == 'var':
        length = len(n.access_noun(al1.value))
        return [NounRef(i, subref = al1.value) for i in range(length)]
    else:
        length = len(al1.value)
        return [al1.value[i].value for i in range(length)]
        
def force_eval_op(v1):
    return n.access_noun(v1.value)
    
def to_str_op(a1):
    return new_string(print_helper(a1))
    
def to_type_op(a1):
    return new_string(a1.type.to_string())
    
def str_concat_op(s1, s2):
    return new_string(s1.value.to_str() + s2.value.to_str())
    
def str_or_op(s1, s2):
    return new_string("(" + s1.value.to_str() + "|" + s2.value.to_str() + ")")
    
def str_star_op(s1):
    return new_string("(" + s1.value.to_str() + ")*")
    
def str_match_op(s1, s2):
    regex = re.compile("^" + s2.value.to_str() + "$")
    if regex.match(s1.value.to_str()):
        return True
    else:
        return False
        
def str_contains_op(s1, s2):
    regex = re.compile(s2.value.to_str())
    if regex.search(s1.value.to_str()):
        return True
    else:
        return False
        
def str_index_op(n1, n2, s1):
    sr = s1.value
    if n2.value > sr.length() or n1.value < 0 or n1.value > n2.value:
        raise MyRuntimeError("%s through %s is not a valid section of string %s." % (n1.value, n2.value, sr.to_str()))
    return StringRef(sr.index, sr.beginning + to_ind(n1), sr.beginning + to_ind(n2) + 1)
    
def str_instances_op(s1, s2):
    regex = re.compile(s1.value.to_str())
    sr = s2.value
    return [Result(StringRef(sr.index, sr.beginning + i.start(), sr.beginning + i.end()), Type("str")) for i in regex.finditer(sr.to_str())]
    
def str_length_op(s1):
    return len(s1.value.to_str())
    
def str_words_op(s1):
    return [Result(new_string(s), Type("str")) for s in s1.value.to_str().split()] # TODO: Make these references!
    
def it_op(av1):
    return av1.value
    
def func_define_op(fs):
    return True # Everything is done during parsing and typechecking
    
def func_call_op(fs, *args_list):
    global n
    # Save and set context
    old_n = n
    n = fs.context
    # Set up main arguments
    n.update_noun(n.get_ref(fs.args[0]).value, old_n.access_noun(args_list[0].value))
    for i in range(1, len(args_list)):
        n.update_noun(n.get_ref(fs.args[i]).value, args_list[i].value)
    # Execute and return
    if not fs.body.operate():
        return False
    old_n.update_noun(args_list[0].value, n.access_noun(n.get_ref(fs.args[0]).value))
    # Restore context
    n = old_n
    return True
    
def quit_op():
    quit()
    
def null_op():
    assert False  # Should never actually execute this!
    
spec_list = {
    'write': (print_op, 'statement', ['any']),
    'read': (read_op, 'statement', ['any_var']),
    'write_file': (write_file_op, 'statement', ['str']),
    'read_file': (read_file_op, 'statement', ['str']),
    
    # Don't change this structure! Things depend on it.
    'let': (let_op, 'statement', ['any_var', 'any']),
    
    'if': (if_op, 'statement', ['bool', 'statement']),
    'if_else': (if_else_op, 'statement', ['bool', 'statement', 'statement']),
    'while': (while_op, 'statement', ['bool', 'statement']),
    'join': (join_op, 'statement', ['statement', 'statement']),
        
    # Don't change this structure! Things depend on it.
    'for': (for_op, 'statement', ['raw_string', 'any_ref', 'statement']),
    
    'plus': (plus_op, 'num', ['num', 'num']),
    'minus': (minus_op, 'num', ['num', 'num']),
    'times': (times_op, 'num', ['num', 'num']),
    'over': (over_op, 'num', ['num', 'num']),
    'modulo': (modulo_op, 'num', ['num', 'num']),
    'negative': (neg_op, 'num', ['num']),
    
    'add': (add_op, 'statement', ['num', 'num_var']),
    'subtract': (sub_op, 'statement', ['num', 'num_var']),
    'multiply': (mul_op, 'statement', ['num_var', 'num']),
    'divide': (div_op, 'statement', ['num_var', 'num']),
    
    'swap': (swap_op, 'statement', ['any_var', 'any_var']),
    'exists': (exists_op, 'bool', ['any_var']),
    
    'equal': (equal_op, 'bool', ['any', 'any']),
    'greater': (greater_op, 'bool', ['any', 'any']),
    'less': (less_op, 'bool', ['any', 'any']),
    'most': (most_op, 'bool', ['any', 'any']),
    'least': (least_op, 'bool', ['any', 'any']),
    'not': (not_op, 'bool', ['bool']),
    'in': (in_op, 'bool', ['any', 'any_list']),
    
    'list_base': (list_b_op, 'any_list', ['any', 'any']),
    'list_ext': (list_e_op, 'any_list', ['any', 'any_list']),
    'list_access': (list_a_op, 'any', ['num', 'any_list']),
    'list_access_var': (list_a_op, 'any_var', ['num', 'any_list_var']),
    'list_length': (list_len_op, 'num', ['any_list']),
    'list_slice': (list_s_op, 'any_list', ['num', 'num', 'any_list']),
    'list_append': (list_append_op, 'statement', ['any', 'any_list_var']),
    'list_min': (list_min_op, 'any', ['any_list']),
    'list_max': (list_max_op, 'any', ['any_list']),
    'list_sort': (list_sort_op, 'statement', ['any_list_var']), 
    
    'list_sum': (list_sum_op, 'num', ['num_list']),
    'list_product': (list_product_op, 'num', ['num_list']),
    'list_and': (list_and_op, 'bool', ['bool_list']),
    'list_or': (list_or_op, 'bool', ['bool_list']),
    'sequence': (sequence_op, 'num_list', ['num', 'num']),
    
    'table_enter': (table_enter_op, 'statement', ['any', 'any_table_var', 'str']),
    'table_access': (table_access_op, 'any', ['str', 'any_table']),
    'table_access_var': (table_access_op, 'any_var', ['str', 'any_table_var']),
    'table_keys': (table_keys_op, 'str_list', ['any_table']),
    'table_vals': (table_vals_op, 'any_list', ['any_table']),
    
    'list_series': (list_series_op, 'any', ['any_list']),
    'list_series_var': (list_series_op, 'any_var', ['any_list_var']),
    'table_key_series': (table_key_series_op, 'str', ['any_table']),
    'table_val_series': (table_val_series_op, 'any', ['any_table']),
    'table_val_series_var': (table_val_series_op, 'any_var', ['any_table_var']),
    
    'force': (force_eval_op, 'any', ['any_var']),
    'to_str': (to_str_op, 'str', ['any']),
    'to_type': (to_type_op, 'str', ['any']),
    
    'str_concat': (str_concat_op, 'str', ['str', 'str']),
    'str_or': (str_or_op, 'str', ['str', 'str']),
    'str_star': (str_star_op, 'str', ['str']),
    'str_match': (str_match_op, 'bool', ['str', 'str']),
    'str_contains': (str_contains_op, 'bool', ['str', 'str']),
    'str_index': (str_index_op, 'str', ['num', 'num', 'str']),
    'str_instances': (str_instances_op, 'str_list', ['str', 'str']),
    'str_length': (str_length_op, 'num', ['str']),
    'str_words': (str_words_op, 'str_list', ['str']),
    
    'it': (it_op, 'any_var', ['any_var']),
    'func_define': (func_define_op, 'statement', ['definition']),
    'func_call': (func_call_op, 'statement', ['definition', 'parameters']),
    'quit': (quit_op, 'statement', []),
    
    'bool': (null_op, 'bool', []),
    'num': (null_op, 'num', []),
    'str': (null_op, 'str', []),
    'empty': (null_op, 'none', []),
    'noun': (null_op, 'noun', [])
}
    
#################################################################################################

def type_from_string(s):
    current_type = None
    for part in s.split('_'):
        current_type = Type(part, subtype = current_type)
    return current_type
    
def get_it():
    return it_value
    
op_list = {}
for key, value in spec_list.items():
    op_list[key] = (value[0], type_from_string(value[1]), [type_from_string(i) for i in value[2]])
n = NounList()
it_value = None
in_file = None
out_file = None
