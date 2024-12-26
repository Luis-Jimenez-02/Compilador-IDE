import ply.lex as lex

# Lista de nombres de tokens. Esta lista es requerida.
tokens = [
    'IDENT', 'NUMBER',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'EQUALS', 'POWER',
    'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'STRING',
    'SEMICOLON', 'COMMA',
    'LESS', 'LESSEQUAL', 'GREATER', 'GREATEREQUAL', 'NOTEQUAL', 'ASSIGN',
    'LBRACE', 'RBRACE'
]

# Palabras reservadas
reserved = {
    'program': 'PROGRAM',
    'if': 'IF',
    'else': 'ELSE',
    'while': 'WHILE',
    'read': 'READ',
    'write': 'WRITE',
    'int': 'INT',
    'float': 'FLOAT',
    'bool': 'BOOL',
    'true': 'TRUE',
    'false': 'FALSE',
    'not': 'NOT',
    'and': 'AND',
    'or': 'OR',
    'fi': 'FI',
    'do': 'DO',
    'until': 'UNTIL',
    'then': 'THEN',
    'break': 'BREAK'
}

tokens += list(reserved.values())

# Reglas para tokens simples
t_PLUS     = r'\+'
t_MINUS    = r'-'
t_TIMES    = r'\*'
t_DIVIDE   = r'/'
t_POWER    = r'\^' 
t_EQUALS   = r'=='
t_LESS     = r'<'
t_LESSEQUAL = r'<='
t_GREATER  = r'>'
t_GREATEREQUAL = r'>='
t_NOTEQUAL = r'!='
t_ASSIGN   = r'='
t_LPAREN   = r'\('
t_RPAREN   = r'\)'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_LBRACE   = r'\{'
t_RBRACE   = r'\}'
t_SEMICOLON = r';'
t_COMMA = r','

# Regla para identificadores y palabras reservadas
def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value, 'IDENT')  # Check for reserved words
    return t

# Regla para números (enteros y flotantes)
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

# Reglas para manejar comentarios
def t_COMMENT(t):
    r'//.*'
    pass  # No se devuelve ningún token para los comentarios.

# Regla para manejar bloques de comentarios (múltiples líneas)
def t_BLOCKCOMMENT(t):
    r'/\*(.|\n)*?\*/'
    pass  # Token ignorado

# Regla para manejar espacios en blanco (espacios y tabs)
t_ignore  = ' \t'

# Función para rastrear el número de línea
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Función para calcular la columna del token
def find_column(input, token):
    line_start = input.rfind('\n', 0, token.lexpos) + 1
    return (token.lexpos - line_start) + 1

# Regla para manejar errores léxicos (caracteres ilegales)
def t_error(t):
    error_msg = f"Error léxico: Carácter ilegal '{t.value[0]}' en línea {t.lineno}, columna {find_column(t.lexer.lexdata, t)}"
    raise ValueError(error_msg) # Retornamos t en lugar del mensaje

def t_STRING(t):
    r'\"([^\\\n]|(\\.))*?\"'
    t.value = t.value[1:-1]  # Quitar las comillas
    return t
        
# Construye el lexer
lexer = lex.lex()

