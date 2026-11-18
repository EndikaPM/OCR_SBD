import os
import csv
import cv2
import matplotlib
matplotlib.use('Agg')  # Evita usar la ventana Tkinter (_imagingtk) bloqueada por Windows
from matplotlib import pyplot as plt
import pytesseract
from PIL import Image

# Ruta del ejecutable de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# --- PASO 1 y 2: Leer imagen, recortar agujeros y preprocesar ---
ruta_img = os.path.join(os.path.dirname(__file__), 'app', 'apollo_11_ascent_timeline.webp')
img = cv2.imread(ruta_img)

# Recortamos la zona de datos de la tabla (quitamos los agujeros de arriba y los bordes)
# Alto: de la fila 260 a la 1085 | Ancho: de la columna 125 a la 1400
recorte = img[260:1085, 125:1400]

# Pasamos a escala de grises y binarizamos (blanco y negro puro)
gray = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
_, imagen_procesada = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

# Mostramos/guardamos el resultado limpio con Matplotlib
plt.imshow(imagen_procesada, cmap='gray')
plt.title("Imagen preprocesada (sin agujeros)")
plt.axis("off")
ruta_plot = os.path.join(os.path.dirname(__file__), 'imagen_procesada.png')
plt.savefig(ruta_plot, bbox_inches='tight')
print(f"Gráfico de Matplotlib guardado en: {ruta_plot}")

# --- PASO 3: Conversión de la imagen a texto (string) ---
pil_img = Image.fromarray(imagen_procesada)
texto = pytesseract.image_to_string(pil_img, config='--psm 6')

print("\n=== TEXTO BRUTO RECONOCIDO ===")
print(texto)

# --- PASO 4: Limpiar y formatear el resultado en 3 columnas (TIME, EVENT, REMARKS) ---
datos_csv = [["TIME", "EVENT", "REMARKS"]]  # Cabecera con las 3 columnas

# Palabras con las que empiezan los textos de la tercera columna (REMARKS)
inicios_remarks = ["FIRST OPPORTUNITY", "SITE 2.", "PROP DUMP", "ALTITUDE"]

for linea in texto.splitlines():
    # 1. Limpiamos símbolos basura y corregimos letras que el OCR confunde
    linea_limpia = (
        linea.replace("|", "")
        .replace("_", "")
        .replace(";", "")
        .replace("“", "")
        .replace(" ,", "")
        .replace("- ", "-")
        .replace("COR:", "CDR:")
        .replace("coR:", "CDR:")
        .replace("Lec:", "LCC:")
        .replace("S-I1", "S-II")
        .strip()
    )

    if not linea_limpia:
        continue

    # 2. Separamos la primera palabra (TIME) del resto de la línea
    partes = linea_limpia.split(" ", 1)

    if ":" in partes[0] and len(partes) == 2:
        tiempo = partes[0]
        evento = partes[1].strip()
        remark = ""

        # 3. Si en la línea hay texto de la 3ª columna (REMARKS), lo separamos de EVENT
        for inicio in inicios_remarks:
            if inicio in evento:
                division = evento.split(inicio, 1)
                evento = division[0].strip()
                remark = (inicio + division[1]).strip()
                break

        datos_csv.append([tiempo, evento, remark])
    else:
        # 4. Si es una línea suelta de continuación (ej. "INITIATE" o "0932 EDT..."):
        # Si la fila anterior tenía REMARKS, la pegamos en REMARKS; si no, en EVENT
        if len(datos_csv) > 1:
            if datos_csv[-1][2] != "":
                datos_csv[-1][2] += " " + linea_limpia
            else:
                datos_csv[-1][1] += " " + linea_limpia

# --- PASO 5: Guardar el resultado en un CSV ---
ruta_csv = os.path.join(os.path.dirname(__file__), 'resultado_ocr.csv')
with open(ruta_csv, mode='w', newline='', encoding='utf-8') as archivo_csv:
    writer = csv.writer(archivo_csv, delimiter=';')
    writer.writerows(datos_csv)

print(f"\n¡CSV guardado correctamente en: {ruta_csv}!")
