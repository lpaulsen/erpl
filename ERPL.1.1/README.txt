README and Documentation
ERPL 1.0
Luke Paulsen
April 16, 2014

Welcome to ERPL! ERPL is a new programming language designed to allow you to read and write code in plain English. This file is designed to walk you through how the language works and what it"s capable of. Lines with a > will denote runnable ERPL code throughout. Lines with a % will denote incorrect ERPL code.

To run ERPL from the command line, cd into the ERPL folder and type "python erpl.py". ERPL should run correctly on Python 2.6 and 2.7; Python 3 is not currently supported. ERPL has one dependency, the PLY package, available at www.dabeaz.com/ply/.

Every statement in ERPL-- a line of code in most other languages-- works like an English sentence. In most cases, a statement will begin with a main verb that is imperative (i.e. a command). The first word of each statement may be capitalized or not, but each statement must end with a period. At present there is only support for programs with one statement per line.

> Let X be 42.
> Add 7 to X.
> Write X.              [This will print 49.]

X, 42, and 7 are all nouns. Nouns can either be literals, like 7 and 42 (their value is written directly into the program), or variables, like X. Variable names always begin with a capital letter (like nouns in German) and can contain only alphanumeric characters and underscores. Each variable can hold values of a particular type. The basic types are numbers (= Python float and int) as shown above, texts (= Python string) in double quotes, and decisions (=> boolean) of yes or no. Assign a value to a variable using the 'Let' statement shown above. You cannot assign values of different types to the same variable.

> Let Y be "hello".
% Let Y be 5.           [This will be an error.]

'Let' here, like 'add', 'write', and most other verbs, takes one or more nouns as its arguments. Most verbs require certain things about the type of their arguments. For example, 'add' requires both of its arguments to be numbers. It also requires its second argument to be a variable. A defining feature of verbs is that they have some kind of effect, either modifying a variable argument (as with 'let' and 'add') or performing I/O (as with 'write'). Compare this with the following code:

> Write X plus 4.       [This will print 53, but X will still be 49.]

The phrase 'X plus 4' acts like a noun, but in most languages it would be treated as an operation of its own. Functions in a language like Python can have both effects and values, and can be chained together arbitrarily. ERPL, on the other hand, distinguishes between verbs (which have effects but not values) and attributes (which have values but not effects). If X still has the value 49, then 'X plus 4' has the value 53 but does not change X, while 'Add 4 to X' would change X to 53 but would not have a value. The other usual operations on numbers are also supported.

> Write X minus 1.
> Subtract 1 from X.
> Write X times 2.
> Multiply X by 2.
> Write X over 3.
> Divide X by 3.
> Write negative X.

ERPL also supports the use of lists (= Python lists) and tables (= Python dicts) to store information. Lists are currently easier to work with. They can be written as literals (connected by commas and/or 'and's), and accessed by index. All list elements must be of the same type (though they may be other lists-- ERPL supports higher-order types), and lists are indexed from 1. A few other useful operations on lists, such as minimum, maximum, range, sorting, and slicing, are also supported. Also, note that the word 'the' can be placed before any expression (i.e. value-bearing phrase) without effect, for readability purposes.

> Let the Data be 3, 5, 1, and 8.
> Write item 1 of the Data.
> Let item 4 of Data be 9.
> Append 6 to the Data.
> Write the maximum of the Data.
> Write the range of the Data.
> Sort the Data.
> Write items 2 to 5 of the Data.
% Write item 0 of the Data. [Error: index out of bounds.]

ERPL also provides some helpful functions for aggregating lists of particular types.

> Write the sum of 1, 2, 3, 4, and 5.
> Write the product of 6 and 7.     [2-element lists are still lists!]

There is no notation at present for constructing table literals in ERPL, so it is currently necessary to use the type declaration system. In ERPL, the name of a type is equivalent to a default, 'empty' value of that type. This is especially useful when creating empty lists or tables.

> Let X be a number.
> Let the Dictionary be a table of texts.
> Let Matrix be a list of lists of numbers.

If you need to check the type of a variable or value for some reason, ERPL provides a handy attribute for doing so. A similar attribute lets you extract the value itself as a string. Finally, 'exists' is a useful predicate for checking whether some variable (or subdivision thereof) has been defined at all.

> Write the type of the Matrix.
> Write the contents of the Matrix.
> If item 42 of the Matrix exists, write "This shouldn't be true".

Tables work much the same way that Python dictionaries do, except that their keys are always texts (=> strings), not arbitrary types as in Python. To use other data types as the keys, you can use the 'name' attribute, which an arbitrary data type to a string. To iterate over a table, you will need to extract a list of its keys or values using the "labels" and "entries" attributes, respectively.

> Enter "A meaningless word" into the Dictionary under "foo".
> Enter the name of 17 into the Dictionary under "bar".
> Write entry "bar" of the Dictionary.
> Let entry "foo" of the Dictionary be "An arbitrary word".
> Write the labels of the Dictionary.
> Write the entries of the Dictionary.

All values in ERPL are just that-- values-- unless they are designed to work as references (as in the 'item' and 'entry' attributes). So the following statement will make a separate copy of the Data list:

> Let the Final_version be the Data.

On the other hand, often you will want to do the same thing to every item of a list or every entry of a table. ERPL supports a powerful parallel-operation construct signalled by the word 'each'. This allows the result of any computation to be a series of values, rather than a single value. It also allows this series of values to be passed through multiple operations if necessary. 'Each' can be used to implement computations that other languages would rely on map-reduce or loops to accomplish. (The parsing here is currently a bit ambiguous; don't hesitate to use parentheses if necessary.)

> Add 1 to each item of the Data.
> Write 10 times each item of Data.
> Write each label of the Dictionary.
> Let each entry of the Dictionary be "Something".
> Let N be 0.
> Add (each item of the Data) to N.
> Write N.

Control flow in ERPL consists primarily of 'if' and 'while' statements. These statements are unusual in that they include one or more other statements within them, as well as an expression with a decision (=> boolean) value. The decision literals are yes and no, but more often a decision will be the result of a comparison of two other values. ERPL is built so that any pair of values of the same type can be meaningfully compared. Numbers are compared in the usual way; texts, lists, and tables are compared in 'dictionary order'.  'At least' and 'At most' are used for non-strict inequality.

> While X is less than 5, add 1 to X.
> If X is at least 8, let X be 8.
> If "foo" is greater than "fob", write "Right".
> If "foo" is not at most "foot", write "Also right".
> While yes, write "Infinite loop!".
> Let B be no.
> While B is equal to no, let B be yes.

Note that the 'one-liner' syntax requires that the statement inside the loop not be capitalized. This is a quirk of the way ERPL currently parses input and should be fixed in future versions. For a more robust way of creating control structures with ERPL, consider using the block structure. This allows multiple statements (a "block") to be nested under one 'if' or 'while'-- including additional 'if' or 'while' statements. 'Then:' (usually on its own line) signals the end of the immediately preceding 'if' or 'while'; an empty line breaks out of all levels of nesting.

> Let Z be 1.
> If Z is less than 5:
    > Write "Increasing Z".
    > While Z is less than 5:
        > Add 1 to Z.
        > Then:
    > Write Z.          [Z will only be written once, when it is 5.]
    >
    
> If 1 is greater than 2:
    > Write "Not true".
    > Otherwise:
    > Write "True".     [This works like an 'else' statement.]
    >

'For' statements in ERPL are a hybrid of 'while' statements and the 'each' syntax. A 'for' statement is designed to iterate over each element of a list and perform some series of operations related to the current element. A loop variable is used to refer to the current element. (Don't try to use the loop variable outside the loop; the behavior of this is undefined!) Note the syntax of this operation; it is slightly different from the usual 'each' syntax and from the Python for-loop syntax. Also, ERPL has a list-creation function analogous to Python's range function, which may be useful in 'for' loops.

> For each item I in (1, 2, and 3), write I.
> For each item I in the Data, let I be 0.
> Let the Factorial be 1.
> For each item I in 1 through 10:
    > Multiply the Factorial by I.
    > Write the Factorial.
    >
    
ERPL also allows you to define your own custom functions, using a combination of a new main verb and one or more nouns. The first noun used in a function must always be a variable that the function may modify; further nouns, if any, cannot be modified. The keyword 'with' is used to add additional nouns, both when the function is defined and when it is called. For example, the following function implements (positive integer) exponents.

> To exponentiate a number X with a number Power:
    > Let Y be X.
    > While the Power is greater than 1:
        > Multiply X by Y.
        > Subtract 1 from the Power.
        >
         
> Let M be 3.
> Let N be 4
> Exponentiate M with N.    [M is now 81; N is still 4.]
         
ERPL supports a rich library of regular expression operations to search through text. Regular expressions are represented as normal strings, with additional symbolic notation added as needed. Matches for regular expressions in a string are represented as references into that string; substrings of a string (1-indexed like lists) are similarly represented. Note that this is a major difference from Python's treatment of strings: ERPL strings are mutable and are passed by reference by default.

> Let S be "aardvark".
> Write characters 6 through 8 of S.    [Writes "ark".]
> If S matches "ar", write "Not true!"
> If S contains "ar", write "True!"
> Let R be any number of "a" followed by "r" followed by "dv" or "k".
> Write R.                              [Writes "(a)*r(dv|k)"]
> If S matches R, write "True!"
> Let the Ars be the instances of "ar" in S.
> Write the Ars.
> Let each item of the Ars be "arrr".
> Write S.                              [Writes "aarrrdvarrrk".]
> Let characters 1 through 2 of S be "b".
> Write S.                              [Writes "brrrdvarrrk".]
> Write the length of S.

ERPL also allows you to read strings in from the command line, and to perform file I/O.

> Read S.                           [Reads a one-line string from the command line, storing it in S.]
> Start reading from "source.txt".  [Opens the file source.txt for reading.]
> Read S.                           [Reads the first line of source.txt, storing it in S.]
> Start writing to "target.txt".    [Opens the file target.txt for writing.]
> Write S.                          [The first line of target.txt is now the first line of source.txt.]