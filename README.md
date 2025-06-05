#Documentacion los pasos para poder usar


 
#Tecnical pasos, para instalar preparar ambiente:
 
# 1. Crear entorno virtual
python3 -m venv venv

# 2. Activar entorno
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Extractor de GTINs de XLSx
gtin_extractor.py

# 5. Correr en forma de lotes 100, 500, 1000 GTins, con el XLSx, o forma manual de forma balanceada y optima,  Generara reporte CSV feedback de carga exitosa, fallida y reintentos. 
gtin_engineLoader_balanced.py



# 6.Para mas detalles, Manual de Usuario: 
README/Manual de Usuario V1.pdf
#Mejor visibilidad del Manual de usuario en:
https://share.evernote.com/note/8f1371aa-ee75-17f6-c245-ff1742f94ae1

