# Aplicación para Eliminar Fondos

Una aplicación Streamlit que permite a los usuarios subir imágenes y remover automáticamente sus fondos usando la librería [rembg](https://github.com/danielgatis/rembg).

## Características

- Subir imágenes (formatos PNG, JPG, JPEG soportados)
- Eliminación automática de fondo
- Descargar la imagen procesada
- Maneja imágenes grandes con redimensionamiento automático
- Indicadores de progreso para mejor experiencia del usuario

## Comenzar

### Requisitos Previos

- Python 3.8+
- pip

### Instalación

1. Clonar el repositorio
```bash
git clone https://github.com/puchiamdp-a11y/EliminaFondo.git
cd EliminaFondo
```

2. Crear un entorno virtual (opcional pero recomendado)
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### Ejecutar la Aplicación

```bash
streamlit run bg_remove.py
```

La aplicación estará disponible en http://localhost:8501 en tu navegador web.

## Guía de Uso

- Tamaño máximo de archivo: 10MB
- Las imágenes grandes se redimensionarán automáticamente para procesarse
- Formatos soportados: PNG, JPG, JPEG

## Licencia

MIT
