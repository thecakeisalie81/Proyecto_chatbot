from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import os
import re
from difflib import SequenceMatcher
import torch
from sentence_transformers import SentenceTransformer, util
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from email.mime.multipart import MIMEMultipart
import psycopg2
from datetime import datetime
import uuid


app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)

@app.route('/')
def home():
    return send_file('chatbot.html')

# Carga del dataset desde archivo JSON

DATA_FILE = os.path.join(os.path.dirname(__file__), 'dataset.json')

def load_dataset():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

DATASET = load_dataset()

def clean_text(text):
    text = text.lower()
    text = re.sub(r'[¿?¡!.,]', '', text)
    return text.strip()


def split_questions(text):
    # Dividir por conectores o signos de puntuación
    parts = re.split(r'\?|y |además|también|,|\.|;', text.lower())
    # Quitar vacíos y limpiar espacios
    return [p.strip() for p in parts if len(p.strip()) > 3]

# ============================================
# Conexion a postgreeSQL
conn = psycopg2.connect(database="Hotel", host='localhost', user="postgres", password="1234", port="5432")
cur = conn.cursor()

# ============================================

# ============================================
# Chatbot semántico (modelo de comprensión)
# ============================================
data = load_dataset()
questions = [clean_text(item["question"]) for item in data]
responses = [item["response"] for item in data]
print("Cargando modelo de comprensión semántica... (esto tarda unos segundos)")
model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
embeddings = model.encode(questions, convert_to_tensor=True)


def get_responses(user_input, threshold=0.5):
    subquestions = split_questions(user_input)
    found_responses = []

    for sub in subquestions:
        sub_clean = clean_text(sub)
        user_emb = model.encode(sub_clean, convert_to_tensor=True)
        similarities = util.cos_sim(user_emb, embeddings)

        best_match_index = int(torch.argmax(similarities))
        best_score = float(similarities[0][best_match_index])

        if best_score >= threshold:
            found_responses.append(responses[best_match_index])

    

    return list(dict.fromkeys(found_responses))

# Menú principal estructurado
MAIN_MENU = {
    "1": {"name": "Reservas y precios", "intent": "reserva_info"},
    "2": {"name": "Habitaciones", "intent": "habitacion_info"},
    "3": {"name": "Servicios del hotel", "intent": "servicios_info"},
    "4": {"name": "Check-in / Check-out", "intent": "checkin_info"},
    "5": {"name": "Ubicación y contacto", "intent": "ubicacion_info"},
    "6": {"name": "Promociones y políticas", "intent": "promociones_info"},
    "7": {"name": "Actividades y alrededores", "intent": "sugerencias"},
    "8": {"name": "Reportar un problema", "intent": "quejas"}
}

# Contexto temporal de usuario (por sesión)
USER_CONTEXT = {}  # { session_id: { "intent": str, "submenu": list } }

# Funciones auxiliares
def show_main_menu():
    menu_text = "🏖️ *Bienvenido al Hotel Paraíso Azul*\n\nSelecciona una opción:\n"
    for key, item in MAIN_MENU.items():
        menu_text += f"{key}. {item['name']}\n"
    menu_text += "\nEscribe el número de la opción o 'salir' para terminar."
    
    return menu_text

def show_submenu(intent):
    items = [it for it in DATASET if it.get('intent') == intent]
    if not items:
        return "No hay información disponible para esta sección."
    submenu_text = f"Has seleccionado '{intent}'. Estas son las opciones disponibles:\n"
    for idx, it in enumerate(items, start=1):
        submenu_text += f"{idx}. {it['question']}\n"
    submenu_text += "\nEscribe el número de la pregunta para ver la respuesta o 'menu' para regresar al inicio."
    return submenu_text

# Lógica principal del chatbot
@app.route('/chat', methods=['POST'])
def chat():
    # Si el usuario está en contexto de contacto directo
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    session_id = data.get('session', 'default')
    msg = user_message.lower()

    context = USER_CONTEXT.get(session_id, {})

    # Si el usuario pide salir
    if msg in ['salir', 'adios', 'gracias']:
        USER_CONTEXT.pop(session_id, None)
        return jsonify({'reply': "👋 ¡Gracias por visitar el Hotel Paraíso Azul! Esperamos verte pronto.", 'source': 'exit'})

    # Si el usuario está en un submenú
    if context.get('submenu'):
        submenu = context['submenu']

        if context.get('intent') == 'reserva_info' and msg.isdigit():
            idx = int(msg) - 1

            if idx == 1:  
                return jsonify({
                    'reply': "Perfecto 😊 Vamos a iniciar tu reserva.",
                    'source': 'formulario_fecha'
                })
        
        if context.get('intent') == 'quejas' and msg.isdigit():
            return jsonify({
                'reply': "Vamos a registrar tu queja.",
                'source': "formulario_queja"
            })


        if msg.isdigit():
            idx = int(msg) - 1
            if 0 <= idx < len(submenu):
                item = submenu[idx]
                return jsonify({'reply': item['response'], 'source': 'submenu'})
            else:
                return jsonify({'reply': "Opción no válida. Intenta de nuevo.", 'source': 'submenu'})
        elif msg in ['menu', 'inicio']:
            USER_CONTEXT.pop(session_id, None)
            return jsonify({'reply': show_main_menu(), 'source': 'menu'})
        else:
            return jsonify({'reply': "Por favor, selecciona un número válido o escribe 'menu' para regresar.", 'source': 'submenu'})

    # Si el usuario saluda o pide el menú
    if msg in ['hola', 'buenos días', 'buenas tardes', 'menu', 'inicio']:
        USER_CONTEXT.pop(session_id, None)
        return jsonify({'reply': show_main_menu(), 'source': 'menu'})

    # Si el usuario está en contexto de contacto directo
    if context.get('intent') == 'contacto_directo':
        if msg in ['sí', 'si', 'claro', 'ok', 'quiero']:
            USER_CONTEXT.pop(session_id, None)
            return jsonify({
                'reply': "Abriendo formulario de contacto...",
                'source': 'formulario',
                'form': '/formulario_contacto'
            })

        elif msg in ['no', 'nah', 'no gracias']:
            # Reinicia el chatbot completamente
            USER_CONTEXT.pop(session_id, None)
            return jsonify({
                'reply': "Entendido 😊. Volviendo al menú principal...\n\n" + show_main_menu(),
                'source': 'menu'
            })

        else:
            return jsonify({
                'reply': "¿Quieres contactar directamente con el personal del hotel? (Responde 'sí' o 'no')",
                'source': 'confirmacion'
            })

    # Detectar si el usuario quiere hacer una reserva
    if any(p in msg for p in ["reservar", "quiero hacer una reserva", "hacer una reserva", "quiero reservar", "reserva"]):
        return jsonify({
            'reply': "Perfecto 😊 Necesito algunos datos para ayudarte con tu reserva.",
            'source': 'formulario_fecha'
    })
    
    # Detectar si el usuario quiere hacer una queja
    if any(p in msg for p in [
        "queja", "quejas", "poner una queja", "hacer una queja",
        "quiero quejarme", "reclamo", "reclamos", "reportar un problema",
        "hacer un reclamo", "reclamar", "reclamación", "problema", "Quiero reportar un problema"
    ]):
        return jsonify({
            'reply': "Perfecto 😟 Necesito algunos datos para ayudarte con tu queja.",
            'source': "formulario_queja"
        })



    # Si elige una opción del menú principal
    if msg in MAIN_MENU:
        intent = MAIN_MENU[msg]['intent']
        items = [it for it in DATASET if it.get('intent') == intent]
        USER_CONTEXT[session_id] = {"intent": intent, "submenu": items}
        reply = show_submenu(intent)
        return jsonify({'reply': reply, 'source': 'submenu'})

    if msg == "8":  
        return jsonify({
            'reply': "Vamos a registrar tu queja.",
            'source': "formulario_queja"
        })


    
   # Si no coincide con ninguna opción, usa el modelo semántico
    semantic_responses = get_responses(user_message)
    if semantic_responses:
        reply_text = "\n".join(semantic_responses)
    
    else:
        USER_CONTEXT[session_id] = {"intent": "contacto_directo"}
        reply_text = "Lo siento, no estoy seguro de entenderte. 😕 ¿Quieres contactar directamente con el personal del hotel? (Responde 'si' o 'no')"
    
    return jsonify({'reply': reply_text, 'source': 'semantic'})



def enviar_correo(nombre, correo, mensaje):
    try:
        # Configuración del servidor SMTP de Gmail
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        remitente = "www.lui81@gmail.com"  
        password = "orcl xqap lsua ikou"  

        # Crear mensaje
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Nuevo mensaje de contacto - {nombre}"
        msg["From"] = remitente
        msg["To"] = "contactohotelparaiso@gmail.com"

        # Cuerpo del correo
        html = f"""
        <html>
          <body>
            <h2>Nuevo mensaje de contacto</h2>
            <p><b>Nombre:</b> {nombre}</p>
            <p><b>Correo:</b> {correo}</p>
            <p><b>Mensaje:</b></p>
            <p>{mensaje}</p>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        # Enviar correo
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(remitente, password)
            server.sendmail(remitente, msg["To"], msg.as_string())

        print("✅ Correo enviado correctamente")
        return True

    except Exception as e:
        print("❌ Error al enviar correo:", e)
        return False


@app.route('/enviar-contacto', methods=['POST'])
def enviar_contacto():
    data = request.get_json()
    nombre = data.get('nombre')
    correo = data.get('correo')
    mensaje = data.get('mensaje')

    if enviar_correo(nombre, correo, mensaje):
        return jsonify({'reply': '✅ Gracias por tu mensaje. El personal del hotel te contactará pronto.'})
    else:
        return jsonify({'reply': '❌ Hubo un problema al enviar tu mensaje. Intenta más tarde.'})

def generar_codigo_ticket():
    try:
        cur.execute("SELECT codigo_ticket FROM tickets ORDER BY id_ticket DESC LIMIT 1")
        row = cur.fetchone()

        if row and row[0]:
            ultimo_num = int(row[0].split('-')[1])
            nuevo_num = ultimo_num + 1
        else:
            nuevo_num = 1

        return f"Res-{nuevo_num:03d}"  
    except Exception as e:
        print("❌ Error generando código:", e)
        return "Res-000"  

def generar_codigo_ticket_queja():
    try:
        cur.execute("SELECT codigo_ticket FROM tickets ORDER BY id_ticket DESC LIMIT 1")
        row = cur.fetchone()

        if row and row[0]:
            ultimo_num = int(row[0].split('-')[1])
            nuevo_num = ultimo_num + 1
        else:
            nuevo_num = 1

        return f"QJ-{nuevo_num:03d}"  
    except Exception as e:
        print("❌ Error generando código:", e)
        return "QJ-000"  

@app.post("/enviar-queja")
def enviar_queja():
    data = request.json
    nombre = data.get("nombre")
    correo = data.get("correo")
    telefono = data.get("telefono")
    motivo = data.get("motivo")

    print("📩 Nueva reserva recibida:")
    print(data)

    codigo = generar_codigo_ticket_queja()   
    estado = "pendiente"
    fecha_creacion = datetime.now()
    try:
        cur.execute("""
            INSERT INTO tickets (
                codigo_ticket, nombre_cliente, telefono_cliente, correo_cliente, estado, fecha_creacion, mensaje
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            codigo, nombre, telefono, correo,
            estado, fecha_creacion, motivo
        ))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print("❌ Error guardando en PostgreSQL:", e)

    # Aquí podrías guardar en DB o enviar correo
    return jsonify({"reply": f"✔ Gracias {nombre}, tu queja fue registrada."})



@app.route('/enviar-fecha', methods=['POST'])
def enviar_fecha():
    data = request.get_json()

    nombre = data.get('nombre')
    correo = data.get('correo')
    numero = data.get('numero')
    fecha_inicio = data.get('fecha_inicio')
    fecha_final = data.get('fecha_final')

    print("📩 Nueva reserva recibida:")
    print(data)

    codigo = generar_codigo_ticket()   
    estado = "pendiente"
    fecha_creacion = datetime.now()

    try:
        cur.execute("""
            INSERT INTO tickets (
                codigo_ticket, nombre_cliente, telefono_cliente, correo_cliente,
                fecha_entrada, fecha_salida, estado, fecha_creacion
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            codigo, nombre, numero, correo,
            fecha_inicio, fecha_final,
            estado, fecha_creacion
        ))
        conn.commit()

    except Exception as e:
        conn.rollback()
        print("❌ Error guardando en PostgreSQL:", e)

    return jsonify({
        'reply': '📅 Tu solicitud de reserva fue enviada correctamente. El personal del hotel te contactará pronto.'
    })



#  Endpoints adicionales opcionales (debug/consulta)
@app.route('/menu', methods=['GET'])
def menu():
    intents = {}
    for item in DATASET:
        intent = item.get('intent', 'general')
        intents[intent] = intents.get(intent, 0) + 1
    menu_list = [{'intent': k, 'count': v} for k, v in intents.items()]
    return jsonify({'menu': menu_list})

@app.route('/menu/<intent>', methods=['GET'])
def menu_intent(intent):
    items = [{'id': it['id'], 'question': it['question']} for it in DATASET if it.get('intent') == intent]
    return jsonify({'intent': intent, 'items': items})

@app.route('/faq/<int:item_id>', methods=['GET'])
def faq(item_id):
    for it in DATASET:
        if int(it.get('id')) == int(item_id):
            return jsonify({'id': it.get('id'), 'question': it.get('question'), 'answer': it.get('response')})
    return jsonify({'error': 'not found'}), 404

# ============================================
# PANEL DE ADMINISTRADOR
# ============================================

ADMIN_PASSWORD = 'admin123'  # Contraseña por defecto
ADMIN_TOKENS = {}  # Token temporal para sesiones

def verify_admin_token(token):
    """Verifica si el token es válido"""
    return token in ADMIN_TOKENS

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'GET':
        return send_file('admin_login.html')
    
    # POST request para login
    data = request.get_json()
    password = data.get('password', '')
    
    if password == ADMIN_PASSWORD:
        # Generar token simple (en producción usar JWT)
        token = os.urandom(16).hex()
        ADMIN_TOKENS[token] = True
        return jsonify({'success': True, 'token': token})
    else:
        return jsonify({'success': False, 'message': 'Contraseña incorrecta'}), 401

@app.route('/admin', methods=['GET'])
def admin_panel():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token or not verify_admin_token(token):
        # Verificar en localStorage desde el navegador
        return send_file('admin.html')
    return send_file('admin.html')

@app.route('/admin/stats', methods=['GET'])
def admin_stats():
    """Retorna estadísticas del dataset"""
    global DATASET
    DATASET = load_dataset()
    
    intents = set(item.get('intent', 'general') for item in DATASET)
    last_modified = os.path.getmtime(DATA_FILE)
    from datetime import datetime
    last_mod_date = datetime.fromtimestamp(last_modified).strftime('%Y-%m-%d %H:%M:%S')
    
    return jsonify({
        'total_items': len(DATASET),
        'unique_intents': len(intents),
        'last_modified': last_mod_date
    })

@app.route('/admin/items', methods=['GET'])
def admin_get_items():
    """Retorna todos los items del dataset"""
    global DATASET
    DATASET = load_dataset()
    return jsonify({'items': DATASET})

@app.route('/admin/add-item', methods=['POST'])
def admin_add_item():
    """Agrega un nuevo item al dataset"""
    global DATASET, embeddings, questions, responses, model
    
    data = request.get_json()
    
    # Validar datos
    if not data.get('id') or not data.get('question') or not data.get('response'):
        return jsonify({'success': False, 'error': 'Faltan campos requeridos'}), 400
    
    # Verificar que el ID sea único
    if any(item['id'] == data['id'] for item in DATASET):
        return jsonify({'success': False, 'error': 'El ID ya existe'}), 400
    
    new_item = {
        'id': data['id'],
        'question': data['question'],
        'response': data['response'],
        'intent': data.get('intent', 'general')
    }
    
    DATASET.append(new_item)
    
    # Guardar cambios
    save_dataset()
    
    # Recargar modelo
    reload_model()
    
    return jsonify({'success': True, 'message': 'Item agregado exitosamente'})

@app.route('/admin/update-item', methods=['POST'])
def admin_update_item():
    """Actualiza un item existente"""
    global DATASET, embeddings, questions, responses, model
    
    data = request.get_json()
    item_id = data.get('id')
    
    # Buscar y actualizar el item
    for item in DATASET:
        if item['id'] == item_id:
            item['question'] = data.get('question', item['question'])
            item['response'] = data.get('response', item['response'])
            item['intent'] = data.get('intent', item.get('intent', 'general'))
            
            # Guardar cambios
            save_dataset()
            
            # Recargar modelo
            reload_model()
            
            return jsonify({'success': True, 'message': 'Item actualizado exitosamente'})
    
    return jsonify({'success': False, 'error': 'Item no encontrado'}), 404

@app.route('/admin/delete-item', methods=['POST'])
def admin_delete_item():
    """Elimina un item del dataset"""
    global DATASET, embeddings, questions, responses, model
    
    data = request.get_json()
    item_id = data.get('id')
    
    # Buscar y eliminar el item
    for i, item in enumerate(DATASET):
        if item['id'] == item_id:
            DATASET.pop(i)
            
            # Guardar cambios
            save_dataset()
            
            # Recargar modelo
            reload_model()
            
            return jsonify({'success': True, 'message': 'Item eliminado exitosamente'})
    
    return jsonify({'success': False, 'error': 'Item no encontrado'}), 404

@app.route('/admin/export', methods=['GET'])
def admin_export():
    """Descarga el archivo dataset.json actual"""
    return send_file(DATA_FILE, as_attachment=True, download_name='dataset.json')

@app.route('/admin/import', methods=['POST'])
def admin_import():
    """Importa un archivo JSON de dataset"""
    global DATASET, embeddings, questions, responses, model
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No se envió archivo'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Archivo vacío'}), 400
    
    if not file.filename.endswith('.json'):
        return jsonify({'success': False, 'error': 'El archivo debe ser JSON'}), 400
    
    try:
        imported_data = json.load(file)
        
        # Validar estructura
        if not isinstance(imported_data, list):
            return jsonify({'success': False, 'error': 'El JSON debe contener una lista de items'}), 400
        
        # Validar que cada item tenga los campos necesarios
        for item in imported_data:
            if not all(key in item for key in ['id', 'question', 'response']):
                return jsonify({'success': False, 'error': 'Items inválidos. Deben tener id, question y response'}), 400
        
        # Reemplazar dataset
        DATASET = imported_data
        save_dataset()
        reload_model()
        
        return jsonify({'success': True, 'message': f'Se importaron {len(imported_data)} items exitosamente'})
    
    except json.JSONDecodeError:
        return jsonify({'success': False, 'error': 'JSON inválido'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def save_dataset():
    """Guarda el dataset en el archivo JSON"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(DATASET, f, ensure_ascii=False, indent=2)

def reload_model():
    """Recarga el dataset después de cambios"""
    global DATASET
    DATASET = load_dataset()
    print("✅ Dataset actualizado después de cambios")

# Ejecución del servidor Flask

if __name__ == '__main__':
    app.run(debug=True)


