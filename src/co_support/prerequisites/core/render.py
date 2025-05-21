import yaml
from prettytable import PrettyTable, HRuleStyle, VRuleStyle
from colorama import Fore, Style


def print_yaml(titles: list[str], data: list[list]) -> str:
    """
    Converts data into a YAML-formatted string.
    """
    yaml_data = []
    for p in data:
        entry = {titles[i]: p[i] for i in range(len(titles))}
        yaml_data.append(entry)
    return yaml.dump(yaml_data, default_flow_style=False, width=float("inf"))


def print_table(titles: list[str], data: list[list]) -> PrettyTable:
    """
    Creates a formatted table using PrettyTable.
    """
    table = PrettyTable()
    table.field_names = titles
    table.hrules = HRuleStyle.ALL
    table.vrules = VRuleStyle.ALL
    table.header = True
    table.max_width = 30
    table.align = "c"
    table.valign = "m"

    for p in data:
        table.add_row([("✔" if p[0] else "✘"), *p[1:]])

    return table


def print_summary(total_failed: int) -> None:
    """
    Prints a summary of the prerequisite checks.
    """
    if total_failed == 0:
        print(Fore.GREEN + "✅ All prerequisites are met!" + Style.RESET_ALL)
    else:
        print(
            Fore.RED + f"❌ {total_failed} prerequisite(s) are missing. "
            "Please review the results." + Style.RESET_ALL
        )
