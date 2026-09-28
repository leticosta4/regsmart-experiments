from datetime import date
import subprocess

# Lista de repositórios
repos = [
    "aeon",
    "apscheduler",
    "dask",
    "dvc",
    "ipython",
    "librosa",
    "networkx",
    "pytest-django",
    "pytest-xdist",
    "pytorch-lightning",
    "trimesh",
    "ultralytics",
]

# Pega a data atual no formato ISO (YYYY-MM-DD)
hoje = date.today().isoformat()

# Escreve o cabeçalho no arquivo CSV
with open("data/fork_commits.csv", "w", encoding="utf-8") as f:
  f.write("repo,commit,data\n")

  for r in repos:
    url = f"https://github.com/leticosta4/{r}"

    # Executa o comando 'git ls-remote' via subprocesso
    resultado = subprocess.run(
        ["git", "ls-remote", url, "HEAD"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # O output vem no formato "sha\tHEAD", pegamos apenas o hash (sha)
    sha = ""
    if resultado.returncode == 0 and resultado.stdout:
      sha = resultado.stdout.split()[0]

    # Salva a linha no CSV
    f.write(f"{r},{sha},{hoje}\n")

print("Arquivo fork_commits.csv gerado com sucesso!")