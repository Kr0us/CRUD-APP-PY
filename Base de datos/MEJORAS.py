import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os

# Conexión a la base de datos SQLite
db_path = 'Base de datos\\empresa.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Ruta del archivo de usuarios
USUARIOS_FILE = 'SQL_PY\\usuarios.txt'

# Función para leer usuarios desde el archivo de texto
def leer_usuarios():
    usuarios = {}
    if os.path.exists(USUARIOS_FILE):
        with open(USUARIOS_FILE, 'r') as file:
            for line in file:
                line = line.strip()
                rut, password = line.split(',')
                usuarios[rut] = password
    return usuarios

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
    elif tabla == 'pedidos':
        columns = ("ID_Pedido", "Total", "Pago", "Tipo_Despacho", "Especificación", "Fecha", "RUT")
    elif tabla == 'fabricacion':
        columns = ("ID_Fabricacion", "Detalles", "Estado1", "Estado2", "Cantidad", "ID_Pedido")
    elif tabla == 'PedidoSantiago':
        columns = ("ID_PedidoSantiago", "Estado", "ID_Pedido")
    elif tabla == 'PedidoStarken':
        columns = ("ID_PedidoStarken", "Estado", "ID_Pedido")
    
    tree["columns"] = columns
    for col in columns:
        tree.heading(col, text=col)
    
    form_entries = {}
    for i, col in enumerate(columns):
        tk.Label(form_frame, text=col).grid(row=i, column=0)
        entry = tk.Entry(form_frame)
        entry.grid(row=i, column=1)
        form_entries[col] = entry
    
    read_records()

# Función para insertar registros en la tabla seleccionada
def insert_record():
    tabla = combo_tablas.get()
    values = [entry.get() for entry in form_entries.values()]
    
    if all(values):
        placeholders = ", ".join("?" for _ in values[1:])
        columns_str = ", ".join(columns[1:])
        query = f"INSERT INTO {tabla} ({columns_str}) VALUES ({placeholders})"
        c.execute(query, values[1:])
        conn.commit()
        messagebox.showinfo("Success", f"Registro insertado exitosamente en {tabla}")
        clear_entries()
        read_records()
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
        c.execute(query, values[1:] + [record_id])
        conn.commit()
        messagebox.showinfo("Success", f"Registro actualizado exitosamente en {tabla}")
        clear_entries()
        read_records()
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
    c.execute(f"SELECT * FROM {tabla}")
    all_records = c.fetchall()
    display_records(all_records)

# Función para mostrar registros en el Treeview
def display_records(records):
    for i in tree.get_children():
        tree.delete(i)
    for row in records:
        tree.insert('', tk.END, values=row)

# Función para filtrar registros en el Treeview
def filter_records():
    search_term = search_entry.get().lower()
    filtered_records = [record for record in all_records if any(search_term in str(value).lower() for value in record)]
    display_records(filtered_records)

def main_window():
    global form_frame, tree, combo_tablas, form_entries, search_entry, all_records
    
    root = tk.Tk()
    root.title("Sistema de Información de Clientes")

    # Crear el frame para el formulario
    form_frame = tk.Frame(root)
    form_frame.pack(pady=20)
    
    # Crear el combo para seleccionar la tabla
    tk.Label(root, text="Seleccionar Tabla").pack()
    combo_tablas = ttk.Combobox(root, values=['Cliente', 'pedidos', 'fabricacion', 'PedidoSantiago', 'PedidoStarken'])
    combo_tablas.pack()
    combo_tablas.bind("<<ComboboxSelected>>", lambda event: load_table(combo_tablas.get()))

    # Crear el Treeview
    columns = ()
    tree = ttk.Treeview(root, columns=columns, show='headings')
    tree.pack(pady=20, fill='x')

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

    tk.Label(search_frame, text="Buscar").grid(row=0, column=0)
    search_entry = tk.Entry(search_frame)
    search_entry.grid(row=0, column=1)

    tk.Button(search_frame, text="Filtrar", command=filter_records).grid(row=0, column=2, padx=10)

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

login_window.mainloop()
conn.close()