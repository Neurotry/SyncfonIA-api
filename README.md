# 🚀 GTIN Processor - Extractor y Procesador de GTINs

 
Herramienta para extraer GTINs desde archivos Excel y procesarlos en lotes de forma balanceada y optimizada.

---

## 📋 Características

- ✅ **Extracción automática** de GTINs desde archivos Excel (.xlsx)
- ✅ **Procesamiento por lotes** (100, 500, 1000+ GTINs)
- ✅ **Balanceado y optimizado** para máximo rendimiento
- ✅ **Reportes CSV detallados** con feedback de carga
- ✅ **Manejo de reintentos** automático para fallos
- ✅ **Compatible** con Linux, macOS y Windows

---

## 🛠️ Instalación y Configuración

### 📦 1. Crear entorno virtual
```bash
python3 -m venv venv
```

### 🔌 2. Activar entorno
```bash
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 📚 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

 
---

## 🚀 Uso del Sistema

### 📊 Paso 1: Extractor de GTINs
```bash
python gtin_extractor.py
```
**📁 Input:** `Productos Syncfonia.xlsx`  
**📄 Output:** `gtins_extracted.py` (lotes de 1000 GTINs)

### ⚡ Paso 2: Procesador por Lotes
```bash
python gtin_engineLoader_balanced.py
```

#### 🎛️ Configuraciones disponibles:
- **🔢 Lotes:** 100, 500, 1000+ GTINs
- **⚖️ Modo:** Balanceado y optimizado
- **📈 Reportes:** CSV con feedback detallado
- **🔄 Reintentos:** Automático para casos de fallo

#### 📊 Resultados generados:
- ✅ **GTINs exitosos** con tiempo de procesamiento
- ❌ **GTINs fallidos** con descripción del error
- 🔄 **Conteo de reintentos** por GTIN
- 📈 **Estadísticas de rendimiento** y gráficos

---

## 📁 Estructura del Proyecto

```
gtin_processor/
├── 📄 gtin_extractor.py              # Extractor de GTINs
├── 📄 gtin_engineLoader_balanced.py  # Procesador optimizado
├── 📄 requirements.txt               # Dependencias
├── 📄 Productos Syncfonia.xlsx       # Archivo de entrada
├── 📄 gtins_extracted.py            # GTINs extraídos (generado)
├── 📂 batch_comparison_results/       # Resultados y reportes
│   ├── 📄 *.csv                      # Reportes CSV
│   └── 📂 charts/                    # Gráficos generados
├── 📂 venv/                          # Entorno virtual
└── 📄 README.md                      # Este archivo
```

---

## 📊 Ejemplo de Resultados

### 📈 Estadísticas típicas:
- **⚡ Velocidad:** 2-8 GTINs por segundo
- **✅ Éxito:** 85-95% de GTINs procesados exitosamente  
- **🔄 Reintentos:** Promedio 0.2-0.5 por GTIN
- **📊 Reportes:** CSV detallado + gráficos automáticos

### 📄 Contenido del reporte CSV:
| GTIN | Éxito | Código Estado | Tiempo (s) | Reintentos | Chunk |
|------|-------|---------------|------------|------------|-------|
| 1234567890123 | ✅ Sí | 200 | 2.34 | 0 | Chunk 1 |
| 9876543210987 | ❌ No | 500 | 5.67 | 2 | Chunk 1 |

---

## 🛠️ Solución de Problemas

### ❌ Errores comunes:

#### `python3: command not found`
```bash
# Instalar Python 3.10+ desde python.org
```

#### `No module named pandas`
```bash
# Activar el venv y reinstalar dependencias
source venv/bin/activate
pip install -r requirements.txt
```

#### `Permission denied`
```bash
# No usar sudo, usar entorno virtual
python3 -m venv venv
source venv/bin/activate
```

#### `QueuePool limit reached`
```python
# Reducir NUM_WORKERS en el script
NUM_WORKERS = 4  # Reducir de 8 a 4
```

#### Archivo Excel muy grande
```python
# Usar lotes específicos en MANUAL_BATCHES
MANUAL_BATCHES = ["GTINS_LOTE_1", "GTINS_LOTE_2"]
```

---

## ⚡ Optimizaciones de Rendimiento

### Para archivos Excel grandes (>50MB):
```bash
pip install fastparquet pyarrow  # Formatos más rápidos
```

### Para monitoreo del sistema:
```bash
pip install psutil  # Monitoreo de CPU/RAM
```

### Para barras de progreso:
```bash
pip install tqdm  # Progreso visual mejorado
```

---

## 📖 Documentación Completa

### 📑 Manual de Usuario Detallado:
- **📄 PDF:** `README/Manual de Usuario V1.pdf`
- **🌐 Online:** [Manual de Usuario en Evernote](https://share.evernote.com/note/8f1371aa-ee75-17f6-c245-ff1742f94ae1)

---



## 🤝 Soporte y Contribuciones

### 📧 Contacto:
- **Issues:** Crear issue en el repositorio
- **Email:** constantino.k@neurotry.com o a soporte@neurot.com

### 🔄 Actualizaciones:
- **Versión actual:** 1.0
- **Última actualización:** Junio 2025

---

 

<div align="center">

### 🎉 ¡Listo para procesar miles de GTINs! 🎉

**[⬆️ Volver al inicio](#-gtin-processor---extractor-y-procesador-de-gtins)**

</div>
