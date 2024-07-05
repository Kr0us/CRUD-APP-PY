import tkinter as tk
from tkinter import ttk, messagebox
from ttkthemes import ThemedTk
from reportlab.pdfgen import canvas
from fpdf import FPDF
from tkcalendar import DateEntry
import sqlite3
import re
import pyperclip

class EncargadoApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Casa de la Impresión - Encargado")
        self.master.state('zoomed')
        self.conn = sqlite3.connect('empresa.db')
        self.c = self.conn.cursor()
        self.create_widgets()

    def create_widgets(self):
        self.form_frame = tk.Frame(self.master)
        self.form_frame.pack(pady=20)
        
        self.top_frame = tk.Frame(self.master)
        self.top_frame.pack(pady=20)

        ttk.Label(self.master, text="Registro").pack()
        self.combo_tablas = ttk.Combobox(self.master, values=['CLIENTE', 'PEDIDOS', 'FABRICACION'])
        self.combo_tablas.pack(padx=10, pady=10)
        self.combo_tablas.bind("<<ComboboxSelected>>", self.toggle_admin_buttons)

        self.tree_frame = tk.Frame(self.master)
        self.tree_frame.pack(pady=20, fill='x')

        self.tree = ttk.Treeview(self.tree_frame, columns=(), show='headings')
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')

        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        self.tree.bind("<Double-1>", self.on_tree_double_click)

        self.button_frame = ttk.Frame(self.master)
        self.button_frame.pack(pady=20)

        ttk.Button(self.button_frame, text="Insertar", command=self.insertar_registro).pack(side='left', padx=10)
        ttk.Button(self.button_frame, text="Actualizar", command=self.update_record).pack(side='left', padx=10)
        ttk.Button(self.button_frame, text="Eliminar", command=self.delete_record).pack(side='left', padx=10)
        ttk.Button(self.button_frame, text="Limpiar", command=self.clear_entries).pack(side='left', padx=10)

        self.btn_admin_pedido_santiago = ttk.Button(self.top_frame, text="Pedido Santiago", command=self.admin_pedido_santiago)
        self.btn_admin_pedido_starken = ttk.Button(self.top_frame, text="Pedido Starken", command=self.admin_pedido_starken)

        self.search_frame = tk.Frame(self.master)
        self.search_frame.pack(pady=20)

        ttk.Label(self.search_frame, text="Buscar por").grid(row=0, column=0, padx=5, pady=5, sticky='W')
        self.search_field = ttk.Combobox(self.search_frame)
        self.search_field.grid(row=0, column=1, padx=5, pady=5, sticky='W')

        ttk.Label(self.search_frame, text="Buscar").grid(row=0, column=2, padx=5, pady=5, sticky='W')
        self.search_entry = tk.Entry(self.search_frame)
        self.search_entry.grid(row=0, column=3, padx=5, pady=5, sticky='W')

        ttk.Button(self.search_frame, text="Filtrar", command=self.filter_records).grid(row=0, column=4, padx=10, pady=5)

        self.load_table('PEDIDOS')

    def toggle_admin_buttons(self, event):
        selected_table = self.combo_tablas.get()
        if selected_table == 'PEDIDOS':
            self.btn_admin_pedido_santiago.pack(side='left', padx=10)
            self.btn_admin_pedido_starken.pack(side='left', padx=10)
        else:
            self.btn_admin_pedido_santiago.pack_forget()
            self.btn_admin_pedido_starken.pack_forget()
        self.load_table(selected_table)

    def load_table(self, tabla):
        for widget in self.form_frame.winfo_children():
            widget.destroy()

        self.form_entries = {}
        self.columns = []
        self.tabla = tabla

        estados = ["Atrasado", "Cancelado", "En Tránsito", "Entregado", "Procesando"]
        cantidades = [25, 50, 100, 200, 500, 750, 1000, 2000]
        pagos = ["Efectivo", "Tarjeta", "Transferencia"]
        tipo_despacho = ["Domicilio", "Sucursal", "Starken"]

        if tabla == 'CLIENTE':
            self.columns = ["ID_Cliente", "Nombre", "Apellido", "RUT", "Dirección", "Comuna", "Teléfono", "Correo"]
        elif tabla == 'PEDIDOS':
            self.columns = ["ID_Pedido", "Total", "Pago", "Tipo Despacho", "Especificación", "Fecha", "RUT"]
        elif tabla == 'PEDIDOSTARKEN':
            self.columns = ["ID_PedidoStarken", "Estado", "ID_Pedido"]
        elif tabla == 'PEDIDOSANTIAGO':
            self.columns = ["ID_PedidoSantiago", "Estado", "ID_Pedido"]
        elif tabla == 'FABRICACION':
            self.columns = ["ID_Fabricacion", "Detalles", "Estado", "Aprobado", "Cantidad", "ID_Pedido"]

        for i, col in enumerate(self.columns):
            ttk.Label(self.form_frame, text=col).grid(row=i, column=0, padx=5, pady=5, sticky='W')
            if col == "Estado":
                entry = ttk.Combobox(self.form_frame, values=estados, width=28)
            elif col == "Tipo Despacho":
                entry = ttk.Combobox(self.form_frame, values=tipo_despacho, width=28)
            elif col == "Fecha":
                entry = DateEntry(self.form_frame, width=30, date_pattern='dd-mm-yyyy')
            elif col == "Pago":
                entry = ttk.Combobox(self.form_frame, values=pagos, width=28)
            else:
                entry = ttk.Entry(self.form_frame, width=30)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky='W')
            if col.startswith("ID_"):
                entry.config(state='normal')  # Hacer el campo de ID editable
            self.form_entries[col] = entry

        self.tree["columns"] = self.columns
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda _col=col: self.sort_column(self.tree, _col, False))

        self.search_field['values'] = self.columns
        self.read_records()

    def read_records(self):
        query = f"SELECT * FROM {self.tabla}"
        self.c.execute(query)
        all_records = self.c.fetchall()
        self.display_records(all_records)

    def display_records(self, records):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in records:
            self.tree.insert('', tk.END, values=row)

    def insertar_registro(self):
        current_values = [self.form_entries[col].get() for col in self.columns]

        if all(current_values):  # Verificar que todos los campos estén llenos
            query = f"INSERT INTO {self.tabla} ({', '.join(self.columns)}) VALUES ({', '.join(['?'] * len(self.columns))})"
            try:
                self.c.execute(query, current_values)
                self.conn.commit()
                messagebox.showinfo("Success", f"Registro insertado exitosamente en {self.tabla}")
                self.clear_entries()
                self.read_records()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al insertar el registro en {self.tabla}: {e}")
        else:
            messagebox.showwarning("Input error", "Por favor, complete todos los campos")

    def update_record(self):
        current_values = [self.form_entries[col].get() for col in self.columns]
        record_id = self.form_entries[self.columns[0]].get()

        if all(current_values):  # Verificar que todos los campos estén llenos
            updates = ", ".join(f"{col} = ?" for col in self.columns)
            query = f"UPDATE {self.tabla} SET {updates} WHERE {self.columns[0]} = ?"
            try:
                self.c.execute(query, current_values + [record_id])
                self.conn.commit()
                messagebox.showinfo("Success", f"Registro actualizado exitosamente en {self.tabla}")
                self.clear_entries()
                self.read_records()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error al actualizar el registro: {e}")
        else:
            messagebox.showwarning("Input error", "Por favor, complete todos los campos")

    def delete_record(self):
        record_id = self.form_entries[self.columns[0]].get()
        if not record_id:
            messagebox.showwarning("Input error", f"Por favor, ingrese el ID del registro en {self.columns[0]} para eliminar")
            return

        query = f"DELETE FROM {self.tabla} WHERE {self.columns[0]} = ?"
        try:
            self.c.execute(query, (record_id,))
            self.conn.commit()
            messagebox.showinfo("Success", f"Registro eliminado exitosamente en {self.tabla}")
            self.clear_entries()
            self.read_records()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar el registro: {e}")

    def clear_entries(self):
        for entry in self.form_entries.values():
            entry.delete(0, tk.END)

    def on_tree_select(self, event):
        selected_item = self.tree.focus()
        values = self.tree.item(selected_item, 'values')

        for col, val in zip(self.columns, values):
            if col in self.form_entries:
                self.form_entries[col].config(state='normal')  # Habilitar temporalmente para actualizar el valor
                self.form_entries[col].delete(0, tk.END)
                self.form_entries[col].insert(0, val)
                if col.startswith("ID_"):
                    self.form_entries[col].config(state='normal')  # Volver a configurar como solo lectura después de la actualización

    def on_tree_double_click(self, event):
        item = self.tree.selection()[0]
        values = self.tree.item(item, "values")
        if self.tabla == "PEDIDOSTARKEN" or self.tabla == "PEDIDOSANTIAGO":
            id_pedido = values[2]
            self.mostrar_info_completa(id_pedido)
        elif self.tabla == "FABRICACION":
            id_pedido = values[-1]
            self.mostrar_info_completa(id_pedido)
        elif self.tabla == "PEDIDOS":
            id_pedido = values[0]
            self.mostrar_info_completa(id_pedido)
        elif self.tabla == "CLIENTE":
            rut = values[3]
            self.mostrar_info_cliente(rut)
        else:
            messagebox.showinfo("Información", "Esta funcionalidad no está implementada para esta tabla")

    def filter_records(self):
        search_term = self.search_entry.get().lower()
        search_by = self.search_field.get()

        if search_by and search_term:
            query = f"SELECT * FROM {self.tabla} WHERE LOWER({search_by}) = ?"
            self.c.execute(query, (search_term,))
            records = self.c.fetchall()
            self.display_records(records)
        else:
            self.read_records()

    def admin_pedido_santiago(self):
        self.load_table('PEDIDOSANTIAGO')

    def admin_pedido_starken(self):
        self.load_table('PEDIDOSTARKEN')

    def mostrar_info_completa(self, id_pedido):
        query_pedido = "SELECT * FROM PEDIDOS WHERE ID_Pedido = ?"
        self.c.execute(query_pedido, (id_pedido,))
        pedido = self.c.fetchone()

        if not pedido:
            messagebox.showerror("Error", "Pedido no encontrado")
            return

        rut = pedido[-1]

        query_cliente = "SELECT * FROM CLIENTE WHERE RUT = ?"
        self.c.execute(query_cliente, (rut,))
        cliente = self.c.fetchone()

        if not cliente:
            messagebox.showerror("Error", "Cliente no encontrado")
            return

        query_fabricacion = "SELECT * FROM FABRICACION WHERE ID_Pedido = ?"
        self.c.execute(query_fabricacion, (id_pedido,))
        fabricacion = self.c.fetchone()

        if not fabricacion:
            messagebox.showerror("Error", "Fabricación no encontrada")
            return

        ventana_info = tk.Toplevel()
        ventana_info.title("Información Completa")

        info_pedido = f"ID Pedido: {pedido[0]}\nTotal: {pedido[1]}\nMetodo de Pago: {pedido[2]}\nTipo Despacho: {pedido[3]}\nEspecificación: {pedido[4]}\nFecha: {pedido[5]}\nRUT: {pedido[6]}"
        info_cliente = f"ID Cliente: {cliente[0]}\nNombre: {cliente[1]}\nApellido: {cliente[2]}\nRUT: {cliente[3]}\nDirección: {cliente[4]}\nComuna: {cliente[5]}\nTeléfono: {cliente[6]}\nCorreo: {cliente[7]}"
        info_fabricacion = f"ID Fabricación: {fabricacion[0]}\nDetalles: {fabricacion[1]}\nEstado: {fabricacion[2]}\nAprobado: {fabricacion[3]}\nCantidad: {fabricacion[4]}\nID Pedido: {fabricacion[5]}"

        info = f"Información del Pedido:\n{info_pedido}\n\nInformación del Cliente:\n{info_cliente}\n\nInformación de Fabricación:\n{info_fabricacion}"

        def copiar_info():
            pyperclip.copy(info)
            messagebox.showinfo("Copiado", "Información completa copiada al portapapeles")

        def descargar_info():
            self.descargar_pdf_info_completa(info, id_pedido)

        boton_copiar = tk.Button(ventana_info, text="Copiar", command=copiar_info)
        boton_copiar.pack(anchor='nw', padx=5, pady=5)

        boton_descargar = tk.Button(ventana_info, text="Descargar información", command=descargar_info)
        boton_descargar.pack(anchor='nw', padx=5, pady=5)

        label_info = tk.Label(ventana_info, text=info, justify=tk.LEFT)
        label_info.pack(padx=10, pady=10)

    def descargar_pdf_info_completa(self, info, id_pedido):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        lineas_info = info.split('\n')
        for linea in lineas_info:
            pdf.cell(0, 10, linea, ln=True)
        
        nombre_archivo = f"Informacion_Completa_{id_pedido}.pdf"
        pdf.output(nombre_archivo)
        messagebox.showinfo("PDF guardado", f"La información completa ha sido guardada en {nombre_archivo}")


class AdminApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Administración de Usuarios")
        self.conn = sqlite3.connect('empresa.db')
        self.c = self.conn.cursor()
        self.create_widgets()

    def create_widgets(self):
        self.form_frame = tk.Frame(self.master)
        self.form_frame.pack(pady=20)

        self.user_entries = {}
        ttk.Label(self.form_frame, text="Usuario:").grid(row=0, column=0, padx=10, pady=10)
        self.user_entries['usuario'] = ttk.Entry(self.form_frame)
        self.user_entries['usuario'].grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.form_frame, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)
        self.user_entries['contrasenia'] = ttk.Entry(self.form_frame, show="*")
        self.user_entries['contrasenia'].grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.form_frame, text="Rol:").grid(row=2, column=0, padx=10, pady=10)
        self.user_entries['rol'] = ttk.Entry(self.form_frame)
        self.user_entries['rol'].grid(row=2, column=1, padx=10, pady=10)

        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=20)

        ttk.Button(button_frame, text="Insertar", command=self.insertar_usuario).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Actualizar", command=self.actualizar_usuario).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Eliminar", command=self.eliminar_usuario).pack(side='left', padx=10)
        ttk.Button(button_frame, text="Limpiar", command=self.limpiar_entradas).pack(side='left', padx=10)

        tree_frame = tk.Frame(self.master)
        tree_frame.pack(pady=20, fill='x')

        self.columns = ["ID", "RUT", "contraseña", "role"]
        self.tree = ttk.Treeview(tree_frame, columns=self.columns, show='headings')
        for col in self.columns:
            self.tree.heading(col, text=col)
        self.tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        scrollbar.pack(side='right', fill='y')

        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        self.selected_user_id = None
        self.leer_usuarios()

    def insertar_usuario(self):
        usuario = self.user_entries['usuario'].get()
        contrasenia = self.user_entries['contrasenia'].get()
        rol = self.user_entries['rol'].get()
        
        if not usuario or not contrasenia or not rol:
            messagebox.showwarning("Error", "Todos los campos son obligatorios")
            return

        try:
            self.c.execute("INSERT INTO usuarios (RUT, contraseña, role) VALUES (?, ?, ?)", (usuario, contrasenia, rol))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario insertado exitosamente")
            self.leer_usuarios()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al insertar el usuario: {e}")

    def actualizar_usuario(self):
        if not self.selected_user_id:
            messagebox.showwarning("Error", "Seleccione un usuario para actualizar")
            return

        usuario = self.user_entries['usuario'].get()
        contrasenia = self.user_entries['contrasenia'].get()
        rol = self.user_entries['rol'].get()

        try:
            self.c.execute("UPDATE usuarios SET RUT=?, contraseña=?, role=? WHERE ID=?", (usuario, contrasenia, rol, self.selected_user_id))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario actualizado exitosamente")
            self.leer_usuarios()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al actualizar el usuario: {e}")

    def eliminar_usuario(self):
        if not self.selected_user_id:
            messagebox.showwarning("Error", "Seleccione un usuario para eliminar")
            return

        try:
            self.c.execute("DELETE FROM usuarios WHERE ID=?", (self.selected_user_id,))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Usuario eliminado exitosamente")
            self.leer_usuarios()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error al eliminar el usuario: {e}")

    def limpiar_entradas(self):
        for entry in self.user_entries.values():
            entry.delete(0, tk.END)

    def on_tree_select(self, event):
        selected_item = self.tree.selection()[0]
        user_data = self.tree.item(selected_item)['values']
        self.selected_user_id = user_data[0]
        self.user_entries['usuario'].delete(0, tk.END)
        self.user_entries['usuario'].insert(0, user_data[1])
        self.user_entries['contrasenia'].delete(0, tk.END)
        self.user_entries['contrasenia'].insert(0, user_data[2])
        self.user_entries['rol'].delete(0, tk.END)
        self.user_entries['rol'].insert(0, user_data[3])

    def leer_usuarios(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.c.execute("SELECT * FROM usuarios")
        for row in self.c.fetchall():
            self.tree.insert('', tk.END, values=row)

def login_encargado():
    username = username_entry.get()
    password = password_entry.get()
    conn = sqlite3.connect('empresa.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE RUT=? AND contraseña=? AND role='Encargado'", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        messagebox.showinfo("Login exitoso", "Bienvenido, {}".format(username))
        root.destroy()
        root_encargado = tk.Tk()
        app = EncargadoApp(root_encargado)
        root_encargado.mainloop()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

def login_admin():
    username = username_entry.get()
    password = password_entry.get()
    conn = sqlite3.connect('empresa.db')
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE RUT=? AND contraseña=? AND role='Admin'", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        messagebox.showinfo("Login exitoso", "Bienvenido, {}".format(username))
        root.destroy()
        root_admin = tk.Tk()
        app = AdminApp(root_admin)
        root_admin.mainloop()
    else:
        messagebox.showerror("Error", "Usuario o contraseña incorrectos")

# Ventana de inicio de sesión
root = ThemedTk(theme="breeze")
root.title("Inicio de Sesión")
root.geometry("400x350")
root.resizable(False, False)
root.configure(bg="#f0f0f0")

main_frame = tk.Frame(root, bg="#f0f0f0")
main_frame.place(relwidth=1, relheight=1)

title_label = tk.Label(main_frame, text="INICIO DE SESIÓN", font=("Helvetica", 16, "bold"), bg="#f0f0f0", fg="black")
title_label.pack(pady=20)

entry_frame = tk.Frame(main_frame, bg="white", bd=5)
entry_frame.pack(pady=20)

username_entry = ttk.Entry(entry_frame, font=("Helvetica", 12))
username_entry.grid(row=0, column=1, padx=10, pady=10)
password_entry = ttk.Entry(entry_frame, font=("Helvetica", 12), show="*")
password_entry.grid(row=1, column=1, padx=10, pady=10)

ttk.Label(entry_frame, text="Usuario:").grid(row=0, column=0, padx=10, pady=10)
ttk.Label(entry_frame, text="Contraseña:").grid(row=1, column=0, padx=10, pady=10)

ttk.Button(main_frame, text="Login Encargado", command=login_encargado).pack(pady=10)
ttk.Button(main_frame, text="Login Admin", command=login_admin).pack(pady=10)

root.mainloop()
