import math
import tkinter as tk
from tkinter import filedialog, ttk

from bucket_manager import create_buckets
from hasher import hash_word_to_bucket
from index_builder import build_index, count_indexed_registers
from index_search import search_with_index_trace
from index_statistics import bucket_chain, collision_statistics, overflow_statistics
from performance_comparator import compare
from table_scan import table_scan

BUCKET_SIZE = 10  # FR: capacidade do bucket definida pela equipe (RN09)
HIGHLIGHT_COLOR = "#c8f7c5"


def read_words(path):
    with open(path, encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def split_into_pages(words, page_size):
    """
    CA02: As páginas devem ser criadas vazias antes de serem carregadas com as palavras.
    RN06 / RN07: Divisão calculada automaticamente (NR / tamanho de página).
    """
    num_pages = math.ceil(len(words) / page_size)
    pages = [[] for _ in range(num_pages)]  # Cria as páginas vazias antes da carga
    for index, word in enumerate(words):
        pages[index // page_size].append(word)
    return pages


def format_int(value):
    return f"{value:_}".replace("_", ".")


def scrolled_list(parent, title):
    """Cria uma lista com barra de rolagem e um título que pode ser atualizado."""
    frame = ttk.Frame(parent)
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(1, weight=1)

    title_var = tk.StringVar(value=title)
    ttk.Label(frame, textvariable=title_var, font="TkHeadingFont").grid(
        row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

    listbox = tk.Listbox(frame, font="TkFixedFont", activestyle="none", exportselection=False)
    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=listbox.yview)
    listbox.configure(yscrollcommand=scrollbar.set)
    listbox.grid(row=1, column=0, sticky="nsew")
    scrollbar.grid(row=1, column=1, sticky="ns")

    return frame, listbox, title_var


def fill_list(listbox, lines, highlight=None):
    listbox.delete(0, "end")
    if lines:
        listbox.insert("end", *lines)
    if highlight is not None:
        listbox.itemconfigure(highlight, background=HIGHLIGHT_COLOR)
        listbox.see(highlight)


def page_lines(page):
    return [f"{position:>6} | {register}" for position, register in enumerate(page)]


def bucket_lines(bucket, highlight_key=None):
    """Monta as linhas de um bucket e da sua cadeia de overflow (CA28)."""
    lines = []
    highlight = None

    for level, current in enumerate(bucket_chain(bucket)):
        title = "Bucket primário" if level == 0 else f"Overflow {level}"
        lines.append(f"── {title} ({len(current.registers)}/{current.bucket_size}) ──")

        for key, page_id in current.registers:
            if key == highlight_key:
                highlight = len(lines)
            lines.append(f"   {key}  →  página {page_id}")

    return lines, highlight


class HashIndexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Índice Hash Estático")

        self.file_path = None
        self.pages = []
        self.buckets = []
        self.highlighted_bucket = None

        self.file_label = tk.StringVar(value="Nenhum arquivo selecionado")
        self.page_size = tk.StringVar()
        self.search_key = tk.StringVar()
        self.bucket_number = tk.StringVar()
        self.search_result = tk.StringVar()
        self.scan_result = tk.StringVar()
        self.status = tk.StringVar(value="Selecione um arquivo .txt para começar.")

        self._build_layout()
        self.search_key.trace_add("write", self._update_search_buttons)

    # ------------------------------------------------------------------ layout

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(3, weight=1)

        # HU02 / HU06 - tamanho da página e construção do índice
        data = ttk.LabelFrame(self.root, text="Construção do índice (HU02 / HU06)", padding=10)
        data.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        data.columnconfigure(3, weight=1)

        ttk.Button(data, text="Selecionar arquivo .txt", command=self.select_file).grid(
            row=0, column=0, sticky="w")
        ttk.Label(data, textvariable=self.file_label).grid(
            row=0, column=1, columnspan=3, sticky="w", padx=10)

        ttk.Label(data, text="Tamanho da página:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(data, textvariable=self.page_size, width=10).grid(
            row=1, column=1, sticky="w", padx=10, pady=(8, 0))
        self.build_button = ttk.Button(
            data, text="Construir índice", command=self.build, state="disabled")
        self.build_button.grid(row=1, column=2, sticky="w", pady=(8, 0))

        # HU06, HU08, HU12 e HU13 - resultados da construção
        results = ttk.LabelFrame(
            self.root, text="Resultados do índice (HU06 / HU08 / HU12 / HU13)", padding=10)
        results.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        results.columnconfigure((1, 3), weight=1)

        self.index_info = {}
        fields = [
            ("registers", "Registros indexados:"),
            ("build_time", "Tempo de construção:"),
            ("pages", "Quantidade de páginas (CA06):"),
            ("buckets", "Buckets (NB / FR):"),
            ("collision_rate", "Taxa de colisões:"),
            ("overflow_rate", "Taxa de overflow:"),
            ("collisions", "Colisões (registros em bucket cheio):"),
            ("overflowed", "Buckets em overflow:"),
            ("longest_chain", "Maior cadeia de overflow:"),
            ("overflow_created", "Buckets de overflow criados:"),
        ]
        for position, (name, text) in enumerate(fields):
            row, column = divmod(position, 2)
            self.index_info[name] = tk.StringVar(value="-")
            ttk.Label(results, text=text).grid(row=row, column=column * 2, sticky="w", pady=2)
            ttk.Label(results, textvariable=self.index_info[name], font="TkHeadingFont").grid(
                row=row, column=column * 2 + 1, sticky="w", padx=10, pady=2)

        # Chave de busca compartilhada entre a busca por índice e o table scan
        search = ttk.LabelFrame(self.root, text="Busca", padding=10)
        search.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        search.columnconfigure(1, weight=1)

        ttk.Label(search, text="Chave de busca:").grid(row=0, column=0, sticky="w")
        key_entry = ttk.Entry(search, textvariable=self.search_key)
        key_entry.grid(row=0, column=1, sticky="ew", padx=10)
        key_entry.bind("<Return>", lambda _event: self.run_index_search())
        self.index_search_button = ttk.Button(
            search, text="Buscar com índice", command=self.run_index_search, state="disabled")
        self.index_search_button.grid(row=0, column=2)
        self.scan_button = ttk.Button(
            search, text="Table scan", command=self.run_table_scan, state="disabled")
        self.scan_button.grid(row=0, column=3, padx=(8, 0))
        self.compare_button = ttk.Button(
            search, text="Comparar", command=self.run_comparison, state="disabled")
        self.compare_button.grid(row=0, column=4, padx=(8, 0))

        # HU14 - visualização das estruturas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=3, column=0, sticky="nsew", padx=10, pady=5)
        self._build_pages_tab()
        self._build_buckets_tab()
        self._build_index_search_tab()
        self._build_scan_tab()
        self._build_comparison_tab()

        self.status_label = ttk.Label(
            self.root, textvariable=self.status, anchor="w", padding=(10, 4), relief="sunken")
        self.status_label.grid(row=4, column=0, sticky="ew")

    def _build_pages_tab(self):
        # CA27: primeira e última página
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Páginas")
        tab.columnconfigure((0, 1), weight=1)
        tab.rowconfigure(0, weight=1)

        frame, self.first_page_list, self.first_page_title = scrolled_list(tab, "Primeira página")
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        frame, self.last_page_list, self.last_page_title = scrolled_list(tab, "Última página")
        frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def _build_buckets_tab(self):
        # CA28: buckets e seus conteúdos
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Buckets")
        tab.columnconfigure(0, weight=1)
        tab.columnconfigure(1, weight=2)
        tab.rowconfigure(1, weight=1)

        go_to = ttk.Frame(tab)
        go_to.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))
        ttk.Label(go_to, text="Ir para o bucket:").pack(side="left")
        bucket_entry = ttk.Entry(go_to, textvariable=self.bucket_number, width=10)
        bucket_entry.pack(side="left", padx=8)
        bucket_entry.bind("<Return>", lambda _event: self.go_to_bucket())
        ttk.Button(go_to, text="Mostrar", command=self.go_to_bucket).pack(side="left")

        frame, self.bucket_list, _ = scrolled_list(tab, "Buckets (clique para ver o conteúdo)")
        frame.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        self.bucket_list.bind("<<ListboxSelect>>", self._on_bucket_selected)

        frame, self.bucket_content_list, self.bucket_content_title = scrolled_list(
            tab, "Conteúdo do bucket")
        frame.grid(row=1, column=1, sticky="nsew", padx=(5, 0))

    def _build_index_search_tab(self):
        # CA29 / RN27: processo de busca e localização do registro
        self.index_search_tab = ttk.Frame(self.notebook, padding=10)
        tab = self.index_search_tab
        self.notebook.add(tab, text="Busca por índice")
        tab.columnconfigure((0, 1), weight=1)
        tab.rowconfigure(2, weight=1)

        ttk.Label(tab, textvariable=self.search_result, font="TkHeadingFont").grid(
            row=0, column=0, columnspan=2, sticky="w")

        self.search_steps = tk.Listbox(tab, height=5, activestyle="none", exportselection=False)
        self.search_steps.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8)

        frame, self.accessed_bucket_list, self.accessed_bucket_title = scrolled_list(
            tab, "Bucket acessado")
        frame.grid(row=2, column=0, sticky="nsew", padx=(0, 5))
        frame, self.accessed_page_list, self.accessed_page_title = scrolled_list(
            tab, "Página acessada")
        frame.grid(row=2, column=1, sticky="nsew", padx=(5, 0))

    def _build_scan_tab(self):
        # HU10: registros lidos durante o table scan
        self.scan_tab = ttk.Frame(self.notebook, padding=10)
        tab = self.scan_tab
        self.notebook.add(tab, text="Table scan")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        ttk.Label(tab, textvariable=self.scan_result, font="TkHeadingFont").grid(
            row=0, column=0, sticky="w", pady=(0, 8))

        frame, self.records_list, _ = scrolled_list(tab, "Registros lidos durante o scan")
        frame.grid(row=1, column=0, sticky="nsew")

    def _build_comparison_tab(self):
        # HU11: Comparativo de tempo e custo entre índice e table scan (CA23 / CA24)
        self.comparison_tab = ttk.Frame(self.notebook, padding=10)
        tab = self.comparison_tab
        self.notebook.add(tab, text="Comparativo (HU11)")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        self.comparison_summary = tk.StringVar(
            value="Digite uma chave e clique em 'Comparar' para visualizar o comparativo.")
        ttk.Label(tab, textvariable=self.comparison_summary, font="TkHeadingFont").grid(
            row=0, column=0, sticky="w", pady=(0, 8))

        columns = ("metric", "index", "scan", "diff")
        self.comparison_tree = ttk.Treeview(tab, columns=columns, show="headings", height=7)
        self.comparison_tree.heading("metric", text="Métrica de Comparação")
        self.comparison_tree.heading("index", text="Busca por Índice (HU09)")
        self.comparison_tree.heading("scan", text="Table Scan (HU10)")
        self.comparison_tree.heading("diff", text="Comparativo / Ganho (HU11)")

        self.comparison_tree.column("metric", width=250, anchor="w")
        self.comparison_tree.column("index", width=180, anchor="center")
        self.comparison_tree.column("scan", width=180, anchor="center")
        self.comparison_tree.column("diff", width=240, anchor="center")

        self.comparison_tree.grid(row=1, column=0, sticky="nsew", pady=(0, 10))

        notes_frame = ttk.LabelFrame(tab, text="Análise Didática de Desempenho", padding=10)
        notes_frame.grid(row=2, column=0, sticky="ew")
        notes_frame.columnconfigure(0, weight=1)

        self.comparison_notes = tk.StringVar(value="-")
        ttk.Label(notes_frame, textvariable=self.comparison_notes, wraplength=850, justify="left").grid(
            row=0, column=0, sticky="w")

    # ------------------------------------------------------------------ estado

    def _set_status(self, message, error=False):
        self.status.set(message)
        self.status_label.configure(foreground="#b00020" if error else "")

    def _update_search_buttons(self, *_args):
        # RN20: as buscas só ficam habilitadas depois que uma chave é digitada
        enabled = bool(self.search_key.get().strip()) and bool(self.pages)
        state = "normal" if enabled else "disabled"
        self.index_search_button.configure(state=state)
        self.scan_button.configure(state=state)
        self.compare_button.configure(state=state)

    def _clear_index(self):
        self.pages = []
        self.buckets = []
        self.highlighted_bucket = None

        for value in self.index_info.values():
            value.set("-")

        for listbox in (self.first_page_list, self.last_page_list, self.bucket_list,
                        self.bucket_content_list, self.search_steps, self.accessed_bucket_list,
                        self.accessed_page_list, self.records_list):
            listbox.delete(0, "end")

        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)

        self.first_page_title.set("Primeira página")
        self.last_page_title.set("Última página")
        self.bucket_content_title.set("Conteúdo do bucket")
        self.accessed_bucket_title.set("Bucket acessado")
        self.accessed_page_title.set("Página acessada")
        self.search_result.set("")
        self.scan_result.set("")
        self.comparison_summary.set("Digite uma chave e clique em 'Comparar' para visualizar o comparativo.")
        self.comparison_notes.set("-")
        self._update_search_buttons()

    # ------------------------------------------------------------------ ações

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo de palavras",
            filetypes=[("Arquivos de texto", "*.txt")],
        )
        if not path:
            return

        self._clear_index()
        self.file_path = path

        # CA02 / CA03: Valida e informa o total de palavras carregadas logo na seleção
        try:
            words = read_words(path)
            if not words:
                self.file_label.set(f"{path} (Arquivo vazio!)")
                self.build_button.configure(state="disabled")
                self._set_status("O arquivo selecionado está vazio.", error=True)
                return

            self.file_label.set(f"{path} ({format_int(len(words))} palavras)")
            self.build_button.configure(state="normal")
            self._set_status(f"Arquivo carregado com sucesso ({format_int(len(words))} palavras). Informe o tamanho da página e construa o índice.")
        except (OSError, UnicodeDecodeError) as error:
            self.file_label.set(f"{path} (Erro de leitura)")
            self.build_button.configure(state="disabled")
            self._set_status(f"Não foi possível ler o arquivo: {error}", error=True)

    def build(self):
        # CA05: com um valor inválido o índice anterior não fica disponível para continuar
        self._clear_index()

        try:
            page_size = int(self.page_size.get())
        except ValueError:
            page_size = 0

        if page_size <= 0:
            self._set_status("Tamanho da página inválido: informe um inteiro maior que zero.", error=True)
            return

        self._set_status("Construindo índice...")
        self.root.configure(cursor="watch")
        self.root.update_idletasks()

        try:
            words = read_words(self.file_path)
            if not words:
                self._set_status("O arquivo selecionado está vazio.", error=True)
                return

            pages = split_into_pages(words, page_size)
            buckets = create_buckets(len(words), BUCKET_SIZE)
            build_info = build_index(pages, buckets, hash_word_to_bucket)
            overflow = overflow_statistics(buckets)
            collisions = collision_statistics(buckets, len(words))
        except (OSError, UnicodeDecodeError) as error:
            self._set_status(f"Não foi possível ler o arquivo: {error}", error=True)
            return
        finally:
            self.root.configure(cursor="")

        self.pages = pages
        self.buckets = buckets

        # CA13: conta os registros armazenados nos buckets e compara com o total do arquivo
        self.index_info["registers"].set(
            f"{format_int(count_indexed_registers(buckets))} de {format_int(len(words))} do arquivo")
        self.index_info["pages"].set(format_int(build_info["pages_read"]))
        self.index_info["buckets"].set(f"{format_int(build_info['number_of_buckets'])} / {BUCKET_SIZE}")
        self.index_info["build_time"].set(f"{build_info['build_time_ms']:.2f} ms")
        self.index_info["collision_rate"].set(f"{collisions['collision_rate_pct']:.2f}%")
        self.index_info["collisions"].set(
            f"{format_int(collisions['collisions'])} de {format_int(len(words))}")
        self.index_info["overflow_rate"].set(f"{overflow['overflow_rate_pct']:.2f}%")
        self.index_info["overflowed"].set(
            f"{format_int(overflow['overflowed_buckets'])} de {format_int(overflow['number_of_buckets'])}")
        self.index_info["overflow_created"].set(format_int(overflow["overflow_buckets_created"]))
        self.index_info["longest_chain"].set(
            f"{overflow['longest_overflow_chain']} bucket(s) de overflow")

        self._show_first_and_last_pages()
        self._show_buckets()
        self._update_search_buttons()
        self._set_status("Índice construído com sucesso.")

    def _show_first_and_last_pages(self):
        last_page_id = len(self.pages) - 1

        for listbox, title, page_id, name in (
            (self.first_page_list, self.first_page_title, 0, "Primeira"),
            (self.last_page_list, self.last_page_title, last_page_id, "Última"),
        ):
            page = self.pages[page_id]
            title.set(f"{name} página: Página {page_id} ({format_int(len(page))} registros)")
            fill_list(listbox, page_lines(page))

    def _show_buckets(self):
        lines = []
        for index, bucket in enumerate(self.buckets):
            extras = sum(1 for _ in bucket_chain(bucket.overflow))
            overflow = f"+{extras} overflow" if extras else ""
            lines.append(f"Bucket {index:>6} | {len(bucket.registers):>3}/{bucket.bucket_size} {overflow}")
        fill_list(self.bucket_list, lines)

    def _show_bucket(self, index, highlight_key=None):
        lines, highlight = bucket_lines(self.buckets[index], highlight_key)
        self.bucket_content_title.set(f"Conteúdo do bucket {index}")
        fill_list(self.bucket_content_list, lines, highlight)

        if self.bucket_list.size() > index:
            self.bucket_list.selection_clear(0, "end")
            self.bucket_list.selection_set(index)
            self.bucket_list.see(index)

    def _on_bucket_selected(self, _event):
        selection = self.bucket_list.curselection()
        if selection:
            self._show_bucket(selection[0])

    def go_to_bucket(self):
        if not self.buckets:
            return

        try:
            index = int(self.bucket_number.get())
        except ValueError:
            index = -1

        if not 0 <= index < len(self.buckets):
            self._set_status(
                f"Bucket inválido: informe um número entre 0 e {len(self.buckets) - 1}.", error=True)
            return

        self._show_bucket(index)
        self._set_status(f"Mostrando o bucket {index}.")

    def _highlight_bucket(self, index):
        if self.bucket_list.size() > index:
            if self.highlighted_bucket is not None and self.bucket_list.size() > self.highlighted_bucket:
                self.bucket_list.itemconfigure(self.highlighted_bucket, background="")
            self.bucket_list.itemconfigure(index, background=HIGHLIGHT_COLOR)
            self.highlighted_bucket = index

    def _search_steps(self, key, result):
        # RN27: ilustra o processo de busca passo a passo
        index = result["bucket_index"]
        steps = [f"1. Função hash: hash('{key}') → bucket {index}"]

        for level in range(result["bucket_reads"]):
            name = "bucket primário" if level == 0 else f"overflow {level}"
            if result["chain_position"] == level:
                outcome = f"chave encontrada → página {result['page_id']}"
            else:
                outcome = "chave não está aqui"
            steps.append(f"{len(steps) + 1}. Leitura do {name} do bucket {index}: {outcome}")

        if result["page_reads"]:
            if result["found"]:
                outcome = f"registro encontrado na posição {result['page_position']}"
            else:
                outcome = "registro não encontrado"
            steps.append(f"{len(steps) + 1}. Leitura da página {result['page_id']}: {outcome}")
        else:
            steps.append(f"{len(steps) + 1}. Fim da cadeia de buckets: chave não encontrada")

        return steps

    def run_index_search(self):
        key = self.search_key.get().strip()
        if not key or not self.buckets:
            return

        result = search_with_index_trace(key, self.buckets, hash_word_to_bucket, self.pages)
        bucket_index = result["bucket_index"]

        # CA29: destaca o bucket acessado (na aba Buckets e aqui) e a página acessada
        self._highlight_bucket(bucket_index)
        self._show_bucket(bucket_index, highlight_key=key)

        lines, highlight = bucket_lines(self.buckets[bucket_index], key)
        self.accessed_bucket_title.set(f"Bucket acessado: {bucket_index}")
        fill_list(self.accessed_bucket_list, lines, highlight)

        fill_list(self.search_steps, self._search_steps(key, result))

        if result["page_id"] is not None:
            self.accessed_page_title.set(f"Página acessada: {result['page_id']}")
            fill_list(self.accessed_page_list, page_lines(self.pages[result["page_id"]]),
                      result["page_position"])
        else:
            self.accessed_page_title.set("Página acessada: nenhuma")
            fill_list(self.accessed_page_list, [])

        reads = "leitura" if result["cost_io"] == 1 else "leituras"
        cost = (f"Custo: {result['cost_io']} {reads} "
                f"({result['bucket_reads']} de bucket + {result['page_reads']} de página)")
        elapsed = f"Tempo: {result['time_ms']:.4f} ms"

        if result["found"]:
            self.search_result.set(
                f"Chave encontrada na página {result['page_id']}  |  {cost}  |  {elapsed}")
        else:
            self.search_result.set(f"Chave não encontrada  |  {cost}  |  {elapsed}")

        self.notebook.select(self.index_search_tab)
        self._set_status(f"Busca por índice executada para '{key}'.")

    def run_table_scan(self):
        key = self.search_key.get().strip()
        if not key or not self.pages:
            return

        self.root.configure(cursor="watch")
        self.root.update_idletasks()

        # Limita a 1.000 registros na visualização para não travar a UI (RNF01)
        result = table_scan(self.pages, key, max_records=1000)

        # CA21: exibe os registros lidos durante o scan
        lines = [f"Página {page_id:>6} | {register}" for page_id, register in result["records_read"]]
        if result["records_truncated"]:
            lines.append(f"... (exibindo os primeiros 1.000 de {format_int(result['records_read_count'])} registros lidos)")

        self.records_list.delete(0, "end")
        self.records_list.insert("end", *lines)
        self.root.configure(cursor="")

        pages_read = result["cost_io"]
        cost = f"Custo: {format_int(pages_read)} {'página lida' if pages_read == 1 else 'páginas lidas'}"
        read = f"Registros lidos: {format_int(result['records_read_count'])}"
        elapsed = f"Tempo: {result['time_ms']:.4f} ms"

        if result["found"]:
            last = self.records_list.size() - 1
            self.records_list.itemconfigure(last, background=HIGHLIGHT_COLOR)
            self.records_list.see(last)
            self.scan_result.set(f"Chave encontrada na página {result['page_id']}  |  {cost}  |  {elapsed}  |  {read}")
        else:
            self.records_list.see("end")
            self.scan_result.set(f"Chave não encontrada  |  {cost}  |  {elapsed}  |  {read}")

        self.notebook.select(self.scan_tab)
        self._set_status(f"Table scan executado para '{key}'.")

    def run_comparison(self):
        # HU11: Executa a comparação entre busca com índice e table scan
        key = self.search_key.get().strip()
        if not key or not self.buckets or not self.pages:
            return

        self.root.configure(cursor="watch")
        self.root.update_idletasks()

        try:
            res = compare(key, self.buckets, hash_word_to_bucket, self.pages)
        finally:
            self.root.configure(cursor="")

        idx = res["index"]
        scn = res["scan"]

        status_text = f"Chave comparada: '{key}' — "
        if res["found"]:
            status_text += f"Encontrada na Página {idx['page_id']}"
        else:
            status_text += "Não encontrada em nenhuma página"
        self.comparison_summary.set(status_text)

        for item in self.comparison_tree.get_children():
            self.comparison_tree.delete(item)

        # 1. Tempo de Execução (CA23)
        t_idx = f"{idx['time_ms']:.4f} ms"
        t_scn = f"{scn['time_ms']:.4f} ms"
        t_red = res["time_reduction_pct"]
        t_diff = res["time_diff_ms"]
        speedup = res["speedup_ratio"]

        if t_diff >= 0:
            diff_time_str = f"Índice {t_red:.1f}% mais rápido ({speedup:.1f}x speedup)"
        else:
            diff_time_str = f"Scan foi {abs(t_red):.1f}% mais rápido (diferença: {abs(t_diff):.4f} ms)"

        self.comparison_tree.insert("", "end", values=(
            "Tempo de Execução (CA23)",
            t_idx,
            t_scn,
            diff_time_str
        ))

        # 2. Custo de I/O / Páginas Lidas (CA24)
        io_idx = f"{idx['cost_io']} leitura(s)"
        io_scn = f"{format_int(scn['cost_io'])} leitura(s)"
        io_red = res["io_reduction_pct"]
        io_diff = res["io_diff"]

        if io_diff > 0:
            diff_io_str = f"Redução de {io_red:.1f}% ({io_diff} leituras economizadas)"
        elif io_diff == 0:
            diff_io_str = "Mesmo custo (0% de redução)"
        else:
            diff_io_str = f"Scan leu {abs(io_diff)} página(s) a menos ({io_red:.1f}%)"

        self.comparison_tree.insert("", "end", values=(
            "Custo de I/O / Páginas Lidas (CA24)",
            io_idx,
            io_scn,
            diff_io_str
        ))

        # 3. Detalhamento dos Acessos
        idx_detail = f"{idx['bucket_reads']} bucket(s) + {idx['page_reads']} pág. dados"
        scn_detail = f"{format_int(scn['cost_io'])} páginas lidas em sequência"
        diff_detail = f"{scn['cost_io'] - idx['cost_io']} página(s) de diferença"
        self.comparison_tree.insert("", "end", values=(
            "Detalhamento dos Acessos",
            idx_detail,
            scn_detail,
            diff_detail
        ))

        # 4. Localização do Registro
        found_idx = f"Página {idx['page_id']}" if idx["found"] else "Não encontrada"
        found_scn = f"Página {scn['page_id']}" if scn["found"] else "Não encontrada"
        match_str = "Ambos concordam" if idx["found"] == scn["found"] else "Divergência"
        self.comparison_tree.insert("", "end", values=(
            "Localização do Registro",
            found_idx,
            found_scn,
            match_str
        ))

        # Notas didáticas explicativas (item 2 dos apontamentos)
        if res["found"] and idx["page_id"] == 0:
            note = (
                "📌 Observação sobre chaves no início do arquivo (Página 0):\n"
                "Para palavras localizadas na página 0, o Table Scan realiza apenas 1 leitura de bloco e para imediatamente. "
                "Já o Índice Hash requer 2 leituras mínimas obrigatórias (1 leitura do bucket do índice + 1 leitura da página de dados). "
                "Por essa razão, o custo do índice nesta faixa inicial pode ser superior ao scan (-100% de redução), o que reflete com precisão o "
                "comportamento real de SGBDs (onde o Query Optimizer prefere Sequential Scan para primeiros blocos ou tabelas muito reduzidas)."
            )
        elif res["found"]:
            note = (
                f"✅ Eficiência do Índice Hash comprovada:\n"
                f"O Índice Hash localizou a chave realizando apenas {idx['cost_io']} leitura(s) de disco (I/O), enquanto o Table Scan precisou "
                f"percorrer sequencialmente {format_int(scn['cost_io'])} páginas. Isso representa uma economia real de {io_red:.1f}% no tráfego de I/O."
            )
        else:
            note = (
                f"❌ Chave não existente no banco de dados:\n"
                f"O Índice Hash detectou que a palavra não existe após consultar apenas {idx['cost_io']} bucket(s). "
                f"Por outro lado, o Table Scan foi forçado a varrer a tabela inteira ({format_int(scn['cost_io'])} páginas lidas) até confirmar a ausência."
            )
        self.comparison_notes.set(note)

        # Destaca o bucket acessado na aba de Buckets
        self._highlight_bucket(idx["bucket_index"])
        self._show_bucket(idx["bucket_index"], highlight_key=key)

        self.notebook.select(self.comparison_tab)
        self._set_status(f"Comparativo executado com sucesso para '{key}'.")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1100x850")
    root.minsize(900, 700)
    HashIndexApp(root)
    root.mainloop()
