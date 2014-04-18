import calc

print """
Welcome to ERPL! 

ERPL is a language you can use to write simple computer programs in plain English. To get started, please take a look at the sample programs in this folder and/or the README file. ERPL will read your commands and execute them one by one. If something goes wrong interpreting your commands, ERPL will produce an error message. If you ever need to stop ERPL, you can press Control-C to quit.

If you would like to use a program from a file, please type the file's full name here, or press Enter to skip this step and write the program as you go.
"""

program_file = raw_input("Filename: ")
print "-----------------------------------"
print ""

if program_file == "":
    while True:
        try:
            l = raw_input('calc ' + '... ' * calc.get_nesting_level() + '> ')
        except EOFError:
            break
        calc.process_line(l)
else:
    with open(program_file, "r") as f:
        while True:
            l = f.readline()
            if l.endswith("\n"):
                calc.process_line(l.strip())
            else:
                calc.process_line(l.strip())
                break
