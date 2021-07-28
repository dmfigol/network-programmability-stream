from datetime import datetime
from pathlib import Path
import shutil

from nornir import InitNornir

# from nornir_netmiko.tasks import netmiko_send_command
# from nornir.core.filter import F
from nornir_scrapli.tasks import send_command as scrapli_send_command

NR_CONFIG_FILE = "config.yaml"

COMMANDS = [
    "show version",
    "show ip int br",
    "show ip arp",
    "show platform resources",
]

OUTPUT_DIR = Path("output/cli")


def gather_commands(task, commands):
    dt = datetime.now()
    dt_str = dt.strftime("%Y-%m-%dT%H:%M:%S")

    file_path = OUTPUT_DIR / f"{task.host.name}_{dt_str}.txt"
    with open(file_path, "w") as f:
        for command in commands:
            output = task.run(scrapli_send_command, command=command)
            f.write(f"===== {command} ======\n{output.result}\n\n")


def main():
    with InitNornir(config_file=NR_CONFIG_FILE) as nr:
        nr.run(gather_commands, commands=COMMANDS)


if __name__ == "__main__":
    if OUTPUT_DIR.is_dir():
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    main()
