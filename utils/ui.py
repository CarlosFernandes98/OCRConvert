import json
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel, Text, BooleanVar
from utils.image_analyzer import analyze_image
from utils.pdf_analyzer import analyze_pdf
import os
import threading  # Para processamento em background

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")  # temas: blue, dark-blue, green

# Lista para armazenar os arquivos carregados
arquivos_carregados = []
lista_arquivos = None
entry_keywords = None  # Será definido na interface

# Variáveis globais para atualizar a UI durante o processamento
app = None
progress_bar = None
status_label = None
process_button = None

def carregar_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("Arquivos PDF", "*.pdf")])
    if file_path:
        arquivos_carregados.append(file_path)
        atualizar_lista_arquivos()
        messagebox.showinfo("PDF Carregado", "O PDF foi adicionado à lista. Clique em 'Processar Tudo' para processar.")

def carregar_imagem():
    file_path = filedialog.askopenfilename(filetypes=[("Imagens", "*.png;*.jpg;*.jpeg;*.bmp")])
    if file_path:
        arquivos_carregados.append(file_path)
        atualizar_lista_arquivos()
        messagebox.showinfo("Imagem Carregada", "A imagem foi adicionada à lista. Clique em 'Processar Tudo' para processar.")

def remover_arquivo_selecionado():
    selecionado = lista_arquivos.get()
    if selecionado:
        arquivos_carregados.remove(selecionado)
        atualizar_lista_arquivos()
    else:
        messagebox.showwarning("Nenhum selecionado", "Selecione um arquivo da lista para remover.")

def atualizar_lista_arquivos():
    status_label.configure(text="")
    progress_bar.set(0)
    lista_arquivos.configure(values=arquivos_carregados)
    if arquivos_carregados:
        lista_arquivos.set(arquivos_carregados[-1])
    else:
        lista_arquivos.set("Nenhum ficheiro carregado")

def limpar_tudo():
    """
    Remove todos os arquivos carregados e limpa o campo de palavras-chave.
    """
    global arquivos_carregados, entry_keywords
    arquivos_carregados.clear()
    atualizar_lista_arquivos()
    status_label.configure(text="")
    progress_bar.set(0)
    entry_keywords.delete(0, "end")
    messagebox.showinfo("Limpar", "Todos os arquivos e palavras-chave foram removidos.")

def verificar_keywords(json_path, lista_keywords):
    """
    Verifica se as keywords existem no conteúdo do JSON gerado pela análise do arquivo.
    
    Para arquivos do tipo imagem (chave "text" ou "Text"), retorna um dicionário onde cada chave é uma keyword
    e o valor é uma lista de tuplas (número_da_linha, texto_da_linha).
    
    Para arquivos PDF (chave "pages"), retorna um dicionário onde cada chave é uma keyword
    e o valor é uma lista de tuplas (número_da_página, número_da_linha, texto_da_linha).
    """
    occurrences = {}
    if json_path and os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            conteudo = json.load(f)
        if "pages" in conteudo:
            # Processa o formato PDF
            for page in conteudo["pages"]:
                page_number = page.get("page", None)
                lines = page.get("lines", [])
                for idx, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    for kw in lista_keywords:
                        if kw in line_lower:
                            if kw not in occurrences:
                                occurrences[kw] = []
                            # Retorna (número da página, número da linha, texto da linha)
                            occurrences[kw].append((page_number, idx, line))
        else:
            # Processa o formato antigo (imagens) com chave "text" ou "Text"
            texto = conteudo.get("text") or conteudo.get("Text") or ""
            if isinstance(texto, list):
                linhas = texto
            elif isinstance(texto, str):
                linhas = texto.splitlines()
            else:
                linhas = []
            for idx, line in enumerate(linhas, 1):
                line_lower = line.lower()
                for kw in lista_keywords:
                    if kw in line_lower:
                        if kw not in occurrences:
                            occurrences[kw] = []
                        # Retorna (número da linha, texto da linha)
                        occurrences[kw].append((idx, line))
    return occurrences

def process_files(lista_keywords, progress_callback):
    """
    Processa cada arquivo e atualiza o progresso através do callback.
    Retorna a lista de resultados.
    """
    resultados = []
    total = len(arquivos_carregados)
    for i, arquivo in enumerate(arquivos_carregados):
        json_path = None
        if arquivo.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            json_path = analyze_image(arquivo)
        elif arquivo.lower().endswith('.pdf'):
            json_path = analyze_pdf(arquivo)
        if json_path and lista_keywords:
            ocorrencias = verificar_keywords(json_path, lista_keywords)
            resultados.append((arquivo, ocorrencias))
        # Atualiza a barra de progresso
        progress = (i + 1) / total
        progress_callback(progress)
    return resultados

def show_results(resultados):
    """
    Exibe os resultados em uma nova janela e atualiza o status.
    """
    global status_label, progress_bar, process_button
    result_window = Toplevel()
    result_window.title("Resultado das Palavras-chave")
    text_widget = Text(result_window, wrap="word")
    text_widget.pack(expand=True, fill="both")
    text_widget.tag_config("header", font=("Helvetica", 14, "bold"))
    text_widget.tag_config("keyword", font=("Helvetica", 12, "bold"), foreground="blue")
    text_widget.tag_config("highlight", background="yellow", foreground="red")
    for arquivo, ocorrencias in resultados:
        nome_arquivo = os.path.basename(arquivo)
        text_widget.insert("end", f"Arquivo: {nome_arquivo}\n", "header")
        if ocorrencias:
            for kw, occ_list in ocorrencias.items():
                text_widget.insert("end", f"Keyword: {kw}\n", "keyword")
                for occurrence in occ_list:
                    if len(occurrence) == 3:
                        page, lineno, line_text = occurrence
                        text_widget.insert("end", f"  Página {page}, Linha {lineno}: ")
                    elif len(occurrence) == 2:
                        lineno, line_text = occurrence
                        text_widget.insert("end", f"  Linha {lineno}: ")
                    else:
                        continue
                    start_pos = 0
                    lower_line_text = line_text.lower()
                    while True:
                        idx = lower_line_text.find(kw, start_pos)
                        if idx == -1:
                            text_widget.insert("end", line_text[start_pos:])
                            break
                        else:
                            text_widget.insert("end", line_text[start_pos:idx])
                            text_widget.insert("end", line_text[idx:idx+len(kw)], "highlight")
                            start_pos = idx + len(kw)
                    text_widget.insert("end", "\n")
        else:
            text_widget.insert("end", "Nenhuma palavra-chave encontrada.\n")
        text_widget.insert("end", "\n")
    # Atualiza o status e reabilita o botão de processamento
    status_label.configure(text="Concluído!")
    progress_bar.set(1.0)
    process_button.configure(state="normal")
    messagebox.showinfo("Concluído", "Processamento completo!")

def start_processing():
    """
    Inicia o processamento em uma thread separada e atualiza o status na UI.
    """
    global app, status_label, process_button
    keywords = entry_keywords.get().strip()
    lista_keywords = [kw.strip().lower() for kw in keywords.split(",") if kw.strip()] if keywords else []
    
    # Atualiza status e desabilita o botão de processamento
    status_label.configure(text="A processar...")
    progress_bar.set(0)
    process_button.configure(state="disabled")
    
    def progress_callback(value):
        app.after(0, lambda: progress_bar.set(value))
    
    def processing_task():
        resultados = process_files(lista_keywords, progress_callback)
        app.after(0, lambda: show_results(resultados))
    
    threading.Thread(target=processing_task, daemon=True).start()

def abrir_pasta_local():
    # Se estiver executando como exe empacotado, use sys.executable.
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    folder_path = os.path.join(base_path, "output")
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    os.startfile(folder_path)

def create_interface():
    global lista_arquivos, entry_keywords, app, progress_bar, status_label, process_button

    app = ctk.CTk()
    app.title("Análise de PDFs e Imagens")
    app.geometry("600x700")  # Ajustado para acomodar os novos widgets

    # Frame principal para conter todos os elementos
    main_frame = ctk.CTkFrame(app)
    main_frame.pack(fill="both", expand=True, padx=20, pady=20)    
        
    # Variável e switch para alternar o modo de aparência
    switch_var = BooleanVar(value=False)  # False: Light, True: Dark
    def toggle_mode():
        if switch_var.get():
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
    appearance_switch = ctk.CTkSwitch(main_frame, text="Dark Mode", variable=switch_var, command=toggle_mode)
    appearance_switch.pack(pady=10, padx=15, anchor="e")

    # Frame superior: Seleção de arquivos
    frame_files = ctk.CTkFrame(main_frame)
    frame_files.pack(fill="x", pady=10, padx=15)

    ctk.CTkLabel(frame_files, text="Tool de Conversão de PDF e Imagens", 
                 font=ctk.CTkFont(size=18, weight="normal")).pack(pady=5)

    ctk.CTkLabel(frame_files, text="Selecione arquivos para análise", 
                 font=ctk.CTkFont(size=14, weight="bold")).pack(pady=5)

    buttons_frame = ctk.CTkFrame(frame_files)
    buttons_frame.pack(fill="x", pady=5)
    ctk.CTkButton(buttons_frame, text="📄 Carregar PDF", command=carregar_pdf, 
                  font=ctk.CTkFont(size=14)).pack(side="left", expand=True, padx=5, pady=5)
    ctk.CTkButton(buttons_frame, text="🖼️ Carregar Imagem", command=carregar_imagem, 
                  font=ctk.CTkFont(size=14)).pack(side="left", expand=True, padx=5, pady=5)
    ctk.CTkButton(buttons_frame, text="📂 Abrir Pasta Local", command=abrir_pasta_local, 
                  font=ctk.CTkFont(size=14)).pack(side="left", expand=True, padx=5, pady=5)

    # Frame intermediário: Lista e gerenciamento de arquivos
    frame_list = ctk.CTkFrame(main_frame)
    frame_list.pack(pady=10)
    lista_arquivos = ctk.CTkOptionMenu(frame_list, values=[], dynamic_resizing=True)
    lista_arquivos.pack(fill="x", padx=5)
    lista_arquivos.set("Nenhum ficheiro carregado")
    
    manage_buttons_frame = ctk.CTkFrame(frame_list)
    manage_buttons_frame.pack(fill="x", pady=5)
    ctk.CTkButton(manage_buttons_frame, text="Remover Selecionado", command=remover_arquivo_selecionado)\
        .pack(side="left", expand=True, padx=5)
    ctk.CTkButton(manage_buttons_frame, text="Apagar Tudo", command=limpar_tudo)\
        .pack(side="left", expand=True, padx=5)

    # Frame inferior: Entrada de palavras-chave e processamento
    frame_keywords = ctk.CTkFrame(main_frame)
    frame_keywords.pack(fill="x", pady=20)
    ctk.CTkLabel(frame_keywords, text="Palavras-chave (separadas por vírgula):")\
        .pack(pady=5)
    entry_keywords = ctk.CTkEntry(frame_keywords, width=400, 
                                  placeholder_text="ex: produto, preço, validade")
    entry_keywords.pack(fill="x", padx=5, pady=5)
    process_button = ctk.CTkButton(frame_keywords, text="Processar Tudo", 
                                   command=start_processing, font=ctk.CTkFont(size=14))
    process_button.pack(pady=10)
    
    # Widgets de status: rótulo e barra de progresso
    status_label = ctk.CTkLabel(main_frame, text="")
    status_label.pack(pady=5)
    progress_bar = ctk.CTkProgressBar(main_frame, width=400)
    progress_bar.set(0)
    progress_bar.pack(pady=5)

    # Frame de Tutorial: Instruções de uso
    frame_tutorial = ctk.CTkFrame(main_frame)
    frame_tutorial.pack(fill="x", pady=10)
    tutorial_text = (
        "Tutorial de Uso:\n"
        "• Clique em 'Carregar PDF' para selecionar um arquivo PDF.\n"
        "• Clique em 'Carregar Imagem' para selecionar uma imagem (apenas png, jpg, jpeg e bmp).\n"
        "• Utilize 'Remover Selecionado' para excluir um arquivo da lista.\n"
        "• Use 'Apagar Tudo' para limpar todos os arquivos e o campo de palavras-chave.\n"
        "• Insira as palavras-chave separadas por vírgula e clique em 'Processar Tudo' para iniciar a análise.\n"
        "• Para visualizar os resultados, utilize '📂 Abrir Pasta Local'."
    )
    ctk.CTkLabel(frame_tutorial, text=tutorial_text, justify="left",
                 font=ctk.CTkFont(size=12)).pack(padx=5, pady=5)
    
  
    # Rótulo discreto no rodapé
    footer_label = ctk.CTkLabel(main_frame, text="Criado por Carlos Fernandes e Carlos Lemos", font=ctk.CTkFont(size=7), text_color="gray")
    footer_label.pack(side="bottom", pady=5)

    app.mainloop()

if __name__ == "__main__":
    create_interface()
