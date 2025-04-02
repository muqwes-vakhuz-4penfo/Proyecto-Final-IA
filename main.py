import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageEnhance
import numpy as np
import random
import os
import cv2
from rembg import remove

class GeneradorFondosGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Fondos para Fotografía")
        self.root.geometry("1200x700")
        self.root.minsize(1000, 600)
        
        # Variables de estado
        self.imagen_original = None
        self.imagen_sin_fondo = None
        self.fondo_actual = None
        self.ancho_fondo = 1920
        self.alto_fondo = 1080
        self.resultado_combinado = None
        self.tk_images = []  # Para mantener referencias a las imágenes de Tkinter
        
        # Configurar estilo
        self._configurar_estilo()
        
        # Crear directorio para guardar fondos
        if not os.path.exists('fondos_generados'):
            os.makedirs('fondos_generados')
        
        # Crear la interfaz
        self._crear_interfaz()
    
    def _configurar_estilo(self):
        """Configurar el estilo visual de la aplicación"""
        style = ttk.Style()
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabelFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0')
        style.configure('TButton', padding=5)
        style.configure('TNotebook.Tab', padding=[10, 5])
    
    def _crear_interfaz(self):
        """Crear la interfaz gráfica de usuario"""
        # Panel principal dividido en dos partes
        panel_principal = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        panel_principal.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo para opciones (30% del ancho)
        panel_opciones = ttk.Frame(panel_principal, width=360)
        panel_principal.add(panel_opciones, weight=1)
        
        # Panel derecho para visualización (70% del ancho)
        panel_visualizacion = ttk.Frame(panel_principal)
        panel_principal.add(panel_visualizacion, weight=3)
        
        # --- Panel de opciones ---
        # Sección de carga de imagen
        seccion_imagen = ttk.LabelFrame(panel_opciones, text="Imagen", padding=(10, 5))
        seccion_imagen.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(seccion_imagen, text="Cargar Imagen", command=self._cargar_imagen).pack(fill=tk.X, pady=3)
        ttk.Button(seccion_imagen, text="Eliminar Fondo", command=self._eliminar_fondo).pack(fill=tk.X, pady=3)
        
        # Sección de dimensiones del fondo
        seccion_dimensiones = ttk.LabelFrame(panel_opciones, text="Dimensiones del Fondo", padding=(10, 5))
        seccion_dimensiones.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(seccion_dimensiones, text="Ancho:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.ancho_var = tk.StringVar(value=str(self.ancho_fondo))
        ttk.Entry(seccion_dimensiones, textvariable=self.ancho_var, width=8).grid(row=0, column=1, padx=5, pady=3)
        
        ttk.Label(seccion_dimensiones, text="Alto:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.alto_var = tk.StringVar(value=str(self.alto_fondo))
        ttk.Entry(seccion_dimensiones, textvariable=self.alto_var, width=8).grid(row=1, column=1, padx=5, pady=3)
        
        ttk.Button(seccion_dimensiones, text="Actualizar Dimensiones", command=self._actualizar_dimensiones).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Sección de fondos
        seccion_fondos = ttk.LabelFrame(panel_opciones, text="Generación de Fondos", padding=(10, 5))
        seccion_fondos.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Notebook para las diferentes pestañas de fondos
        notebook = ttk.Notebook(seccion_fondos)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Pestaña de degradado
        tab_degradado = ttk.Frame(notebook)
        notebook.add(tab_degradado, text="Degradado")
        
        ttk.Label(tab_degradado, text="Color 1:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.color1_btn = ttk.Button(tab_degradado, text="Seleccionar", command=lambda: self._seleccionar_color(1))
        self.color1_btn.grid(row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color1_value = (65, 105, 225)  # Azul por defecto
        
        ttk.Label(tab_degradado, text="Color 2:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.color2_btn = ttk.Button(tab_degradado, text="Seleccionar", command=lambda: self._seleccionar_color(2))
        self.color2_btn.grid(row=1, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color2_value = (255, 105, 180)  # Rosa por defecto
        
        ttk.Label(tab_degradado, text="Dirección:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.direccion_var = tk.StringVar(value="vertical")
        ttk.Combobox(tab_degradado, textvariable=self.direccion_var, 
                    values=["vertical", "horizontal", "diagonal"]).grid(
            row=2, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Button(tab_degradado, text="Generar Degradado", command=self._generar_degradado).grid(
            row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Pestaña de textura
        tab_textura = ttk.Frame(notebook)
        notebook.add(tab_textura, text="Textura")
        
        ttk.Label(tab_textura, text="Tipo:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.tipo_textura_var = tk.StringVar(value="ruido")
        ttk.Combobox(tab_textura, textvariable=self.tipo_textura_var, 
                     values=["ruido", "lienzo", "marmol"]).grid(
            row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_textura, text="Intensidad:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.intensidad_var = tk.DoubleVar(value=0.5)
        ttk.Scale(tab_textura, variable=self.intensidad_var, from_=0.1, to=1.0).grid(
            row=1, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_textura, text="Color Base:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.color_textura_btn = ttk.Button(tab_textura, text="Seleccionar", command=lambda: self._seleccionar_color(3))
        self.color_textura_btn.grid(row=2, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color_textura_value = (200, 200, 200)  # Gris por defecto
        
        ttk.Button(tab_textura, text="Generar Textura", command=self._generar_textura).grid(
            row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Pestaña de bokeh
        tab_bokeh = ttk.Frame(notebook)
        notebook.add(tab_bokeh, text="Bokeh")
        
        ttk.Label(tab_bokeh, text="Color Fondo:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.color_bokeh_btn = ttk.Button(tab_bokeh, text="Seleccionar", command=lambda: self._seleccionar_color(4))
        self.color_bokeh_btn.grid(row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color_bokeh_value = (20, 20, 50)  # Azul oscuro por defecto
        
        ttk.Label(tab_bokeh, text="Número de Puntos:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.num_puntos_var = tk.IntVar(value=100)
        ttk.Scale(tab_bokeh, variable=self.num_puntos_var, from_=10, to=300).grid(
            row=1, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_bokeh, text="Tamaño Máximo:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.tamano_max_var = tk.IntVar(value=50)
        ttk.Scale(tab_bokeh, variable=self.tamano_max_var, from_=10, to=100).grid(
            row=2, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Button(tab_bokeh, text="Generar Bokeh", command=self._generar_bokeh).grid(
            row=3, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Pestaña de geométrico
        tab_geometrico = ttk.Frame(notebook)
        notebook.add(tab_geometrico, text="Geométrico")
        
        ttk.Label(tab_geometrico, text="Tipo:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        self.tipo_geo_var = tk.StringVar(value="cuadricula")
        ttk.Combobox(tab_geometrico, textvariable=self.tipo_geo_var, 
                     values=["cuadricula", "triangulos", "hexagonos"]).grid(
            row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_geometrico, text="Color Fondo:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.color_geo_fondo_btn = ttk.Button(tab_geometrico, text="Seleccionar", command=lambda: self._seleccionar_color(5))
        self.color_geo_fondo_btn.grid(row=1, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color_geo_fondo_value = (240, 240, 240)  # Blanco por defecto
        
        ttk.Label(tab_geometrico, text="Color Líneas:").grid(row=2, column=0, padx=5, pady=3, sticky=tk.W)
        self.color_geo_lineas_btn = ttk.Button(tab_geometrico, text="Seleccionar", command=lambda: self._seleccionar_color(6))
        self.color_geo_lineas_btn.grid(row=2, column=1, padx=5, pady=3, sticky=tk.EW)
        self.color_geo_lineas_value = (30, 30, 30)  # Negro por defecto
        
        ttk.Label(tab_geometrico, text="Espaciado:").grid(row=3, column=0, padx=5, pady=3, sticky=tk.W)
        self.espaciado_var = tk.IntVar(value=50)
        ttk.Scale(tab_geometrico, variable=self.espaciado_var, from_=10, to=100).grid(
            row=3, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_geometrico, text="Grosor:").grid(row=4, column=0, padx=5, pady=3, sticky=tk.W)
        self.grosor_var = tk.IntVar(value=2)
        ttk.Scale(tab_geometrico, variable=self.grosor_var, from_=1, to=5).grid(
            row=4, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Button(tab_geometrico, text="Generar Geométrico", command=self._generar_geometrico).grid(
            row=5, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Pestaña de imagen personalizada
        tab_personalizado = ttk.Frame(notebook)
        notebook.add(tab_personalizado, text="Personalizado")
        
        ttk.Label(tab_personalizado, text="Fondo Personalizado:").grid(row=0, column=0, padx=5, pady=3, sticky=tk.W)
        ttk.Button(tab_personalizado, text="Cargar Fondo", command=self._cargar_fondo_personalizado).grid(
            row=0, column=1, padx=5, pady=3, sticky=tk.EW)
        
        ttk.Label(tab_personalizado, text="Ajustar Tamaño:").grid(row=1, column=0, padx=5, pady=3, sticky=tk.W)
        self.ajustar_tamano_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab_personalizado, variable=self.ajustar_tamano_var).grid(
            row=1, column=1, padx=5, pady=3, sticky=tk.W)
        
        ttk.Button(tab_personalizado, text="Aplicar Fondo", command=self._aplicar_fondo_personalizado).grid(
            row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.EW)
        
        # Botón de guardado
        ttk.Button(panel_opciones, text="Guardar Resultado", command=self._guardar_resultado).pack(fill=tk.X, padx=5, pady=10)
        
        # --- Panel de visualización ---
        # Canvas para mostrar la imagen con scrollbars
        self.canvas_frame = ttk.Frame(panel_visualizacion)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="lightgray")
        self.scroll_y = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_x = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)
        
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Mostrar mensaje inicial
        self._mostrar_mensaje_inicial()
    
    def _mostrar_mensaje_inicial(self):
        """Mostrar mensaje inicial en el canvas"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2, 
            self.canvas.winfo_height() // 2,
            text="Cargue una imagen para empezar",
            font=("Arial", 16),
            fill="gray"
        )
    
    def _cargar_imagen(self):
        """Cargar una imagen desde el sistema de archivos"""
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
        )
        
        if ruta_archivo:
            try:
                self.imagen_original = Image.open(ruta_archivo)
                self._mostrar_imagen(self.imagen_original)
                self.imagen_sin_fondo = None  # Resetear la imagen sin fondo
                self.fondo_actual = None
                self.resultado_combinado = None
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar la imagen: {str(e)}")
    
    def _cargar_fondo_personalizado(self):
        """Cargar una imagen como fondo personalizado"""
        ruta_archivo = filedialog.askopenfilename(
            title="Seleccionar Imagen de Fondo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp")]
        )
        
        if ruta_archivo:
            try:
                self.fondo_actual = Image.open(ruta_archivo)
                if self.ajustar_tamano_var.get():
                    # Redimensionar el fondo a las dimensiones actuales
                    self.fondo_actual = self.fondo_actual.resize((self.ancho_fondo, self.alto_fondo), Image.LANCZOS)
                self._aplicar_fondo_actual()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo cargar el fondo: {str(e)}")
    
    def _aplicar_fondo_personalizado(self):
        """Aplicar el fondo personalizado cargado"""
        if self.fondo_actual:
            self._aplicar_fondo_actual()
        else:
            messagebox.showwarning("Advertencia", "Primero debe cargar un fondo personalizado")
    
    def _eliminar_fondo(self):
        """Eliminar el fondo de la imagen cargada usando rembg"""
        if self.imagen_original is None:
            messagebox.showwarning("Advertencia", "Primero debe cargar una imagen")
            return
        
        try:
            # Convertir a RGB si es necesario (rembg requiere RGB)
            if self.imagen_original.mode != 'RGB':
                img_rgb = self.imagen_original.convert('RGB')
            else:
                img_rgb = self.imagen_original
            
            # Eliminar el fondo
            resultado = remove(img_rgb)
            self.imagen_sin_fondo = resultado
            
            # Mostrar el resultado
            self._mostrar_imagen(self.imagen_sin_fondo)
            
            messagebox.showinfo("Éxito", "Fondo eliminado correctamente. Ahora puede generar un nuevo fondo.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al eliminar el fondo: {str(e)}")
    
    def _actualizar_dimensiones(self):
        """Actualizar las dimensiones del fondo"""
        try:
            self.ancho_fondo = int(self.ancho_var.get())
            self.alto_fondo = int(self.alto_var.get())
            
            if self.fondo_actual:
                # Si ya hay un fondo, recrearlo con las nuevas dimensiones
                self._aplicar_fondo_actual()
        except ValueError:
            messagebox.showerror("Error", "Las dimensiones deben ser valores numéricos enteros.")
    
    def _seleccionar_color(self, opcion):
        """Abrir selector de color y guardar el color seleccionado"""
        color = colorchooser.askcolor(title="Seleccionar Color")
        if color[0]:  # Si se seleccionó un color
            r, g, b = [int(c) for c in color[0]]
            if opcion == 1:
                self.color1_value = (r, g, b)
                self.color1_btn.configure(text=f"RGB: {r},{g},{b}")
            elif opcion == 2:
                self.color2_value = (r, g, b)
                self.color2_btn.configure(text=f"RGB: {r},{g},{b}")
            elif opcion == 3:
                self.color_textura_value = (r, g, b)
                self.color_textura_btn.configure(text=f"RGB: {r},{g},{b}")
            elif opcion == 4:
                self.color_bokeh_value = (r, g, b)
                self.color_bokeh_btn.configure(text=f"RGB: {r},{g},{b}")
            elif opcion == 5:
                self.color_geo_fondo_value = (r, g, b)
                self.color_geo_fondo_btn.configure(text=f"RGB: {r},{g},{b}")
            elif opcion == 6:
                self.color_geo_lineas_value = (r, g, b)
                self.color_geo_lineas_btn.configure(text=f"RGB: {r},{g},{b}")
    
    def _generar_degradado(self):
        """Generar un fondo con degradado"""
        try:
            fondo = self._crear_fondo_degradado(
                self.color1_value,
                self.color2_value,
                self.direccion_var.get()
            )
            self.fondo_actual = fondo
            self._aplicar_fondo_actual()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el degradado: {str(e)}")
    
    def _generar_textura(self):
        """Generar un fondo con textura"""
        try:
            fondo = self._crear_fondo_textura(
                self.tipo_textura_var.get(),
                self.intensidad_var.get(),
                self.color_textura_value
            )
            self.fondo_actual = fondo
            self._aplicar_fondo_actual()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar la textura: {str(e)}")
    
    def _generar_bokeh(self):
        """Generar un fondo con efecto bokeh"""
        try:
            fondo = self._crear_fondo_bokeh(
                self.color_bokeh_value,
                int(self.num_puntos_var.get()),
                int(self.tamano_max_var.get())
            )
            self.fondo_actual = fondo
            self._aplicar_fondo_actual()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el bokeh: {str(e)}")
    
    def _generar_geometrico(self):
        """Generar un fondo con patrón geométrico"""
        try:
            fondo = self._crear_fondo_geometrico(
                self.color_geo_fondo_value,
                self.color_geo_lineas_value,
                self.tipo_geo_var.get(),
                int(self.espaciado_var.get()),
                int(self.grosor_var.get())
            )
            self.fondo_actual = fondo
            self._aplicar_fondo_actual()
        except Exception as e:
            messagebox.showerror("Error", f"Error al generar el patrón geométrico: {str(e)}")
    
    def _aplicar_fondo_actual(self):
        """Aplicar el fondo actual a la imagen sin fondo"""
        if self.fondo_actual:
            # Si hay una imagen sin fondo, combinarla con el fondo
            if self.imagen_sin_fondo:
                self.resultado_combinado = self._combinar_imagen_con_fondo(self.imagen_sin_fondo, self.fondo_actual)
                self._mostrar_imagen(self.resultado_combinado)
            else:
                # Si no hay imagen sin fondo, mostrar solo el fondo
                self._mostrar_imagen(self.fondo_actual)
        else:
            messagebox.showwarning("Advertencia", "Primero debe generar o cargar un fondo")
    
    def _crear_fondo_degradado(self, color1, color2, direccion):
        """Crear un fondo con degradado entre dos colores"""
        fondo = Image.new('RGB', (self.ancho_fondo, self.alto_fondo))
        draw = ImageDraw.Draw(fondo)
        
        if direccion == "vertical":
            for y in range(self.alto_fondo):
                ratio = y / self.alto_fondo
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(0, y), (self.ancho_fondo, y)], fill=(r, g, b))
        
        elif direccion == "horizontal":
            for x in range(self.ancho_fondo):
                ratio = x / self.ancho_fondo
                r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                draw.line([(x, 0), (x, self.alto_fondo)], fill=(r, g, b))
        
        else:  # diagonal
            for y in range(self.alto_fondo):
                for x in range(self.ancho_fondo):
                    ratio = (x + y) / (self.ancho_fondo + self.alto_fondo)
                    r = int(color1[0] + (color2[0] - color1[0]) * ratio)
                    g = int(color1[1] + (color2[1] - color1[1]) * ratio)
                    b = int(color1[2] + (color2[2] - color1[2]) * ratio)
                    draw.point((x, y), fill=(r, g, b))
        
        return fondo
    
    def _crear_fondo_textura(self, tipo, intensidad, color_base):
        """Crear un fondo con textura"""
        fondo = Image.new('RGB', (self.ancho_fondo, self.alto_fondo), color_base)
        
        if tipo == "ruido":
            # Crear ruido gaussiano
            ruido = np.random.normal(128 * intensidad, 64 * intensidad, 
                                   (self.alto_fondo, self.ancho_fondo, 3))
            ruido = np.clip(ruido, 0, 255).astype(np.uint8)
            textura = Image.fromarray(ruido, 'RGB')
            fondo = Image.blend(fondo, textura, intensidad)
        
        elif tipo == "lienzo":
            # Simular textura de lienzo
            for _ in range(int(50 * intensidad)):
                x1 = random.randint(0, self.ancho_fondo)
                y1 = random.randint(0, self.alto_fondo)
                x2 = x1 + random.randint(10, 100)
                y2 = y1 + random.randint(10, 100)
                color = (color_base[0] + random.randint(-30, 30),
                         color_base[1] + random.randint(-30, 30),
                         color_base[2] + random.randint(-30, 30))
                draw = ImageDraw.Draw(fondo)
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=None)
        
        elif tipo == "marmol":
            # Simular textura de mármol
            base = np.zeros((self.alto_fondo, self.ancho_fondo, 3), dtype=np.uint8)
            base[:, :] = color_base
            
            for _ in range(int(5 * intensidad)):
                x = random.randint(0, self.ancho_fondo)
                y = random.randint(0, self.alto_fondo)
                radio = random.randint(50, 200)
                color = (color_base[0] + random.randint(-50, 50),
                         color_base[1] + random.randint(-50, 50),
                         color_base[2] + random.randint(-50, 50))
                
                cv2.circle(base, (x, y), radio, color, -1)
            
            # Aplicar desenfoque gaussiano
            base = cv2.GaussianBlur(base, (0, 0), 10 * intensidad)
            fondo = Image.fromarray(base)
        
        return fondo
    
    def _crear_fondo_bokeh(self, color_fondo, num_puntos, tamano_max):
        """Crear un fondo con efecto bokeh (puntos de luz desenfocados)"""
        fondo = Image.new('RGB', (self.ancho_fondo, self.alto_fondo), color_fondo)
        draw = ImageDraw.Draw(fondo)
        
        for _ in range(num_puntos):
            x = random.randint(0, self.ancho_fondo)
            y = random.randint(0, self.alto_fondo)
            tamano = random.randint(5, tamano_max)
            
            # Color aleatorio con tonos brillantes
            r = random.randint(150, 255)
            g = random.randint(150, 255)
            b = random.randint(150, 255)
            alpha = random.randint(100, 200)
            
            # Crear una imagen para el punto de luz
            punto = Image.new('RGBA', (tamano * 2, tamano * 2), (0, 0, 0, 0))
            punto_draw = ImageDraw.Draw(punto)
            
            # Dibujar un círculo con transparencia
            punto_draw.ellipse([(0, 0), (tamano * 2, tamano * 2)], 
                              fill=(r, g, b, alpha))
            
            # Pegar el punto en el fondo
            fondo.paste(punto, (x - tamano, y - tamano), punto)
        
        # Aplicar desenfoque para simular efecto bokeh
        fondo = fondo.filter(ImageFilter.GaussianBlur(radius=tamano_max // 5))
        return fondo
    
    def _crear_fondo_geometrico(self, color_fondo, color_lineas, tipo, espaciado, grosor):
        """Crear un fondo con patrón geométrico"""
        fondo = Image.new('RGB', (self.ancho_fondo, self.alto_fondo), color_fondo)
        draw = ImageDraw.Draw(fondo)
        
        if tipo == "cuadricula":
            # Dibujar cuadrícula
            for x in range(0, self.ancho_fondo, espaciado):
                draw.line([(x, 0), (x, self.alto_fondo)], fill=color_lineas, width=grosor)
            
            for y in range(0, self.alto_fondo, espaciado):
                draw.line([(0, y), (self.ancho_fondo, y)], fill=color_lineas, width=grosor)
        
        elif tipo == "triangulos":
            # Dibujar triángulos
            altura = int(espaciado * (3**0.5) / 2)
            
            for y in range(0, self.alto_fondo + altura, altura):
                for x in range(0, self.ancho_fondo + espaciado, espaciado):
                    # Triángulo apuntando hacia arriba
                    puntos = [
                        (x, y),
                        (x + espaciado // 2, y - altura),
                        (x + espaciado, y)
                    ]
                    draw.polygon(puntos, outline=color_lineas, width=grosor)
                    
                    # Triángulo apuntando hacia abajo
                    puntos = [
                        (x, y),
                        (x + espaciado // 2, y + altura),
                        (x + espaciado, y)
                    ]
                    draw.polygon(puntos, outline=color_lineas, width=grosor)
        
        elif tipo == "hexagonos":
            # Dibujar hexágonos
            ancho_hex = espaciado
            alto_hex = int(ancho_hex * (3**0.5) / 2)
            
            for y in range(0, self.alto_fondo + alto_hex, int(alto_hex * 1.5)):
                for x in range(0, self.ancho_fondo + ancho_hex, int(ancho_hex * 1.5)):
                    # Hexágono
                    puntos = [
                        (x + ancho_hex // 2, y),
                        (x + ancho_hex, y + alto_hex // 2),
                        (x + ancho_hex, y + alto_hex),
                        (x + ancho_hex // 2, y + alto_hex + alto_hex // 2),
                        (x, y + alto_hex),
                        (x, y + alto_hex // 2)
                    ]
                    draw.polygon(puntos, outline=color_lineas, width=grosor)
        
        return fondo
    
    def _combinar_imagen_con_fondo(self, imagen, fondo):
        """Combinar la imagen sin fondo con el fondo generado"""
        # Redimensionar el fondo si es necesario
        if fondo.size != (self.ancho_fondo, self.alto_fondo):
            fondo = fondo.resize((self.ancho_fondo, self.alto_fondo), Image.LANCZOS)
        
        # Redimensionar la imagen sin fondo para que encaje bien en el fondo
        img_ancho, img_alto = imagen.size
        ratio = min((self.ancho_fondo * 0.8) / img_ancho, (self.alto_fondo * 0.8) / img_alto)
        nueva_img_ancho = int(img_ancho * ratio)
        nueva_img_alto = int(img_alto * ratio)
        imagen = imagen.resize((nueva_img_ancho, nueva_img_alto), Image.LANCZOS)
        
        # Crear una copia del fondo para no modificarlo directamente
        resultado = fondo.copy()
        
        # Pegar la imagen en el centro del fondo
        pos_x = (self.ancho_fondo - nueva_img_ancho) // 2
        pos_y = (self.alto_fondo - nueva_img_alto) // 2
        resultado.paste(imagen, (pos_x, pos_y), imagen)
        
        return resultado
    
    def _mostrar_imagen(self, imagen):
        """Mostrar una imagen en el canvas"""
        # Limpiar canvas y lista de referencias a imágenes
        self.canvas.delete("all")
        self.tk_images.clear()
        
        # Redimensionar la imagen para que quepa en el canvas
        canvas_ancho = self.canvas.winfo_width()
        canvas_alto = self.canvas.winfo_height()
        
        if canvas_ancho <= 1 or canvas_alto <= 1:
            canvas_ancho = 800
            canvas_alto = 600
        
        img_ancho, img_alto = imagen.size
        ratio = min(canvas_ancho / img_ancho, canvas_alto / img_alto)
        nueva_img_ancho = int(img_ancho * ratio)
        nueva_img_alto = int(img_alto * ratio)
        
        imagen = imagen.resize((nueva_img_ancho, nueva_img_alto), Image.LANCZOS)
        
        # Convertir a formato Tkinter
        tk_img = ImageTk.PhotoImage(imagen)
        self.tk_images.append(tk_img)  # Mantener referencia
        
        # Mostrar la imagen en el canvas
        self.canvas.create_image(
            canvas_ancho // 2,
            canvas_alto // 2,
            anchor=tk.CENTER,
            image=tk_img
        )
        
        # Configurar el área de desplazamiento
        self.canvas.config(scrollregion=(0, 0, nueva_img_ancho, nueva_img_alto))
    
    def _guardar_resultado(self):
        """Guardar el resultado combinado o el fondo actual"""
        if self.resultado_combinado:
            imagen_a_guardar = self.resultado_combinado
        elif self.fondo_actual:
            imagen_a_guardar = self.fondo_actual
        else:
            messagebox.showwarning("Advertencia", "No hay nada que guardar")
            return
        
        ruta_archivo = filedialog.asksaveasfilename(
            title="Guardar Imagen",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg *.jpeg"), ("Todos los archivos", "*.*")]
        )
        
        if ruta_archivo:
            try:
                imagen_a_guardar.save(ruta_archivo)
                messagebox.showinfo("Éxito", f"Imagen guardada en:\n{ruta_archivo}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar la imagen: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = GeneradorFondosGUI(root)
    root.mainloop()
