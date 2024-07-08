import subprocess
import pandas as pd
import re
import argparse

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

def get_slurm_usage(verbose=False, version=False):
    if version:
        print("scredits version 1.1.1 by Giulio Librando")
        return None  # Restituisci None quando si richiede solo la versione

    # Esegui il comando sshare
    cmd = ['sshare', '-o', 'account,user,GrpTRESRaw,GrpTRESMins', '-P']
    if verbose:
        print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    df = parse_sshare_output(output)

    accounts = []
    for _, row in df.iterrows():
        account = row["Account"]
        user = row["User"]

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
                "Account": account,
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
        print("Nessun dato disponibile.")
        return pd.DataFrame(columns=["Account", "User", "Allocation(SU)", "Remaining(SU)", "Used(SU)", "Used(%)"])

def show_account_users(verbose=False):
    cmd = ['sshare', '-a', '-o', 'account,user,GrpTRESRaw,GrpTRESMins', '-P']
    if verbose:
        print(f"Executing command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    output = result.stdout

    df = parse_sshare_output(output)

    su_data = []
    current_account = None
    account_billing_raw = 0
    account_billing_mins = 0

    for _, row in df.iterrows():
        account = row["Account"]
        user = row["User"]
        grp_tres_raw = row["GrpTRESRaw"]
        grp_tres_mins = row["GrpTRESMins"]

        raw_billing_raw = re.search(r'billing=(\d+)', grp_tres_raw)
        mins_billing_raw = re.search(r'billing=(\d+)', grp_tres_mins)

        su_value_raw = int(raw_billing_raw.group(1)) if raw_billing_raw else 0
        total_su = int(mins_billing_raw.group(1)) if mins_billing_raw else 0

        if account != current_account:
            if current_account and su_data:
                su_data.append(["-" * 20, "-" * 15, "-" * 15, "-" * 15, "-" * 30])
            su_data.append([account, "", "", "", ""])
            current_account = account
            account_billing_raw = 0
            account_billing_mins = total_su

        if user:
            if account_billing_mins > 0:
                user_usage_percent = (su_value_raw / account_billing_mins) * 100
            else:
                user_usage_percent = 0

            resources_used = extract_resources(grp_tres_raw)

            su_data.append(["", user, su_value_raw, f"{user_usage_percent:.2f}%", resources_used])

    print(f"{'Account':<20} | {'User':<15} | {'Consumed (SU)':<15} | {'% SU Usage':<15} | {'Used Resources':<30}")
    print("-" * 90)
    for row in su_data:
        print(f"{row[0]:<20} | {row[1]:<15} | {row[2]:<15} | {row[3]:<15} | {row[4]:<30}")


def extract_resources(raw_usage):
    resources = re.findall(r'(\w+)=(\d+)', raw_usage)
    resources_str = ", ".join([f"{res[0]}={res[1]}" for res in resources if res[0] in ['cpu', 'mem', 'gpu']])
    return resources_str

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retrieve and display Slurm usage data.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print debug messages")
    parser.add_argument("-V", "--version", action="store_true", help="Print program version")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed account and user association")

    args = parser.parse_args()

    if args.version:
        get_slurm_usage(version=True)  # Chiamiamo get_slurm_usage con version=True per stampare la versione
    elif args.detailed:
        show_account_users(verbose=args.verbose)
    else:
        result_df = get_slurm_usage(verbose=args.verbose)
        if not result_df.empty:
            print(f"{'Account':<15} | {'Allocation(SU)':<15} | {'Remaining(SU)':<15} | {'Used(SU)':<10} | {'Used(%)':<7} |")
            print("-" * 77)
            for index, row in result_df.iterrows():
                print(f"{index:<15} | {row['Allocation(SU)']:<15.1f} | {row['Remaining(SU)']:<15.1f} | {row['Used(SU)']:<10.1f} | {row['Used(%)']:<7.1f}")
        else:
            print("Nessun dato disponibile.")
