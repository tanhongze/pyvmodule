code_generators = {}
class CodeGen:
    precedences_list = {
        0:('const','wire','reg','[]','{}','{{}}'),
        1:('~','!',' ',' +',' -',' &',' ^',' |'),
        2:('**',),
        3:('*','/','//','%'),
        4:('+','-'),
        5:('<<','>>','<<<','>>>'),
        6:('<=','<','>=','>'),
        7:('==','!=','===','!=='),
        8:('&',),
        9:('^',),
        10:('|',),
        11:('&&',),
        12:('||',),
        13:('?:',)}
    precedences = {}
    for level in range(len(precedences_list)):
        for op in precedences_list[level]:
            precedences[op] = level