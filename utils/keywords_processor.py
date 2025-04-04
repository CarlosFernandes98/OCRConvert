import json
import os
from datetime import datetime
from tkinter import messagebox

# Função para processar as palavras-chave
def processar_keywords(keywords):
    if keywords:
        # Separando as palavras-chave por vírgula e removendo espaços extras
        keywords_list = [keyword.strip() for keyword in keywords.split(',')]
        
        # Diretório de saída
        output_dir = './output/keywords/'
        os.makedirs(output_dir, exist_ok=True)

        # Criar o nome do arquivo com a data atual
        current_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_file = f"{output_dir}date_keywords_{current_date}.json"

        # Guardar as palavras-chave no arquivo JSON
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(keywords_list, file, ensure_ascii=False, indent=4)

        return output_file  # Retorna o caminho do arquivo salvo
    else:
        return None
