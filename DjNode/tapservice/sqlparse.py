
# define a simple SQL grammar
from pyparsing import *

def setupSQLparser():
    selectStmt = Forward()
    selectToken = Keyword("select", caseless=True)
    ident = Word( alphas, alphanums ).setName("identifier")
    columnName     = delimitedList( ident, ".", combine=True )
    columnNameList = Group( delimitedList( columnName ) )
    whereExpression = Forward()
    and_ = Keyword("and", caseless=True)
    or_ = Keyword("or", caseless=True)
    in_ = Keyword("in", caseless=True)
    E = CaselessLiteral("E")
    binop = oneOf("= != < > >= <= eq ne lt le gt ge", caseless=True)
    arithSign = Word("+-",exact=1)
    realNum = Combine( Optional(arithSign) + ( Word( nums ) + "." + Optional( Word(nums) )  |
                                           ( "." + Word(nums) ) ) + 
                       Optional( E + Optional(arithSign) + Word(nums) ) )
    intNum = Combine( Optional(arithSign) + Word( nums ) + 
                      Optional( E + Optional("+") + Word(nums) ) )

    columnRval = realNum | intNum | quotedString | columnName
    whereCondition = Group(
        ( columnName + binop + columnRval ) |
        ( columnName + in_ + "(" + delimitedList( columnRval ) + ")" ) |
        ( columnName + in_ + "(" + selectStmt + ")" ) |
        ( "(" + whereExpression + ")" )
        )
    whereExpression << whereCondition + ZeroOrMore( ( and_ | or_ ) + whereExpression ) 
    
    selectStmt      << ( selectToken + 
                         Optional(CaselessLiteral('count')).setResultsName("count")  + 
                         Optional(Group(CaselessLiteral('top') + intNum )).setResultsName("top") + 
                         ( oneOf('* ALL', caseless=True) | columnNameList ).setResultsName( "columns" ) + 
                         Optional( CaselessLiteral("where") + whereExpression.setResultsName("where") ) )

    
    
    # define Oracle comment format, and ignore them
    oracleSqlComment = "--" + restOfLine
    selectStmt.ignore( oracleSqlComment )

    return selectStmt

SQL=setupSQLparser()

############ SQL PARSER FINISHED; SOME HELPER THINGS BELOW


OPTRANS= { # transfer SQL operators to django-style
    '<':  '__lt',
    '>':  '__gt',
    '=':  '__exact',
    '<=': '__lte',
    '>=': '__gte',
    'in': '__in',
}

import sys
def LOG(s):
    print >> sys.stderr, s


def singleWhere(w,RESTRICTABLES):
    if not RESTRICTABLES.has_key(w[0]): return
    if not OPTRANS.has_key(w[1]): return
    return 'Q(%s=%s)'%(RESTRICTABLES[w[0]] + OPTRANS[w[1]],w[2])

def where2q(ws,RESTRICTABLES):
    q=''
    for w in ws:
        if w=='and': q+=' & '
        elif w=='or': q+=' | '
        elif len(w)==3: q+=singleWhere(w,RESTRICTABLES)
        elif w[0]=='(' and w[-1]==')': 
            q+=' ( '
            q+=where2q(w[1:-1])
            q+=' ) '
        LOG(q)
        

    return q
