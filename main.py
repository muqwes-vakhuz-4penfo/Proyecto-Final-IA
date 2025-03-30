import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torchvision.models.segmentation import deeplabv3_resnet50
from diffusers import StableDiffusionInpaintPipeline
from PIL import Image, ImageOps, ImageFilter
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
from io import BytesIO
import cv2  # Added for better mask processing
from skimage import morphology

class BackgroundGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador de Fondos con IA - Versión Mejorada")
        
        # Cargar modelos
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.load_models()
        
        # Interfaz gráfica
        self.create_widgets()
        
    def load_models(self):
        """Carga los modelos de segmentación y generación"""
        # Modelo para segmentación de personas (pre-entrenado)
        self.seg_model = deeplabv3_resnet50(pretrained=True)
        self.seg_model = self.seg_model.to(self.device)
        self.seg_model.eval()
        
        # Modelo para generación de fondos (Stable Diffusion)
        self.sd_pipe = StableDiffusionInpaintPipeline.from_pretrained(
            "stabilityai/stable-diffusion-2-inpainting",
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        ).to(self.device)
        
        # Transformaciones para la imagen
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
    
    def create_widgets(self):
        """Crea los elementos de la interfaz gráfica"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Botón para cargar imagen
        ttk.Button(main_frame, text="Cargar Imagen", command=self.load_image).grid(row=0, column=0, pady=5, sticky=tk.W)
        
        # Entrada para el prompt
        ttk.Label(main_frame, text="Descripción del fondo:").grid(row=1, column=0, pady=5, sticky=tk.W)
        self.prompt_entry = ttk.Entry(main_frame, width=50)
        self.prompt_entry.grid(row=2, column=0, pady=5, sticky=tk.W)
        self.prompt_entry.insert(0, "fondo profesional, oficina moderna, luz natural")
        
        # Botón para generar
        ttk.Button(main_frame, text="Generar Fondo", command=self.generate_background).grid(row=3, column=0, pady=10, sticky=tk.W)
        
        # Área para mostrar imágenes
        self.image_frame = ttk.Frame(main_frame)
        self.image_frame.grid(row=4, column=0, pady=10)
        
        # Labels para imágenes original y resultado
        self.original_label = ttk.Label(self.image_frame, text="Imagen Original")
        self.original_label.grid(row=0, column=0, padx=5)
        
        self.result_label = ttk.Label(self.image_frame, text="Resultado")
        self.result_label.grid(row=0, column=1, padx=5)
        
        # Canvas para imágenes
        self.original_canvas = tk.Canvas(self.image_frame, width=300, height=400)
        self.original_canvas.grid(row=1, column=0, padx=5)
        
        self.result_canvas = tk.Canvas(self.image_frame, width=300, height=400)
        self.result_canvas.grid(row=1, column=1, padx=5)
        
        # Barra de progreso
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
        self.progress.grid(row=5, column=0, pady=10)
        
        # Estado
        self.status_var = tk.StringVar()
        self.status_var.set("Listo")
        ttk.Label(main_frame, textvariable=self.status_var).grid(row=6, column=0, pady=5, sticky=tk.W)
        
    def load_image(self):
        """Carga la imagen original"""
        file_path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            self.original_image = Image.open(file_path).convert("RGB")
            self.display_image(self.original_image, self.original_canvas)
            self.status_var.set(f"Imagen cargada: {file_path}")
    
    def segment_person(self, image):
        """Segmenta a la persona/objeto principal de la imagen con mejoras"""
        # Preprocesamiento
        input_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # Predicción
        with torch.no_grad():
            output = self.seg_model(input_tensor)['out'][0]
        output = output.argmax(0)
        
        # Máscara mejorada: persona (15) + otros objetos relevantes
        mask = (output == 15).cpu().numpy()  # Persona
        mask |= (output == 12).cpu().numpy()  # Otros objetos importantes
        mask = mask.astype(np.uint8)
        
        # Mejorar la máscara
        mask = self.refine_mask(mask)
        
        return mask
    
    def refine_mask(self, mask):
        """Mejora la máscara con operaciones morfológicas más robustas"""
        # Convertir a formato OpenCV
        mask = mask.astype(np.uint8) * 255
        
        # Operaciones morfológicas
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Suavizado de bordes
        mask = cv2.GaussianBlur(mask, (5,5), 0)
        
        # Umbralizar después del suavizado
        _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        
        return mask > 0
    
    def generate_background(self):
        """Genera el fondo basado en el prompt con mejoras en el recorte"""
        if not hasattr(self, 'original_image'):
            self.status_var.set("Error: Primero carga una imagen")
            return
            
        prompt = self.prompt_entry.get()
        if not prompt:
            self.status_var.set("Error: Ingresa una descripción para el fondo")
            return
            
        self.status_var.set("Procesando...")
        self.progress['value'] = 20
        self.root.update_idletasks()
        
        try:
            # Paso 1: Segmentar persona/objeto con mejoras
            mask = self.segment_person(self.original_image)
            mask_image = Image.fromarray((mask * 255).astype(np.uint8))
            
            # Mejorar la máscara con un filtro Gaussiano para bordes más suaves
            mask_image = mask_image.filter(ImageFilter.GaussianBlur(2))
            
            # Guardar máscara para depuración (opcional)
            # mask_image.save("debug_mask.png")
            
            # Invertir máscara para el inpainting (queremos reemplazar el fondo)
            inverted_mask = ImageOps.invert(mask_image)
            
            self.progress['value'] = 40
            self.root.update_idletasks()
            
            # Paso 2: Generar nuevo fondo
            # Redimensionar para Stable Diffusion (múltiplos de 64)
            width, height = self.original_image.size
            new_width = (width // 64) * 64
            new_height = (height // 64) * 64
            
            input_image = self.original_image.resize((new_width, new_height))
            input_mask = inverted_mask.resize((new_width, new_height))
            
            generated_image = self.sd_pipe(
                prompt=prompt,
                image=input_image,
                mask_image=input_mask,
                width=new_width,
                height=new_height,
                num_inference_steps=30,
                guidance_scale=7.5
            ).images[0]
            
            self.progress['value'] = 70
            self.root.update_idletasks()
            
            # Paso 3: Combinar persona con nuevo fondo (versión mejorada)
            # Redimensionar a tamaño original
            generated_image = generated_image.resize(self.original_image.size)
            mask_image = mask_image.resize(self.original_image.size, Image.NEAREST)
            
            # Convertir a arrays numpy para mejor control
            original_array = np.array(self.original_image)
            generated_array = np.array(generated_image)
            mask_array = np.array(mask_image) > 128  # Binarizar la máscara
            
            # Combinar las imágenes usando la máscara
            result_array = np.where(
                np.repeat(mask_array[:, :, np.newaxis], 3, axis=2),
                original_array,
                generated_array
            )
            
            # Convertir de vuelta a imagen PIL
            result_image = Image.fromarray(result_array.astype(np.uint8))
            
            self.progress['value'] = 90
            self.root.update_idletasks()
            
            # Mostrar resultado
            self.display_image(result_image, self.result_canvas)
            self.result_image = result_image
            
            self.progress['value'] = 100
            self.status_var.set("¡Fondo generado con éxito!")
            
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.progress['value'] = 0
    
    def display_image(self, image, canvas):
        """Muestra una imagen en un canvas de Tkinter"""
        # Redimensionar para mostrar
        display_width = 300
        display_height = int(display_width * image.height / image.width)
        if display_height > 400:
            display_height = 400
            display_width = int(display_height * image.width / image.height)
            
        display_image = image.resize((display_width, display_height))
        
        # Convertir a formato Tkinter
        with BytesIO() as output:
            display_image.save(output, format="PNG")
            img_data = output.getvalue()
            
        tk_image = tk.PhotoImage(data=img_data)
        canvas.image = tk_image  # Guardar referencia
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_image)
        canvas.config(width=display_width, height=display_height)

if __name__ == "__main__":
    root = tk.Tk()
    app = BackgroundGeneratorApp(root)
    root.mainloop()