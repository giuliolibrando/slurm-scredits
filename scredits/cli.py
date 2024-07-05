import argparse
from .scredits import get_slurm_usage, show_account_users

def main():
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

if __name__ == "__main__":
    main()
