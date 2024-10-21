import subprocess
import pandas as pd
import re
import argparse
import os
import json
from datetime import datetime

def parse_sshare_output(output):
    lines = output.strip().split('\n')
    data = []
    headers = ["Account", "User", "GrpTRESRaw", "GrpTRESMins"]

    for line in lines[1:]:  # Skip header line
        fields = line.strip().split('|')
        account = fields[0].strip()
        user = fields[1].strip() if len(fields) > 1 else ""
        grp_tres_raw = fields[2].strip() if len(fields) > 2 else ""
        grp_tres_mins = fields[3].strip() if len(fields) > 3 else ""
        data.append([account, user, grp_tres_raw, grp_tres_mins])

    df = pd.DataFrame(data, columns=headers)
    return df

def get_slurm_usage(verbose=False, version=False, account=None):
    if version:
        print("scredits version 1.4")
        return None  # Return None when only version is requested

    # Print prune dates
    last_prune, next_prune = read_prune_dates()
    if last_prune and next_prune:
        print(f"\nLast credits reset: {last_prune}\nNext credits reset: {next_prune}\n")
    else:
        print("Reset dates not found or invalid format.")
    
    # Execute sshare command
    cmd = ['sshare', '-o', 'account,user,GrpTRESRaw,GrpTRESMins', '-P']
    if verbose:
        print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    df = parse_sshare_output(output)

    accounts = []
    for _, row in df.iterrows():
        acc = row["Account"]
        user = row["User"]

        if account and acc != account:
            continue  # Skip if account is specified and does not match

        grp_tres_raw = row["GrpTRESRaw"]
        grp_tres_mins = row["GrpTRESMins"]

        raw_billing = re.search(r'billing=(\d+)', grp_tres_raw)
        mins_billing = re.search(r'billing=(\d+)', grp_tres_mins)

        if raw_billing and mins_billing:
            used_su = int(raw_billing.group(1))
            allocation_su = int(mins_billing.group(1))
            remaining_su = allocation_su - used_su
            used_percent = (used_su / allocation_su) * 100 if allocation_su != 0 else 0

            accounts.append({
                "Account": acc,
                "User": user,
                "Allocation(SU)": allocation_su,
                "Remaining(SU)": remaining_su,
                "Used(SU)": used_su,
                "Used(%)": round(used_percent, 2)
            })

    if accounts:
        result_df = pd.DataFrame(accounts, columns=["Account", "User", "Allocation(SU)", "Remaining(SU)", "Used(SU)", "Used(%)"])
        result_df.set_index("Account", inplace=True)
        return result_df
    else:
        print(f"No data available for account '{account}'." if account else "No data available.")
        return pd.DataFrame(columns=["Account", "User", "Allocation(SU)", "Remaining(SU)", "Used(SU)", "Used(%)"])

def show_account_users(verbose=False, account=None):
    last_prune, next_prune = read_prune_dates()
    
    if last_prune and next_prune:
        print(f"\nLast credits reset: {last_prune}\nNext credits reset: {next_prune}\n")
    else:
        print("Reset dates not found or invalid format.")
    
    cmd = ['sshare', '-a', '-o', 'account,user,GrpTRESRaw,GrpTRESMins', '-P']
    if verbose:
        print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    df = parse_sshare_output(output)

    if account:
        if account not in df['Account'].values:
            print(f"The account '{account}' doesn't exists.")
            return

    su_data = []
    current_account = None
    account_billing_raw = 0
    account_billing_mins = 0
    account_total_usage = 0
    account_resources = {'cpu': 0, 'mem': 0, 'gpu': 0}

    for _, row in df.iterrows():
        acc = row["Account"]
        user = row["User"]
        grp_tres_raw = row["GrpTRESRaw"]
        grp_tres_mins = row["GrpTRESMins"]

        if account and acc != account:
            continue  # Skip if account is specified and does not match

        raw_billing_raw = re.search(r'billing=(\d+)', grp_tres_raw)
        mins_billing_raw = re.search(r'billing=(\d+)', grp_tres_mins)

        su_value_raw = int(raw_billing_raw.group(1)) if raw_billing_raw else 0
        total_su = int(mins_billing_raw.group(1)) if mins_billing_raw else 0

        if acc != current_account:
            if current_account:
                if su_data:
                    account_usage_percent = (account_total_usage / account_billing_mins) * 100 if account_billing_mins > 0 else 0
                    print("-" * 90)
                    su_data.append(" " * 21 + "-" * 69)
                    su_data.append([
                        "", "Total:", f"{account_total_usage}/{account_billing_mins}", f"{account_usage_percent:.2f}%",
                        f"cpu={account_resources['cpu']}, mem={account_resources['mem']}, gpu={account_resources['gpu']}"
                    ])
            su_data.append([acc, "", "", "", ""])
            current_account = acc
            account_billing_raw = 0
            account_billing_mins = total_su
            account_total_usage = 0
            account_resources = {'cpu': 0, 'mem': 0, 'gpu': 0}

        if user:
            if account_billing_mins > 0:
                user_usage_percent = (su_value_raw / account_billing_mins) * 100
            else:
                user_usage_percent = 0

            resources_used = extract_resources(grp_tres_raw)
            resources_dict = {k: int(v) for k, v in re.findall(r'(\w+)=(\d+)', grp_tres_raw)}

            for resource in ['cpu', 'mem', 'gpu']:
                account_resources[resource] += resources_dict.get(resource, 0)

            su_data.append(["", user, su_value_raw, f"{user_usage_percent:.2f}%", resources_used])
            account_total_usage += su_value_raw

    if current_account and su_data:
        account_usage_percent = (account_total_usage / account_billing_mins) * 100 if account_billing_mins > 0 else 0
        su_data.append(" " * 21 + "-" * 69)
        su_data.append([
            "", "Total:", f"{account_total_usage}/{account_billing_mins}", f"{account_usage_percent:.2f}%",
            f"cpu={account_resources['cpu']}, mem={account_resources['mem']}, gpu={account_resources['gpu']}"
        ])

    # Print the table with proper formatting
    print(f"{'Account':<20} | {'User':<15} | {'Consumed (SU)':<15} | {'% SU Usage':<15} | {'Used Resources':<30}")
    print("-" * 90)
    for row in su_data:
        if len(row) >= 5:
            if row[0].startswith('-'):
                print("-" * 90)
            else:
                print(f"{row[0]:<20} | {row[1]:<15} | {row[2]:<15} | {row[3]:<15} | {row[4]:<30}")
            if row[1] == "Total:":
                print("-" * 90)
        else:
            print(row)  # Print any rows that may have caused issues for debugging purposes


def print_json():
    cmd = ['sshare', '-a', '-o', 'account,user,GrpTRESRaw,GrpTRESMins', '-P']
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    # Converti l'output in un DataFrame
    df = parse_sshare_output(output)

    balances = []
    account_totals = {}

    for _, row in df.iterrows():
        acc = row["Account"]
        user = row["User"]
        grp_tres_raw = row["GrpTRESRaw"]

        # Ignora l'account root
        if acc == "root":
            continue

        # Se l'utente è vuoto, si tratta della riga di intestazione per l'account
        if user == "":
            # Billing consumato
            consumed_raw = re.search(r'billing=(\d+)', grp_tres_raw)
            consumed = int(consumed_raw.group(1)) if consumed_raw else 0
            
            # Billing totale
            total_billing_raw = re.search(r'billing=(\d+)$', row["GrpTRESMins"])
            total_billing = int(total_billing_raw.group(1)) if total_billing_raw else 0
            
            # Ignora se il billing totale è zero
            if total_billing == 0:
                continue
            
            # Calcola il rimanente e memorizza il valore
            account_totals[acc] = total_billing - consumed  # Calcola il rimanente
        else:
            # Aggiungi il valore residuo per ogni utente
            if acc in account_totals:
                balances.append({
                    "user": user.strip(),
                    "project": acc,
                    "value": account_totals[acc]
                })

    # Crea l'output JSON
    output_json = {
        "version": 1,
        "timestamp": int(datetime.now().timestamp()),
        "config": {
            "unit": "SU",
            "project_type": "project"
        },
        "balances": balances
    }

    print(json.dumps(output_json, indent=2))

def extract_resources(raw_usage):
    resources = re.findall(r'(\w+)=(\d+)', raw_usage)
    resources_str = ", ".join([f"{res[0]}={res[1]}" for res in resources if res[0] in ['cpu', 'mem', 'gpu']])
    return resources_str

def read_prune_dates():
    last_prune_file = '/etc/scredits/last_prune'
    next_prune_file = '/etc/scredits/next_prune'
    date_format = '%Y-%m-%d-%H-%M'
    
    last_prune, next_prune = None, None
    
    if os.path.exists(last_prune_file):
        with open(last_prune_file, 'r') as file:
            date_str = file.read().strip()
            try:
                last_prune = datetime.strptime(date_str, date_format).strftime('%d/%m/%Y %H:%M')
            except ValueError:
                pass
    
    if os.path.exists(next_prune_file):
        with open(next_prune_file, 'r') as file:
            date_str = file.read().strip()
            try:
                next_prune = datetime.strptime(date_str, date_format).strftime('%d/%m/%Y %H:%M')
            except ValueError:
                pass
    
    return last_prune, next_prune

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and display Slurm usage data.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug messages")
    parser.add_argument("-V", "--version", action="store_true", help="Print program version")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed account and user association")
    parser.add_argument("-a", "--account", type=str, required=False, help="Account name to filter results")

    args = parser.parse_args()

    if args.version:
        get_slurm_usage(version=True)  # Chiamiamo get_slurm_usage con version=True per stampare la versione
    elif args.detailed:
        show_account_users(verbose=args.verbose, account=args.account)
    else:
        last_prune, next_prune = read_prune_dates()
        if last_prune and next_prune:
            print(f"Last credits reset: {last_prune}\nNext credits reset: {next_prune}")
        else:
            print("Reset dates not found or invalid format.")
            
        result_df = get_slurm_usage(verbose=args.verbose, account=args.account)
        if not result_df.empty:
            print(f"{'Account':<15} | {'Allocation(SU)':<15} | {'Remaining(SU)':<15} | {'Used(SU)':<10} | {'Used(%)':<7} |")
            print("-" * 77)
            for index, row in result_df.iterrows():
                print(f"{index:<15} | {row['Allocation(SU)']:<15.1f} | {row['Remaining(SU)']:<15.1f} | {row['Used(SU)']:<10.1f} | {row['Used(%)']:<7.1f}")
        else:
            print("No data available.")
