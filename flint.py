import os
import subprocess
from tabulate import tabulate

GIT_DIR = "/home/biganon/tipee/bael"
WT_DIR = os.path.join(GIT_DIR, ".git", "worktrees")
WT_TO_IGNORE = ("migrations",)
DOCKER_PS_OUTPUT = subprocess.run(("docker", "ps"), capture_output = True, text = True).stdout

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'

# Création du worktree "maître"
worktrees = {
    os.path.basename(os.path.normpath(GIT_DIR)): {
        "directory": GIT_DIR,
        "branch": open(os.path.join(GIT_DIR, ".git", "HEAD"), "r").read().replace("ref: refs/heads/", "").strip(),
    },
}

# Création des worktrees "esclaves"
worktrees.update({worktree: {
    "directory": os.path.dirname(open(os.path.join(WT_DIR, worktree, "gitdir"), "r").read()),
    "branch": open(os.path.join(WT_DIR, worktree, "HEAD"), "r").read().replace("ref: refs/heads/", "").strip(),
} for worktree in os.listdir(WT_DIR) if worktree not in WT_TO_IGNORE})

# Ajout des infos supplémentaires
for worktree_name in worktrees:
    worktree_dir = worktrees[worktree_name]["directory"]
    with open(os.path.join(worktree_dir, ".make.client"), "r") as f:
        worktrees[worktree_name]["client"] = next(l for l in f.read().splitlines() if l.startswith("TIPEE_CLIENT")).split("=")[1].strip()
    with open(os.path.join(worktree_dir, ".make.local"), "r") as f:
        lines = f.read().splitlines()
        worktrees[worktree_name]["ports"] = {
            "mysql": {"port": (p := next(l for l in lines if l.startswith("MYSQL_PORT")).split("=")[1].strip()), "found": p in DOCKER_PS_OUTPUT},
            "redis": {"port": (p := next(l for l in lines if l.startswith("REDIS_PORT")).split("=")[1].strip()), "found": p in DOCKER_PS_OUTPUT},
            "tipee": {"port": (p := next(l for l in lines if l.startswith("TIPEE_PORT")).split("=")[1].strip()), "found": p in DOCKER_PS_OUTPUT},
            "maildev": {"port": (p := next(l for l in lines if l.startswith("MAILDEV_PORT")).split("=")[1].strip()), "found": p in DOCKER_PS_OUTPUT},
        }

# Affichage
table = []
for worktree_name in sorted(worktrees, key=lambda x: worktrees[x]["ports"]["tipee"]["port"]):
    worktree_data = worktrees[worktree_name]
    used_ports = len([p for p in worktree_data["ports"].values() if p["found"]])
    if used_ports == len(worktree_data["ports"]):
        color = Colors.GREEN
    elif used_ports == 0:
        color = Colors.RED
    else:
        color = Colors.PURPLE
    table += (
        (
            color + worktree_name + Colors.END,
            worktree_data["client"],
            worktree_data["branch"],
            "http://localhost:" + worktree_data["ports"]["tipee"]["port"],
        ),
    )

print(tabulate(table, headers = ["Worktree", "Client", "Branche", "URL"], tablefmt="rounded_grid"))
