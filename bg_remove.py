import streamlit as st
from rembg import remove
from PIL import Image
import numpy as np
from io import BytesIO
import base64
import os
import traceback
import time

st.set_page_config(layout="wide", page_title="Eliminador de Fondos")

st.write("## Elimina el fondo de tu imagen")
st.write(
    ":dog: Intenta subir una imagen para ver cómo se elimina el fondo automáticamente. Las imágenes en calidad completa se pueden descargar desde la barra lateral. Este código es de código abierto y está disponible [aquí](https://github.com/tyler-simons/BackgroundRemoval) en GitHub. Gracias especiales a la [librería rembg](https://github.com/danielgatis/rembg) :grin:"
)
st.sidebar.write("## Subir y descargar :gear:")

# Límite de tamaño de archivo
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Dimensiones máximas para procesamiento
MAX_IMAGE_SIZE = 2000  # píxeles

# Convertir imagen para descargar
def convert_image(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    byte_im = buf.getvalue()
    return byte_im

# Redimensionar imagen manteniendo proporción
def resize_image(image, max_size):
    width, height = image.size
    if width <= max_size and height <= max_size:
        return image

    if width > height:
        new_width = max_size
        new_height = int(height * (max_size / width))
    else:
        new_height = max_size
        new_width = int(width * (max_size / height))

    return image.resize((new_width, new_height), Image.LANCZOS)

@st.cache_data
def process_image(image_bytes):
    """Procesa la imagen con caché para evitar procesamiento redundante"""
    try:
        image = Image.open(BytesIO(image_bytes))
        resized = resize_image(image, MAX_IMAGE_SIZE)
        fixed = remove(resized)
        return image, fixed
    except Exception as e:
        st.error(f"Error al procesar la imagen: {str(e)}")
        return None, None

def fix_image(upload):
    try:
        start_time = time.time()
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()

        status_text.text("Cargando imagen...")
        progress_bar.progress(10)

        # Leer bytes de la imagen
        if isinstance(upload, str):
            # Ruta de imagen predeterminada
            if not os.path.exists(upload):
                st.error(f"Imagen no encontrada en la ruta: {upload}")
                return
            with open(upload, "rb") as f:
                image_bytes = f.read()
        else:
            # Archivo subido
            image_bytes = upload.getvalue()

        status_text.text("Procesando imagen...")
        progress_bar.progress(30)

        # Procesar imagen (usando caché si está disponible)
        image, fixed = process_image(image_bytes)
        if image is None or fixed is None:
            return

        progress_bar.progress(80)
        status_text.text("Mostrando resultados...")

        # Mostrar imágenes
        col1.write("Imagen Original :camera:")
        col1.image(image)

        col2.write("Imagen Procesada :wrench:")
        col2.image(fixed)

        # Botón de descarga
        st.sidebar.markdown("\n")
        st.sidebar.download_button(
            "Descargar imagen procesada",
            convert_image(fixed),
            "imagen_sin_fondo.png",
            "image/png"
        )

        progress_bar.progress(100)
        processing_time = time.time() - start_time
        status_text.text(f"Completado en {processing_time:.2f} segundos")

    except Exception as e:
        st.error(f"Ocurrió un error: {str(e)}")
        st.sidebar.error("Error al procesar la imagen")
        print(f"Error en fix_image: {traceback.format_exc()}")

# Diseño de interfaz
col1, col2 = st.columns(2)
my_upload = st.sidebar.file_uploader("Subir una imagen", type=["png", "jpg", "jpeg"])

# Información sobre limitaciones
with st.sidebar.expander("ℹ️ Guía de Imágenes"):
    st.write("""
    - Tamaño máximo de archivo: 10MB
    - Las imágenes grandes se redimensionarán automáticamente
    - Formatos soportados: PNG, JPG, JPEG
    - El tiempo de procesamiento depende del tamaño de la imagen
    """)

# Procesar la imagen
if my_upload is not None:
    if my_upload.size > MAX_FILE_SIZE:
        st.error(f"El archivo subido es demasiado grande. Por favor, sube una imagen menor a {MAX_FILE_SIZE/1024/1024:.1f}MB.")
    else:
        fix_image(upload=my_upload)
else:
    # Intentar imágenes predeterminadas
    default_images = ["./zebra.jpg", "./wallaby.png"]
    for img_path in default_images:
        if os.path.exists(img_path):
            fix_image(img_path)
            break
    else:
        st.info("¡Por favor, sube una imagen para comenzar!")
