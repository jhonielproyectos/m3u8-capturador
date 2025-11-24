from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import os

app = Flask(__name__)

def capturar_m3u8(url_video):
    """Configura y ejecuta Selenium para capturar el M3U8."""
    
    # --- Configuración del Headless Chrome para Render ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")         # No se muestra la interfaz gráfica
    chrome_options.add_argument("--no-sandbox")       # Requerido para entornos de servidor (Render)
    chrome_options.add_argument("--disable-dev-shm-usage") # Evita problemas de memoria compartida
    
    # Habilitar logging de rendimiento para capturar peticiones de red (M3U8)
    chrome_options.add_experimental_option('w3c', False)
    chrome_options.add_experimental_option('perfLoggingPrefs', {
        'enableNetwork': True,
        'enablePage': False,
    })
    
    # Render ya tiene Chrome instalado en una ruta predefinida, 
    # pero a veces necesita que se le especifique la ruta del binario.
    # Si da error, Render te dirá la ruta correcta.
    # driver = webdriver.Chrome(options=chrome_options) 
    
    try:
        # Intenta inicializar sin especificar la ruta del ejecutable (lo normal en Render)
        driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        # En caso de error, puedes intentar con la ruta del binario de Chrome que proporciona Render
        # chrome_options.binary_location = "/usr/bin/google-chrome" # Ruta común en Render
        # driver = webdriver.Chrome(options=chrome_options)
        print(f"Error al iniciar el driver: {e}")
        return None

    enlace_m3u8_capturado = None
    
    try:
        driver.get(url_video)
        # Espera un poco para que el video empiece a cargar y el M3U8 aparezca
        import time
        time.sleep(10)
        
        logs = driver.get_log('performance')
        
        for log in logs:
            if 'message' in log:
                message = log['message']
                if '.m3u8' in message:
                    entry = json.loads(message)['message']['params']
                    if entry.get('method') == 'Network.responseReceived':
                        url = entry['response']['url']
                        if '.m3u8' in url:
                            enlace_m3u8_capturado = url
                            break
                            
    except Exception as e:
        print(f"Error durante la navegación: {e}")
        
    finally:
        driver.quit()
        
    return enlace_m3u8_capturado


@app.route('/capturar', methods=['GET'])
def api_capturar():
    """Endpoint para iniciar la captura de M3U8."""
    
    # URL de ejemplo que quieres analizar (la que proporcionaste)
    url_a_analizar = "https://ico3c.com/bkg/1vd4knukxrnu" 
    
    m3u8_encontrado = capturar_m3u8(url_a_analizar)
    
    if m3u8_encontrado:
        # Devuelve el resultado como JSON
        return jsonify({
            "status": "success",
            "enlace_m3u8": m3u8_encontrado,
            "analizada": url_a_analizar
        })
    else:
        # Si no se encuentra
        return jsonify({
            "status": "error",
            "mensaje": "No se pudo encontrar un enlace .m3u8 en el tráfico de red.",
            "analizada": url_a_analizar
        }), 404

# Asegúrate de que Gunicorn ejecute esto cuando se use Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)