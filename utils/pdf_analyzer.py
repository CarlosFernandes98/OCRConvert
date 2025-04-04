from datetime import datetime
import pytesseract
from pdf2image import convert_from_path
import os
import time
import cv2
import numpy as np
import json

def analyze_pdf(pdf_path):
    # Converter PDF para imagens
    images = convert_from_path(pdf_path)
    
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    basename = os.path.splitext(os.path.basename(pdf_path))[0]
    output_dir = f'./output/pdf/{basename}_{current_date}'
    
    
    # output_dir = './output/pdf'
    os.makedirs(output_dir, exist_ok=True)
    
    # Estrutura para armazenar os resultados
    result = {"pages": []}
    
    for i, image in enumerate(images):
        # Converter a imagem (PIL) para array e ajustar para escala de cinza
        np_image = np.array(image)
        bgr_image = cv2.cvtColor(np_image, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY)
        
        # Extrair texto com OCR
        texto_extraido = pytesseract.image_to_string(gray, lang='por')
        
        # Dividir o texto em linhas e remover linhas vazias
        linhas = [line for line in texto_extraido.splitlines() if line.strip()]
        
        # Armazenar os resultados da página
        result["pages"].append({
            "page": i + 1,
            "lines": linhas
        })
    
    nome_arquivo_json = f"{output_dir}/produto_{current_date}.json"

    # Salvar os resultados em um arquivo JSON
    with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
        
    print(f"Texto extraído guardado em {nome_arquivo_json}")
    return nome_arquivo_json
