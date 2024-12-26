import ply.yacc as yacc
from lexer import tokens  # Importamos los tokens desde nuestro analizador léxico

class SyntaxError(Exception):
    pass

# Definición de la producción principal del programa
def p_program(p):
    'program : PROGRAM LBRACE list_decl list_sent RBRACE'
    p[0] = ('program', p[3], p[4])

# Lista de declaraciones (variables)
def p_list_decl(p):
    '''list_decl : list_decl decl
                 | decl
                 | empty'''
    if len(p) == 3:
        if p[1]:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[2]]
    elif len(p) == 2:
        if p[1]:
            p[0] = [p[1]]
        else:
            p[0] = []
    else:
        p[0] = []

def p_decl(p):
    '''decl : tipo list_id_array SEMICOLON'''  # Cambiamos list_id por list_id_array
    p[0] = ('decl', p[1], p[2], p.lineno(3))

def p_list_id_array(p):
    '''list_id_array : list_id_array COMMA id_array
                    | id_array'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_id_array(p):
    '''id_array : IDENT LBRACKET NUMBER RBRACKET
                | IDENT'''
    if len(p) == 5:
        p[0] = ('array_decl', p[1], p[3])
    else:
        p[0] = p[1]

def p_tipo(p):
    '''tipo : INT
            | FLOAT
            | BOOL'''
    p[0] = p[1]

def p_list_id(p):
    '''list_id : list_id COMMA IDENT
               | IDENT'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# Lista de sentencias (statements)
def p_list_sent(p):
    '''list_sent : list_sent sent
                 | sent
                 | empty'''
    if len(p) == 3:
        if p[1]:
            p[0] = p[1] + [p[2]]
        else:
            p[0] = [p[2]]
    elif len(p) == 2:
        if p[1]:
            p[0] = [p[1]]
        else:
            p[0] = []
    else:
        p[0] = []

def p_sent(p):
    '''sent : IF LPAREN exp_bool RPAREN THEN bloque ELSE bloque FI
            | IF LPAREN exp_bool RPAREN THEN bloque FI
            | WHILE LPAREN exp_bool RPAREN bloque
            | DO bloque UNTIL LPAREN exp_bool RPAREN SEMICOLON
            | READ IDENT SEMICOLON
            | WRITE write_list SEMICOLON
            | IDENT ASSIGN exp_bool SEMICOLON
            | IDENT LPAREN expression_list RPAREN SEMICOLON
            | BREAK SEMICOLON'''
    if p.slice[1].type == 'IF' and len(p) == 10:
        p[0] = ('if', p[3], p[6], p[8], p.lineno(1))
    elif p.slice[1].type == 'IF':
        p[0] = ('if', p[3], p[6], None, p.lineno(1))
    elif p.slice[1].type == 'WHILE':
        p[0] = ('while', p[3], p[5], p.lineno(1))
    elif p.slice[1].type == 'DO':
        p[0] = ('do_until', p[2], p[5], p.lineno(1))
    elif p.slice[1].type == 'READ':
        p[0] = ('sent_read', p[2], p.lineno(3), find_column(p.lexer.lexdata, p.lexpos(3)))
    elif p.slice[1].type == 'WRITE':
        p[0] = ('sent_write', p[2])
    elif p.slice[2].type == 'ASSIGN':
        p[0] = ('sent_assign', p[1], p[3], p.lineno(4), find_column(p.lexer.lexdata, p.lexpos(4)))
    elif p.slice[2].type == 'LPAREN':
        p[0] = ('sent_func_call', p[1], p[3])
    elif p.slice[1].type == 'BREAK':
        p[0] = ('sent_break',)

def p_write_list(p):
    '''write_list : write_list COMMA write_item
                 | write_item'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_write_item(p):
    '''write_item : exp_bool
                  | STRING'''
    if isinstance(p[1], str):
        p[0] = ('string', p[1])
    else:
        p[0] = p[1]

def p_bloque(p):
    'bloque : LBRACE list_sent RBRACE'
    p[0] = ('bloque', p[2])

def p_exp_bool(p):
    '''exp_bool : exp_bool OR comb
                | comb'''
    if len(p) == 4:
        p[0] = ('or', p[1], p[3])
    else:
        p[0] = p[1]

def p_comb(p):
    '''comb : comb AND igualdad
            | igualdad'''
    if len(p) == 4:
        p[0] = ('and', p[1], p[3])
    else:
        p[0] = p[1]

def p_igualdad(p):
    '''igualdad : igualdad EQUALS rel
                | igualdad NOTEQUAL rel
                | rel'''
    if len(p) == 4:
        if p[2] == '==':
            p[0] = ('equals', p[1], p[3])
        else:
            p[0] = ('not_equals', p[1], p[3])
    else:
        p[0] = p[1]

def p_rel(p):
    '''rel : expr op_rel expr
           | expr'''
    if len(p) == 4:
        p[0] = ('rel', p[2], p[1], p[3])
    else:
        p[0] = p[1]

def p_op_rel(p):
    '''op_rel : LESS
              | LESSEQUAL
              | GREATER
              | GREATEREQUAL'''
    p[0] = p[1]

def p_expr(p):
    '''expr : expr PLUS term
            | expr MINUS term
            | term'''
    if len(p) == 4:
        if p[2] == '+':
            p[0] = ('plus', p[1], p[3])
        else:
            p[0] = ('minus', p[1], p[3])
    else:
        p[0] = p[1]

def p_term(p):
    '''term : term TIMES power
            | term DIVIDE power
            | power'''
    if len(p) == 4:
        if p[2] == '*':
            p[0] = ('times', p[1], p[3])
        else:
            p[0] = ('divide', p[1], p[3])
    else:
        p[0] = p[1]

def p_power(p):
    '''power : unario POWER power
             | unario'''
    if len(p) == 4:
        p[0] = ('power', p[1], p[3])
    else:
        p[0] = p[1]

def p_unario(p):
    '''unario : NOT unario
              | MINUS unario
              | factor'''
    if len(p) == 3:
        if p[1] == '!':
            p[0] = ('not', p[2])
        else:
            p[0] = ('negate', p[2])
    else:
        p[0] = p[1]

def p_factor(p):
    '''factor : IDENT LBRACKET expr RBRACKET
              | LPAREN exp_bool RPAREN
              | IDENT
              | NUMBER
              | TRUE
              | FALSE'''
    if len(p) == 5:
        p[0] = ('array_access', p[1], p[3])
    elif len(p) == 4:
        p[0] = p[2]
    else:
        if p.slice[1].type == 'IDENT':
            p[0] = ('ident', p[1])
        else:
            p[0] = (p.slice[1].type.lower(), p[1])

def p_expression_list(p):
    '''expression_list : expression_list COMMA exp_bool
                       | exp_bool'''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_empty(p):
    'empty :'
    pass

# Manejo de errores sintácticos con recuperación
def p_error(p):
    if p:
        error_msg = f"Error de sintaxis en '{p.value}' (tipo: {p.type}) en la línea {p.lineno}"
        raise SyntaxError(error_msg)
    else:
        raise SyntaxError("Error de sintaxis al final del archivo")

# Función para calcular la columna
def find_column(input, token):
    last_cr = input.rfind('\n', 0, token)
    if last_cr < 0:
        last_cr = 0
    column = (token - last_cr) + 1
    return column

# Construye el parser con opción de recuperación de errores
parser = yacc.yacc(debug=False, errorlog=yacc.NullLogger())

def build_tree(ast):
    # Esta función devuelve el AST para su uso en el Treeview
    return ast