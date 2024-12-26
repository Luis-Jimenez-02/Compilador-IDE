import tkinter as tk
from tkinter import filedialog, Menu, ttk, Label, Frame, messagebox
import lexer
import syntax_parser
from syntax_parser import parser, build_tree
import re
import semantic_analyzer

class PCodeInterpreter:
    def __init__(self, console_widget):
        self.stack = []
        self.variables = {}
        self.code = []
        self.pc = 0  # Program Counter
        self.console = console_widget
        self.labels = {}
        self.waiting_for_input = False
        self.input_variable = None
        self.arrays = {}

    def load_program(self, p_code):
        self.stack = []
        self.variables = {}
        self.code = []
        self.pc = 0
        self.labels = {}
        
        # Procesar el código y registrar las etiquetas
        for i, line in enumerate(p_code):
            line = line.strip()
            if not line:  # Ignorar líneas vacías
                continue
            if line.endswith(':'):  # Es una etiqueta
                label = line[:-1]  # Quitar el :
                self.labels[label] = len(self.code)  # Usar la longitud actual del código
                print(f"Etiqueta registrada: {label} -> posición {len(self.code)}")
            else:
                self.code.append(line)
                print(f"Instrucción {len(self.code)-1}: {line}")

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if self.stack:
            return self.stack.pop()
        raise Exception("Stack underflow")

    def execute_next(self):
        if self.pc >= len(self.code):
            return False

        instruction = self.code[self.pc].strip()
        print(f"Stack antes: {self.stack}")  # Para depuración
        print(f"Ejecutando: '{instruction}'")  # Para depuración
        
        
        if not instruction or instruction.startswith('//'):
            self.pc += 1
            return True

        try:
            # Instrucciones aritméticas
            if instruction == 'adi':
                b = self.pop()
                a = self.pop()
                self.push(a + b)
            elif instruction == 'sbi':
                b = self.pop()
                a = self.pop()
                self.push(a - b)
            elif instruction == 'mpi':
                b = self.pop()
                a = self.pop()
                self.push(a * b)
            elif instruction == 'div':
                b = self.pop()
                a = self.pop()
                if b == 0:
                    raise Exception("División por cero")
                self.push(a / b)
            elif instruction == 'not':
                value = self.pop()
                self.push(1 if value == 0 else 0)
                
            elif instruction == 'equ':
                b = self.pop()
                a = self.pop()
                self.push(1 if a == b else 0)
                
            elif instruction == 'neq':
                b = self.pop()
                a = self.pop()
                self.push(1 if a != b else 0)
            
            # Carga y almacenamiento
            elif instruction.startswith('ldc '):
                value = float(instruction.split()[1])
                self.push(value)
            elif instruction.startswith('sto '):
                var = instruction.split()[1]
                print(f"Variable a almacenar: '{var}'")  # Para depuración
                var = var.replace('*temp*', '_temp_')
                print(f"Variable después del reemplazo: '{var}'")
                value = self.pop()
                self.variables[var] = value   
            elif instruction.startswith('lod '):
                var = instruction.split()[1].replace('*temp*', '_temp_')  # Normalizar nombres de variables
                if var not in self.variables:
                    raise Exception(f"Variable {var} no inicializada")
                self.push(self.variables[var])

            elif instruction.startswith('print '):
                # Extraer la cadena entre comillas
                string = instruction[7:-1]  # Quitar 'print "' y la última comilla
                self.console.insert('end', f"{string}\n")
                self.console.see('end')
            
            # Entrada/Salida
            elif instruction == 'inp':
                self.waiting_for_input = True
                self.input_variable = self.code[self.pc + 1].split()[1]
                self.console.insert('end', f"Ingrese valor para {self.input_variable}: ")
                return True
            elif instruction == 'out':
                value = self.pop()
                self.console.insert('end', f"{value}\n")
                self.console.see('end')
            
            # Control de flujo
            elif instruction.startswith('jmp '):
                label = instruction.split()[1]
                print(f"jmp: Saltando a {label}")  # Para depuración
                if label in self.labels:
                    self.pc = self.labels[label]
                    print(f"Salto realizado a posición {self.pc}")  # Para depuración
                    return True
                return False
            elif instruction.startswith('jz '):
                label = instruction.split()[1]
                condition = self.pop()
                print(f"jz: Condición = {condition}, Label = {label}")  # Para depuración
                if condition == 0:
                    if label in self.labels:
                        self.pc = self.labels[label]
                        print(f"Saltando a {label} en posición {self.pc}")  # Para depuración
                        return True
                self.pc += 1
                return True
            elif instruction.startswith('array_store'):
                # array_store nombre_array índice
                _, array_name, index = instruction.split()
                index = int(index)
                value = self.pop()
                if array_name not in self.arrays:
                    self.arrays[array_name] = []
                while len(self.arrays[array_name]) <= index:
                    self.arrays[array_name].append(0)
                self.arrays[array_name][index] = value

            elif instruction.startswith('array_load'):
                # array_load nombre_array índice
                _, array_name, index = instruction.split()
                index = int(index)
                if array_name not in self.arrays:
                    raise Exception(f"Array {array_name} no inicializado")
                if index >= len(self.arrays[array_name]):
                    raise Exception(f"Índice {index} fuera de rango")
                self.push(self.arrays[array_name][index])
            
            # Comparaciones
            elif instruction == 'grt':
                b = self.pop()
                a = self.pop()
                self.push(1 if a > b else 0)
            elif instruction == 'les':
                b = self.pop()
                a = self.pop()
                self.push(1 if a < b else 0)
            elif instruction == 'equ':
                b = self.pop()
                a = self.pop()
                self.push(1 if a == b else 0)
            elif instruction == 'neq':
                b = self.pop()
                a = self.pop()
                self.push(1 if a != b else 0)
            elif instruction == 'geq':
                b = self.pop()
                a = self.pop()
                self.push(1 if a >= b else 0)
            elif instruction == 'leq':
                b = self.pop()
                a = self.pop()
                self.push(1 if a <= b else 0)
            
            # Fin del programa
            elif instruction == 'hlt':
                return False

        except Exception as e:
            self.console.insert('end', f"Error de ejecución: {str(e)}\n")
            print(f"Error en instrucción {self.pc}: {instruction}")  # Para depuración
            print(f"Stack al momento del error: {self.stack}")       # Para depuración
            return False

        self.pc += 1
        return True

    def handle_input(self, value):
        if self.waiting_for_input:
            try:
                num_value = float(value)
                self.push(num_value)
                self.waiting_for_input = False
                self.pc += 1  # Avanzar al 'sto'
                return True
            except ValueError:
                self.console.insert('end', "Error: Por favor ingrese un número válido\n")
                return False
        return True

root = tk.Tk()
root.title("IDE-JCLO_PGSOE")
root.state('zoomed')  # Para la pantalla completa

# Definición de colores con tonos grises y texto en blanco
color_lexico = "#D3D3D3"
color_sintactico = "#D3D3D3"
color_semantico = "#D3D3D3"
color_errores = "#D3D3D3"
color_resultados = "#D3D3D3"

# Colores de texto
texto_color_errores = "#404040"
texto_color_resultados = "#404040"


def convert_p_to_tiny(p_code):
    tiny_code = []
    label_map = {}
    current_line = 0
    
    # Primera pasada: mapear etiquetas a números de línea
    for line in p_code:
        if line.strip().endswith(':'):  # Es una etiqueta
            label = line.strip()[:-1]  # Quitar el ':'
            label_map[label] = current_line
        else:
            current_line += 1

    # Segunda pasada: convertir instrucciones
    current_line = 0
    for line in p_code:
        line = line.strip()
        if not line or line.startswith('//'):  # Ignorar líneas vacías y comentarios
            continue
            
        if line.endswith(':'):  # Ignorar etiquetas en la segunda pasada
            continue

        # Mapear instrucciones de código P a Tiny
        parts = line.split()
        opcode = parts[0]

        if opcode == 'ldc':
            tiny_code.append(f"r1 = {parts[1]}")
        
        elif opcode == 'sto':
            tiny_code.append(f"{parts[1]} = r1")
            
        elif opcode == 'lod':
            tiny_code.append(f"r1 = {parts[1]}")
            
        elif opcode == 'adi':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 + r2")
            
        elif opcode == 'sbi':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 - r2")
            
        elif opcode == 'mpi':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 * r2")
            
        elif opcode == 'div':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 / r2")
            
        elif opcode == 'equ':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 == r2")
            
        elif opcode == 'grt':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 > r2")
            
        elif opcode == 'les':
            tiny_code.append("r2 = r1")
            tiny_code.append("r1 = pop")
            tiny_code.append("r1 = r1 < r2")
            
        elif opcode == 'jmp':
            if parts[1] in label_map:
                tiny_code.append(f"goto {label_map[parts[1]]}")
            
        elif opcode == 'jz':
            if parts[1] in label_map:
                tiny_code.append("if r1 == 0")
                tiny_code.append(f"goto {label_map[parts[1]]}")
                tiny_code.append("endif")
            
        elif opcode == 'inp':
            tiny_code.append("read r1")
            
        elif opcode == 'out':
            tiny_code.append("write r1")
            
        elif opcode.startswith('print'):
            # Extraer el string entre comillas
            string = line[7:-1]  # Quitar 'print "' y la última comilla
            tiny_code.append(f'write "{string}"')
            
        elif opcode == 'hlt':
            tiny_code.append("halt")
        
        current_line += 1

    # Numerar las líneas del código Tiny
    numbered_tiny_code = [f"{i}: {line}" for i, line in enumerate(tiny_code)]
    return numbered_tiny_code

def nuevoArchivo():
    editorTexto.delete(1.0, tk.END)


def abrirArchivo():
    ruta_archivo = filedialog.askopenfilename(filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")])
    if ruta_archivo:
        try:
            with open(ruta_archivo, "r") as archivo:
                contenido = archivo.read()
            editorTexto.delete(1.0, tk.END)
            editorTexto.insert(tk.END, contenido)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")


def guardarArchivo():
    ruta_archivo = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Archivos de texto", "*.txt"),
                                                                                    ("Todos los archivos", "*.*")])
    if ruta_archivo:
        try:
            with open(ruta_archivo, "w") as archivo:
                contenido = editorTexto.get(1.0, tk.END)
                archivo.write(contenido)
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")


def compilarCodigo():
    # Limpiar las áreas de salida
    errores.delete('1.0', tk.END)
    resultados.delete('1.0', tk.END)
    codigoP.delete('1.0', tk.END)  # Limpiar la pestaña del código P

    # Limpiar los árboles
    for item in sintactico_tree.get_children():
        sintactico_tree.delete(item)
    for item in semantico_tree.get_children():
        semantico_tree.delete(item)
    for item in lexico_tree.get_children():
        lexico_tree.delete(item)
    for item in tablaSimbolos_tree.get_children():
        tablaSimbolos_tree.delete(item)

    codigo = editorTexto.get("1.0", tk.END).strip()

    if not codigo:
        messagebox.showwarning("Advertencia", "El editor de código está vacío.")
        return

    # Análisis léxico
    tiene_errores = False
    lexer.lexer.lineno = 1  # Reiniciar el contador de líneas
    lexer.lexer.input(codigo)
    try:
        while True:
            tok = lexer.lexer.token()
            if not tok:
                break
            columna = lexer.find_column(lexer.lexer.lexdata, tok)
            lexico_tree.insert('', 'end', values=(tok.type, tok.value, tok.lineno, columna))
    except ValueError as e:
        errores.insert(tk.END, str(e) + "\n")
        return
    except Exception as e:
        errores.insert(tk.END, f"Error inesperado durante el análisis léxico: {str(e)}\n")
        return

    if tiene_errores:
        return

    # Análisis sintáctico
    try:
        resultado = syntax_parser.parser.parse(codigo, lexer=lexer.lexer)
        if resultado:
            # Mostrar árbol sintáctico
            build_syntax_tree(sintactico_tree, resultado)
            resultados.insert(tk.END, "Análisis sintáctico completado con éxito.\n")

            # Análisis semántico
            try:
                annotated_ast, symbol_table, semantic_errors = semantic_analyzer.analyze(resultado)
                print("Árbol semántico anotado:", annotated_ast)  # Depuración
                build_semantic_tree(semantico_tree, annotated_ast)

                if semantic_errors:
                    for error in semantic_errors:
                        errores.insert(tk.END, f"Error Semántico: {error}\n")
                else:
                    resultados.insert(tk.END, "Análisis semántico completado sin errores.\n")

                # Mostrar la tabla de símbolos
                for scope_index, scope in enumerate(symbol_table.scope_stack):
                    scope_id = tablaSimbolos_tree.insert('', 'end', text=f"Ámbito {scope_index}")
                    for name, symbol in scope.items():
                        if isinstance(symbol, list):
                            for idx, sym in enumerate(symbol):
                                lines_info = sym.lines if sym.lines else []
                                loc_info = sym.loc if sym.loc is not None else "N/A"
                                insert_symbol(scope_id, f"{sym.name} (colisión {idx})", sym.type, str(sym.value),
                                              str(loc_info), lines_info)
                        else:
                            lines_info = symbol.lines if symbol.lines else []
                            loc_info = symbol.loc if symbol.loc is not None else "N/A"
                            insert_symbol(scope_id, symbol.name, symbol.type, str(symbol.value), str(loc_info),
                                          lines_info)

                resultados.insert(tk.END, "Tabla de símbolos generada y mostrada.\n")

                # Generar código P
                try:
                    p_code = generate_code_p_from_tree(annotated_ast)
                    print("Código P generado:", p_code)  # Depuración
                    if p_code:
                        codigoP.insert(tk.END, "\n".join(p_code))  # Mostrar el código P
                        resultados.insert(tk.END, "Código P generado y mostrado.\n")
                    else:
                        resultados.insert(tk.END, "No se generó código P.\n")
                except Exception as e:
                    errores.insert(tk.END, f"Error al generar el código P: {str(e)}\n")
                
                # Dentro de la función compilarCodigo(), reemplaza la parte de generación de código P por:
                try:
                    p_code = generate_code_p_from_tree(annotated_ast)
                    if p_code:
                        codigoP.insert(tk.END, "\n".join(p_code))
                        resultados.insert(tk.END, "Código P generado y mostrado.\n")
                        
                        # Generar y mostrar código Tiny
                        '''try:
                            tiny_code = convert_p_to_tiny(p_code)
                            codigoTiny.delete('1.0', tk.END)  # Limpiar contenido previo
                            codigoTiny.insert(tk.END, "\n".join(tiny_code))
                            resultados.insert(tk.END, "Código Tiny generado y mostrado.\n")
                        except Exception as e:
                            errores.insert(tk.END, f"Error al generar el código Tiny: {str(e)}\n")'''
                    else:
                        resultados.insert(tk.END, "No se generó código P.\n")
                except Exception as e:
                    errores.insert(tk.END, f"Error al generar el código P: {str(e)}\n")

            except SyntaxError as se:
                errores.insert(tk.END, str(se) + "\n")
                return
            except Exception as se:
                errores.insert(tk.END, f"Error en el análisis semántico: {str(se)}\n")
        else:
            errores.insert(tk.END, "No se pudo construir el árbol sintáctico.\n")
    except Exception as e:
        errores.insert(tk.END, f"Error de análisis: {str(e)}\n")


def generate_code_p_from_tree(ast, indent=0, p_code=None, label_counter=None):
    if p_code is None:
        p_code = []
    if label_counter is None:
        label_counter = {"label": 0}

    def get_label():
        label = f"L{label_counter['label']}"
        label_counter['label'] += 1
        return label
    
    def generate_power_code(base, exponent):
        # Generar una etiqueta única para el bucle de potencia
        start_label = get_label()
        end_label = get_label()

        # Cargar y guardar la base en una variable temporal
        generate_code_p_from_tree(base, indent + 4, p_code, label_counter)
        p_code.append("sto _temp_base")  # Guardar base

        # Cargar y guardar el exponente en una variable temporal
        generate_code_p_from_tree(exponent, indent + 4, p_code, label_counter)
        p_code.append("sto _temp_exp")  # Guardar exponente
        
        # Cargar el resultado inicial (1)
        p_code.append("ldc 1")  # Resultado = 1
        p_code.append("sto _temp_result")
        
        # Inicio del bucle
        p_code.append(f"{start_label}:")
        p_code.append("lod _temp_result")
        p_code.append("lod _temp_exp")   # Cargar exponente
        p_code.append("ldc 0")           # Cargar 0 para comparación
        p_code.append("grt")             # Comparar si exponente > 0
        p_code.append(f"jz {end_label}") # Si no es mayor que 0, terminar
        
        # Multiplicar resultado por base
        p_code.append("lod _temp_result")
        p_code.append("lod _temp_base")  # Cargar base
        p_code.append("mpi")             # Multiplicar por resultado actual
        p_code.append("sto _temp_result")
        
        # Decrementar exponente
        p_code.append("lod _temp_exp")
        p_code.append("ldc 1")
        p_code.append("sbi")             # Restar 1
        p_code.append("sto _temp_exp")   # Guardar nuevo valor
        
        p_code.append(f"jmp {start_label}")  # Volver al inicio del bucle
        p_code.append(f"{end_label}:")       # Etiqueta de fin

        p_code.append("lod _temp_result")

        

    if isinstance(ast, tuple) and ast[0] == 'program':
        p_code.append("// Inicio del programa")
        for child in ast[1:]:
            generate_code_p_from_tree(child, indent + 4, p_code, label_counter)
        p_code.append("hlt")
        return p_code

    if isinstance(ast, dict):
        node_repr = ast.get('node')
        node_type = ast.get('type')

        if node_repr is None:
            return p_code

        if node_repr[0] == 'program':
            p_code.append("// Inicio del programa")
            for child in node_repr[1:]:
                generate_code_p_from_tree(child, indent + 4, p_code, label_counter)
            p_code.append("hlt")

        elif node_repr[0] == 'sent_assign':
            variable = node_repr[1]
            expression = node_repr[2]
            generate_code_p_from_tree(expression, indent + 4, p_code, label_counter)
            p_code.append(f"sto {variable}")

        elif node_repr[0] in ['plus', 'minus', 'times', 'divide']:
            left_operand = node_repr[1]
            right_operand = node_repr[2]
            generate_code_p_from_tree(left_operand, indent + 4, p_code, label_counter)
            generate_code_p_from_tree(right_operand, indent + 4, p_code, label_counter)
            op_map = {
                'plus': 'adi',
                'minus': 'sbi',
                'times': 'mpi',
                'divide': 'div'
            }
            p_code.append(op_map[node_repr[0]])

        elif node_repr[0] == 'power':
            base = node_repr[1]
            exponent = node_repr[2]
            generate_power_code(base, exponent)
        
        elif node_repr[0] == 'number':
            p_code.append(f"ldc {node_repr[1]}")

        elif node_repr[0] == 'ident':
            variable = node_repr[1]
            p_code.append(f"lod {variable}")

        elif node_repr[0] == 'if':
            condition = node_repr[1]
            then_block = node_repr[2]
            else_block = node_repr[3]
            
            end_label = get_label()
            else_label = get_label()
            
            # Generar código para la condición
            generate_code_p_from_tree(condition, indent + 4, p_code, label_counter)
            p_code.append(f"jz {else_label}")
            
            # Generar código para el bloque then
            generate_code_p_from_tree(then_block, indent + 4, p_code, label_counter)
            p_code.append(f"jmp {end_label}")
            
            # Generar código para el bloque else
            p_code.append(f"{else_label}:")
            if else_block:
                generate_code_p_from_tree(else_block, indent + 4, p_code, label_counter)
            
            p_code.append(f"{end_label}:")

        elif node_repr[0] == 'while':
            condition = node_repr[1]
            body = node_repr[2]
            
            start_label = get_label()
            end_label = get_label()
            
            p_code.append(f"{start_label}:")
            generate_code_p_from_tree(condition, indent + 4, p_code, label_counter)
            p_code.append(f"jz {end_label}")
            
            generate_code_p_from_tree(body, indent + 4, p_code, label_counter)
            p_code.append(f"jmp {start_label}")
            p_code.append(f"{end_label}:")

        elif node_repr[0] == 'do_until':
            body = node_repr[1]
            condition = node_repr[2]
            
            start_label = get_label()
            
            # Etiqueta de inicio del bucle
            p_code.append(f"{start_label}:")
            
            # Generar código para el cuerpo del do-until
            generate_code_p_from_tree(body, indent + 4, p_code, label_counter)
            
            # Generar código para la condición
            generate_code_p_from_tree(condition, indent + 4, p_code, label_counter)
            
            # Si la condición es falsa (0), volver al inicio
            p_code.append(f"jz {start_label}")

        elif node_repr[0] == 'bloque':
            for stmt in node_repr[1]:
                generate_code_p_from_tree(stmt, indent + 4, p_code, label_counter)

        elif node_repr[0] == 'rel':
            operator = node_repr[1]
            left = node_repr[2]
            right = node_repr[3]
            
            generate_code_p_from_tree(left, indent + 4, p_code, label_counter)
            generate_code_p_from_tree(right, indent + 4, p_code, label_counter)
            
            op_map = {
                '>': 'grt',
                '<': 'les',
                '>=': 'geq',
                '<=': 'leq'
            }
            p_code.append(op_map[operator])

        elif node_repr[0] == 'equals':
            left = node_repr[1]
            right = node_repr[2]
            generate_code_p_from_tree(left, indent + 4, p_code, label_counter)
            generate_code_p_from_tree(right, indent + 4, p_code, label_counter)
            p_code.append('equ')

        elif node_repr[0] == 'and':
            left = node_repr[1]
            right = node_repr[2]
            generate_code_p_from_tree(left, indent + 4, p_code, label_counter)
            generate_code_p_from_tree(right, indent + 4, p_code, label_counter)
            p_code.append('and')

        elif node_repr[0] == 'sent_read':
            variable = node_repr[1]
            p_code.append('inp')
            p_code.append(f'sto {variable}')

        elif node_repr[0] == 'sent_write':
            for item in node_repr[1]:
                if isinstance(item, dict) and item['type'] == 'string':
                    # Es una cadena
                    p_code.append(f'print "{item["value"]}"')  # Cambiamos 'str' por 'print'
                else:
                    # Es una expresión normal
                    generate_code_p_from_tree(item, indent + 4, p_code, label_counter)
                    p_code.append('out')

        elif node_repr[0] == 'array_decl':
            name = node_repr[1]
            size = node_repr[2]
            # Reservar espacio para el array
            for i in range(size):
                p_code.append(f"ldc 0")
                p_code.append(f"sto {name}_{i}")

        elif node_repr[0] == 'array_access':
            name = node_repr[1]
            index = node_repr[2]
            # Generar código para calcular el índice
            generate_code_p_from_tree(index, indent + 4, p_code, label_counter)
            # Cargar el elemento del array
            p_code.append(f"lod {name}_index")
            

    elif isinstance(ast, tuple):
        # Manejo especial para sent_write cuando viene como tupla
        if ast[0] == 'sent_write':
            expression = ast[1]
            if isinstance(expression, tuple) and expression[0] == 'ident':
                p_code.append(f"lod {expression[1]}")
                p_code.append("out")
            else:
                generate_code_p_from_tree(expression, indent + 4, p_code, label_counter)
                p_code.append("out")
        else:
            for child in ast[1:]:
                generate_code_p_from_tree(child, indent + 4, p_code, label_counter)

    elif isinstance(ast, list):
        for item in ast:
            generate_code_p_from_tree(item, indent, p_code, label_counter)

    return p_code



'''def print_semantic_tree(ast, indent=0):
    if isinstance(ast, dict):
        node_repr = ast.get('node')
        node_type = ast.get('type')
        value = ast.get('value')
        if node_repr[0] == 'error':
            node_text = f"{' ' * indent}🐥 Error Semántico: {node_repr[1]}"
            print(node_text)
        else:
            node_text = f"{' ' * indent}{node_repr[0]} (Tipo: {node_type}, Valor: {value})"
            print(node_text)
            for child in node_repr[1:]:
                print_semantic_tree(child, indent + 4)
    elif isinstance(ast, tuple):
        node_text = f"{' ' * indent}{ast[0]}"
        print(node_text)
        for child in ast[1:]:
            print_semantic_tree(child, indent + 4)
    elif isinstance(ast, list):
        for item in ast:
            print_semantic_tree(item, indent)
    else:
        node_text = f"{' ' * indent}{str(ast)}"
        print(node_text)'''


def ejecutarCodigo():
    try:
        # Limpiar la consola
        console.delete(1.0, tk.END)
        console.insert('end', "Iniciando ejecución...\n\n")
        
        # Obtener el código P
        code = codigoP.get('1.0', tk.END).split('\n')
        
        # Cargar el programa en el intérprete
        interpreter.load_program(code)
        
        # Cambiar a la pestaña de la consola
        notebook.select(notebook.index(console_frame))
        
        # Comenzar la ejecución
        execute_next_instruction()
        
    except Exception as e:
        console.insert('end', f"Error al iniciar la ejecución: {str(e)}\n")


# Configuración de la barra de menú
menubar = Menu(root)
root.config(menu=menubar)

# Menú para archivos (hay que arreglar la de guardar y cambiar la actual de guardar, por "guardar como")
menu_archivo = Menu(menubar, tearoff=0)
menu_archivo.add_command(label="Nuevo", command=nuevoArchivo)
menu_archivo.add_command(label="Abrir", command=abrirArchivo)
menu_archivo.add_command(label="Guardar", command=guardarArchivo)
menubar.add_cascade(label="Archivo", menu=menu_archivo)

# Menú Compilar
menu_compilar = Menu(menubar, tearoff=0)
menu_compilar.add_command(label="Compilar", command=compilarCodigo)
menubar.add_cascade(label="Compilar", menu=menu_compilar)

# Menú Ejecutar
menu_ejecutar = Menu(menubar, tearoff=0)
menu_ejecutar.add_command(label="Ejecutar", command=ejecutarCodigo)
menubar.add_cascade(label="Ejecutar", menu=menu_ejecutar)


# Clase para los números de línea
class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget

    def redraw(self, *args):
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True:
            dline = self.textwidget.dlineinfo(i)
            if dline is None:
                break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=linenum, font=("Consolas", 10), fill='gray')
            i = self.textwidget.index("%s+1line" % i)


# Área de texto principal para el código
editorFrame = Frame(root)
editorFrame.pack(side='left', fill='both', padx=10, pady=10)

# editorLabel = Label(editorFrame, text="Editor de Código:", font=("Times new Roman", 12, "bold"))
# editorLabel.pack(anchor='w')

# Frame que contiene los números de línea y el editor de texto
editor_container = Frame(editorFrame)
editor_container.pack(expand=True, fill='both')

# Crear el widget de números de línea
line_numbers = TextLineNumbers(editor_container, width=30)
line_numbers.pack(side='left', fill='y')

# Crear el editor de texto
editorTexto = tk.Text(editor_container, wrap='none', font=("Monaco", 10))
editorTexto.pack(side='left', expand=True, fill='both')

# Asociar el widget de números de línea con el editor de texto
line_numbers.attach(editorTexto)

# Añadir barras de desplazamiento al editor
scroll_y = tk.Scrollbar(editor_container, orient='vertical', command=editorTexto.yview)
editorTexto.configure(yscrollcommand=scroll_y.set)
scroll_y.pack(side='right', fill='y')

scroll_x = tk.Scrollbar(editorFrame, orient='horizontal', command=editorTexto.xview)
editorTexto.configure(xscrollcommand=scroll_x.set)
scroll_x.pack(side='bottom', fill='x')

# Definir estilos para el resaltado de sintaxis
editorTexto.tag_configure("reserved", foreground="#007BFF")
editorTexto.tag_configure("ident", foreground="#28A745")
editorTexto.tag_configure("number", foreground="#E69F00")
editorTexto.tag_configure("operator", foreground="#000000")
editorTexto.tag_configure("string", foreground="#D63384")
editorTexto.tag_configure("comment", foreground="#808080")

# Crear patrones para el resaltado de sintaxis
pattern_reserved = r'\b(' + '|'.join(lexer.reserved.keys()) + r')\b'
pattern_number = r'\b\d+(\.\d+)?\b'
pattern_operator = r'[+\-*/=<>!]+'
pattern_string = r'\".*?\"|\'.*?\''
pattern_comment = r'//.*'


def highlight_syntax(event=None):
    editorTexto.tag_remove("reserved", "1.0", tk.END)
    editorTexto.tag_remove("ident", "1.0", tk.END)
    editorTexto.tag_remove("number", "1.0", tk.END)
    editorTexto.tag_remove("operator", "1.0", tk.END)
    editorTexto.tag_remove("string", "1.0", tk.END)
    editorTexto.tag_remove("comment", "1.0", tk.END)

    code = editorTexto.get("1.0", tk.END)

    for match in re.finditer(pattern_comment, code):
        start = "1.0 + {}c".format(match.start())
        end = "1.0 + {}c".format(match.end())
        editorTexto.tag_add("comment", start, end)

    for match in re.finditer(pattern_string, code):
        start = "1.0 + {}c".format(match.start())
        end = "1.0 + {}c".format(match.end())
        editorTexto.tag_add("string", start, end)

    for match in re.finditer(pattern_reserved, code):
        start = "1.0 + {}c".format(match.start())
        end = "1.0 + {}c".format(match.end())
        editorTexto.tag_add("reserved", start, end)

    for match in re.finditer(pattern_number, code):
        start = "1.0 + {}c".format(match.start())
        end = "1.0 + {}c".format(match.end())
        editorTexto.tag_add("number", start, end)

    for match in re.finditer(pattern_operator, code):
        start = "1.0 + {}c".format(match.start())
        end = "1.0 + {}c".format(match.end())
        editorTexto.tag_add("operator", start, end)


# Actualizar los números de línea y el resaltado cuando el texto cambia
def on_text_change(event=None):
    line_numbers.redraw()
    highlight_syntax()


editorTexto.bind("<KeyRelease>", on_text_change)
editorTexto.bind("<MouseWheel>", on_text_change)
editorTexto.bind("<Button-4>", on_text_change)  # Para sistemas Linux
editorTexto.bind("<Button-5>", on_text_change)
editorTexto.bind("<Configure>", on_text_change)
editorTexto.bind("<FocusIn>", on_text_change)
editorTexto.bind("<FocusOut>", on_text_change)

# Notebook para las pestañas de compilación
notebook = ttk.Notebook(root)
notebook.pack(side='right', fill='both', padx=10, pady=10)

style = ttk.Style()
style.theme_use('default')
style.configure('Treeview', background=color_lexico, foreground='black', fieldbackground=color_lexico, rowheight=100)
style.map('Treeview', background=[('selected', '#4a4a4a')])

# Pestaña Léxico
lexico_frame = Frame(notebook, bg=color_lexico)
lexico_frame.pack(expand=True, fill='both')
lexico_label = Label(lexico_frame, text='Análisis Léxico', bg=color_lexico, fg='black',
                     font=("DejaVu Sans Mono", 10, "bold"))
lexico_label.pack(anchor='w')

# Crear Treeview para la tabla léxica
lexico_tree = ttk.Treeview(lexico_frame, columns=("Clave", "Lexema", "Fila", "Columna"), show='headings')
lexico_tree.heading("Clave", text="Token Type")
lexico_tree.heading("Lexema", text="Token Value")
lexico_tree.heading("Fila", text="Row")
lexico_tree.heading("Columna", text="Column")
lexico_tree.column("Clave", width=100, anchor='center')
lexico_tree.column("Lexema", width=150, anchor='center')
lexico_tree.column("Fila", width=50, anchor='center')
lexico_tree.column("Columna", width=70, anchor='center')
lexico_tree.pack(expand=True, fill='both')

# Añadir barra de desplazamiento a la pestaña léxico
scroll_lex_y = tk.Scrollbar(lexico_frame, orient='vertical', command=lexico_tree.yview)
lexico_tree.configure(yscrollcommand=scroll_lex_y.set)
scroll_lex_y.pack(side='right', fill='y')

# Pestaña Sintáctico
sintactico_frame = Frame(notebook, bg=color_sintactico)
sintactico_frame.pack(expand=True, fill='both')
sintactico_label = Label(sintactico_frame, text='Análisis Sintáctico', bg=color_sintactico, fg='black',
                         font=("DejaVu Sans Mono", 10, "bold"))
sintactico_label.pack(anchor='w')

# Crear Treeview para el árbol sintáctico
sintactico_tree = ttk.Treeview(sintactico_frame)
sintactico_tree.pack(expand=True, fill='both')

# Añadir barra de desplazamiento al árbol sintáctico
scroll_sint_y = tk.Scrollbar(sintactico_frame, orient='vertical', command=sintactico_tree.yview)
sintactico_tree.configure(yscrollcommand=scroll_sint_y.set)
scroll_sint_y.pack(side='right', fill='y')

# Pestaña Semántico
semantico_frame = Frame(notebook, bg=color_semantico)
semantico_frame.pack(expand=True, fill='both')
semantico_label = Label(semantico_frame, text='Análisis Semántico', bg=color_semantico, fg='black',
                        font=("DejaVu Sans Mono", 10, "bold"))
semantico_label.pack(anchor='w')

# Crear Treeview para el árbol semántico
semantico_tree = ttk.Treeview(semantico_frame)
semantico_tree.pack(expand=True, fill='both')

# Añadir barra de desplazamiento al árbol semántico
scroll_sem_y = tk.Scrollbar(semantico_frame, orient='vertical', command=semantico_tree.yview)
semantico_tree.configure(yscrollcommand=scroll_sem_y.set)
scroll_sem_y.pack(side='right', fill='y')

# Pestaña tabla de símbolos
tablaSimbolos_frame = Frame(notebook, bg=color_semantico)
tablaSimbolos_frame.pack(expand=True, fill='both')
tablaSimbolos_label = Label(tablaSimbolos_frame, text='Tabla de símbolos', bg=color_semantico, fg='black',
                            font=("DejaVu Sans Mono", 10, "bold"))


# tablaSimbolos_label.pack(anchor='w')

# Función para formatear la lista de líneas
def format_lines(lines, max_width=15):  # Ajusta max_width según el ancho de tu columna
    if not lines:
        return "N/A"
    lines_str = ', '.join(map(str, lines))
    formatted_lines = []
    current_line = ""
    for num in lines_str.split(', '):
        if len(current_line) + len(num) + 2 > max_width:  # +2 para la coma y el espacio
            formatted_lines.append(current_line.rstrip(', '))
            current_line = num + ", "
        else:
            current_line += num + ", "
    if current_line:
        formatted_lines.append(current_line.rstrip(', '))
    return '\n'.join(formatted_lines)


# Crear Treeview para la tabla de símbolos
tablaSimbolos_tree = ttk.Treeview(tablaSimbolos_frame, columns=("Name", "Type", "Value", "Loc", "Lines"),
                                  show='tree headings')
tablaSimbolos_tree.heading("#0", text="Ámbito")
tablaSimbolos_tree.heading("Name", text="Nombre")
tablaSimbolos_tree.heading("Type", text="Tipo")
tablaSimbolos_tree.heading("Value", text="Valor")
tablaSimbolos_tree.heading("Loc", text="Loc")
tablaSimbolos_tree.heading("Lines", text="Líneas")
tablaSimbolos_tree.column("#0", width=100, anchor='w')
tablaSimbolos_tree.column("Name", width=100, anchor='center')
tablaSimbolos_tree.column("Type", width=100, anchor='center')
tablaSimbolos_tree.column("Value", width=100, anchor='center')
tablaSimbolos_tree.column("Loc", width=70, anchor='center')
tablaSimbolos_tree.column("Lines", width=100, anchor='center')
tablaSimbolos_tree.pack(expand=True, fill='both')


# Función para insertar datos en la tabla de símbolos con soporte para múltiples líneas
def insert_symbol(parent, name, type, value, loc, lines):
    formatted_lines = format_lines(lines) if isinstance(lines, (list, tuple)) else str(lines)
    tablaSimbolos_tree.insert(parent, 'end', values=(name, type, value, loc, formatted_lines))


# Añadir barra de desplazamiento al árbol de la tabla de símbolos
scroll_tablaSimbolos_y = tk.Scrollbar(tablaSimbolos_frame, orient='vertical', command=tablaSimbolos_tree.yview)
tablaSimbolos_tree.configure(yscrollcommand=scroll_tablaSimbolos_y.set)
scroll_tablaSimbolos_y.pack(side='right', fill='y')

#Añadir la seccion para el codigo Tiny
#codigoTiny_frame = Frame(notebook, bg=color_resultados)
#codigoTiny_frame.pack(expand=True, fill='both')
#codigoTiny_label = Label(codigoTiny_frame, text='Código Tiny', bg=color_resultados, fg='black', font=("DejaVu Sans Mono", 10, "bold"))
#codigoTiny_label.pack(anchor='w')
# Text widget para mostrar el código Tiny
#codigoTiny = tk.Text(codigoTiny_frame, wrap='none', font=("Consolas", 10), bg=color_resultados, fg=texto_color_resultados)
#codigoTiny.pack(expand=True, fill='both')

# Scrollbar para el código Tiny
#scroll_codigoTiny_y = tk.Scrollbar(codigoTiny_frame, orient='vertical', command=codigoTiny.yview)
#codigoTiny.configure(yscrollcommand=scroll_codigoTiny_y.set)
#scroll_codigoTiny_y.pack(side='right', fill='y')

#Añadir la seccion para el codigo P
codigoP_frame = Frame(notebook, bg=color_resultados)
codigoP_frame.pack(expand=True, fill='both')
codigoP_label = Label(codigoP_frame, text='Código P', bg=color_resultados, fg='black', font=("DejaVu Sans Mono", 10, "bold"))
codigoP_label.pack(anchor='w')
# Text widget para mostrar el código P
codigoP = tk.Text(codigoP_frame, wrap='none', font=("Consolas", 10), bg=color_resultados, fg=texto_color_resultados)
codigoP.pack(expand=True, fill='both')

# Scrollbar para el código P
scroll_codigoP_y = tk.Scrollbar(codigoP_frame, orient='vertical', command=codigoP.yview)
codigoP.configure(yscrollcommand=scroll_codigoP_y.set)
scroll_codigoP_y.pack(side='right', fill='y')


# Añadir las pestañas al Notebook
notebook.add(lexico_frame, text='Léxico')
notebook.add(sintactico_frame, text='Sintáctico')
notebook.add(semantico_frame, text='Semántico')
notebook.add(tablaSimbolos_frame, text='Tabla de simbolos')
#notebook.add(codigoTiny_frame, text='Código Tiny')
notebook.add(codigoP_frame, text='Código P')

# Frame para la consola de ejecución
console_frame = Frame(notebook, bg=color_resultados)
console_frame.pack(expand=True, fill='both')
console_label = Label(console_frame, text='Consola de Ejecución', bg=color_resultados, fg='black', 
                     font=("DejaVu Sans Mono", 10, "bold"))
console_label.pack(anchor='w')

# Text widget para la consola
console = tk.Text(console_frame, wrap='word', font=("Consolas", 10), bg='black', fg='white')
console.pack(expand=True, fill='both')

# Entry para entrada de datos
input_frame = Frame(console_frame, bg=color_resultados)
input_frame.pack(fill='x', pady=5)
input_entry = tk.Entry(input_frame, font=("Consolas", 10))
input_entry.pack(side='left', expand=True, fill='x', padx=5)

# Botón de enviar
send_button = tk.Button(input_frame, text="Enviar", font=("DejaVu Sans Mono", 9))
send_button.pack(side='right', padx=5)

# Scrollbar para la consola
scroll_console_y = tk.Scrollbar(console_frame, orient='vertical', command=console.yview)
console.configure(yscrollcommand=scroll_console_y.set)
scroll_console_y.pack(side='right', fill='y')

# Agregar la pestaña de consola al notebook
notebook.add(console_frame, text='Consola')

# Crear el intérprete
interpreter = PCodeInterpreter(console)

def send_input(event=None):
    if interpreter.waiting_for_input:
        value = input_entry.get()
        input_entry.delete(0, tk.END)
        if interpreter.handle_input(value):
            console.insert('end', f"> {value}\n")
            console.see('end')
            execute_next_instruction()

def execute_next_instruction():
    if interpreter.execute_next():
        if not interpreter.waiting_for_input:
            root.after(10, execute_next_instruction)
    else:
        console.insert('end', "\nEjecución finalizada\n")
        console.see('end')

def ejecutarCodigo():
    try:
        # Limpiar la consola
        console.delete(1.0, tk.END)
        console.insert('end', "Iniciando ejecución...\n\n")
        
        # Obtener el código P
        code = codigoP.get('1.0', tk.END).split('\n')
        
        # Cargar el programa en el intérprete
        interpreter.load_program(code)
        
        # Cambiar a la pestaña de la consola
        notebook.select(notebook.index(console_frame))
        
        # Comenzar la ejecución
        execute_next_instruction()
        
    except Exception as e:
        console.insert('end', f"Error al iniciar la ejecución: {str(e)}\n")

# Vincular el botón de enviar y la tecla Enter
send_button.config(command=send_input)
input_entry.bind('<Return>', send_input)


# Paneles de Errores y Resultados con Leyendas en sus propios marcos
bottom_frame = Frame(root)
bottom_frame.pack(expand=True, fill='both', side='bottom')

# Errores
frame_errores = Frame(bottom_frame, bg=color_errores, bd=2, relief='sunken')
frame_errores.pack(side='top', expand=True, fill='both', padx=(0, 5))
label_errores = Label(frame_errores, text='Errores', bg=color_errores, fg='black',
                      font=("DejaVu Sans Mono", 10, "bold"))
label_errores.pack(anchor='w')
errores = tk.Text(frame_errores, height=5, fg=texto_color_errores, bg=color_errores, font=("Consolas", 10))
errores.pack(expand=True, fill='both')

# Añadir barra de desplazamiento a errores
scroll_err_y = tk.Scrollbar(frame_errores, orient='vertical', command=errores.yview)
errores.configure(yscrollcommand=scroll_err_y.set)
scroll_err_y.pack(side='right', fill='y')

# Resultados
frame_resultados = Frame(bottom_frame, bg=color_resultados, bd=2, relief='sunken')
frame_resultados.pack(side='bottom', expand=True, fill='both', padx=(5, 0))
label_resultados = Label(frame_resultados, text='Resultados', bg=color_resultados, fg='black',
                         font=("DejaVu Sans Mono", 10, "bold"))
label_resultados.pack(anchor='w')
resultados = tk.Text(frame_resultados, height=5, fg=texto_color_resultados, bg=color_resultados, font=("Consolas", 10))
resultados.pack(expand=True, fill='both')

# Añadir barra de desplazamiento a resultados
scroll_res_y = tk.Scrollbar(frame_resultados, orient='vertical', command=resultados.yview)
resultados.configure(yscrollcommand=scroll_res_y.set)
scroll_res_y.pack(side='right', fill='y')


# Funciones para construir los árboles en los Treeview
def build_syntax_tree(treeview, ast):
    treeview.heading('#0', text='Árbol Sintáctico')
    insert_syntax_node(treeview, '', ast)
    expand_all(treeview)  # Expandir todos los nodos


def insert_syntax_node(treeview, parent, node):
    if isinstance(node, tuple):
        node_id = treeview.insert(parent, 'end', text=node[0])
        for child in node[1:]:
            insert_syntax_node(treeview, node_id, child)
    elif isinstance(node, list):
        for item in node:
            insert_syntax_node(treeview, parent, item)
    else:
        treeview.insert(parent, 'end', text=str(node))


def build_semantic_tree(treeview, ast):
    treeview.heading('#0', text='Árbol Semántico')
    insert_semantic_node(treeview, '', ast)
    expand_all(treeview)  # Expandir todos los nodos


def insert_semantic_node(treeview, parent, node):
    if isinstance(node, dict):
        node_repr = node.get('node')
        node_type = node.get('type')
        value = node.get('value')
        if node_repr[0] == 'error':
            node_text = f"🐥 Error Semántico: {node_repr[1]}"
        else:
            # Filtrar los elementos que no son None y no son números
            filtered_repr = [item for item in node_repr if item is not None and not isinstance(item, (int, float))]
            node_text = f"{filtered_repr[0]} (Tipo: {node_type}, Valor: {value})"
        node_id = treeview.insert(parent, 'end', text=node_text)
        for child in filtered_repr[1:]:
            insert_semantic_node(treeview, node_id, child)
    elif isinstance(node, tuple):
        # Filtrar los elementos que no son None y no son números
        filtered_node = [item for item in node if item is not None and not isinstance(item, (int, float))]
        node_id = treeview.insert(parent, 'end', text=filtered_node[0])
        for child in filtered_node[1:]:
            insert_semantic_node(treeview, node_id, child)
    elif isinstance(node, list):
        for item in node:
            insert_semantic_node(treeview, parent, item)
    else:
        treeview.insert(parent, 'end', text=str(node))


def expand_all(treeview):
    items = treeview.get_children()
    for item in items:
        treeview.item(item, open=True)
        expand_all_children(treeview, item)


def expand_all_children(treeview, item):
    children = treeview.get_children(item)
    for child in children:
        treeview.item(child, open=True)
        expand_all_children(treeview, child)


# Ejecutar la aplicación
root.mainloop()

