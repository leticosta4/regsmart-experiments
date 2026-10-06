import subprocess

"""
- gh auth status
- python3 experiments_labels.py
"""


SOURCE_REPO = "leticosta4/ipython"

TARGET_REPOS = [
    "leticosta4/librosa",
    "leticosta4/pytest-xdist",
    "leticosta4/pytest-django",
    "leticosta4/dvc",
    "leticosta4/dask",
    "leticosta4/pytorch-lightning",
    "leticosta4/ultralytics",
    "leticosta4/networkx",
    "leticosta4/trimesh",
    "leticosta4/aeon",
    "leticosta4/apscheduler",
]


def run_gh(*args: str) -> str:
    result = subprocess.run(
        ["gh", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def get_labels(repo: str) -> list[str]:
    output = run_gh(
        "label",
        "list",
        "--repo",
        repo,
        "--json",
        "name",
        "--jq",
        ".[].name",
    )

    if not output:
        return []

    return output.splitlines()


def delete_labels(repo: str) -> None:
    labels = get_labels(repo)

    for label in labels:
        print(f"  Removendo label: {label}")
        run_gh(
            "label",
            "delete",
            label,
            "--repo",
            repo,
            "--yes",
        )


def clone_labels(repo: str) -> None:
    print(f"  Copiando labels de {SOURCE_REPO}...")
    run_gh(
        "label",
        "clone",
        SOURCE_REPO,
        "--repo",
        repo,
    )


def main() -> None:
    for repo in TARGET_REPOS:
        print(f"\n=== {repo} ===")

        print("Removendo labels existentes...")
        delete_labels(repo)

        clone_labels(repo)

        print("Concluído!")


if __name__ == "__main__":
    main()
