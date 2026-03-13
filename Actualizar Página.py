import os
import re
import time
import requests
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- 1. CONFIGURACIÓN DE RUTAS ---
BASE_PATH = os.getcwd() 
VEHICULOS_PATH = "VEHICULOS"
CSV_GENERAL = "registro_completo.csv"
LOG_FILE = "ultimo_registro.txt"

MESES = {'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
         'julio': 7, 'agosto': 8, 'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12}

# --- 2. FUNCIONES DEL SCRAPER (Tus funciones originales) ---

def limpiar_nombre_vehiculo(titulo_sucio):
    nombre = titulo_sucio.replace("Lanzamiento:", "").strip()
    nombre = re.sub(r'\(.*?\)', '', nombre).strip()
    nombre = re.sub(r'\d+[.,]?\d*\s?kwh', '', nombre, flags=re.IGNORECASE).strip()
    return nombre

def extraer_datos_tecnicos(driver, titulo_original):
    try:
        cuerpo = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".post-body, .entry-content")))
        texto_min = cuerpo.text.lower()
        elementos_li = cuerpo.find_elements(By.TAG_NAME, "li")
    except:
        return {k: "N/A" for k in ["Tipo", "Bateria_kWh", "Potencia_CV", "Autonomia_km", "Precio_USD", "Torque_Nm"]}

    specs = {"Tipo": "Compacto", "Bateria_kWh": "N/A", "Potencia_CV": "N/A", "Autonomia_km": "N/A", "Precio_USD": "N/A", "Torque_Nm": "N/A"}

    # BATERÍA
    m_bat = re.search(r'\((\d+[.,]?\d*)\s?kwh\)', titulo_original.lower())
    if m_bat: specs["Bateria_kWh"] = m_bat.group(1).replace(",", ".")
    
    # AUTONOMÍA (Con tus nuevos parámetros)
    patrones_aut = [r'autonomía.*?\s*(\d{2,4})\s*(?:km|kilómetro)', r'(\d{2,4})\s*(?:km|kilómetro)']
    for p in patrones_aut:
        m = re.search(p, texto_min)
        if m: specs["Autonomia_km"] = m.group(1); break

    # PRECIO
    for li in reversed(elementos_li):
        if "u$s" in li.text.lower():
            nums = re.findall(r'\d+', li.text.replace(".", ""))
            for n in nums:
                if len(n) >= 5: specs["Precio_USD"] = n; break
        if specs["Precio_USD"] != "N/A": break

    return specs

def descargar_fotos(driver, folder):
    try:
        all_imgs = driver.find_elements(By.CSS_SELECTOR, ".post-body img, .entry-content img")
        cnt = 0
        for img in all_imgs:
            if cnt >= 4: break
            src = img.get_attribute("src")
            if not src or "http" not in src: continue
            try:
                r = requests.get(src, timeout=10)
                if r.status_code == 200 and len(r.content) > 10000:
                    with open(os.path.join(folder, f"foto_{cnt+1}.jpg"), 'wb') as f:
                        f.write(r.content)
                    cnt += 1
            except: continue
        return cnt
    except: return 0

# --- 3. LÓGICA DE CONTROL DE FECHAS ---

def limpiar_fecha(texto_fecha):
    match = re.search(r'(\d+)\s+de\s+(\w+)\s+de\s+(\d+)', texto_fecha.lower())
    if match:
        return datetime(int(match.group(3)), MESES[match.group(2)], int(match.group(1)))
    return None

# --- 4. EJECUCIÓN PRINCIPAL (EL BOT MAESTRO) ---

opts = Options()
opts.add_argument("--headless=new")
driver = webdriver.Chrome(options=opts)

try:
    print("🔍 Buscando novedades...")
    driver.get("https://www.autoblog.com.uy/search/label/El%C3%A9ctricos")
    time.sleep(3)

    # Leer fecha del último registro
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            ultima_registrada = datetime.strptime(f.read().strip(), "%Y-%m-%d")
    else:
        ultima_registrada = datetime(2026, 3, 12) # Fecha base de inicio

    publicaciones = driver.find_elements(By.CLASS_NAME, "post-outer")
    novedades = []

    for pub in publicaciones:
        titulo_el = pub.find_element(By.CSS_SELECTOR, ".entry-title a")
        fecha_texto = pub.find_element(By.CLASS_NAME, "post-header").text
        fecha_dt = limpiar_fecha(fecha_texto)
        
        if fecha_dt and fecha_dt > ultima_registrada and "Lanzamiento" in titulo_el.text:
            novedades.append((titulo_el.text, titulo_el.get_attribute("href"), fecha_dt))

    if not novedades:
        print("✅ Todo actualizado.")
    else:
        print(f"🆕 ¡Hay {len(novedades)} lanzamientos nuevos! Procesando...")
        
        # Procesar de más antiguo a más nuevo
        for titulo, url, f_dt in reversed(novedades):
            print(f"📦 Descargando: {titulo}")
            driver.get(url)
            
            nombre_limpio = limpiar_nombre_vehiculo(titulo)
            datos = extraer_datos_tecnicos(driver, titulo)
            datos.update({"Vehículo": nombre_limpio, "Link": url})
            
            # Crear carpeta
            folder_slug = "".join(c for c in nombre_limpio if c.isalnum() or c == ' ').strip().replace(" ", "_").upper()[:30]
            car_folder = os.path.join(VEHICULOS_PATH, folder_slug)
            os.makedirs(car_folder, exist_ok=True)
            
            # Guardar CSV individual y fotos
            pd.DataFrame([datos]).to_csv(os.path.join(car_folder, "datos.csv"), index=False, encoding='utf-8-sig')
            descargar_fotos(driver, car_folder)
            
            # Actualizar marca temporal solo tras éxito
            with open(LOG_FILE, "w") as f:
                f.write(f_dt.strftime("%Y-%m-%d"))
            print(f"   ∟ OK guardado.")

finally:
    driver.quit()
    print("\n🏁 Proceso de actualización terminado.")