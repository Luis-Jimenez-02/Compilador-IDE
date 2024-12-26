import lexer
from lexer import tokens
import hashlib


class SemanticError(Exception):
    pass


class Symbol:
    def __init__(self, name, type_, size=None, value=None, loc=None):
        self.name = name
        self.type = type_
        self.size = size
        self.value = value
        self.loc = None
        self.lines = []
        self.line_occurrences = {}
        self.is_array = size is not None

    def add_line(self, line):
        if line is not None:
            print(f"Añadiendo línea {line} a {self.name}")
            if line in self.line_occurrences:
                self.line_occurrences[line] += 1
            else:
                self.line_occurrences[line] = 1

            current_occurrences = len([l for l in self.lines if l == line])
            target_occurrences = max(1, self.line_occurrences[line] - 1)

            if current_occurrences < target_occurrences:
                self.lines.append(line)
            elif current_occurrences > target_occurrences:
                # Eliminamos las ocurrencias extra si hay más de las necesarias
                extra_occurrences = current_occurrences - target_occurrences
                for _ in range(extra_occurrences):
                    self.lines.remove(line)

            print(f"Líneas actuales para {self.name}: {self.lines}")

    def __repr__(self):
        return f"Symbol(name={self.name}, type={self.type}, value={self.value}, loc={self.loc}, lines={self.lines})"


class SymbolTable:
    def __init__(self):
        self.table = {}
        self.scope_stack = [{}]
        self.loc_counter = 1

    @staticmethod
    def generate_unique_loc(name, type_):
        # Crear un hash basado en el nombre y el tipo del símbolo, y truncarlo a los primeros 6 caracteres
        hash_input = f"{name}{type_}".encode()
        hash_digest = hashlib.md5(hash_input).hexdigest()[:6]
        return hash_digest

    def put(self, symbol: Symbol):
        scope = self.scope_stack[-1]
        if symbol.name in scope:
            existing = scope[symbol.name]
            if isinstance(existing, list):
                existing.append(symbol)
            else:
                scope[symbol.name] = [existing, symbol]
        else:
            symbol.loc = symbol.loc or self.generate_unique_loc(symbol.name,
                                                                symbol.type)  # Asigna un loc único al insertar
            scope[symbol.name] = symbol

        # print(f"Símbolo añadido: {symbol}")

    def reset_loc(self):
        # Reinicia el contador para asegurarse de que cada compilación tenga locs únicos
        self.loc_counter = 1

    def get(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return None

    def enter_scope(self):
        self.scope_stack.append({})
        # print("Nuevo scope ingresado:", self.scope_stack)

    def exit_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            # print(f"Scope salido: {scope}")
            # print(f"Pila actual: {self.scope_stack}")

    def get_all_symbols(self):
        symbols = []
        for scope in self.scope_stack:
            for name, symbol in scope.items():
                if isinstance(symbol, list):
                    symbols.extend(symbol)
                else:
                    symbols.append(symbol)
        return symbols

    def update_symbol_line(self, name, line):
        symbol = self.get(name)
        if symbol and line is not None:
            if isinstance(symbol, Symbol):
                symbol.add_line(line)
            elif isinstance(symbol, list):
                for sym in symbol:
                    sym.add_line(line)


def arithmetic_result_type(type1, type2, operator=None):
    numeric_types = {'int', 'float'}
    if type1 == 'error' or type2 == 'error':
        return 'error'
    if operator == 'divide':
        if type1 == 'int' and type2 == 'int':
            return 'int'  # División entera
        elif type1 in numeric_types and type2 in numeric_types:
            return 'float'  # División con 'float' produce 'float'
        else:
            raise SemanticError("Tipos incompatibles en división.")
    elif operator == 'power':
        if type1 in numeric_types and type2 == 'int':
            return type1  # La potencia con exponente entero mantiene el tipo de la base
        elif type1 in numeric_types and type2 in numeric_types:
            return 'float'  # Si el exponente es float, el resultado es float
        else:
            raise SemanticError("Tipos incompatibles en operación de potencia.")
    if type1 == type2:
        return type1
    elif type1 in numeric_types and type2 in numeric_types:
        return 'float'  # Promueve a 'float' si uno es 'float'
    else:
        raise SemanticError("Tipos incompatibles en operación aritmética.")


# Funcion de analisis
def analyze(ast):
    symbol_table = SymbolTable()
    errors = []
    annotated_ast = annotate_ast(ast, symbol_table, errors)
    return annotated_ast, symbol_table, errors

'''def generate_p_code(node):
        instructions=[]

        if node_type=='program':'''


# Función para anotar el AST con valores de 'loc' y 'line'
def annotate_ast(node, symbol_table, errors, current_type=None):
    if not isinstance(node, tuple):
        return node

    node_type = node[0]

    def process_node(node, line_info=None):
        if isinstance(node, tuple):
            node_type = node[0]
            if node_type == 'ident':
                ident = node[1] if len(node) > 1 else None
                ident_line_info = node[2] if len(node) > 2 else line_info
                if ident is not None and ident_line_info is not None:
                    symbol_table.update_symbol_line(ident, ident_line_info)
            elif node_type in ['rel', 'equals', 'not_equals', 'and', 'or']:
                for subnode in node[1:]:
                    process_node(subnode, line_info)
            else:
                for subnode in node[1:]:
                    process_node(subnode, line_info)
        elif isinstance(node, list):
            for subnode in node:
                process_node(subnode, line_info)

    def process_condition(condition, line_info):
        if isinstance(condition, tuple):
            if condition[0] in ['rel', 'equals', 'not_equals', 'and', 'or']:
                for subexpr in condition[1:]:
                    process_condition(subexpr, line_info)
            elif condition[0] == 'ident':
                ident = condition[1] if len(condition) > 1 else None
                if ident is not None:
                    symbol_table.update_symbol_line(ident, line_info)
                    print(f"Procesando identificador en condición: {ident} en línea {line_info}")
            elif condition[0] in ['not', 'negate']:
                process_condition(condition[1], line_info)
            else:
                for subexpr in condition[1:]:
                    if isinstance(subexpr, (tuple, list)):
                        process_condition(subexpr, line_info)
        elif isinstance(condition, list):
            for subexpr in condition:
                process_condition(subexpr, line_info)

    def process_expression(expr, line_info=None, processed_idents=None):
        if processed_idents is None:
            processed_idents = set()

        if isinstance(expr, tuple):
            if expr[0] == 'ident':
                ident = expr[1] if len(expr) > 1 else None
                if ident is not None and ident not in processed_idents:
                    print(f"Procesando identificador {ident} en línea {line_info}")
                    symbol_table.update_symbol_line(ident, line_info)
                    processed_idents.add(ident)
            elif expr[0] in ['rel', 'equals', 'not_equals', 'plus', 'minus', 'times', 'divide', 'and', 'or']:
                for subexpr in expr[1:]:
                    process_expression(subexpr, line_info, processed_idents)
        elif isinstance(expr, list):
            for subexpr in expr:
                process_expression(subexpr, line_info, processed_idents)

    if node_type == 'program':
        symbol_table.enter_scope()
        decls = [annotate_ast(decl, symbol_table, errors) for decl in node[1]]
        sents = [annotate_ast(sent, symbol_table, errors) for sent in node[2]]
        return ('program', decls, sents)
        #generate_code_p(node_type)

    elif node_type == 'decl':
        tipo = node[1]
        ids = node[2]
        line_info = node[3] if len(node) > 3 else None
        loc_info = node[4] if len(node) > 4 else None
        
        for id_node in ids:
            if isinstance(id_node, tuple) and id_node[0] == 'array_decl':
                # Declaración de array
                array_name = id_node[1]
                array_size = id_node[2]
                symbol = Symbol(name=array_name, type_=tipo, size=array_size)
                symbol.add_line(line_info)
                symbol_table.put(symbol)
            else:
                # Variable normal - aquí está el error, usabas 'ident' en lugar de 'id_node'
                symbol = Symbol(name=id_node, type_=tipo, loc=loc_info)
                symbol.add_line(line_info)
                symbol_table.put(symbol)

        return ('decl', tipo, ids)

    elif node_type == 'sent_assign':
        if isinstance(node[1], tuple) and node[1][0] == 'array_access':
            # Asignación a elemento de array
            array_name = node[1][1]
            index_expr = annotate_ast(node[1][2], symbol_table, errors)
            value_expr = annotate_ast(node[2], symbol_table, errors)
            line_info = node[3] if len(node) > 3 else None
            
            symbol = symbol_table.get(array_name)
            if not symbol:
                error_msg = f"Array '{array_name}' no declarado"
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}
            
            if not symbol.is_array:
                error_msg = f"'{array_name}' no es un array"
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}
            
            # Verificar que el índice sea entero
            if index_expr['type'] != 'int':
                error_msg = f"El índice debe ser entero"
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}
            
            # Verificar tipo del valor asignado
            if value_expr['type'] != symbol.type:
                error_msg = f"Tipo incompatible en asignación a elemento de array"
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}
            
            return {'node': ('array_assign', array_name, index_expr, value_expr, line_info), 'type': symbol.type}
        else:
            # Asignación normal (mantener el código existente)
            ident = node[1]
            expr = annotate_ast(node[2], symbol_table, errors)
            line_info = node[3] if len(node) > 3 else None
            loc_info = node[4] if len(node) > 4 else None

            symbol_table.update_symbol_line(ident, line_info)
            process_expression(node[2], line_info)  # Asegurarse de procesar la expresión

            symbol = symbol_table.get(ident)
            if not symbol:
                error_msg = f"Variable '{ident}' usada sin declarar en la línea {line_info if line_info else 'desconocida'}."
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}

            # Actualizar la línea y loc del símbolo
            if isinstance(symbol, Symbol):
                symbol.add_line(line_info)
                symbol.loc = loc_info if symbol.loc is None else symbol.loc
            elif isinstance(symbol, list):
                for sym in symbol:
                    sym.add_line(line_info)
                    sym.loc = loc_info if sym.loc is None else sym.loc

            # Verificación de tipos en asignación
            expr_type = expr.get('type')
            if symbol.type == expr_type:
                symbol.value = expr.get('value')
                return {'node': ('sent_assign', ident, expr, line_info, loc_info), 'type': symbol.type}
            else:
                error_msg = f"Tipo incompatible en asignación a '{ident}'. Se esperaba '{symbol.type}', se obtuvo '{expr_type}'."
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}

    elif node_type == 'array_access':
        array_name = node[1]
        index_expr = annotate_ast(node[2], symbol_table, errors)
        
        symbol = symbol_table.get(array_name)
        if not symbol:
            error_msg = f"Array '{array_name}' no declarado"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        
        if not symbol.is_array:
            error_msg = f"'{array_name}' no es un array"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        
        if index_expr['type'] != 'int':
            error_msg = f"El índice debe ser entero"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        
        return {'node': ('array_access', array_name, index_expr), 'type': symbol.type}
    
    elif node_type == 'sent_read':
        ident = node[1]
        line_info = node[2] if len(node) > 2 else None
        loc_info = node[3] if len(node) > 3 else None
        symbol_table.update_symbol_line(ident, line_info)
        symbol = symbol_table.get(ident)
        if not symbol:
            error_msg = f"Variable '{ident}' usada sin declarar en 'read'."
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}

        # Actualizar `loc` y `line` si están disponibles
        if isinstance(symbol, Symbol):
            symbol.add_line(line_info)
            symbol.loc = loc_info if symbol.loc is None else symbol.loc
        elif isinstance(symbol, list):
            for sym in symbol:
                sym.add_line(line_info)
                sym.loc = loc_info if sym.loc is None else sym.loc
        return {'node': ('sent_read', ident, line_info, loc_info), 'type': symbol.type}
    
    elif node_type == 'sent_write':
        expressions = node[1]
        processed_items = []
        for expr in expressions:
            if isinstance(expr, tuple) and expr[0] == 'string':
                processed_items.append({'node': expr, 'type': 'string', 'value': expr[1]})
            else:
                processed_items.append(annotate_ast(expr, symbol_table, errors))
        return {'node': ('sent_write', processed_items), 'type': 'void'}

    elif node_type == 'number':
        value = node[1]
        return {'node': node, 'type': 'int' if isinstance(value, int) else 'float', 'value': value}

    elif node_type == 'bool':
        value = node[1]
        return {'node': node, 'type': 'bool', 'value': value}

    elif node_type == 'ident':
        ident = node[1]
        line_info = node[2] if len(node) > 2 else None
        symbol_table.update_symbol_line(ident, line_info)
        symbol = symbol_table.get(ident)
        if not symbol:
            error_msg = f"Variable '{ident}' usada sin declarar."
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        if isinstance(symbol, Symbol):
            symbol.add_line(line_info)
        elif isinstance(symbol, list):
            for sym in symbol:
                sym.add_line(line_info)
        return {'node': node, 'type': symbol.type, 'value': symbol.value}

    elif node_type in ('plus', 'minus', 'times', 'divide'):
        left = annotate_ast(node[1], symbol_table, errors)
        right = annotate_ast(node[2], symbol_table, errors)
        process_expression(node[1], node[3] if len(node) > 3 else None)
        process_expression(node[2], node[3] if len(node) > 3 else None)
        if isinstance(node[1], tuple) and node[1][0] == 'ident':
            symbol_table.update_symbol_line(node[1][1], node[1][2] if len(node[1]) > 2 else None)
        if isinstance(node[2], tuple) and node[2][0] == 'ident':
            symbol_table.update_symbol_line(node[2][1], node[2][2] if len(node[2]) > 2 else None)
        try:
            result_type = arithmetic_result_type(left['type'], right['type'], node_type)
        except SemanticError as e:
            error_msg = f"Tipos incompatibles en operación '{node_type}': {e}"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}

        # Evaluación si es posible
        value = None
        if left.get('value') is not None and right.get('value') is not None and result_type != 'error':
            if node_type == 'plus':
                value = left['value'] + right['value']
            elif node_type == 'minus':
                value = left['value'] - right['value']
            elif node_type == 'times':
                value = left['value'] * right['value']
            elif node_type == 'divide':
                if right['value'] == 0:
                    error_msg = "División por cero."
                    errors.append(error_msg)
                    return {'node': ('error', error_msg), 'type': 'error'}
                value = left['value'] / right['value'] if result_type == 'float' else left['value'] // right['value']
        return {'node': (node_type, left, right), 'type': result_type, 'value': value}
    
    elif node_type == 'power':
        base = annotate_ast(node[1], symbol_table, errors)
        exponent = annotate_ast(node[2], symbol_table, errors)
        
        # Procesar expresiones para actualizar líneas
        process_expression(node[1])
        process_expression(node[2])
        
        try:
            result_type = arithmetic_result_type(base['type'], exponent['type'], 'power')
        except SemanticError as e:
            error_msg = f"Tipos incompatibles en operación de potencia: {e}"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}

        # Evaluación si es posible
        value = None
        if base.get('value') is not None and exponent.get('value') is not None and result_type != 'error':
            try:
                value = base['value'] ** exponent['value']
                # Si el resultado debe ser entero, convertirlo
                if result_type == 'int':
                    value = int(value)
            except ZeroDivisionError:
                error_msg = "Error matemático: 0 elevado a potencia negativa."
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}
            except OverflowError:
                error_msg = "Error matemático: resultado demasiado grande."
                errors.append(error_msg)
                return {'node': ('error', error_msg), 'type': 'error'}

        return {'node': ('power', base, exponent), 'type': result_type, 'value': value}

    elif node_type == 'rel':
        operator = node[1]
        left = annotate_ast(node[2], symbol_table, errors)
        right = annotate_ast(node[3], symbol_table, errors)
        process_expression(node[2])
        process_expression(node[3])
        try:
            result_type = arithmetic_result_type(left['type'], right['type'])
        except SemanticError as e:
            error_msg = f"Tipos incompatibles en operación relacional '{operator}': {e}"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = None
        if left.get('value') is not None and right.get('value') is not None and result_type != 'error':
            value = eval(f"left['value'] {operator} right['value']")
        return {'node': ('rel', operator, left, right), 'type': 'bool', 'value': value}

    elif node_type == 'equals':
        left = annotate_ast(node[1], symbol_table, errors)
        right = annotate_ast(node[2], symbol_table, errors)
        process_expression(node[1])
        process_expression(node[2])
        try:
            result_type = arithmetic_result_type(left['type'], right['type'])
        except SemanticError as e:
            error_msg = f"Tipos incompatibles en igualdad: {e}"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = left['value'] == right['value'] if left.get('value') is not None and right.get(
            'value') is not None else None
        return {'node': ('equals', left, right), 'type': 'bool', 'value': value}

    elif node_type == 'not_equals':
        left = annotate_ast(node[1], symbol_table, errors)
        right = annotate_ast(node[2], symbol_table, errors)
        process_expression(node[1])
        process_expression(node[2])
        try:
            result_type = arithmetic_result_type(left['type'], right['type'])
        except SemanticError as e:
            error_msg = f"Tipos incompatibles en desigualdad: {e}"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = left['value'] != right['value'] if left.get('value') is not None and right.get(
            'value') is not None else None
        return {'node': ('not_equals', left, right), 'type': 'bool', 'value': value}

    elif node_type == 'not':
        operand = annotate_ast(node[1], symbol_table, errors)
        if operand['type'] != 'bool':
            error_msg = "Operador 'not' aplicado a un tipo no booleano."
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = not operand['value'] if operand.get('value') is not None else None
        return {'node': ('not', operand), 'type': 'bool', 'value': value}

    elif node_type == 'and':
        left = annotate_ast(node[1], symbol_table, errors)
        right = annotate_ast(node[2], symbol_table, errors)
        process_expression(node[1])
        process_expression(node[2])
        if left['type'] != 'bool' or right['type'] != 'bool':
            error_msg = "Operador 'and' requiere operandos booleanos."
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = left['value'] and right['value'] if left.get('value') is not None and right.get(
            'value') is not None else None
        return {'node': ('and', left, right), 'type': 'bool', 'value': value}

    elif node_type == 'or':
        left = annotate_ast(node[1], symbol_table, errors)
        right = annotate_ast(node[2], symbol_table, errors)
        process_expression(node[1])
        process_expression(node[2])
        if left['type'] != 'bool' or right['type'] != 'bool':
            error_msg = "Operador 'or' requiere operandos booleanos."
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        value = left['value'] or right['value'] if left.get('value') is not None and right.get(
            'value') is not None else None
        return {'node': ('or', left, right), 'type': 'bool', 'value': value}

    elif node_type == 'bloque':
        symbol_table.enter_scope()
        statements = [annotate_ast(stmt, symbol_table, errors) for stmt in node[1]]
        symbol_table.exit_scope()
        return ('bloque', statements)

    elif node_type == 'if':
        condition = annotate_ast(node[1], symbol_table, errors)
        then_block = annotate_ast(node[2], symbol_table, errors)
        else_block = annotate_ast(node[3], symbol_table, errors) if len(node) > 3 else None
        line_info = node[4] if len(node) > 4 else None
        
        # Verificar que la condición sea booleana
        if condition['type'] != 'bool':
            error_msg = f"La condición del if debe ser booleana"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        
        return {
            'node': ('if', condition, then_block, else_block, line_info),
            'type': 'void'
        }

    elif node_type == 'while':
        condition = annotate_ast(node[1], symbol_table, errors)
        body = annotate_ast(node[2], symbol_table, errors)
        line_info = node[3] if len(node) > 3 else None
        
        # Verificar que la condición sea booleana
        if condition['type'] != 'bool':
            error_msg = f"La condición del while debe ser booleana"
            errors.append(error_msg)
            return {'node': ('error', error_msg), 'type': 'error'}
        
        return {
            'node': ('while', condition, body, line_info),
            'type': 'void'
        }

    elif node_type == 'do_until':
        body = annotate_ast(node[1], symbol_table, errors) if len(node) > 1 else None
        condition = annotate_ast(node[2], symbol_table, errors) if len(node) > 2 else None
        line_info = node[3] if len(node) > 3 else None

        if condition is not None:
            process_condition(node[2], line_info)

        # print(f"\nEntrando al do_until en la línea {line_info}")
        return {'node': ('do_until', body, condition, line_info), 'type': 'void'}

    else:
        # Retorna el nodo sin modificaciones para casos no manejados
        return node
