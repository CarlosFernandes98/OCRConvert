# image_analyzer.py

from datetime import datetime
import cv2
import pytesseract
from pytesseract import Output
import os
import time
import json

# Função para agrupar textos por linha
def agrupar_textos_por_linha(details):
    linhas = []
    linha_atual = []
    linha_top = -1
    
    for i in range(len(details['text'])):
        if details['text'][i].strip() != "":
            if linha_top == -1 or abs(details['top'][i] - linha_top) < 10:
                linha_atual.append(details['text'][i])
            else:
                linhas.append(' '.join(linha_atual))
                linha_atual = [details['text'][i]]
            linha_top = details['top'][i]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))
    return linhas

# Função para analisar a imagem
def analyze_image(image_path):
    # Carregar a imagem
    img = cv2.imread(image_path)
    
    # Converter para escala de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar threshold para melhorar a detecção de texto
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    # Extrair informações de OCR
    details = pytesseract.image_to_data(thresh, lang='por', output_type=Output.DICT)
    
    # Agrupar os textos por linha
    linhas = agrupar_textos_por_linha(details)
    
  # Criar pasta de saída com nome do arquivo original + timestamp
    # timestamp = int(time.time())
    current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    basename = os.path.splitext(os.path.basename(image_path))[0]
    output_dir = f'./output/image/{basename}_{current_date}'
    os.makedirs(output_dir, exist_ok=True)

    # Nome do arquivo JSON

    nome_arquivo_json = f"{output_dir}/produto_{current_date}.json"
    
    with open(nome_arquivo_json, 'w', encoding='utf-8') as f:
        json.dump({"Text": linhas}, f, ensure_ascii=False, indent=4)
    
    # Desenhar caixas delimitadoras
    for i in range(len(details['text'])):
        if details['text'][i].strip() != "":
            x, y, w, h = details['left'][i], details['top'][i], details['width'][i], details['height'][i]
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return nome_arquivo_json
    
    # Exibir a imagem com as marcações
    # cv2.imshow('Contornos de Texto', img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
