import types

import ply.lex as lex
import ply.yacc as yacc
from ply.lex import Lexer

# List of token names.
tokens = (
    "VARIABLE",
    "AND",
    "OR",
    "NOT",
    "XOR",
    "LPAREN",
    "RPAREN",
)

# Regular expression rules
t_AND = r"\&"
t_OR = r"\|"
t_NOT = r"\!"
t_XOR = r"\^"
t_LPAREN = r"\("
t_RPAREN = r"\)"


def t_VARIABLE(t):
    r"[\d\w]+"
    return t


t_ignore = " \t"


def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)


lexer = lex.lex()


def get_all_tokens(self):
    tokens = []
    while True:
        tok = self.token()
        if not tok:
            break
        tokens.append(tok)

    return tokens


lexer.get_all_tokens = types.MethodType(get_all_tokens, lexer)
