# Explicação das GitHub Actions Criadas

Duas GitHub Actions que foram configuradas neste projeto. Ambas têm o mesmo objetivo — bloquear pull requests que contenham arquivos `.view.lkml` vazios — mas utilizam abordagens técnicas diferentes.

## Conceitos Fundamentais do GitHub Actions

Antes de analisar os arquivos, vamos a alguns conceitos básicos:

*   **Workflow (Fluxo de Trabalho):** É o processo automatizado como um todo. Cada arquivo `.yml` que criamos no diretório `.github/workflows` define um workflow.
*   **Event (Evento):** É o que dispara o workflow. No nosso caso, o evento é um `pull_request` para o branch `main`.
*   **Job (Trabalho):** Um workflow é composto por um ou mais jobs que rodam em paralelo por padrão. Cada job é executado em uma máquina virtual nova.
*   **Runner:** É o servidor (máquina virtual) que o GitHub provisiona para executar seu job. Nós especificamos o sistema operacional, como `runs-on: ubuntu-latest`.
*   **Step (Passo):** Cada job é uma sequência de steps. Os steps podem ser comandos de shell (`run`) ou podem usar **actions** pré-construídas (`uses:`).

---

### Action 1: A Abordagem com Script Shell

Este foi o nosso primeiro workflow: `.github/workflows/validate-empty-view-files.yml`. Ele faz toda a lógica de verificação diretamente dentro do arquivo de workflow usando comandos de shell.

**O Código Comentado:**
```yaml
# Nome do workflow, que aparece na aba "Actions" do GitHub.
name: "Block Empty LookML Views"

# Define o gatilho (evento) que inicia o workflow.
on:
  pull_request: # Será executado em pull requests.
    branches:
      - main    # Apenas nos PRs que têm o branch 'main' como destino.

# Define os trabalhos a serem executados.
jobs:
  validate-view-files: # ID do nosso job.
    # Define a máquina virtual que executará o job.
    runs-on: ubuntu-latest
    # Define a sequência de passos do job.
    steps:
      # Passo 1: Baixar o código do repositório para o runner.
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          # fetch-depth: 0 garante que baixamos todo o histórico do git.
          fetch-depth: 0

      # Passo 2: Lógica principal para encontrar e validar os arquivos.
      - name: Find empty .view.lkml files
        run: |
          set -e # Garante que o script pare imediatamente se um comando falhar.

          files=$(git diff --name-only --diff-filter=AM ${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }} | grep '\.view\.lkml$' || true)

          if [ -z "$files" ]; then
            echo "No added or modified .view.lkml files to check."
            exit 0 # Sai com sucesso.
          fi

          empty_files=""
          for file in $files; do
            if [ -f "$file" ] && [ ! -s "$file" ]; then
              echo "::error file=$file::This file is empty and must have content."
              empty_files="$empty_files $file"
            fi
          done

          if [ -n "$empty_files" ]; then
            echo "Found empty .view.lkml files. Failing the workflow."
            exit 1 # Sai com um código de erro, o que faz o job falhar.
          fi
```

---

### Action 2: A Abordagem com Script Python

Este é o nosso segundo workflow: `.github/workflows/validate-with-python.yml`. Ele delega a lógica de verificação para um script Python externo, o que torna o workflow mais limpo e a lógica mais fácil de manter.

**O Workflow (`validate-with-python.yml`):**
```yaml
name: "Block Empty LookML Views (Python)"
on:
  pull_request:
    branches:
      - main
jobs:
  validate-view-files-python:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Find and validate .view.lkml files
        run: |
          set -e
          files=$(git diff --name-only --diff-filter=AM ${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }} | grep '\.view\.lkml$' || true)

          if [ -z "$files" ]; then
            echo "No added or modified .view.lkml files to check."
            exit 0
          fi

          echo "$files" | xargs python .github/scripts/check_empty_files.py
```

**O Script (`.github/scripts/check_empty_files.py`):**
```python
import sys
import os

def main():
    files_to_check = sys.argv[1:]
    empty_files = []

    for file_path in files_to_check:
        if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
            empty_files.append(file_path)

    if empty_files:
        for file_path in empty_files:
            print(f"::error file={file_path}::This file is empty and must have content.")
        sys.exit(1)

    print("All checked files have content.")
    sys.exit(0)

if __name__ == "__main__":
    main()
```

---

### Comparação das Abordagens

| Característica | Abordagem Shell | Abordagem Python |
| :--- | :--- | :--- |
| **Legibilidade** | Menor. A sintaxe do shell (`[ ! -s ]`) pode ser críptica. | Maior. A lógica em Python (`os.path.getsize() == 0`) é mais explícita. |
| **Manutenção** | Mais difícil. Lógicas complexas em shell se tornam difíceis de gerenciar. | Mais fácil. O código é separado, pode ser testado localmente e é mais fácil de expandir. |
| **Dependências** | Nenhuma. O shell e os comandos já vêm instalados nos runners. | Requer um passo extra para instalar o Python (`actions/setup-python`). |
| **Portabilidade** | Alta (dentro de ambientes Linux/macOS). | Altíssima. O script Python pode ser executado em qualquer sistema. |

### Conclusão

Para uma verificação simples como esta, ambas as abordagens funcionam bem. No entanto, à medida que a lógica se torna mais complexa, **separar o código em um script (como o de Python) é quase sempre a melhor prática**, pois torna seu workflow mais limpo, mais fácil de ler, testar e manter.
