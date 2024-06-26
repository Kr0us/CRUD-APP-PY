import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# Conexión a la base de datos SQLite
db_path = 'empresa.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()


# Función para insertar un nuevo usuario
def insertar_usuario(rut, contraseña):
    try:
        c.execute("INSERT INTO usuarios (RUT, contraseña) VALUES (?, ?)", (rut, contraseña))
        conn.commit()
        messagebox.showinfo("Success", "Usuario insertado exitosamente")
    except sqlite3.IntegrityError:
        messagebox.showwarning("Error", "El RUT ya está registrado")

# Función para leer usuarios desde la base de datos
def leer_usuarios():
    c.execute("SELECT RUT, contraseña FROM usuarios")
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
    global columns, form_entries, all_records
    for widget in form_frame.winfo_children():
        widget.destroy()

    if tabla == 'Cliente':
        columns = ("ID_Cliente", "Nombre", "Apellido", "RUT", "Dirección", "Comuna", "Teléfono", "Correo")
    elif tabla == 'Pedidos':
        columns = ("ID_Pedido", "Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha", "RUT")
    elif tabla == 'Fabricacion':
        columns = ("ID_Fabricacion", "Detalles", "Estado", "Aprobado", "Cantidad", "ID_Pedido")
    elif tabla == 'PedidoSantiago':
        columns = ("ID_PedidoSantiago", "Estado", "ID_Pedido")
    elif tabla == 'PedidoStarken':
        columns = ("ID_PedidoStarken", "Estado", "ID_Pedido")

    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col, command=lambda _col=col: sort_column(tree, _col, False))

    form_entries = {}
    for i, col in enumerate(columns):
        tk.Label(form_frame, text=col).grid(row=i, column=0)
        entry = tk.Entry(form_frame)
        entry.grid(row=i, column=1)
        form_entries[col] = entry

    search_field['values'] = columns  # Actualizar el Combobox de búsqueda
    read_records()

# Función para insertar registros en la tabla seleccionada
def insert_record():
    tabla = combo_tablas.get()
    values = [entry.get() for entry in form_entries.values()]
    
    if all(values):
        placeholders = ", ".join("?" for _ in values[1:])
        columns_str = ", ".join(columns[1:])
        query = f"INSERT INTO {tabla} ({columns_str}) VALUES ({placeholders})"
        try:
            c.execute(query, values[1:])
            conn.commit()
            messagebox.showinfo("Success", f"Registro insertado exitosamente en {tabla}")
            clear_entries()
            read_records()
            if tabla == 'Cliente':
                ventana_pedido(values[3])  # Pasar el RUT a la función ventana_pedido
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al insertar el registro: {e}")
    else:
        messagebox.showwarning("Input error", "Por favor, complete todos los campos")





# Función para actualizar registros en la tabla seleccionada
def update_record():
    tabla = combo_tablas.get()
    id_col = columns[0]
    record_id = form_entries[id_col].get()
    
    if not record_id:
        messagebox.showwarning("Input error", f"Por favor, ingrese el ID del registro en {id_col} para actualizar")
        return
    
    values = [entry.get() for entry in form_entries.values()]
    if any(values[1:]):
        updates = ", ".join(f"{col} = COALESCE(?, {col})" for col in columns[1:])
        query = f"UPDATE {tabla} SET {updates} WHERE {id_col} = ?"
        try:
            c.execute(query, values[1:] + [record_id])
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
    for col, val in zip(columns, values):
        form_entries[col].delete(0, tk.END)
        form_entries[col].insert(0, val)


# Función para filtrar registros en el Treeview
def filter_records():
    search_term = search_entry.get().lower()
    search_by = search_field.get()
    tabla = combo_tablas.get()

    if search_by and search_term:
        # Usar una coincidencia exacta en lugar de LIKE para coincidencias parciales
        query = f"SELECT * FROM {tabla} WHERE LOWER({search_by}) = ?"
        c.execute(query, (search_term,))
        filtered_records = c.fetchall()
        display_records(filtered_records)
    else:
        messagebox.showwarning("Input error", "Por favor, seleccione un campo y escriba un término de búsqueda")



#Funcion para ordenar las columnas al presionarlas con click
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
            c.execute("INSERT INTO Pedidos (Total, Pago, Tipo_Despacho, Especificación, Fecha, RUT) VALUES (?, ?, ?, ?, ?, ?)", valores_pedido)
            conn.commit()
            messagebox.showinfo("Success", "Pedido insertado exitosamente")
            pedido_window.destroy()
        else:
            messagebox.showwarning("Input error", "Por favor, complete todos los campos del pedido")

    pedido_window = tk.Toplevel()
    pedido_window.title("Agregar Pedido")

    pedido_columns = ("Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha", "RUT")
    pedido_entries = {}
    for i, col in enumerate(pedido_columns):
        tk.Label(pedido_window, text=col).grid(row=i, column=0)
        entry = tk.Entry(pedido_window)
        entry.grid(row=i, column=1)
        pedido_entries[col] = entry

    pedido_entries["RUT"].insert(0, rut)  # Llenar automáticamente el campo RUT

    tk.Button(pedido_window, text="Agregar Pedido", command=agregar_pedido).grid(row=len(pedido_columns), column=0, columnspan=2)



def main_window():
    global form_frame, tree, combo_tablas, form_entries, search_entry, search_field, all_records
 
    root = tk.Tk()
    root.title("Sistema de Información de Clientes")
    root.bind('<Escape>', lambda e: root.attributes('-fullscreen', False)) # PANTALLA COMPLETA SIN BORDES
    root.state('zoomed')
 
    # Crear el frame para el formulario
    form_frame = tk.Frame(root)
    form_frame.pack(pady=20)
 
    # Crear el combo para seleccionar la tabla
    tk.Label(root, text="Seleccionar Tabla").pack()
    combo_tablas = ttk.Combobox(root, values=['Cliente', 'Pedidos', 'Fabricacion', 'PedidoSantiago', 'PedidoStarken'])
    combo_tablas.pack()
    combo_tablas.bind("<<ComboboxSelected>>", lambda event: load_table(combo_tablas.get()))
 
    # Crear el Treeview
    columns = ()
    tree = ttk.Treeview(root, columns=columns, show='headings')
    tree.pack(pady=20, fill='x')
 
    # Asociar el evento de selección con la función on_tree_select
    tree.bind("<<TreeviewSelect>>", on_tree_select)
 
    # Crear el frame para los botones
    button_frame = tk.Frame(root)
    button_frame.pack(pady=20)
 
    tk.Button(button_frame, text="Insertar", command=insert_record).pack(side='left', padx=10)
    tk.Button(button_frame, text="Actualizar", command=update_record).pack(side='left', padx=10)
    tk.Button(button_frame, text="Eliminar", command=delete_record).pack(side='left', padx=10)
    tk.Button(button_frame, text="Limpiar", command=clear_entries).pack(side='left', padx=10)
 
    # Crear el frame para la búsqueda
    search_frame = tk.Frame(root)
    search_frame.pack(pady=20)
 
    tk.Label(search_frame, text="Buscar por").grid(row=0, column=0)
    search_field = ttk.Combobox(search_frame)
    search_field.grid(row=0, column=1)
 
    tk.Label(search_frame, text="Buscar").grid(row=0, column=2)
    search_entry = tk.Entry(search_frame)
    search_entry.grid(row=0, column=3)
 
    tk.Button(search_frame, text="Filtrar", command=filter_records).grid(row=0, column=4, padx=10)
 
    root.mainloop()


# Ventana de inicio de sesión
login_window = tk.Tk()
login_window.title("Inicio de Sesión")

tk.Label(login_window, text="RUT").grid(row=0, column=0)
entry_rut_login = tk.Entry(login_window)
entry_rut_login.grid(row=0, column=1)

tk.Label(login_window, text="Contraseña").grid(row=1, column=0)
entry_password = tk.Entry(login_window, show="*")
entry_password.grid(row=1, column=1)

tk.Button(login_window, text="Iniciar Sesión", command=autenticar_usuario).grid(row=2, column=0, columnspan=2)

# Ventana para agregar nuevos usuarios
def ventana_nuevo_usuario():
    global entry_rut_nuevo, entry_password_nuevo

    new_user_window = tk.Toplevel()
    new_user_window.title("Nuevo Usuario")

    tk.Label(new_user_window, text="RUT").grid(row=0, column=0)
    entry_rut_nuevo = tk.Entry(new_user_window)
    entry_rut_nuevo.grid(row=0, column=1)

    tk.Label(new_user_window, text="Contraseña").grid(row=1, column=0)
    entry_password_nuevo = tk.Entry(new_user_window, show="*")
    entry_password_nuevo.grid(row=1, column=1)

    tk.Button(new_user_window, text="Agregar Usuario", command=lambda: insertar_usuario(entry_rut_nuevo.get(), entry_password_nuevo.get())).grid(row=2, column=0, columnspan=2)

    

login_window.mainloop()
conn.close()
