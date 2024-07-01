import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
import sqlite3
import re
from fpdf import FPDF

# Conexión a la base de datos SQLite
db_path = 'empresa.db'
try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
except sqlite3.OperationalError as e:
    print(f"No se puede abrir el archivo de la base de datos: {e}")
    exit()

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
        messagebox.showinfo("Éxito", "Usuario insertado exitosamente")
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

def main_window():
    global form_frame, tree, combo_tablas, form_entries, search_entry, search_field, all_records, entry_numero_rut, entry_dv, root

    root = ThemedTk(theme="breeze")
    root.title("Casa de la Impresión")
    root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False)) # PANTALLA COMPLETA SIN BORDES
    root.state('zoomed')

    # Frame fijo en la parte superior para los botones y la búsqueda
    fixed_frame = tk.Frame(root, bg="#f0f0f0")
    fixed_frame.pack(side=tk.TOP, fill=tk.X, pady=10)

    button_frame = ttk.Frame(fixed_frame, padding=10)
    button_frame.pack(side=tk.LEFT, padx=20)

    ttk.Button(button_frame, text="Insertar", command=ventana_insertar, style="TButton").pack(side='left', padx=10)
    ttk.Button(button_frame, text="Actualizar", command=update_record, style="TButton").pack(side='left', padx=10)
    ttk.Button(button_frame, text="Eliminar", command=delete_record, style="TButton").pack(side='left', padx=10)
    ttk.Button(button_frame, text="Limpiar", command=clear_entries, style="TButton").pack(side='left', padx=10)
    ttk.Button(button_frame, text="Ver Inventario", command=mostrar_inventario, style="TButton").pack(side='left', padx=10)

    search_frame = tk.Frame(fixed_frame, bg="#f0f0f0")
    search_frame.pack(side=tk.RIGHT, padx=20)

    ttk.Label(search_frame, text="Buscar por", background="#f0f0f0", font=("Helvetica", 12)).grid(row=0, column=0, padx=10)
    search_field = ttk.Combobox(search_frame)
    search_field.grid(row=0, column=1, padx=10)

    ttk.Label(search_frame, text="Buscar", background="#f0f0f0", font=("Helvetica", 12)).grid(row=0, column=2, padx=10)
    search_entry = tk.Entry(search_frame)
    search_entry.grid(row=0, column=3, padx=10)

    ttk.Button(search_frame, text="Filtrar", command=filter_records, style="TButton").grid(row=0, column=4, padx=10)

    # Crear el frame para el formulario
    form_frame = tk.Frame(root)
    form_frame.pack(pady=20, fill=tk.X)

    ttk.Label(root, text="Seleccionar Tabla", background="#f0f0f0", font=("Helvetica", 12)).pack(pady=10)
    combo_tablas = ttk.Combobox(root, values=['CLIENTE', 'PEDIDOS', 'FABRICACION', 'PEDIDOSANTIAGO', 'PEDIDOSTARKEN'])
    combo_tablas.pack()
    combo_tablas.bind("<<ComboboxSelected>>", lambda event: load_table(combo_tablas.get()))

    # Sección de la tabla desplazable
    table_frame = tk.Frame(root, bg="#f0f0f0")
    table_frame.pack(fill=tk.BOTH, expand=True)

    columns = ()
    tree = ttk.Treeview(table_frame, columns=columns, show='headings')
    tree.pack(pady=20, fill=tk.BOTH, expand=True)

    # Configurar el estilo de la barra de desplazamiento
    style = ttk.Style()
    style.configure("Vertical.TScrollbar", gripcount=0,
                    background="#f0f0f0", darkcolor="#d3d3d3", lightcolor="#d3d3d3",
                    troughcolor="#f0f0f0", bordercolor="#d3d3d3", arrowcolor="#d3d3d3",
                    width=30, arrowsize=20)

    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
    tree.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    root.mainloop()

# Función para cargar la tabla seleccionada
def load_table(tabla):
    global columns, form_entries, all_records, entry_numero_rut, entry_dv, estado_combobox, aprobado_combobox
    for widget in form_frame.winfo_children():
        widget.destroy()

    form_entries = {}

    if tabla == 'CLIENTE':
        columns = ("ID_Cliente", "Nombre", "Apellido", "RUT", "Dirección", "Comuna", "Teléfono", "Correo")
        
        # Añadir campos para número RUT y dígito verificador solo si la tabla es Cliente
        ttk.Label(form_frame, text="Número RUT").grid(row=3, column=0, padx=5, pady=5, sticky='W')
        entry_numero_rut = ttk.Entry(form_frame)
        entry_numero_rut.grid(row=3, column=1, padx=5, pady=5, sticky='W')

        ttk.Label(form_frame, text="Dígito Verificador").grid(row=3, column=2, padx=5, pady=5, sticky='W')
        entry_dv = ttk.Entry(form_frame, width=5)
        entry_dv.grid(row=3, column=3, padx=5, pady=5, sticky='W')
    elif tabla == 'PEDIDOS':
        columns = ("ID_Pedido", "Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha", "RUT")

        # Añadir campos para número RUT y dígito verificador
        ttk.Label(form_frame, text="Número RUT").grid(row=6, column=0, padx=5, pady=5, sticky='W')
        entry_numero_rut = ttk.Entry(form_frame)
        entry_numero_rut.grid(row=6, column=1, padx=5, pady=5, sticky='W')

        ttk.Label(form_frame, text="Dígito Verificador").grid(row=6, column=2, padx=5, pady=5, sticky='W')
        entry_dv = ttk.Entry(form_frame, width=5)
        entry_dv.grid(row=6, column=3, padx=5, pady=5, sticky='W')
    elif tabla == 'FABRICACION':
        columns = ("ID_Fabricacion", "Detalles", "Estado", "Aprobado", "Cantidad", "ID_Pedido")
        
        # Añadir campo para Estado con menú desplegable
        ttk.Label(form_frame, text="Estado").grid(row=2, column=0, padx=5, pady=5, sticky='W')
        estado_combobox = ttk.Combobox(form_frame, values=["Empaquetado", "No Empaquetado"])
        estado_combobox.grid(row=2, column=1, padx=5, pady=5, sticky='W')
        form_entries["Estado"] = estado_combobox

        # Añadir campo para Aprobado con menú desplegable
        ttk.Label(form_frame, text="Aprobado").grid(row=3, column=0, padx=5, pady=5, sticky='W')
        aprobado_combobox = ttk.Combobox(form_frame, values=["Sí", "No"])
        aprobado_combobox.grid(row=3, column=1, padx=5, pady=5, sticky='W')
        form_entries["Aprobado"] = aprobado_combobox

        # Añadir campo para ID_Pedido
        ttk.Label(form_frame, text="ID_Pedido").grid(row=5, column=0, padx=5, pady=5, sticky='W')
        id_pedido_entry = ttk.Entry(form_frame)
        id_pedido_entry.grid(row=5, column=1, padx=5, pady=5, sticky='W')
        form_entries["ID_Pedido"] = id_pedido_entry

        # Validar que el campo Cantidad solo acepte números enteros
        def validar_cantidad(event):
            if not form_entries["Cantidad"].get().isdigit():
                messagebox.showerror("Error", "Cantidad debe ser un número entero")
                form_entries["Cantidad"].delete(0, tk.END)

        ttk.Label(form_frame, text="Cantidad").grid(row=4, column=0, padx=5, pady=5, sticky='W')
        cantidad_entry = ttk.Entry(form_frame)
        cantidad_entry.grid(row=4, column=1, padx=5, pady=5, sticky='W')
        cantidad_entry.bind("<FocusOut>", validar_cantidad)
        form_entries["Cantidad"] = cantidad_entry

    elif tabla == 'PEDIDOSANTIAGO':
        columns = ("ID_PedidoSantiago", "Estado", "ID_Pedido")

        # Añadir campo para Estado con menú desplegable
        ttk.Label(form_frame, text="Estado").grid(row=2, column=0, padx=5, pady=5, sticky='W')
        estado_combobox = ttk.Combobox(form_frame, values=["Entregado", "Cancelado", "En tránsito", "Procesando", "Atrasado"])
        estado_combobox.grid(row=2, column=1, padx=5, pady=5, sticky='W')
        form_entries["Estado"] = estado_combobox

        # Añadir campo para ID_Pedido
        ttk.Label(form_frame, text="ID_Pedido").grid(row=3, column=0, padx=5, pady=5, sticky='W')
        id_pedido_entry = ttk.Entry(form_frame)
        id_pedido_entry.grid(row=3, column=1, padx=5, pady=5, sticky='W')
        form_entries["ID_Pedido"] = id_pedido_entry

    elif tabla == 'PEDIDOSTARKEN':
        columns = ("ID_PedidoStarken", "Estado", "ID_Pedido")

        # Añadir campo para Estado con menú desplegable
        ttk.Label(form_frame, text="Estado").grid(row=2, column=0, padx=5, pady=5, sticky='W')
        estado_combobox = ttk.Combobox(form_frame, values=["Entregado", "Cancelado", "En tránsito", "Procesando", "Atrasado"])
        estado_combobox.grid(row=2, column=1, padx=5, pady=5, sticky='W')
        form_entries["Estado"] = estado_combobox

        # Añadir campo para ID_Pedido
        ttk.Label(form_frame, text="ID_Pedido").grid(row=3, column=0, padx=5, pady=5, sticky='W')
        id_pedido_entry = ttk.Entry(form_frame)
        id_pedido_entry.grid(row=3, column=1, padx=5, pady=5, sticky='W')
        form_entries["ID_Pedido"] = id_pedido_entry

    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))

    for i, col in enumerate(columns):
        if col == "RUT" or col.startswith("ID_"):
            continue  # No agregar campo de RUT o ID directamente en el formulario
        if col not in form_entries:  # Añadir solo si no está ya en form_entries
            ttk.Label(form_frame, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            if col == "Pago" and tabla == 'PEDIDOS':
                entry = ttk.Combobox(form_frame, values=["Efectivo", "Tarjeta", "Transferencia"])
            elif col == "Tipo_Despacho" and tabla == 'PEDIDOS':
                entry = ttk.Combobox(form_frame, values=["Domicilio", "Sucursal"])
            else:
                entry = ttk.Entry(form_frame)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            form_entries[col] = entry

    search_field['values'] = [col for col in columns if not col.startswith("ID_")]  # Actualizar el Combobox de búsqueda
    read_records()

# Función para insertar registros en la tabla seleccionada
def ventana_insertar():
    tabla = combo_tablas.get()

    insertar_window = tk.Toplevel(root)
    insertar_window.title("Insertar Datos")
    insertar_form_entries = {}

    for i, col in enumerate(columns):
        if col == "RUT" and tabla in ('CLIENTE', 'PEDIDOS'):
            ttk.Label(insertar_window, text="Número RUT").grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry_numero_rut = ttk.Entry(insertar_window)
            entry_numero_rut.grid(row=i, column=1, padx=5, pady=5, sticky='W')

            ttk.Label(insertar_window, text="Dígito Verificador").grid(row=i, column=2, padx=5, pady=5, sticky='W')
            entry_dv = ttk.Entry(insertar_window, width=5)
            entry_dv.grid(row=i, column=3, padx=5, pady=5, sticky='W')

            insertar_form_entries["numero_rut"] = entry_numero_rut
            insertar_form_entries["dv"] = entry_dv
        elif col == "Aprobado" and tabla == 'FABRICACION':
            ttk.Label(insertar_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry = ttk.Combobox(insertar_window, values=["Sí", "No"])
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            insertar_form_entries[col] = entry
        elif col == "Estado" and tabla in ('FABRICACION', 'PEDIDOSANTIAGO', 'PEDIDOSTARKEN'):
            ttk.Label(insertar_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry = ttk.Combobox(insertar_window, values=["Entregado", "Cancelado", "En tránsito", "Procesando", "Atrasado"])
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            insertar_form_entries[col] = entry
        else:
            ttk.Label(insertar_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            entry = ttk.Entry(insertar_window)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            insertar_form_entries[col] = entry

    def submit_insertar():
        values = [entry.get() for entry in insertar_form_entries.values()]

        if tabla in ('CLIENTE', 'PEDIDOS'):
            numero_rut = insertar_form_entries["numero_rut"].get()
            dv = insertar_form_entries["dv"].get()
            rut_completo = obtener_rut_completo(numero_rut, dv)

            if not validar_rut(rut_completo):
                messagebox.showwarning("Error", "El RUT no es válido")
                return

            if tabla == 'CLIENTE':
                values.insert(3, rut_completo)
            elif tabla == 'PEDIDOS':
                values.insert(6, rut_completo)

        if all(values):
            placeholders = ", ".join("?" for _ in values[1:])
            columns_str = ", ".join(columns[1:])
            query = f"INSERT INTO {tabla} ({columns_str}) VALUES ({placeholders})"
            try:
                c.execute(query, values[1:])
                conn.commit()
                messagebox.showinfo("Éxito", f"Registro insertado exitosamente en {tabla}")
                insertar_window.destroy()
                read_records()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al insertar el registro: {e}")
        else:
            messagebox.showwarning("Error de entrada", "Por favor, complete todos los campos")

    ttk.Button(insertar_window, text="Insertar", command=submit_insertar).grid(row=len(columns), column=0, columnspan=4, pady=10)

# Función para actualizar registros en la tabla seleccionada
def update_record():
    tabla = combo_tablas.get()
    id_col = columns[0]
    record_id = tree.item(tree.focus())['values'][0]  # Obtener el ID del registro seleccionado

    if not record_id:
        messagebox.showwarning("Error de entrada", f"Por favor, seleccione un registro para actualizar")
        return

    # Leer los valores actuales en el formulario
    current_values = [entry.get() for entry in form_entries.values()]

    # Leer los valores originales del registro seleccionado
    c.execute(f"SELECT * FROM {tabla} WHERE {id_col} = ?", (record_id,))
    original_values = c.fetchone()

    # Convertir los valores originales en una lista (omitimos el ID en original_values[1:])
    if original_values:
        original_values = list(original_values[1:])

    # Convertir los valores de "Sí" y "No" a 1 y 0 respectivamente para la comparación
    if tabla == 'FABRICACION' and "Aprobado" in form_entries:
        if form_entries["Aprobado"].get() == "Sí":
            current_values[columns.index('Aprobado') - 1] = '1'
        elif form_entries["Aprobado"].get() == "No":
            current_values[columns.index('Aprobado') - 1] = '0'

    # Verificar si se ha realizado algún cambio
    if current_values == original_values:
        messagebox.showwarning("Sin cambios", "No estás actualizando nada")
        return

    # Continuar con la actualización si hay cambios
    if tabla in ('CLIENTE', 'PEDIDOS', 'FABRICACION'):
        if tabla in ('CLIENTE', 'PEDIDOS'):
            numero_rut = entry_numero_rut.get()
            dv = entry_dv.get()
            rut_completo = obtener_rut_completo(numero_rut, dv)

            if not validar_rut(rut_completo):
                messagebox.showwarning("Error", "El RUT no es válido")
                return

            if tabla == 'CLIENTE':
                # Remplazar el valor del RUT en la posición correcta
                current_values.insert(columns.index('RUT') - 1, rut_completo)
            elif tabla == 'PEDIDOS':
                # Remplazar el valor del RUT en la posición correcta
                current_values.insert(columns.index('RUT') - 1, rut_completo)

    # Incluir el ID en los valores actuales
    current_values.insert(0, record_id)

    if any(current_values[1:]):
        updates = ", ".join(f"{col} = COALESCE(?, {col})" for col in columns[1:])
        query = f"UPDATE {tabla} SET {updates} WHERE {id_col} = ?"
        try:
            c.execute(query, current_values[1:] + [record_id])
            conn.commit()
            messagebox.showinfo("Éxito", f"Registro actualizado exitosamente en {tabla}")
            clear_entries()
            read_records()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al actualizar el registro: {e}")
    else:
        messagebox.showwarning("Error de entrada", "Por favor, ingrese al menos un dato para actualizar")


# Función para eliminar registros en la tabla seleccionada
def delete_record():
    tabla = combo_tablas.get()
    id_col = columns[0]
    record_id = tree.item(tree.focus())['values'][0]  # Obtener el ID del registro seleccionado

    if not record_id:
        messagebox.showwarning("Error de entrada", f"Por favor, seleccione un registro para eliminar")
        return

    if tabla == 'CLIENTE':
        # Obtener el RUT del cliente a eliminar
        rut_cliente = tree.item(tree.focus())['values'][columns.index('RUT')]

        # Borrar los pedidos asociados con el RUT del cliente y sus datos relacionados
        try:
            c.execute("SELECT ID_Pedido FROM PEDIDOS WHERE RUT = ?", (rut_cliente,))
            pedidos = c.fetchall()

            for pedido in pedidos:
                id_pedido = pedido[0]
                c.execute("DELETE FROM FABRICACION WHERE ID_Pedido = ?", (id_pedido,))
                c.execute("DELETE FROM PEDIDOSANTIAGO WHERE ID_Pedido = ?", (id_pedido,))
                c.execute("DELETE FROM PEDIDOSTARKEN WHERE ID_Pedido = ?", (id_pedido,))
            
            c.execute("DELETE FROM PEDIDOS WHERE RUT = ?", (rut_cliente,))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar los pedidos asociados: {e}")
            return

    elif tabla == 'PEDIDOS':
        # Obtener el ID del pedido a eliminar
        id_pedido = tree.item(tree.focus())['values'][columns.index('ID_Pedido')]

        # Borrar los registros asociados en FABRICACION, PEDIDOSANTIAGO y PEDIDOSTARKEN
        try:
            c.execute("DELETE FROM FABRICACION WHERE ID_Pedido = ?", (id_pedido,))
            c.execute("DELETE FROM PEDIDOSANTIAGO WHERE ID_Pedido = ?", (id_pedido,))
            c.execute("DELETE FROM PEDIDOSTARKEN WHERE ID_Pedido = ?", (id_pedido,))
            conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar los registros asociados: {e}")
            return

    try:
        c.execute(f"DELETE FROM {tabla} WHERE {id_col} = ?", (record_id,))
        conn.commit()
        messagebox.showinfo("Éxito", f"Registro eliminado exitosamente en {tabla}")
        clear_entries()
        read_records()
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error al eliminar el registro: {e}")





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
        elif col == "Estado" and tabla in ('FABRICACION', 'PEDIDOSANTIAGO', 'PEDIDOSTARKEN'):
            form_entries[col].set(val)
        elif col not in form_entries:
            continue  # No actualizar el campo de ID en el formulario
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
        messagebox.showwarning("Error de entrada", "Por favor, seleccione un campo y escriba un término de búsqueda")

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
            messagebox.showinfo("Éxito", "Pedido insertado exitosamente")
            pedido_window.destroy()
        else:
            messagebox.showwarning("Error de entrada", "Por favor, complete todos los campos del pedido")

    pedido_window = tk.Toplevel()
    pedido_window.title("Agregar Pedido")

    pedido_columns = ("Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha")
    pedido_entries = {}
    for i, col in enumerate(pedido_columns):
        ttk.Label(pedido_window, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
        if col == "Pago":
            entry = ttk.Combobox(pedido_window, values=["Efectivo", "Tarjeta", "Transferencia"])
        elif col == "Tipo_Despacho":
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

def mostrar_inventario():
    inventario_window = tk.Toplevel(root)
    inventario_window.title("Inventario")

    def descargar_pdf():
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        pdf.cell(200, 10, txt="Inventario", ln=True, align='C')

        for row in records:
            pdf.cell(200, 10, txt=f"Detalles: {row[0]}, Cantidad: {row[1]}", ln=True, align='L')

        pdf.output("inventario.pdf")
        messagebox.showinfo("Éxito", "Inventario descargado como PDF")

    columns = ("Detalles", "Cantidad")
    tree = ttk.Treeview(inventario_window, columns=columns, show='headings')
    tree.pack(pady=20, fill=tk.BOTH, expand=True)

    for col in columns:
        tree.heading(col, text=col)

    query = "SELECT Detalles, SUM(Cantidad) as Cantidad FROM FABRICACION GROUP BY Detalles"
    c.execute(query)
    records = c.fetchall()
    for row in records:
        tree.insert('', tk.END, values=row)

    ttk.Button(inventario_window, text="Descargar PDF", command=descargar_pdf).pack(pady=10)

# Ventana de inicio de sesión
login_window = ThemedTk(theme="breeze")
login_window.title("Inicio de Sesión")
login_window.geometry("400x350")
login_window.resizable(False, False)
login_window.configure(bg="#f0f0f0")

main_frame = tk.Frame(login_window, bg="#f0f0f0")
main_frame.place(relwidth=1, relheight=1)

title_label = tk.Label(main_frame, text="INICIO DE SESIÓN", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="black")
title_label.pack(pady=20)

entry_frame = tk.Frame(main_frame, bg="white", bd=5)
entry_frame.pack(pady=20)

def on_entry_click(event, entry, placeholder, is_password=False):
    if entry.get() == placeholder:
        entry.delete(0, "end")  # Delete all the text in the entry
        entry.config(foreground='black')
        if is_password:
            entry.config(show='*')  # Set the show character for password

def on_focusout(event, entry, placeholder, is_password=False):
    if entry.get() == '':
        entry.insert(0, placeholder)
        entry.config(foreground='grey')
        if is_password:
            entry.config(show='')  # Remove the show character for password

rut_placeholder = "Ingrese su RUT"
entry_rut_login = ttk.Entry(entry_frame, font=("Helvetica", 12), foreground='grey')
entry_rut_login.insert(0, rut_placeholder)
entry_rut_login.bind('<FocusIn>', lambda event: on_entry_click(event, entry_rut_login, rut_placeholder))
entry_rut_login.bind('<FocusOut>', lambda event: on_focusout(event, entry_rut_login, rut_placeholder))
entry_rut_login.grid(row=0, column=1, padx=10, pady=10)

password_placeholder = "Ingrese su contraseña"
entry_password = ttk.Entry(entry_frame, font=("Helvetica", 12), foreground='grey')
entry_password.insert(0, password_placeholder)
entry_password.bind('<FocusIn>', lambda event: on_entry_click(event, entry_password, password_placeholder, True))
entry_password.bind('<FocusOut>', lambda event: on_focusout(event, entry_password, password_placeholder, True))
entry_password.grid(row=1, column=1, padx=10, pady=10)

rut_icon = tk.Label(entry_frame, text="👤", font=("Helvetica", 14), bg="white")
rut_icon.grid(row=0, column=0, padx=10)

password_icon = tk.Label(entry_frame, text="🔒", font=("Helvetica", 14), bg="white")
password_icon.grid(row=1, column=0, padx=10)

login_button = ttk.Button(main_frame, text="INICIAR SESIÓN", command=autenticar_usuario, style="TButton")
login_button.pack(pady=20)

style = ttk.Style()
style.configure("TButton", font=("Helvetica", 12, "bold"), background="#d3d3d3", foreground="black", borderwidth=1)
style.map("TButton", background=[('active', '#a9a9a9')], foreground=[('active', 'black')])

login_window.mainloop()
conn.close()
