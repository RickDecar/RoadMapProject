import os
import re
import sys
from graphviz import Digraph
from collections import defaultdict

# ------------------------------------------------------------
# FUNCIONES PRINCIPALES
# ------------------------------------------------------------

def detectar_call(linea):
    """
    Detecta llamadas a otros módulos COBOL (CALL o EXEC CICS LINK/START/INVOKE).
    Retorna el nombre del módulo llamado, si lo encuentra.
    """
    linea = linea.upper()

    # CALL 'MODULO' o CALL WS-MODULO
    m = re.search(r"\bCALL\s+['\"]?([\w-]+)['\"]?", linea)
    if m:
        return m.group(1)

    # EXEC CICS LINK/START/INVOKE PROGRAM('MODULO') END-EXEC
    m = re.search(r"EXEC\s+CICS\s+(?:LINK|START|INVOKE)\s+PROGRAM\s*\(['\"]?([\w-]+)['\"]?\)", linea)
    if m:
        return "CICS-" + m.group(1)

    return None


def es_linea_ignorable(linea):
    """Devuelve True si la línea es un comentario o vacía."""
    return not linea.strip() or (len(linea) > 6 and linea[6] == '*')


def analizar_cobol(ruta_archivo):
    """
    Analiza un programa COBOL y extrae todas las llamadas externas (CALL y CICS).
    No tiene en cuenta los párrafos.
    """
    llamadas = defaultdict(list)
    origen = os.path.splitext(os.path.basename(ruta_archivo))[0].upper()

    try:
        with open(ruta_archivo, 'r', encoding='latin-1') as archivo:
            for linea in archivo:
                linea = linea.upper()
                if es_linea_ignorable(linea):
                    continue

                destino = detectar_call(linea)
                if destino:
                    llamadas[origen].append(destino.upper())

    except Exception as e:
        print(f"Error al analizar el archivo: {e}")

    return llamadas


def generar_grafo(llamadas, archivo_salida):
    """
    Genera un grafo PDF con las llamadas externas detectadas.
    """
    dot = Digraph(comment='Llamadas COBOL', format='pdf', engine='dot')
    dot.attr(dpi='200', rankdir='TB', nodesep='1.0', ranksep='1.3', splines='ortho')

    # Crear nodos y relaciones
    for origen, destinos in llamadas.items():
        dot.node(origen, origen, style='filled', fillcolor='#B4C7E7', shape='box', fontname='Helvetica')
        
        # Quitar duplicados de destinos
        destinos_unicos = set(destinos)
        
        for destino in destinos_unicos:
            color = '#A4C2F4'
            shape = 'house'
            shape = 'component'
            
            if destino.startswith('CICS-'):
                color = '#FFD966'
                shape = 'cylinder'
                
            dot.node(destino, destino, style='filled', fillcolor=color, shape=shape, fontname='Helvetica')
            #dot.edge(origen, destino, color='#4A86E8', arrowsize='0.7')
            dot.edge(origen, destino, color='#3D85C6', arrowsize='0.7')

    pdf_path = dot.render(filename=f"{archivo_salida}.pdf", cleanup=True)
    print(f"Grafo generado: {pdf_path}")

    # Abrir el PDF automáticamente según el SO
    if sys.platform.startswith('win'):
        os.startfile(pdf_path)
    elif sys.platform == 'darwin':
        os.system(f'open \"{pdf_path}\"')
    else:
        os.system(f'xdg-open \"{pdf_path}\"')


# ------------------------------------------------------------
# PROGRAMA PRINCIPAL
# ------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python RoadMapCalls.py <fuente_cobol>")
        sys.exit(1)

    ruta_cobol = sys.argv[1]
    archivo_salida = os.path.splitext(os.path.basename(ruta_cobol))[0]

    print(f"Analizando llamadas externas en: {ruta_cobol}")

    llamadas = analizar_cobol(ruta_cobol)
    total_llamadas = sum(len(v) for v in llamadas.values())

    print(f"{total_llamadas} llamadas encontradas.")

    generar_grafo(llamadas, archivo_salida)
