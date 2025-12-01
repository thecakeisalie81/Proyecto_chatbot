# 🏨 Hotel Chatbot - Flask Backend

Un chatbot inteligente para hotel con panel de administrador para gestionar preguntas y respuestas.

## ✨ Características

### Chatbot
- ✅ Comprensión semántica de preguntas usando Sentence Transformers
- ✅ Menú interactivo con categorías de servicios
- ✅ Respuestas contextuales basadas en intents
- ✅ Búsqueda inteligente de respuestas similares
- ✅ Interfaz web moderna y responsive

### Panel de Administrador
- ✅ Crear, editar y eliminar preguntas/respuestas
- ✅ Búsqueda en tiempo real
- ✅ Dashboard con estadísticas
- ✅ Exportar/importar dataset en JSON
- ✅ Interfaz protegida por contraseña
- ✅ Actualizaciones automáticas del modelo

## 📦 Requisitos

- Python 3.7+
- Flask
- Flask-CORS
- Sentence-Transformers
- PyTorch
- JSON (built-in)

## 🚀 Instalación

### 1. Clonar o descargar el proyecto
```bash
cd "ruta/al/proyecto"
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python app.py
```

El servidor estará disponible en: `http://localhost:5000`

## 📖 Uso

### Chatbot Principal
- Accede a: `http://localhost:5000/`
- Selecciona una categoría del menú
- Escribe tus preguntas o selecciona opciones

### Panel de Administrador
- Accede a: `http://localhost:5000/admin-login`
- Contraseña: `admin123` (cambiar en producción)
- Ver: `ADMIN_PANEL_README.md` para instrucciones detalladas

## 📁 Estructura del Proyecto

```
.
├── app.py                    # Aplicación principal Flask
├── chatbot.html              # Página principal del chatbot
├── admin.html                # Panel de administrador
├── admin_login.html          # Página de login
├── dataset.json              # Base de datos Q&A
├── requirements.txt          # Dependencias Python
├── README.md                 # Este archivo
├── ADMIN_PANEL_README.md    # Guía del panel de administrador
├── CSS/                      # Estilos CSS
│   ├── chatbot.css
│   ├── footer.css
│   ├── header.css
│   ├── main.css
│   └── styles.css
├── img/                      # Imágenes
└── video/                    # Videos
```

## 🔌 API Endpoints

### Chat
- **POST** `/chat` - Enviar mensaje al chatbot
  ```json
  {
    "message": "¿Cuáles son las tarifas?",
    "session": "user_session_id"
  }
  ```

### Administrador
- **GET** `/admin-login` - Página de login
- **POST** `/admin-login` - Autenticación
- **GET** `/admin` - Panel de administrador
- **GET** `/admin/stats` - Estadísticas
- **GET** `/admin/items` - Obtener todas las Q&A
- **POST** `/admin/add-item` - Agregar Q&A
- **POST** `/admin/update-item` - Actualizar Q&A
- **POST** `/admin/delete-item` - Eliminar Q&A
- **GET** `/admin/export` - Descargar dataset
- **POST** `/admin/import` - Importar dataset

## 🔐 Seguridad

### Cambiar contraseña del administrador
Edita `app.py` y busca:
```python
ADMIN_PASSWORD = 'admin123'
```

Reemplaza con tu contraseña segura.

## 📊 Formato del Dataset

El archivo `dataset.json` contiene:

```json
[
  {
    "id": "1",
    "question": "¿Cuáles son las tarifas?",
    "response": "Las tarifas varían según la temporada y tipo de habitación...",
    "intent": "reserva_info"
  }
]
```

### Campos:
- `id`: Identificador único
- `question`: Pregunta del usuario
- `response`: Respuesta del chatbot
- `intent`: Categoría (reserva_info, habitacion_info, servicios_info, etc.)

## 🎨 Personalización

### Cambiar colores
Edita los archivos CSS en la carpeta `CSS/`

### Agregar/modificar intents
Edita el diccionario `MAIN_MENU` en `app.py`

### Ajustar sensibilidad del modelo
Modifica el parámetro `threshold` en la función `get_responses()` en `app.py`

## 🐛 Solución de Problemas

### Error: "Módulo no encontrado"
```bash
pip install -r requirements.txt
```

### Error: Puerto 5000 en uso
```bash
# Cambiar puerto en app.py
app.run(debug=True, port=5001)
```

### El modelo tarda mucho en cargar
Es normal la primera vez. El modelo Sentence Transformers se descarga (~80MB) automáticamente.

## 📝 Notas

- El modelo semántico se recarga automáticamente después de cambios en el dataset
- Los cambios en el panel de administrador se guardan inmediatamente
- Se recomienda hacer respaldos periódicos del `dataset.json`

## 📄 Licencia

Proyecto educativo

## 📞 Soporte

Para más información sobre el panel de administrador, consulta `ADMIN_PANEL_README.md`
