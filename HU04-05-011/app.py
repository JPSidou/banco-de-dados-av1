import tkinter as tk
from tkinter import filedialog, ttk

from bucket_manager import create_buckets
from hasher import hash_word_to_bucket
from index_builder import build_index, count_indexed_registers
from index_statistics import overflow_statistics
from table_scan import table_scan

BUCKET_SIZE = 10  # FR: capacidade do bucket definida pela equipe (RN09)


def read_words(path):
    with open(path, encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def split_into_pages(words, page_size):
    return [words[i:i + page_size] for i in range(0, len(words), page_size)]


def format_int(value):
    return f"{value:_}".replace("_", ".")


class HashIndexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Índice Hash Estático")

        self.file_path = None
        self.pages = []
        self.buckets = []

        self.file_label = tk.StringVar(value="Nenhum arquivo selecionado")
        self.page_size = tk.StringVar()
        self.search_key = tk.StringVar()
        self.scan_result = tk.StringVar()
        self.status = tk.StringVar(value="Selecione um arquivo .txt para começar.")

        self._build_layout()
        self.search_key.trace_add("write", self._update_scan_button)

    def _build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(2, weight=1)

        # HU06 - construção do índice
        data = ttk.LabelFrame(self.root, text="Construção do índice (HU06)", padding=10)
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

        # HU06 (CA14) e HU13 (CA26) - resultados da construção
        results = ttk.LabelFrame(self.root, text="Resultados do índice (HU06 / HU13)", padding=10)
        results.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        results.columnconfigure((1, 3), weight=1)

        self.index_info = {}
        fields = [
            ("registers", "Registros indexados:"),
            ("build_time", "Tempo de construção:"),
            ("pages", "Páginas percorridas:"),
            ("overflow_rate", "Taxa de overflow:"),
            ("buckets", "Buckets (NB / FR):"),
            ("overflowed", "Buckets em overflow:"),
        ]
        for position, (name, text) in enumerate(fields):
            row, column = divmod(position, 2)
            self.index_info[name] = tk.StringVar(value="-")
            ttk.Label(results, text=text).grid(row=row, column=column * 2, sticky="w", pady=2)
            ttk.Label(results, textvariable=self.index_info[name], font="TkHeadingFont").grid(
                row=row, column=column * 2 + 1, sticky="w", padx=10, pady=2)

        # HU10 - table scan
        scan = ttk.LabelFrame(self.root, text="Table scan (HU10)", padding=10)
        scan.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        scan.columnconfigure(1, weight=1)
        scan.rowconfigure(2, weight=1)

        ttk.Label(scan, text="Chave de busca:").grid(row=0, column=0, sticky="w")
        key_entry = ttk.Entry(scan, textvariable=self.search_key)
        key_entry.grid(row=0, column=1, sticky="ew", padx=10)
        key_entry.bind("<Return>", lambda event: self.run_table_scan())
        self.scan_button = ttk.Button(
            scan, text="Table scan", command=self.run_table_scan, state="disabled")
        self.scan_button.grid(row=0, column=2)

        ttk.Label(scan, textvariable=self.scan_result, font="TkHeadingFont").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=8)

        list_frame = ttk.Frame(scan)
        list_frame.grid(row=2, column=0, columnspan=3, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.records_list = tk.Listbox(list_frame, font="TkFixedFont", activestyle="none")
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.records_list.yview)
        self.records_list.configure(yscrollcommand=scrollbar.set)
        self.records_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.status_label = ttk.Label(
            self.root, textvariable=self.status, anchor="w", padding=(10, 4), relief="sunken")
        self.status_label.grid(row=3, column=0, sticky="ew")

    def _set_status(self, message, error=False):
        self.status.set(message)
        self.status_label.configure(foreground="#b00020" if error else "")

    def _update_scan_button(self, *args):
        # RN20: o botão só fica habilitado depois que uma chave é digitada
        enabled = bool(self.search_key.get().strip()) and bool(self.pages)
        self.scan_button.configure(state="normal" if enabled else "disabled")

    def select_file(self):
        path = filedialog.askopenfilename(
            title="Selecione o arquivo de palavras",
            filetypes=[("Arquivos de texto", "*.txt")],
        )
        if not path:
            return

        self.file_path = path
        self.file_label.set(path)
        self.build_button.configure(state="normal")
        self._set_status("Arquivo selecionado. Informe o tamanho da página e construa o índice.")

    def build(self):
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
        self.index_info["overflow_rate"].set(f"{overflow['overflow_rate_pct']:.2f}%")
        self.index_info["overflowed"].set(
            f"{format_int(overflow['overflowed_buckets'])} de {format_int(overflow['number_of_buckets'])}")

        self.records_list.delete(0, "end")
        self.scan_result.set("")
        self._update_scan_button()
        self._set_status("Índice construído com sucesso.")

    def run_table_scan(self):
        key = self.search_key.get().strip()
        if not key or not self.pages:
            return

        self.root.configure(cursor="watch")
        self.root.update_idletasks()

        result = table_scan(self.pages, key)

        # CA21: exibe todos os registros lidos durante o scan
        lines = [f"Página {page_id:>6} | {register}" for page_id, register in result["records_read"]]
        self.records_list.delete(0, "end")
        self.records_list.insert("end", *lines)
        self.root.configure(cursor="")

        pages_read = result["cost_io"]
        cost = f"Custo: {format_int(pages_read)} {'página lida' if pages_read == 1 else 'páginas lidas'}"
        read = f"Registros lidos: {format_int(result['records_read_count'])}"

        if result["found"]:
            last = self.records_list.size() - 1
            self.records_list.itemconfigure(last, background="#c8f7c5")
            self.records_list.see(last)
            self.scan_result.set(f"Chave encontrada na página {result['page_id']}  |  {cost}  |  {read}")
        else:
            self.records_list.see("end")
            self.scan_result.set(f"Chave não encontrada  |  {cost}  |  {read}")


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("900x650")
    root.minsize(700, 500)
    HashIndexApp(root)
    root.mainloop()
