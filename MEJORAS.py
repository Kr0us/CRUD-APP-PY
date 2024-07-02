import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import sqlite3
import re
import pyperclip
from fpdf import FPDF

# Conexión a la base de datos SQLite
db_path = 'empresa.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Función para validar el RUT
def validar_rut(rut):
    pattern = re.compile(r'^\d{7,8}-[0-9kK]$')
    return pattern.match(rut) is not None

# Función para concatenar RUT
def obtener_rut_completo(numero, dv):
    return f"{numero}-{dv}"

# Función para insertar un nuevo usuario
def insertar_usuario(rut, contraseña):
    if not validar_rut(rut):
        messagebox.showwarning("Error", "El RUT no es válido")
        return

    try:
        c.execute("INSERT INTO USUARIOS (RUT, contraseña) VALUES (?, ?)", (rut, contraseña))
        conn.commit()
        messagebox.showinfo("Success", "Usuario insertado exitosamente")
    except sqlite3.IntegrityError:
        messagebox.showwarning("Error", "El RUT ya está registrado")

# Función para leer usuarios desde la base de datos
def leer_usuarios():
    c.execute("SELECT RUT, contraseña FROM USUARIOS")
    rows = c.fetchall()
    return {rut: password for rut, password in rows}

# Función para autenticar un usuario
def autenticar_usuario():
    rut = entry_rut_login.get()
    password = entry_password.get()
    usuarios = leer_usuarios()
    if rut in usuarios and usuarios[rut] == password:
        login_window.destroy()
        main_window()
    else:
        messagebox.showerror("Error de inicio de sesión", "RUT o contraseña incorrectos")


# Función para cargar la tabla seleccionada
def load_table(tabla):
    global columns, form_entries, entry_numero_rut, entry_dv, estado_combobox, aprobado_combobox

    for widget in form_frame.winfo_children():
        widget.destroy()

    form_entries = {}
    
    if tabla == 'CLIENTE':
        columns = ["ID_Cliente", "Nombre", "Apellido", "RUT", "Dirección", "Comuna", "Teléfono", "Correo"]
        
        # Añadir campos para número RUT y dígito verificador solo si la tabla es Cliente
        ttk.Label(form_frame, text="RUT").grid(row=3, column=0, padx=5, pady=5, sticky='W')
        entry_numero_rut = ttk.Entry(form_frame)
        entry_numero_rut.grid(row=3, column=1, padx=5, pady=5, sticky='W')

        ttk.Label(form_frame, text="-").grid(row=3, column=2, padx=5, pady=5, sticky='W')
        entry_dv = ttk.Entry(form_frame, width=5)
        entry_dv.grid(row=3, column=3, padx=5, pady=5, sticky='W')
        
        # Crear las entradas para cada columna excepto ID_Cliente
        for i, col in enumerate(columns):
            if col == "ID_Cliente":
                entry = ttk.Entry(form_frame, state='W')
            elif col == "RUT":
                continue  # No agregar campo de RUT directamente en el formulario
            else:
                entry = ttk.Entry(form_frame)
            
            ttk.Label(form_frame, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            form_entries[col] = entry

    elif tabla == 'PEDIDOS':
        columns = ["ID_Pedido", "Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha", "RUT"]

        # Añadir campos para número RUT y dígito verificador
        ttk.Label(form_frame, text="RUT").grid(row=6, column=0, padx=5, pady=5, sticky='W')
        entry_numero_rut = ttk.Entry(form_frame)
        entry_numero_rut.grid(row=6, column=1, padx=5, pady=5, sticky='W')

        ttk.Label(form_frame, text="-").grid(row=6, column=2, padx=5, pady=5, sticky='W')
        entry_dv = ttk.Entry(form_frame, width=5)
        entry_dv.grid(row=6, column=3, padx=5, pady=5, sticky='W')
        
        # Crear las entradas para cada columna excepto ID_Pedido
        for i, col in enumerate(columns):
            if col == "ID_Pedido":
                entry = ttk.Entry(form_frame, state='W')
            elif col == "RUT":
                continue  # No agregar campo de RUT directamente en el formulario
            elif col == "Tipo_Despacho":
                entry = ttk.Combobox(form_frame, values=["Domicilio", "Sucursal"])
            else:
                entry = ttk.Entry(form_frame)
            
            ttk.Label(form_frame, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            form_entries[col] = entry

    elif tabla == 'FABRICACION':
        columns = ["ID_Fabricacion", "Detalles", "Estado", "Aprobado", "Cantidad", "ID_Pedido"]
        
        # Crear las entradas para cada columna excepto ID_Fabricacion
        for i, col in enumerate(columns):
            if col == "ID_Fabricacion":
                entry = ttk.Entry(form_frame, state='W')
            elif col == "Estado":
                entry = ttk.Combobox(form_frame, values=["Empaquetado", "No Empaquetado"])
            elif col == "Aprobado":
                entry = ttk.Combobox(form_frame, values=["Sí", "No"])
            else:
                entry = ttk.Entry(form_frame)
            
            ttk.Label(form_frame, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            form_entries[col] = entry

    # Configurar las columnas del Treeview
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))

    search_field['values'] = columns  # Actualizar el Combobox de búsqueda
    read_records()


    
# Función para insertar un nuevo cliente y mostrar la ventana de pedido
def insertar_cliente():
    cliente_values = [form_entries[col].get() for col in columns if col != "ID_Cliente"]

    if all(cliente_values):
        query = f"INSERT INTO CLIENTE (Nombre, Apellido, RUT, Dirección, Comuna, Teléfono, Correo) VALUES (?, ?, ?, ?, ?, ?, ?)"
        try:
            c.execute(query, cliente_values)
            conn.commit()
            messagebox.showinfo("Success", "Cliente insertado exitosamente")
            clear_entries()
            read_records()
            ventana_pedido(cliente_values[2])  # El RUT es el tercer valor en cliente_values
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al insertar el cliente: {e}")
    else:
        messagebox.showwarning("Input error", "Por favor, complete todos los campos")

# Función para mostrar la ventana de pedido
def ventana_pedido(rut):
    def agregar_pedido():
        valores_pedido = [entry.get() for entry in pedido_entries.values()]
        if all(valores_pedido):
            valores_pedido.append(rut)  # Añadir el RUT al final de los valores del pedido
            c.execute("INSERT INTO PEDIDOS (Total, Pago, Tipo_Despacho, Especificación, Fecha, RUT) VALUES (?, ?, ?, ?, ?, ?)", valores_pedido)
            conn.commit()
            messagebox.showinfo("Success", "Pedido insertado exitosamente")
            pedido_window.destroy()
        else:
            messagebox.showwarning("Input error", "Por favor, complete todos los campos del pedido")

    pedido_window = tk.Toplevel()
    pedido_window.title("Agregar Pedido")

    pedido_columns = ("Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha")
    pedido_entries = {}
    for i, col in enumerate(pedido_columns):
        ttk.Label(pedido_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
        if col == "Tipo_Despacho":
            entry = ttk.Combobox(pedido_window, values=["Domicilio", "Sucursal"])
        else:
            entry = ttk.Entry(pedido_window)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
        pedido_entries[col] = entry


    # Añadir el campo RUT sin permitir su edición
    ttk.Label(pedido_window, text="RUT").grid(row=len(pedido_columns), column=0, padx=5, pady=5, sticky='W')
    entry_rut = ttk.Entry(pedido_window)
    entry_rut.grid(row=len(pedido_columns), column=1, padx=5, pady=5, sticky='W')
    entry_rut.insert(0, rut)
    entry_rut.config(state='disabled')

    ttk.Button(pedido_window, text="Agregar Pedido", command=agregar_pedido).grid(row=len(pedido_columns)+1, column=0, columnspan=2, padx=5, pady=5)

# Función para insertar registros en la tabla seleccionada
def insert_record():
    tabla = combo_tablas.get()
    values = [entry.get() for entry in form_entries.values()]

    if tabla == 'FABRICACION':
        # Asegurarse de que los valores "Sí" y "No" se manejen como texto
        if "Aprobado" in form_entries:
            aprobado_val = form_entries["Aprobado"].get()
            if aprobado_val not in ["Sí", "No"]:
                messagebox.showwarning("Input error", "El valor de 'Aprobado' debe ser 'Sí' o 'No'")
                return
            values[3] = aprobado_val
    
    if tabla == 'CLIENTE':
        numero_rut = entry_numero_rut.get()
        dv = entry_dv.get()
        rut_completo = obtener_rut_completo(numero_rut, dv)

        if not validar_rut(rut_completo):
            messagebox.showwarning("Error", "El RUT no es válido")
            return

        values.insert(2, rut_completo)

    if any(values):
        columns_to_insert = ", ".join(columns)
        placeholders = ", ".join(["?" for _ in columns])
        query = f"INSERT INTO {tabla} ({columns_to_insert}) VALUES ({placeholders})"
        try:
            c.execute(query, values)
            conn.commit()
            messagebox.showinfo("Success", f"Registro insertado exitosamente en {tabla}")
            clear_entries()
            read_records()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al insertar el registro: {e}")
    else:
        messagebox.showwarning("Input error", "Por favor, complete todos los campos")

# Función para actualizar el RUT en ambas tablas
def actualizar_rut_en_tablas(nuevo_rut, antiguo_rut):
    # Actualizar el RUT en la tabla CLIENTE
    query_update_clientes = "UPDATE CLIENTE SET RUT = ? WHERE RUT = ?"
    c.execute(query_update_clientes, (nuevo_rut, antiguo_rut))
    
    # Actualizar el RUT en la tabla PEDIDOS
    query_update_pedidos = "UPDATE PEDIDOS SET RUT = ? WHERE RUT = ?"
    c.execute(query_update_pedidos, (nuevo_rut, antiguo_rut))
    
    conn.commit()


# Función para actualizar registros en la tabla seleccionada
def update_record():
    tabla = combo_tablas.get()
    id_col = columns[0]
    record_id = form_entries[id_col].get()

    if not record_id:
        messagebox.showwarning("Input error", f"Por favor, ingrese el ID del registro en {id_col} para actualizar")
        return

    # Leer los valores actuales en el formulario en el orden correcto
    current_values = []
    for col in columns:
        if col in form_entries:
            current_values.append(form_entries[col].get())
        else:
            current_values.append(None)

    # Leer los valores originales del registro seleccionado
    c.execute(f"SELECT * FROM {tabla} WHERE {id_col} = ?", (record_id,))
    original_values = c.fetchone()

    # Convertir los valores originales en una lista (omitimos el ID en original_values[1:])
    if original_values:
        original_values = list(original_values[1:])

    # Verificar si se ha realizado algún cambio
    if current_values == original_values:
        messagebox.showwarning("No changes", "No estás actualizando nada")
        return

    # Continuar con la actualización si hay cambios
    if tabla == 'FABRICACION':
        # Manejar "Sí" y "No" para el campo "Aprobado"
        aprobado_val = form_entries["Aprobado"].get()
        if aprobado_val not in ["Sí", "No"]:
            messagebox.showwarning("Input error", "El valor de 'Aprobado' debe ser 'Sí' o 'No'")
            return
        current_values[columns.index("Aprobado")] = aprobado_val

    if tabla == 'CLIENTE' or tabla == 'PEDIDOS':
        numero_rut = entry_numero_rut.get()
        dv = entry_dv.get()
        rut_completo = obtener_rut_completo(numero_rut, dv)

        if not validar_rut(rut_completo):
            messagebox.showwarning("Error", "El RUT no es válido")
            return

        if tabla == 'CLIENTE':
            current_values[columns.index("RUT")] = rut_completo  # Insertar el RUT completo en la posición correcta
            antiguo_rut = original_values[columns.index("RUT") - 1]  # Obtener el antiguo RUT

        elif tabla == 'PEDIDOS':
            current_values[columns.index("RUT")] = rut_completo
            antiguo_rut = original_values[columns.index("RUT") - 1]  # Obtener el antiguo RUT

        # Actualizar el RUT en las tablas CLIENTES y PEDIDOS si ha cambiado
        if antiguo_rut != rut_completo:
            actualizar_rut_en_tablas(rut_completo, antiguo_rut)

    # Asegúrate de que los valores de `current_values` están en el orden correcto
    if any(current_values[1:]):
        updates = ", ".join(f"{col} = COALESCE(?, {col})" for col in columns[1:])
        query = f"UPDATE {tabla} SET {updates} WHERE {id_col} = ?"
        try:
            c.execute(query, current_values[1:] + [record_id])
            conn.commit()
            messagebox.showinfo("Success", f"Registro actualizado exitosamente en {tabla}")
            clear_entries()
            read_records()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al actualizar el registro: {e}")
    else:
        messagebox.showwarning("Input error", "Por favor, ingrese al menos un dato para actualizar")

# Función para eliminar registros en la tabla seleccionada
def delete_record():
    tabla = combo_tablas.get()
    id_col = columns[0]
    record_id = form_entries[id_col].get()

    if not record_id:
        messagebox.showwarning("Input error", f"Por favor, ingrese el ID del registro en {id_col} para eliminar")
        return

    c.execute(f"DELETE FROM {tabla} WHERE {id_col} = ?", (record_id,))
    conn.commit()
    messagebox.showinfo("Success", f"Registro eliminado exitosamente en {tabla}")
    clear_entries()
    read_records()

# Función para limpiar las entradas del formulario
def clear_entries():
    for entry in form_entries.values():
        entry.delete(0, tk.END)
    if 'entry_numero_rut' in globals():
        entry_numero_rut.delete(0, tk.END)
    if 'entry_dv' in globals():
        entry_dv.delete(0, tk.END)

# Función para leer los registros de la tabla seleccionada
def read_records():
    tabla = combo_tablas.get()
    query = f"SELECT * FROM {tabla}"
    c.execute(query)
    all_records = c.fetchall()
    display_records(all_records)


# Función para mostrar registros en el Treeview
def display_records(records):
    for i in tree.get_children():
        tree.delete(i)
    for row in records:
        tree.insert('', tk.END, values=row)

# Función para mostrar los registros en los cuadros
def on_tree_select(event):
    selected_item = tree.focus()
    values = tree.item(selected_item, 'values')
    tabla = combo_tablas.get()
    for col, val in zip(columns, values):
        if col == "RUT" and tabla in ('CLIENTE', 'PEDIDOS'):
            numero, dv = val.split('-')
            entry_numero_rut.delete(0, tk.END)
            entry_numero_rut.insert(0, numero)
            entry_dv.delete(0, tk.END)
            entry_dv.insert(0, dv)
        elif col == "Aprobado" and tabla == 'FABRICACION':
            if val == '1':
                form_entries[col].set("Sí")
            else:
                form_entries[col].set("No")
        elif col == "Estado" and tabla == 'FABRICACION':
            form_entries[col].set(val)
        else:
            form_entries[col].delete(0, tk.END)
            form_entries[col].insert(0, val)

# Función para filtrar registros en el Treeview
def filter_records():
    search_term = search_entry.get().lower()
    search_by = search_field.get()
    tabla = combo_tablas.get()

    if search_by and search_term:
        query = f"SELECT * FROM {tabla} WHERE LOWER({search_by}) = ?"
        c.execute(query, (search_term,))
        filtered_records = c.fetchall()
        display_records(filtered_records)
    else:
        messagebox.showwarning("Input error", "Por favor, seleccione un campo y escriba un término de búsqueda")

# Función para ordenar las columnas al presionarlas con click
def sort_column(tree, col, reverse):
    tabla = combo_tablas.get()
    query = f"SELECT * FROM {tabla} ORDER BY {col} {'DESC' if reverse else 'ASC'}"
    c.execute(query)
    records = c.fetchall()
    display_records(records)
    tree.heading(col, command=lambda: sort_column(tree, col, not reverse))

def ventana_pedido(rut):
    def agregar_pedido():
        valores_pedido = [entry.get() for entry in pedido_entries.values()]
        if all(valores_pedido):
            numero_rut = entry_numero_rut.get()
            dv = entry_dv.get()
            rut_completo = obtener_rut_completo(numero_rut, dv)

            if not validar_rut(rut_completo):
                messagebox.showwarning("Error", "El RUT no es válido")
                return

            valores_pedido.append(rut_completo)
            c.execute("INSERT INTO PEDIDOS (Total, Pago, Tipo_Despacho, Especificación, Fecha, RUT) VALUES (?, ?, ?, ?, ?, ?)", valores_pedido)
            conn.commit()
            messagebox.showinfo("Success", "Pedido insertado exitosamente")
            pedido_window.destroy()
        else:
            messagebox.showwarning("Input error", "Por favor, complete todos los campos del pedido")

    pedido_window = tk.Toplevel()
    pedido_window.title("Agregar Pedido")

    pedido_columns = ("Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha")
    pedido_entries = {}
    for i, col in enumerate(pedido_columns):
        ttk.Label(pedido_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
        if col == "Tipo_Despacho":
            entry = ttk.Combobox(pedido_window, values=["Domicilio", "Sucursal"])
        else:
            entry = ttk.Entry(pedido_window)
        entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
        pedido_entries[col] = entry

    # Añadir campos para número RUT y dígito verificador
    ttk.Label(pedido_window, text="Número RUT").grid(row=len(pedido_columns), column=0, padx=5, pady=5, sticky='W')
    entry_numero_rut = ttk.Entry(pedido_window)
    entry_numero_rut.grid(row=len(pedido_columns), column=1, padx=5, pady=5, sticky='W')

    ttk.Label(pedido_window, text="Dígito Verificador").grid(row=len(pedido_columns), column=2, padx=5, pady=5, sticky='W')
    entry_dv = ttk.Entry(pedido_window, width=5)
    entry_dv.grid(row=len(pedido_columns), column=3, padx=5, pady=5, sticky='W')

    ttk.Button(pedido_window, text="Agregar Pedido", command=agregar_pedido).grid(row=len(pedido_columns)+1, column=0, columnspan=4, padx=5, pady=5)

# Función para generar el PDF de nombres únicos de productos
def generar_pdf_productos_unicos(productos_unicos):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Lista de Productos Únicos", ln=True, align='C')

    # Filas de productos únicos
    for producto in productos_unicos:
        pdf.cell(200, 10, txt=producto, ln=True, align='L')

    pdf.output("productos_unicos.pdf")
    messagebox.showinfo("Success", "PDF generado exitosamente")

# Función para generar el PDF de la tabla PRODUCTOS y mostrar la ventana emergente
def generar_pdf_productos():
    query = "SELECT * FROM PRODUCTOS"
    c.execute(query)
    productos = c.fetchall()

    # Extraer nombres únicos de productos
    nombres_productos = {producto[1] for producto in productos}  # Asumiendo que el nombre del producto está en la columna 1

    # Crear ventana emergente con los nombres únicos y un botón para descargar el PDF
    ventana_productos = tk.Toplevel()
    ventana_productos.title("Productos Únicos")

    texto_productos = "\n".join(nombres_productos)
    label_productos = tk.Label(ventana_productos, text=texto_productos, justify=tk.LEFT)
    label_productos.pack(padx=10, pady=10)

    def descargar_pdf():
        generar_pdf_productos_unicos(nombres_productos)

    boton_descargar = tk.Button(ventana_productos, text="Descargar PDF", command=descargar_pdf)
    boton_descargar.pack(pady=10)




def mostrar_info_cliente(rut):
    query = "SELECT * FROM CLIENTE WHERE RUT = ?"
    c.execute(query, (rut,))
    cliente = c.fetchone()

    if cliente:
        ventana_cliente = tk.Toplevel()
        ventana_cliente.title("Información del Cliente")

        info = f"ID Cliente: {cliente[0]}\nNombre: {cliente[1]}\nApellido: {cliente[2]}\nRUT: {cliente[3]}\nDirección: {cliente[4]}\nComuna: {cliente[5]}\nTeléfono: {cliente[6]}\nCorreo: {cliente[7]}"
        
        def copiar_info():
            pyperclip.copy(info)
            messagebox.showinfo("Copiado", "Información del cliente copiada al portapapeles")

        # Botón de copiar en la esquina superior izquierda
        boton_copiar = tk.Button(ventana_cliente, text="Copiar", command=copiar_info)
        boton_copiar.pack(anchor='nw', padx=5, pady=5)

        label_info = tk.Label(ventana_cliente, text=info, justify=tk.LEFT)
        label_info.pack(padx=10, pady=10)
    else:
        messagebox.showerror("Error", "Cliente no encontrado")

def mostrar_info_pedido_cliente(rut, id_pedido, tabla):
    query_cliente = "SELECT * FROM CLIENTE WHERE RUT = ?"
    c.execute(query_cliente, (rut,))
    cliente = c.fetchone()

    query_pedido = f"SELECT * FROM {tabla} WHERE ID_Pedido = ?"
    c.execute(query_pedido, (id_pedido,))
    pedido = c.fetchone()

    if cliente and pedido:
        ventana_info = tk.Toplevel()
        ventana_info.title("Información del Pedido y Cliente")

        info_cliente = f"ID Cliente: {cliente[0]}\nNombre: {cliente[1]}\nApellido: {cliente[2]}\nRUT: {cliente[3]}\nDirección: {cliente[4]}\nComuna: {cliente[5]}\nTeléfono: {cliente[6]}\nCorreo: {cliente[7]}"
        info_pedido = f"ID Pedido: {pedido[0]}\nEstado: {pedido[1]}\nRUT: {pedido[2]}"

        info = f"Información del Cliente:\n{info_cliente}\n\nInformación del Pedido:\n{info_pedido}"

        def copiar_info():
            pyperclip.copy(info)
            messagebox.showinfo("Copiado", "Información del pedido y cliente copiada al portapapeles")

        # Botón de copiar en la esquina superior izquierda
        boton_copiar = tk.Button(ventana_info, text="Copiar", command=copiar_info)
        boton_copiar.pack(anchor='nw', padx=5, pady=5)

        label_info = tk.Label(ventana_info, text=info, justify=tk.LEFT)
        label_info.pack(padx=10, pady=10)
    else:
        messagebox.showerror("Error", "Cliente o Pedido no encontrado")

def mostrar_info_completa(id_pedido):
    # Obtener la información del pedido
    query_pedido = "SELECT * FROM PEDIDOS WHERE ID_Pedido = ?"
    c.execute(query_pedido, (id_pedido,))
    pedido = c.fetchone()

    if not pedido:
        messagebox.showerror("Error", "Pedido no encontrado")
        return

    rut = pedido[-1]  # Asumiendo que el RUT está en la última columna del pedido

    # Obtener la información del cliente
    query_cliente = "SELECT * FROM CLIENTE WHERE RUT = ?"
    c.execute(query_cliente, (rut,))
    cliente = c.fetchone()

    if not cliente:
        messagebox.showerror("Error", "Cliente no encontrado")
        return

    # Obtener la información de fabricación
    query_fabricacion = "SELECT * FROM FABRICACION WHERE ID_Pedido = ?"
    c.execute(query_fabricacion, (id_pedido,))
    fabricacion = c.fetchone()

    if not fabricacion:
        messagebox.showerror("Error", "Fabricación no encontrada")
        return

    # Crear ventana emergente con la información completa
    ventana_info = tk.Toplevel()
    ventana_info.title("Información Completa")

    info_pedido = f"ID Pedido: {pedido[0]}\nTotal: {pedido[1]}\nPago: {pedido[2]}\nTipo Despacho: {pedido[3]}\nEspecificación: {pedido[4]}\nFecha: {pedido[5]}\nRUT: {pedido[6]}"
    info_cliente = f"ID Cliente: {cliente[0]}\nNombre: {cliente[1]}\nApellido: {cliente[2]}\nRUT: {cliente[3]}\nDirección: {cliente[4]}\nComuna: {cliente[5]}\nTeléfono: {cliente[6]}\nCorreo: {cliente[7]}"
    info_fabricacion = f"ID Fabricación: {fabricacion[0]}\nDetalles: {fabricacion[1]}\nEstado: {fabricacion[2]}\nAprobado: {fabricacion[3]}\nCantidad: {fabricacion[4]}\nID Pedido: {fabricacion[5]}"

    info = f"Información del Pedido:\n{info_pedido}\n\nInformación del Cliente:\n{info_cliente}\n\nInformación de Fabricación:\n{info_fabricacion}"

    def copiar_info():
        pyperclip.copy(info)
        messagebox.showinfo("Copiado", "Información completa copiada al portapapeles")

    # Botón de copiar en la esquina superior izquierda
    boton_copiar = tk.Button(ventana_info, text="Copiar", command=copiar_info)
    boton_copiar.pack(anchor='nw', padx=5, pady=5)

    label_info = tk.Label(ventana_info, text=info, justify=tk.LEFT)
    label_info.pack(padx=10, pady=10)

def mostrar_info_completa(id_pedido):
    # Obtener la información del pedido
    query_pedido = "SELECT * FROM PEDIDOS WHERE ID_Pedido = ?"
    c.execute(query_pedido, (id_pedido,))
    pedido = c.fetchone()

    if not pedido:
        messagebox.showerror("Error", "Pedido no encontrado")
        return

    rut = pedido[-1]  # Asumiendo que el RUT está en la última columna del pedido

    # Obtener la información del cliente
    query_cliente = "SELECT * FROM CLIENTE WHERE RUT = ?"
    c.execute(query_cliente, (rut,))
    cliente = c.fetchone()

    if not cliente:
        messagebox.showerror("Error", "Cliente no encontrado")
        return

    # Obtener la información de fabricación
    query_fabricacion = "SELECT * FROM FABRICACION WHERE ID_Pedido = ?"
    c.execute(query_fabricacion, (id_pedido,))
    fabricacion = c.fetchone()

    if not fabricacion:
        messagebox.showerror("Error", "Fabricación no encontrada")
        return

    # Crear ventana emergente con la información completa
    ventana_info = tk.Toplevel()
    ventana_info.title("Información Completa")

    info_pedido = f"ID Pedido: {pedido[0]}\nTotal: {pedido[1]}\nPago: {pedido[2]}\nTipo Despacho: {pedido[3]}\nEspecificación: {pedido[4]}\nFecha: {pedido[5]}\nRUT: {pedido[6]}"
    info_cliente = f"ID Cliente: {cliente[0]}\nNombre: {cliente[1]}\nApellido: {cliente[2]}\nRUT: {cliente[3]}\nDirección: {cliente[4]}\nComuna: {cliente[5]}\nTeléfono: {cliente[6]}\nCorreo: {cliente[7]}"
    info_fabricacion = f"ID Fabricación: {fabricacion[0]}\nDetalles: {fabricacion[1]}\nEstado: {fabricacion[2]}\nAprobado: {fabricacion[3]}\nCantidad: {fabricacion[4]}\nID Pedido: {fabricacion[5]}"

    info = f"Información del Pedido:\n{info_pedido}\n\nInformación del Cliente:\n{info_cliente}\n\nInformación de Fabricación:\n{info_fabricacion}"

    def copiar_info():
        pyperclip.copy(info)
        messagebox.showinfo("Copiado", "Información completa copiada al portapapeles")

    # Botón de copiar en la esquina superior izquierda
    boton_copiar = tk.Button(ventana_info, text="Copiar", command=copiar_info)
    boton_copiar.pack(anchor='nw', padx=5, pady=5)

    label_info = tk.Label(ventana_info, text=info, justify=tk.LEFT)
    label_info.pack(padx=10, pady=10)


def on_tree_double_click(event):
    item = tree.selection()[0]
    values = tree.item(item, "values")
    
    tabla = combo_tablas.get()
    if tabla == "PEDIDOSTARKEN" or tabla == "PEDIDOSANTIAGO":
        id_pedido = values[2]  # Suponiendo que el ID_Pedido es el tercer valor en values
        mostrar_info_completa(id_pedido)
    elif tabla == "FABRICACION":
        id_pedido = values[-1]  # Suponiendo que el ID_Pedido está en la última columna en la tabla FABRICACION
        mostrar_info_completa(id_pedido)
    elif tabla == "PEDIDOS":
        id_pedido = values[0]  # Suponiendo que el ID del pedido es el primer valor en values
        mostrar_info_completa(id_pedido)
    elif tabla == "CLIENTE":
        rut = values[3]  # Suponiendo que el RUT está en la cuarta columna en la tabla CLIENTE
        mostrar_info_cliente_completa(rut)
    else:
        messagebox.showinfo("Información", "Esta funcionalidad no está implementada para esta tabla")


# Integrar el botón en la interfaz principal
def main_window():
    global form_frame, tree, combo_tablas, form_entries, search_entry, search_field, all_records, entry_numero_rut, entry_dv

    root = tk.Tk()
    root.title("Casa de la Impresión")
    root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False))  # PANTALLA COMPLETA SIN BORDES
    root.state('zoomed')

    # Crear el frame para el formulario
    form_frame = tk.Frame(root)
    form_frame.pack(pady=20)

    # Crear el combo para seleccionar la tabla
    ttk.Label(root, text="Registro").pack()
    combo_tablas = ttk.Combobox(root, values=['CLIENTE', 'PEDIDOS', 'FABRICACION', 'PEDIDOSANTIAGO', 'PEDIDOSTARKEN'])
    combo_tablas.pack(padx=10, pady=10)
    combo_tablas.bind("<<ComboboxSelected>>", lambda event: load_table(combo_tablas.get()))

    # Crear el frame para el Treeview y su scrollbar
    tree_frame = tk.Frame(root)
    tree_frame.pack(pady=20, fill='x')

    # Crear el Treeview
    columns = ()
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings')
    tree.pack(side='left', fill='both', expand=True)

    # Crear el scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
    scrollbar.pack(side='right', fill='y')

    tree.configure(yscrollcommand=scrollbar.set)

    # Asociar el evento de selección con la función on_tree_select
    tree.bind("<<TreeviewSelect>>", on_tree_select)

    # Asociar el evento de doble clic con la función on_tree_double_click
    tree.bind("<Double-1>", on_tree_double_click)

    # Crear el frame para los botones
    button_frame = ttk.Frame(root)
    button_frame.pack(pady=20)

    ttk.Button(button_frame, text="Insertar", command=insert_record).pack(side='left', padx=10)
    ttk.Button(button_frame, text="Actualizar", command=update_record).pack(side='left', padx=10)
    ttk.Button(button_frame, text="Eliminar", command=delete_record).pack(side='left', padx=10)
    ttk.Button(button_frame, text="Limpiar", command=clear_entries).pack(side='left', padx=10)

    # Botón para generar PDF de productos
    ttk.Button(button_frame, text="Productos", command=generar_pdf_productos).pack(side='left', padx=10)


    # Crear el frame para la búsqueda
    search_frame = tk.Frame(root)
    search_frame.pack(pady=20)

    ttk.Label(search_frame, text="Buscar por").grid(row=0, column=0, padx=5, pady=5, sticky='W')
    search_field = ttk.Combobox(search_frame)
    search_field.grid(row=0, column=1, padx=5, pady=5, sticky='W')

    ttk.Label(search_frame, text="Buscar").grid(row=0, column=2, padx=5, pady=5, sticky='W')
    search_entry = tk.Entry(search_frame)
    search_entry.grid(row=0, column=3, padx=5, pady=5, sticky='W')

    ttk.Button(search_frame, text="Filtrar", command=filter_records).grid(row=0, column=4, padx=10, pady=5)

    root.mainloop()

# Ventana de inicio de sesión
login_window = tk.Tk()
login_window.title("Inicio de Sesión")

ttk.Label(login_window, text="RUT").grid(row=0, column=0, padx=5, pady=5, sticky='W')
entry_rut_login = ttk.Entry(login_window)
entry_rut_login.grid(row=0, column=1, padx=5, pady=5, sticky='W')

ttk.Label(login_window, text="Contraseña").grid(row=1, column=0, padx=5, pady=5, sticky='W')
entry_password = ttk.Entry(login_window, show="*")
entry_password.grid(row=1, column=1, padx=5, pady=5, sticky='W')

ttk.Button(login_window, text="Iniciar Sesión", command=autenticar_usuario).grid(row=2, column=0, columnspan=2, padx=5, pady=5)

login_window.mainloop()
conn.close()
