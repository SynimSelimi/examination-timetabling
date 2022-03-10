from pyparsing import Word, alphas, nums, alphanums, empty, \
    Literal, delimitedList, Group, Combine, FollowedBy, \
    Dict, Optional, ZeroOrMore, OneOrMore, restOfLine 

class MiniZincData:
    """
        Reads a file in minizinc format and stores the parameters in a dictionary.
    """
    def __init__(self, *args, **kwargs):
        self.parameters = {}
        if len(args) == 1:
            self.parse(args[0])
        elif 'filename' in kwargs:
            with open(kwargs['filename'], 'r') as f:
                self.parse(f.read())
        else:
            raise 'Either the textual content of the .dzn file or a .dzn filename should be specified'
        
    def parse(self, content):
        equal = Literal('=').suppress()
        identifier = Word(alphas, alphanums + "_").setResultsName("identifier")
        lbrack = Literal("[").suppress()
        rbrack = Literal("]").suppress()
        lsetbrack = Literal("{").suppress()
        rsetbrack = Literal("}").suppress()
        semi = Literal(";").suppress()
        point = Literal('.')
        comma = Literal(',').suppress()
        pipe = Literal('|').suppress()
        e = Literal('E')
        comment = '%' + restOfLine
        plusorminus = Literal('+') | Literal('-')
        digits = Word(nums) 
        integer = Combine(Optional(plusorminus) + digits + ~FollowedBy(point)).setParseAction(lambda s, l, t: [int(t[0])])
        floatnumber = Combine(Optional(plusorminus) + digits + point + Optional(digits) + Optional(e + integer)).setParseAction(lambda s, l, t: [float(t[0])])
        number = integer | floatnumber
        iset = lsetbrack + Optional(delimitedList(number, ',')) + rsetbrack
        iset.setResultsName('set')        
        iset.setParseAction(set)
        array = lbrack + Optional(delimitedList((number | iset), ',')) + rbrack
        array.setResultsName('array')
        array.setParseAction(tuple)
        matrix_line = pipe + delimitedList((number | iset), ',')
        matrix_line.setParseAction(tuple)
        matrix = lbrack + OneOrMore(matrix_line) + pipe + rbrack
        matrix.setResultsName('matrix')
        matrix.setParseAction(tuple)
        value = number | iset | array | matrix
        value.setResultsName('value')
        assignment = identifier + equal + value
        grammar = Dict(delimitedList(Group(assignment), ';') + Literal(';').suppress())
        grammar.ignore(comment)
                 
        data = grammar.parseString(content, parseAll=True)
        for k in data.keys():
            self.parameters[k] = eval(str(data[k]))                     