import requests
import json
import time
import os
import csv
import statistics
from datetime import datetime
import matplotlib.pyplot as plt
import concurrent.futures
import threading
import importlib.util
import sys

# ==================== CONFIGURACIÓN DE FUENTE DE GTINS ====================
# Opción 1: Usar GTINs del archivo extraído (recomendado para archivos grandes)
USE_EXTRACTED_FILE = True  #Si ponemos true, va cargar desde el gtins_extracted. Si ponemos false ira a manual
EXTRACTED_FILE_PATH = "gtins_extracted.txt"  # Archivo generado por el extractor

# Opción 2: Especificar lotes manualmente
MANUAL_BATCHES = [
    # Puedes especificar qué lotes usar del archivo extraído
    "GTINS_LOTE_1",    # Procesar lote 1,   primer lote de 1000, o 500 o 50 segun el xlsx que usemos
    #"GTINS_LOTE_2",    # Procesar lote 2 
    # "GTINS_LOTE_3",  # Descomenta para añadir más lotes
]


MANUAL_BATCHES = True	 #Asi podemos cargar en forma manual
# Opción 3: GTINs hardcodeados (como backup)
BACKUP_GTINS = [
    "07502209290686", "07501943474307", "07506052540714", "00613008738884"
    "07501010789211", "07502214983573", "07502214983726", "07502214983726"
]

# Configuración exacta como en Postman (la misma que funciona en scriptPrueba.py)
API_URL = "http://127.0.0.1:8000/api/v1/product/description/generate"

# Configuración de la API y Auth0
API_URL = "http://127.0.0.1:8000/api/v1/product/description/generate"
AUTH0_URL = "https://dev1-gs1mx.us.auth0.com/oauth/token"
AUTH0_PAYLOAD = {
    "grant_type": "password",
    "username": "jflores@gs1mexico.org",
    "password": "test123$%",
    "audience": "https://api.gs1.neurotry.services",
    "scope": "openid profile email",
    "client_id": "BKrpZDHjtvbzcVjXQN4RioAJY8Jk4m7b",
    "client_secret": "toK2LxRXg5nKa0sN6mXW4KnbIqShTbPWrJpuddEJCLn0GJfiMK69iBx0KOkm9HrV"
}

# ==================== CONFIGURACIÓN DE PROCESAMIENTO ====================
# Configuración fija (MISMA QUE EL SCRIPT ORIGINAL)
TOTAL_GTINS_TO_PROCESS = 100  # Procesar máximo 1000 GTINs (ajustable automáticamente)
NUM_WORKERS = 4               # Reducir a 8 workers (1 por CPU lógico) - 
MAX_RETRIES = 4               # Mantener 4 reintentos -  
TIMEOUT = 600                 # Aumentar a 600 segundos (10 minutos) -  
NUM_CHUNKS = 3                # Mantener 5 chunks -  

# Pausa entre chunks (añadir esta variable) - EXACTO COMO ORIGINAL
CHUNK_PAUSE = 5               # 5 segundos de pausa entre chunks (ventanas o lotes)

# ==================== CONFIGURACIÓN DE RESULTADOS ====================
RESULTS_DIR = "batch_comparison_results"
os.makedirs(RESULTS_DIR, exist_ok=True)

# Lock para sincronización de hilos
log_lock = threading.Lock()

# Archivo de log
log_file = os.path.join(RESULTS_DIR, f"batch_processing_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

def log_message(message):
    """Escribe un mensaje en el log y en la consola"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with log_lock:
        print(f"[{timestamp}] {message}")
        
        with open(log_file, "a") as f:
            f.write(f"[{timestamp}] {message}\n")

def load_gtins_from_extracted_file():
    """
    Carga GTINs desde el archivo generado por el extractor
    
    Returns:
        dict: Diccionario con todos los lotes disponibles
        list: Lista consolidada de todos los GTINs
    """
    try:
        if not os.path.exists(EXTRACTED_FILE_PATH):
            log_message(f"❌ Archivo extraído no encontrado: {EXTRACTED_FILE_PATH}")
            return None, None
        
        log_message(f"📁 Cargando GTINs desde: {EXTRACTED_FILE_PATH}")
        
        # Cargar el módulo dinámicamente
        spec = importlib.util.spec_from_file_location("gtins_module", EXTRACTED_FILE_PATH)
        gtins_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gtins_module)
        
        # Obtener todos los lotes disponibles
        available_batches = {}
        all_gtins = []
        
        # Buscar todas las variables que empiecen con GTINS_LOTE_
        for attr_name in dir(gtins_module):
            if attr_name.startswith("GTINS_LOTE_"):
                batch_gtins = getattr(gtins_module, attr_name)
                available_batches[attr_name] = batch_gtins
                log_message(f"   📦 {attr_name}: {len(batch_gtins)} GTINs")
        
        # Intentar obtener ALL_GTINS si existe
        if hasattr(gtins_module, 'ALL_GTINS'):
            all_gtins = gtins_module.ALL_GTINS
            log_message(f"   📋 ALL_GTINS: {len(all_gtins)} GTINs totales")
        else:
            # Si no existe ALL_GTINS, concatenar todos los lotes
            for batch_gtins in available_batches.values():
                all_gtins.extend(batch_gtins)
            log_message(f"   📋 GTINs consolidados: {len(all_gtins)} GTINs totales")
        
        log_message(f"✅ Archivo cargado exitosamente: {len(available_batches)} lotes encontrados")
        return available_batches, all_gtins
        
    except Exception as e:
        log_message(f"❌ Error cargando archivo extraído: {str(e)}")
        return None, None

def get_gtins_to_process():
    """
    Determina qué GTINs procesar según la configuración
    
    Returns:
        list: Lista de GTINs a procesar
        str: Descripción de la fuente de GTINs
    """
    if USE_EXTRACTED_FILE:
        available_batches, all_gtins = load_gtins_from_extracted_file()
        
        if available_batches is None:
            log_message("⚠️  Fallback a GTINs hardcodeados por error en archivo extraído")
            return BACKUP_GTINS, "GTINs de backup (hardcodeados)"
        
        # Si se especificaron lotes manuales, usar esos
        if MANUAL_BATCHES:
            selected_gtins = []
            used_batches = []
            
            for batch_name in MANUAL_BATCHES:
                if batch_name in available_batches:
                    batch_gtins = available_batches[batch_name]
                    selected_gtins.extend(batch_gtins)
                    used_batches.append(f"{batch_name}({len(batch_gtins)})")
                    log_message(f"   ✅ Añadido {batch_name}: {len(batch_gtins)} GTINs")
                else:
                    log_message(f"   ⚠️  Lote no encontrado: {batch_name}")
            
            if selected_gtins:
                source_desc = f"Lotes seleccionados: {', '.join(used_batches)}"
                log_message(f"📋 Total GTINs de lotes seleccionados: {len(selected_gtins)}")
                return selected_gtins, source_desc
            else:
                log_message("⚠️  No se encontraron lotes válidos, usando todos los GTINs")
        
        # Si no se especificaron lotes o no se encontraron, usar todos
        if all_gtins:
            return all_gtins, f"Todos los GTINs del archivo extraído ({len(all_gtins)} GTINs)"
    
    # Fallback a GTINs hardcodeados
    log_message("⚠️  Usando GTINs de backup hardcodeados")
    return BACKUP_GTINS, "GTINs de backup (hardcodeados)"

def get_auth_token():
    """Obtiene el token de autenticación de Auth0"""
    try:
        log_message("🔐 Obteniendo token de autenticación...")
        response = requests.post(
            AUTH0_URL,
            headers={"Content-Type": "application/json"},
            json=AUTH0_PAYLOAD
        )
        
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data.get("access_token")
            id_token = auth_data.get("id_token")
            
            log_message("✅ Token de autenticación obtenido exitosamente")
            return {
                "Authorization": f"Bearer {access_token}",
                "id_token": id_token,
                "Content-Type": "application/json"
            }
        else:
            log_message(f"❌ Error al obtener token: {response.status_code}")
            log_message(response.text)
            return None
    except Exception as e:
        log_message(f"❌ Error en la solicitud de autenticación: {str(e)}")
        return None

def process_single_gtin(gtin, retry_count=0):
    """Procesa un solo GTIN y devuelve el resultado con tiempo de procesamiento"""
    start_time = time.time()
    
    try:
        # Usar el mismo payload que en Postman
        payload = {
            "gtin": gtin,
            "gln": "0000000000000",
            "reprocess": True  # Garantiza que se traiga la descripción de nuevo
        }
        
        # Usar POST con el mismo formato que en Postman
        response = requests.post(
            API_URL,
            headers=HEADERS,
            json=payload,
            timeout=TIMEOUT
        )
        
        processing_time = time.time() - start_time
        
        # Registrar resultado
        if 200 <= response.status_code < 300:
            log_message(f"✅ GTIN {gtin} procesado con éxito en {processing_time:.2f}s")
            return True, gtin, response.status_code, processing_time, response.text
        else:
            log_message(f"❌ Error en GTIN {gtin}: {response.status_code}")
            try:
                error_text = response.text[:200]
                log_message(f"Respuesta: {error_text}")
                # Verificar si es error de pool de conexiones
                if "QueuePool limit" in error_text:
                    log_message(f"🔄 Detectado error de pool de conexiones para GTIN {gtin}")
            except:
                error_text = "No se pudo obtener texto de respuesta"
            return False, gtin, response.status_code, processing_time, error_text
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        log_message(f"❌ Error procesando GTIN {gtin}: {error_msg}")
        return False, gtin, None, processing_time, error_msg

def process_gtin_with_retry(gtin):
    """Procesa un GTIN con reintentos en caso de fallo"""
    for retry in range(MAX_RETRIES):
        success, gtin, status_code, processing_time, response_text = process_single_gtin(gtin, retry)
        if success:
            return success, gtin, status_code, processing_time, retry, response_text
        
        # Si falló pero aún tenemos reintentos, esperamos antes de reintentar
        if retry < MAX_RETRIES - 1:
            # Backoff exponencial para errores de pool de conexiones
            if status_code == 500 and isinstance(response_text, str) and "QueuePool limit" in response_text:
                wait_time = min(30, (2 ** retry) * 5)  # 5s, 10s, 20s con máximo de 30s
                log_message(f"⏱️  Error de pool de conexiones. Esperando {wait_time}s antes de reintentar GTIN {gtin}")
            else:
                wait_time = (retry + 1) * 3  # Espera progresiva: 3s, 6s, 9s...
            
            log_message(f"🔄 Reintentando GTIN {gtin} en {wait_time} segundos (intento {retry+1}/{MAX_RETRIES})")
            time.sleep(wait_time)
    
    # Si llegamos aquí, fallaron todos los intentos
    return False, gtin, status_code, processing_time, MAX_RETRIES - 1, response_text

def process_chunk(chunk_gtins, chunk_id, results_file, global_start_time, processed_so_far=0, successful_so_far=0):
    """Procesa un chunk de GTINs y devuelve estadísticas"""
    log_message(f"🚀 Iniciando procesamiento del chunk {chunk_id} con {len(chunk_gtins)} GTINs")
    
    # Contadores para este chunk
    processed_count = 0
    successful_count = 0
    failed_count = 0
    
    # Lista para almacenar tiempos individuales de cada GTIN en este chunk
    gtin_times = []
    retry_counts = []
    
    # Usar ThreadPoolExecutor para procesar los GTINs en paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        # Crear un futuro para cada GTIN en el chunk
        future_to_gtin = {executor.submit(process_gtin_with_retry, gtin): gtin for gtin in chunk_gtins}
        
        for future in concurrent.futures.as_completed(future_to_gtin):
            gtin = future_to_gtin[future]
            try:
                success, gtin, status_code, processing_time, retries, response_text = future.result()
                
                # Actualizar contadores
                processed_count += 1
                if success:
                    successful_count += 1
                else:
                    failed_count += 1
                
                # Guardar estadísticas
                gtin_times.append(processing_time)
                retry_counts.append(retries)
                
                # Calcular tiempo acumulado
                elapsed_so_far = time.time() - global_start_time
                
                # Guardar resultado en CSV
                with open(results_file, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([
                        gtin, 'Sí' if success else 'No', status_code, f"{processing_time:.2f}",
                        retries, f"{elapsed_so_far:.2f}", processed_so_far + processed_count, 
                        successful_so_far + successful_count, f"Chunk {chunk_id}"
                    ])
                
                # Mostrar progreso
                if processed_count % 5 == 0 or processed_count == len(chunk_gtins):
                    progress_pct = (processed_count / len(chunk_gtins)) * 100
                    success_rate = (successful_count / processed_count) * 100 if processed_count > 0 else 0
                    log_message(f"📊 Chunk {chunk_id} - Progreso: {processed_count}/{len(chunk_gtins)} ({progress_pct:.1f}%) - Éxito: {success_rate:.1f}%")
                
            except Exception as e:
                log_message(f"❌ Error inesperado procesando GTIN {gtin} en chunk {chunk_id}: {str(e)}")
                failed_count += 1
    
    log_message(f"✅ Chunk {chunk_id} completado: {processed_count} GTINs procesados, {successful_count} exitosos, {failed_count} fallidos")
    
    return {
        'processed': processed_count,
        'successful': successful_count,
        'failed': failed_count,
        'times': gtin_times,
        'retries': retry_counts
    }

def generate_processing_charts(gtin_times, retry_counts, timestamp, source_description):
    """Genera gráficos del procesamiento"""
    try:
        # Crear directorio para gráficos si no existe
        charts_dir = os.path.join(RESULTS_DIR, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        # 1. Histograma de tiempos de procesamiento
        plt.figure(figsize=(12, 8))
        plt.hist(gtin_times, bins=30, alpha=0.7, color='blue')
        plt.title(f'Distribución de tiempos de procesamiento\n{source_description}')
        plt.xlabel('Tiempo (segundos)')
        plt.ylabel('Frecuencia')
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(charts_dir, f"processing_time_histogram_{timestamp}.png"))
        plt.close()
        
        # 2. Gráfico de dispersión de tiempos de procesamiento
        plt.figure(figsize=(12, 8))
        plt.scatter(range(len(gtin_times)), gtin_times, alpha=0.7, color='green')
        plt.title(f'Tiempos de procesamiento por GTIN\n{source_description}')
        plt.xlabel('Índice de GTIN')
        plt.ylabel('Tiempo (segundos)')
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(charts_dir, f"processing_time_scatter_{timestamp}.png"))
        plt.close()
        
        # 3. Histograma de reintentos
        plt.figure(figsize=(12, 8))
        plt.hist(retry_counts, bins=MAX_RETRIES+1, alpha=0.7, color='red')
        plt.title(f'Distribución de reintentos\n{source_description}')
        plt.xlabel('Número de reintentos')
        plt.ylabel('Frecuencia')
        plt.xticks(range(MAX_RETRIES+1))
        plt.grid(True, alpha=0.3)
        plt.savefig(os.path.join(charts_dir, f"retry_histogram_{timestamp}.png"))
        plt.close()
        
        log_message(f"📈 Gráficos guardados en el directorio: {charts_dir}")
        
    except Exception as e:
        log_message(f"⚠️  Error generando gráficos: {str(e)}")

def main():
    log_message("🚀 ===== INICIANDO SISTEMA DE PROCESAMIENTO MEJORADO =====")
    
    # Obtener token de autenticación
    global HEADERS
    HEADERS = get_auth_token()
    if not HEADERS:
        log_message("❌ No se pudo obtener el token de autenticación. Saliendo...")
        return
    
    # Obtener GTINs a procesar
    gtins_to_process, source_description = get_gtins_to_process()
    total_gtins = len(gtins_to_process)
    
    log_message(f"📋 Fuente de GTINs: {source_description}")
    log_message(f"📊 Total de GTINs disponibles: {total_gtins:,}")
    
    if total_gtins == 0:
        log_message("❌ No hay GTINs para procesar. Saliendo...")
        return
    
    # APLICAR LÍMITE DE TOTAL_GTINS_TO_PROCESS COMO EN EL SCRIPT ORIGINAL
    if total_gtins > TOTAL_GTINS_TO_PROCESS:
        log_message(f"⚠️  Limitando procesamiento a {TOTAL_GTINS_TO_PROCESS:,} GTINs (configurado en TOTAL_GTINS_TO_PROCESS)")
        gtins_to_process = gtins_to_process[:TOTAL_GTINS_TO_PROCESS]
        total_gtins = len(gtins_to_process)
    
    log_message(f"🎯 GTINs que se procesarán: {total_gtins:,}")
    
    # Crear archivo CSV para resultados
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = os.path.join(RESULTS_DIR, f"batch_processing_{timestamp}.csv")
    
    with open(results_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'GTIN', 'Éxito', 'Código de Estado', 'Tiempo (s)', 'Reintentos', 
            'Tiempo Total Acumulado (s)', 'GTINs Procesados', 'GTINs Exitosos', 'Chunk'
        ])
        # Agregar información de la fuente
        writer.writerow([])
        writer.writerow([f"Fuente de GTINs: {source_description}"])
        writer.writerow([f"GTINs disponibles: {len(gtins_to_process):,}"])
        writer.writerow([f"GTINs a procesar: {total_gtins:,}"])
        writer.writerow([f"Workers: {NUM_WORKERS}"])
        writer.writerow([f"Chunks: {NUM_CHUNKS}"])
        writer.writerow([f"Max reintentos: {MAX_RETRIES}"])
        writer.writerow([f"Timeout: {TIMEOUT}s"])
        writer.writerow([f"Pausa entre chunks: {CHUNK_PAUSE}s"])
        writer.writerow([])
    
    log_message(f"⚙️  Configuración EXACTA como script original:")
    log_message(f"   📊 Total GTINs a procesar: {total_gtins:,}")
    log_message(f"   👥 Workers: {NUM_WORKERS}")
    log_message(f"   📦 Chunks: {NUM_CHUNKS}")
    log_message(f"   🔄 Max reintentos: {MAX_RETRIES}")
    log_message(f"   ⏱️  Timeout: {TIMEOUT}s")
    log_message(f"   ⏸️  Pausa entre chunks: {CHUNK_PAUSE}s")
    
    # Tiempo de inicio global
    global_start_time = time.time()
    
    # Dividir los GTINs en chunks EXACTAMENTE COMO EN EL SCRIPT ORIGINAL
    chunk_size = total_gtins // NUM_CHUNKS
    chunks = [gtins_to_process[i:i + chunk_size] for i in range(0, total_gtins, chunk_size)]
    
    log_message(f"📦 Dividiendo {total_gtins:,} GTINs en {len(chunks)} chunks de ~{chunk_size} GTINs cada uno")
    
    # Contadores globales
    total_processed = 0
    total_successful = 0
    total_failed = 0
    all_times = []
    all_retries = []
    
    # Procesar cada chunk secuencialmente
    for i, chunk in enumerate(chunks):
        chunk_id = i + 1
        chunk_stats = process_chunk(chunk, chunk_id, results_file, global_start_time, total_processed, total_successful)
        
        # Actualizar contadores globales
        total_processed += chunk_stats['processed']
        total_successful += chunk_stats['successful']
        total_failed += chunk_stats['failed']
        all_times.extend(chunk_stats['times'])
        all_retries.extend(chunk_stats['retries'])
        
        # Mostrar progreso global después de cada chunk
        progress_pct = (total_processed / total_gtins) * 100
        success_rate = (total_successful / total_processed) * 100 if total_processed > 0 else 0
        log_message(f"🌍 Progreso global: {total_processed:,}/{total_gtins:,} ({progress_pct:.1f}%) - Éxito: {success_rate:.1f}%")
        
        # Pausa entre chunks
        if i < len(chunks) - 1:  # No pausar después del último chunk
            log_message(f"⏸️  Pausa de {CHUNK_PAUSE} segundos antes del siguiente chunk...")
            time.sleep(CHUNK_PAUSE)
    
    # Calcular tiempo total de ejecución
    total_execution_time = time.time() - global_start_time
    
    # Calcular estadísticas de tiempo
    if all_times:
        time_stats = {
            'min': min(all_times),
            'max': max(all_times),
            'avg': statistics.mean(all_times),
            'median': statistics.median(all_times),
            'stdev': statistics.stdev(all_times) if len(all_times) > 1 else 0
        }
    else:
        time_stats = {'min': 0, 'max': 0, 'avg': 0, 'median': 0, 'stdev': 0}
    
    # Calcular estadísticas de reintentos
    retry_stats = {
        'total_retries': sum(all_retries),
        'avg_retries': statistics.mean(all_retries) if all_retries else 0,
        'max_retries': max(all_retries) if all_retries else 0
    }
    
    # Generar gráficos
    generate_processing_charts(all_times, all_retries, timestamp, source_description)
    
    # Imprimir informe final
    log_message("\n🎯 ===== RESUMEN FINAL DE PROCESAMIENTO =====")
    log_message(f"📋 Fuente: {source_description}")
    log_message(f"📊 Total de GTINs procesados: {total_processed:,}/{total_gtins:,}")
    log_message(f"✅ GTINs exitosos: {total_successful:,} ({total_successful/total_processed*100:.1f}%)")
    log_message(f"❌ GTINs fallidos: {total_failed:,} ({total_failed/total_processed*100:.1f}%)")
    log_message(f"⏱️  Tiempo total de ejecución: {total_execution_time:.2f} segundos ({total_execution_time/60:.2f} minutos)")
    log_message(f"🚄 Velocidad promedio: {total_processed/total_execution_time:.2f} GTINs por segundo")
    log_message(f"⏳ Tiempo promedio por GTIN: {time_stats['avg']:.2f} segundos")
    
    if total_processed > 0:
        estimated_time_1000 = (total_execution_time/total_processed)*1000/60
        log_message(f"🔮 Tiempo estimado para 1000 GTINs: {estimated_time_1000:.2f} minutos")
    
    log_message(f"\n📊 Estadísticas de tiempo (segundos):")
    log_message(f"   Mínimo: {time_stats['min']:.2f}")
    log_message(f"   Máximo: {time_stats['max']:.2f}")
    log_message(f"   Promedio: {time_stats['avg']:.2f}")
    log_message(f"   Mediana: {time_stats['median']:.2f}")
    log_message(f"   Desviación estándar: {time_stats['stdev']:.2f}")
    
    log_message(f"\n🔄 Estadísticas de reintentos:")
    log_message(f"   Total de reintentos: {retry_stats['total_retries']:,}")
    log_message(f"   Promedio de reintentos por GTIN: {retry_stats['avg_retries']:.2f}")
    log_message(f"   Máximo de reintentos en un GTIN: {retry_stats['max_retries']}")
    
    # Guardar el resumen en el archivo CSV
    with open(results_file, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([])
        writer.writerow(["===== RESUMEN FINAL DE PROCESAMIENTO ====="])
        writer.writerow(["Fuente", source_description])
        writer.writerow(["Total de GTINs procesados", f"{total_processed:,}/{total_gtins:,}"])
        writer.writerow(["GTINs exitosos", f"{total_successful:,} ({total_successful/total_processed*100:.1f}%)"])
        writer.writerow(["GTINs fallidos", f"{total_failed:,} ({total_failed/total_processed*100:.1f}%)"])
        writer.writerow(["Tiempo total de ejecución", f"{total_execution_time:.2f} segundos ({total_execution_time/60:.2f} minutos)"])
        writer.writerow(["Velocidad promedio", f"{total_processed/total_execution_time:.2f} GTINs por segundo"])
        writer.writerow(["Tiempo promedio por GTIN", f"{time_stats['avg']:.2f} segundos"])
        if total_processed > 0:
            writer.writerow(["Tiempo estimado para 1000 GTINs", f"{(total_execution_time/total_processed)*1000/60:.2f} minutos"])
    
    log_message(f"\n📄 Resultados guardados en: {results_file}")
    log_message("🎉 ===== FIN DE PROCESAMIENTO =====")

if __name__ == "__main__":
    main()
