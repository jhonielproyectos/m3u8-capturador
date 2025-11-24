from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import time
import os

app = Flask(__name__)

# URL que quieres analizar para capturar el M3U8
URL_A_ANALIZAR = "https://ico3c.com/bkg/1vd4knukxrnu" 

def capturar_m3u8(url_video):
    """Configura y ejecuta Selenium para capturar el M3U8."""
    
    # --- Configuración del Headless Chrome para Render ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")       
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-gpu")
    
    # Habilitar logging de rendimiento para capturar peticiones de red (M3U8)
    chrome_options.add_experimental_option('w3c', False)
    chrome_options.add_experimental_option('perfLoggingPrefs', {
        'enableNetwork': True,
        'enablePage': False,
    })
    
    driver = None
    enlace_m3u8_capturado = None
    
    try:
        # Intenta inicializar el WebDriver.
        # En Render, a veces es necesario especificar la ubicación del binario de Chrome.
        try:
            # Intento 1: Inicialización estándar (usando el PATH)
            driver = webdriver.Chrome(options=chrome_options)
        except Exception as e:
            print(f"Error en Intento 1: {e}. Intentando con la ruta binaria común de Render.")
            
            # Intento 2: Especificar la ruta binaria de Chrome para entornos Linux/Render
            chrome_options.binary_location = "/usr/bin/google-chrome"
            driver = webdriver.Chrome(options=chrome_options)

        # --- Proceso de Captura ---
        driver.get(url_video)
        
        # Tiempo de espera crucial para que el video inicie la reproducción y el M3U8 aparezca
        print("Esperando 10 segundos para la carga del stream...")
        time.sleep(10)
        
        logs = driver.get_log('performance')
        
        for log in logs:
            if 'message' in log:
                message = log['message']
                # Filtra logs que contengan la URL y el patrón M3U8
                if '.m3u8' in message:
                    try:
                        entry = json.loads(message)['message']['params']
                        # Asegúrate de que sea una respuesta de red
                        if entry.get('method') == 'Network.responseReceived':
                            url = entry['response']['url']
                            if '.m3u8' in url:
                                enlace_m3u8_capturado = url
                                print(f"¡M3U8 Capturado!: {enlace_m3u8_capturado}")
                                break
                    except Exception:
                        # Ignorar logs que no son JSON válidos
                        continue
                            
    except Exception as e:
        print(f"❌ Error crítico durante la navegación o inicialización del driver: {e}")
        
    finally:
        if driver:
            driver.quit()
        
    return enlace_m3u8_capturado


@app.route('/capturar', methods=['GET'])
def api_capturar():
    """Endpoint que inicia la función de captura y devuelve el resultado."""
    
    m3u8_encontrado = capturar_m3u8(URL_A_ANALIZAR)
    
    if m3u8_encontrado:
        # Devuelve el resultado como JSON con el código 200 (OK)
        return jsonify({
            "status": "success",
            "enlace_m3u8": m3u8_encontrado,
            "analizada": URL_A_ANALIZAR
        })
    else:
        # Si no se encuentra, devuelve un código 404 personalizado.
        return jsonify({
            "status": "error",
            "mensaje": f"No se pudo encontrar un enlace .m3u8 en el tráfico de red de {URL_A_ANALIZAR}.",
            "analizada": URL_A_ANALIZAR
        }), 404

# Define una ruta raíz simple para evitar el 404 inicial
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "service": "M3U8 Capturador de Render",
        "instructions": f"Para iniciar la captura del enlace, visita la ruta /capturar",
        "target_url": URL_A_ANALIZAR
    })

# Punto de entrada para Gunicorn/Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
