import yaml

from prettytable import PrettyTable, HRuleStyle, VRuleStyle
from colorama import Fore, Style


def print_yaml(titles, data):
    yaml_data = []
    for p in data:
        entry = {titles[i]: p[i] for i in range(len(titles))}
        yaml_data.append(entry)
    return yaml.dump(yaml_data, default_flow_style=False, width=float("inf"))


def print_table(titles, data):
    table = PrettyTable()
    table.field_names = titles
    table.hrules = HRuleStyle.ALL
    table.vrules = VRuleStyle.ALL
    table.header = True
    table.max_width = 30
    table.align = "c"
    table.valign = "m"

    for p in data:
        table.add_row([('✔' if p[0] else '✘'), *p[1:]])

    return table


def print_summary(total_failed):
    if total_failed == 0:
        print(Fore.GREEN + "✅ All prerequisites are met!" + Style.RESET_ALL)
    else:
        print(
            Fore.RED + f"❌ {total_failed} prerequisite(s) are missing. "
            "Please review the results." + Style.RESET_ALL
        )
