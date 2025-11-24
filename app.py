from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time
import os

# --- INICIALIZACIÓN DE FLASK ---
app = Flask(__name__)

# URL a la que el script de Selenium navegará para buscar el stream
URL_A_ANALIZAR = "https://ico3c.com/bkg/1vd4knukxrnu" 

def capturar_m3u8(url_video):
    """
    Configura y ejecuta el navegador Headless Chrome (Selenium) para:
    1. Cargar la página del video.
    2. Simular un clic para iniciar la reproducción.
    3. Analizar los logs de red en busca del enlace M3U8 con parámetros de seguridad.
    """
    
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
    
    # --- SOLUCIÓN AL ERROR DE DRIVER_LOCATION EN RENDER ---
    # Render no siempre configura el PATH automáticamente. Especificamos la ubicación del binario.
    CHROME_BIN_PATH = "/usr/bin/google-chrome"
    chrome_options.binary_location = CHROME_BIN_PATH
    
    driver = None
    enlace_m3u8_capturado = None
    
    try:
        # Inicialización del Driver
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver inicializado correctamente usando la ruta binaria.")

        # --- Proceso de Carga y Clic ---
        print(f"Cargando la página: {url_video}")
        driver.get(url_video)
        
        # Espera inicial para que el HTML se cargue
        time.sleep(5) 
        
        # *** SIMULACIÓN DE CLIC PARA INICIAR EL STREAM ***
        try:
            # Esperar a que el elemento <video> esté presente y simular clic
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            video_element.click()
            print("Clic simulado en el elemento <video>.")
            
        except Exception:
            # Fallback: si no encontramos el video, hacemos clic en el body
            driver.find_element(By.TAG_NAME, 'body').click()
            
        
        # Espera para que el stream se active y se generen los logs de red
        print("Esperando 12 segundos para la activación del stream después del clic...")
        time.sleep(12) 
        
        # --- Captura y Filtrado de Logs ---
        logs = driver.get_log('performance')
        
        for log in logs:
            if 'message' in log:
                message = log['message']
                
                # Filtro Amplio por el nombre del archivo
                if 'master.m3u8' in message:
                    try:
                        entry = json.loads(message)['message']['params']
                        # Aseguramos que sea una respuesta de red
                        if entry.get('method') == 'Network.responseReceived':
                            url = entry['response']['url']
                            
                            # Filtro Estricto: Debe contener 'master.m3u8' Y el token '?t=' o la firma '&s='
                            if 'master.m3u8' in url and ('?t=' in url or '&s=' in url): 
                                enlace_m3u8_capturado = url
                                print(f"¡M3U8 con parámetros capturado!: {enlace_m3u8_capturado}")
                                break
                    except Exception:
                        # Ignorar logs que no son JSON válidos
                        continue
                            
    except Exception as e:
        # Error durante la navegación o procesamiento, no de inicialización
        print(f"❌ Error durante la navegación o procesamiento: {e}") 
        
    finally:
        if driver:
            driver.quit()
        
    return enlace_m3u8_capturado


@app.route('/capturar', methods=['GET'])
def api_capturar():
    """Endpoint principal para iniciar la función de captura."""
    
    m3u8_encontrado = capturar_m3u8(URL_A_ANALIZAR)
    
    if m3u8_encontrado:
        return jsonify({
            "status": "success",
            "enlace_m3u8": m3u8_encontrado,
            "analizada": URL_A_ANALIZAR
        })
    else:
        # Si no se encuentra, devuelve un código 404 personalizado.
        return jsonify({
            "status": "error",
            "mensaje": f"No se pudo encontrar el enlace 'master.m3u8?t=...' en el tráfico de red de {URL_A_ANALIZAR}. Revisa los logs de Render para errores de WebDriver.",
            "analizada": URL_A_ANALIZAR
        }), 404

@app.route('/', methods=['GET'])
def home():
    """Ruta raíz informativa para evitar el 404 inicial."""
    return jsonify({
        "service": "M3U8 Capturador de Render",
        "instructions": f"Para iniciar la captura del enlace, visita la ruta /capturar",
        "target_url": URL_A_ANALIZAR
    })

# Punto de entrada principal, usado por Gunicorn en producción
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # NOTA: Gunicorn manejará esto en Render. Esta parte es para pruebas locales.
    app.run(host='0.0.0.0', port=port)
