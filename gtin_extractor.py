#!/usr/bin/env python3
"""
Extractor de GTINs desde archivo Excel con división en lotes
Optimizado para archivos grandes (24MB+, 90,000+ registros)
"""

import pandas as pd
import math
import os
from typing import List, Iterator
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GTINExtractor:
    def __init__(self, excel_file_path: str, batch_size: int = 1000):
        """
        Inicializa el extractor de GTINs
        
        Args:
            excel_file_path: Ruta al archivo Excel
            batch_size: Tamaño de cada lote (default: 1000)
        """
        self.excel_file_path = excel_file_path
        self.batch_size = batch_size
        self.gtins = []
        
    def extract_gtins_from_excel(self) -> List[str]:
        """
        Extrae GTINs de la primera columna del archivo Excel
        Optimizado para archivos grandes
        """
        try:
            logger.info(f"Leyendo archivo Excel: {self.excel_file_path}")
            
            # Leer solo la primera columna para optimizar memoria
            # usecols=[0] lee solo la primera columna
            df = pd.read_excel(
                self.excel_file_path, 
                usecols=[0],  # Solo primera columna
                engine='openpyxl',  # Motor para archivos .xlsx
                dtype=str  # Leer como string para preservar GTINs con ceros iniciales
            )
            
            # Obtener nombre de la primera columna
            first_column = df.columns[0]
            logger.info(f"Procesando columna: '{first_column}'")
            
            # Extraer valores y limpiar
            raw_gtins = df[first_column].dropna().astype(str).tolist()
            
            # Limpiar GTINs (remover espacios, caracteres especiales)
            cleaned_gtins = []
            for gtin in raw_gtins:
                # Limpiar espacios y convertir a string
                clean_gtin = str(gtin).strip()
                
                # Filtrar solo valores que parezcan GTINs (números de 8-14 dígitos)
                if clean_gtin.isdigit() and 8 <= len(clean_gtin) <= 14:
                    cleaned_gtins.append(clean_gtin)
                else:
                    logger.warning(f"GTIN inválido ignorado: '{clean_gtin}'")
            
            self.gtins = cleaned_gtins
            logger.info(f"Total de GTINs extraídos: {len(self.gtins)}")
            
            return self.gtins
            
        except Exception as e:
            logger.error(f"Error al leer archivo Excel: {e}")
            raise
    
    def create_batches(self, gtins: List[str] = None) -> Iterator[List[str]]:
        """
        Divide los GTINs en lotes del tamaño especificado
        
        Args:
            gtins: Lista de GTINs (opcional, usa self.gtins si no se proporciona)
            
        Yields:
            List[str]: Lote de GTINs
        """
        if gtins is None:
            gtins = self.gtins
            
        if not gtins:
            logger.warning("No hay GTINs para procesar")
            return
        
        total_batches = math.ceil(len(gtins) / self.batch_size)
        logger.info(f"Creando {total_batches} lotes de máximo {self.batch_size} GTINs cada uno")
        
        for i in range(0, len(gtins), self.batch_size):
            batch = gtins[i:i + self.batch_size]
            batch_number = (i // self.batch_size) + 1
            logger.info(f"Lote {batch_number}/{total_batches}: {len(batch)} GTINs")
            yield batch
    
    def generate_python_lists(self, output_file: str = None) -> str:
        """
        Genera código Python con las listas de GTINs en el formato solicitado
        
        Args:
            output_file: Archivo donde guardar el código (opcional)
            
        Returns:
            str: Código Python generado
        """
        if not self.gtins:
            logger.error("No hay GTINs cargados. Ejecuta extract_gtins_from_excel() primero")
            return ""
        
        logger.info("Generando código Python con lotes de GTINs...")
        
        python_code = []
        python_code.append("# Lista de GTINs dividida en lotes de 1000")
        python_code.append("# Total de GTINs: {:,}".format(len(self.gtins)))
        python_code.append("")
        
        for batch_idx, batch in enumerate(self.create_batches(), 1):
            python_code.append(f"# Lote {batch_idx} - {len(batch)} GTINs")
            python_code.append(f"GTINS_LOTE_{batch_idx} = [")
            
            # Formatear GTINs en líneas de ~80 caracteres
            line_items = []
            current_line = "    "
            
            for i, gtin in enumerate(batch):
                gtin_str = f'"{gtin}"'
                if i < len(batch) - 1:  # No es el último
                    gtin_str += ", "
                
                # Si la línea se vuelve muy larga, crear nueva línea
                if len(current_line + gtin_str) > 80:
                    line_items.append(current_line.rstrip(", "))
                    current_line = "    " + gtin_str
                else:
                    current_line += gtin_str
            
            # Añadir la última línea
            if current_line.strip() != "":
                line_items.append(current_line.rstrip(", "))
            
            python_code.extend(line_items)
            python_code.append("]")
            python_code.append("")
        
        # Crear lista consolidada
        python_code.append("# Lista consolidada de todos los lotes")
        python_code.append("ALL_GTINS = [")
        for batch_idx in range(1, math.ceil(len(self.gtins) / self.batch_size) + 1):
            if batch_idx == math.ceil(len(self.gtins) / self.batch_size):
                python_code.append(f"    *GTINS_LOTE_{batch_idx}")
            else:
                python_code.append(f"    *GTINS_LOTE_{batch_idx},")
        python_code.append("]")
        python_code.append("")
        python_code.append(f"# Total: {len(self.gtins):,} GTINs")
        
        final_code = "\n".join(python_code)
        
        # Guardar en archivo si se especifica
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(final_code)
                logger.info(f"Código Python guardado en: {output_file}")
            except Exception as e:
                logger.error(f"Error al guardar archivo: {e}")
        
        return final_code
    
    def get_statistics(self) -> dict:
        """
        Obtiene estadísticas de los GTINs extraídos
        """
        if not self.gtins:
            return {}
        
        total_gtins = len(self.gtins)
        total_batches = math.ceil(total_gtins / self.batch_size)
        
        # Análisis de longitudes de GTIN
        gtin_lengths = {}
        for gtin in self.gtins:
            length = len(gtin)
            gtin_lengths[length] = gtin_lengths.get(length, 0) + 1
        
        return {
            "total_gtins": total_gtins,
            "total_batches": total_batches,
            "batch_size": self.batch_size,
            "gtin_lengths": gtin_lengths,
            "last_batch_size": total_gtins % self.batch_size if total_gtins % self.batch_size != 0 else self.batch_size
        }


def main():
    """
    Función principal para demostrar el uso
    """
    # Configuración
    EXCEL_FILE = "Productos_a_cargar.xlsx"  # Cambia por tu archivo
    OUTPUT_FILE = "gtins_extracted.txt"
    BATCH_SIZE = 1000 # hace cortes de 1000, si tienes menos no problema.  Al rato vemos como lo usamos
    
    try:
        # Verificar si el archivo existe
        if not os.path.exists(EXCEL_FILE):
            logger.error(f"Archivo no encontrado: {EXCEL_FILE}")
            print(f"\n❌ Error: El archivo '{EXCEL_FILE}' no existe.")
            print("Por favor, verifica la ruta del archivo.")
            return
        
        print(f"🚀 Iniciando extracción de GTINs de {EXCEL_FILE}")
        print(f"📦 Tamaño de lote: {BATCH_SIZE}")
        
        # Crear extractor
        extractor = GTINExtractor(EXCEL_FILE, BATCH_SIZE)
        
        # Extraer GTINs
        print("\n📊 Extrayendo GTINs del archivo Excel...")
        gtins = extractor.extract_gtins_from_excel()
        
        # Mostrar estadísticas
        stats = extractor.get_statistics()
        print(f"\n📈 Estadísticas:")
        print(f"   • Total GTINs: {stats['total_gtins']:,}")
        print(f"   • Total lotes: {stats['total_batches']:,}")
        print(f"   • Tamaño último lote: {stats['last_batch_size']}")
        print(f"   • Distribución por longitud:")
        for length, count in sorted(stats['gtin_lengths'].items()):
            print(f"     - {length} dígitos: {count:,} GTINs")
        
        # Generar código Python
        print(f"\n🐍 Generando código Python...")
        code = extractor.generate_python_lists(OUTPUT_FILE)
        
        print(f"\n✅ ¡Proceso completado exitosamente!")
        print(f"   📄 Archivo generado: {OUTPUT_FILE}")
        print(f"   📊 {len(gtins):,} GTINs procesados en {stats['total_batches']} lotes")
        
        # Mostrar preview del código generado
        print(f"\n👀 Preview del código generado:")
        print("=" * 50)
        preview_lines = code.split('\n')[:20]  # Primeras 20 líneas
        for line in preview_lines:
            print(line)
        if len(code.split('\n')) > 20:
            print("... (archivo completo guardado)")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"Error en el proceso principal: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
