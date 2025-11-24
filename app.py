# Importaciones necesarias (asegúrate de que estén al inicio de app.py)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service # ¡NUEVA IMPORTACIÓN!
# ... (otras importaciones) ...

# ...

def capturar_m3u8(url_video):
    """Configura y ejecuta Selenium, simula el clic en el reproductor y captura el M3U8 con parámetros."""
    
    # --- Configuración del Headless Chrome para Render ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")       
    chrome_options.add_argument("--disable-dev-shm-usage") 
    chrome_options.add_argument("--disable-gpu")
    
    # Habilitar logging (igual)
    chrome_options.add_experimental_option('w3c', False)
    chrome_options.add_experimental_option('perfLoggingPrefs', {
        'enableNetwork': True,
        'enablePage': False,
    })
    
    # -----------------------------------------------------------
    # *** SOLUCIÓN AL ERROR DE DRIVER_LOCATION ***
    # -----------------------------------------------------------
    
    # 1. Definir la ubicación del ejecutable de Chrome en Render (Ruta común en Linux)
    CHROME_BIN_PATH = "/usr/bin/google-chrome"
    
    # 2. Asignar la ubicación del binario a las opciones
    chrome_options.binary_location = CHROME_BIN_PATH
    
    # 3. Intentar inicializar el Driver usando el Service
    driver = None
    
    try:
        # Nota: En entornos de servidor, a menudo el servicio y el controlador
        # se encuentran en /usr/bin. No siempre necesitas especificar el ChromeDriver.
        # Intentaremos usar el driver por defecto que está junto al binario de Chrome.
        driver = webdriver.Chrome(options=chrome_options)
        print("✅ WebDriver inicializado correctamente usando la ruta binaria.")
        
    except Exception as e:
        print(f"❌ Error CRÍTICO al inicializar el driver: {e}")
        return None # Detener la ejecución si el driver no se inicializa
    
    enlace_m3u8_capturado = None
    
    # --- CONTINUAR CON EL PROCESO DE CARGA Y CLIC (El resto de la función sigue igual) ---
    
    try:
        # ... (Mantener la lógica de driver.get(url_video), simulación de clic, time.sleep(12),
        # y la captura de logs con el filtro estricto por 'master.m3u8' y parámetros) ...
        
        driver.get(url_video)
        
        # Espera inicial para que el HTML se cargue
        time.sleep(5) 
        
        # *** SIMULACIÓN DE CLIC ***
        try:
            video_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "video"))
            )
            video_element.click()
            print("Clic simulado en el elemento <video>.")
            
        except Exception as e:
            print(f"No se encontró el elemento <video> o el clic falló: {e}. Intentando clic en <body>.")
            driver.find_element(By.TAG_NAME, 'body').click()
            
        
        # Espera para que el stream se active después del clic
        print("Esperando 12 segundos para la activación del stream después del clic...")
        time.sleep(12) 
        
        # --- Captura de Logs ---
        logs = driver.get_log('performance')
        # ... (Resto del bucle de logs y filtrado) ...
        
        for log in logs:
            if 'message' in log:
                message = log['message']
                
                # Filtro Estricto: Buscamos master.m3u8 Y los parámetros de seguridad
                if 'master.m3u8' in message:
                    try:
                        entry = json.loads(message)['message']['params']
                        if entry.get('method') == 'Network.responseReceived':
                            url = entry['response']['url']
                            
                            if 'master.m3u8' in url and ('?t=' in url or '&s=' in url): 
                                enlace_m3u8_capturado = url
                                print(f"¡M3U8 con parámetros capturado!: {enlace_m3u8_capturado}")
                                break
                    except Exception:
                        continue
                            
    except Exception as e:
        print(f"❌ Error durante la navegación o procesamiento: {e}") # Error de navegación o procesamiento, no de inicialización
        
    finally:
        if driver:
            driver.quit()
        
    return enlace_m3u8_capturado

# ... (Mantener el resto de la app.py sin cambios: api_capturar, home, __main__) ...
