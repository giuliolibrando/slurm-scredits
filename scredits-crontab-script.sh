#!/bin/bash

# =============================================================================
# Script Name: scredits-crontab-script.sh
# Description: N.B: This script is a companion of the command scredits. 
#              This script prunes Slurm accounts and users raw usage after N months, resettings billing and resouces consumpion (cpu, gpu, mem). 
#              It supports verbose mode, specifying multiple clusters, and sets the next prune date.
# Author:      Giulio Librando <giuliolibrando@gmail.com>
# Created:     09/07/2024 v1.1
# License:     MIT
# =============================================================================


# Default to non-verbose mode and no cluster specified
VERBOSE=false
CLUSTER_SPECIFIED=false
MONTHS=3

# Function to display help
show_help() {
    echo "Usage: $0 [-v] [-c CLUSTER] [-h] [-m MONTHS]"
    echo ""
    echo "Options:"
    echo "  -v          Enable verbose mode."
    echo "  -c CLUSTER  Specify the cluster name(s), separated by commas."
    echo "  -m MONTHS   Specify the number of months before the next prune."
    echo "  -h          Show this help message."
}

# Parse command line options
while getopts ":vc:m:h" opt; do
  case $opt in
    v)
      VERBOSE=true
      ;;
    c)
      CLUSTER_SPECIFIED=true
      CLUSTER="$OPTARG"
      ;;
    m)
      if [[ "$OPTARG" =~ ^[0-9]+$ ]]; then
        MONTHS="$OPTARG"
      else
        echo "Option -m requires a numeric argument."
        show_help
        exit 1
      fi
      ;;
    h)
      show_help
      exit 0
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      show_help
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      show_help
      exit 1
      ;;
  esac
done
# Shift past all options
shift $((OPTIND - 1))

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root."
    exit 1
fi

# Function for verbose output
verbose_echo() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo "$@"
    fi
}

# Ensure directory /etc/scredits exists and has correct permissions
SCREDITS_DIR="/etc/scredits"
if [[ ! -d "$SCREDITS_DIR" ]]; then
    mkdir -p "$SCREDITS_DIR"
    chmod 755 "$SCREDITS_DIR"
fi

# Ensure file /etc/scredits/last_prune exists and has correct permissions
LAST_PRUNE_FILE="$SCREDITS_DIR/last_prune"
if [[ ! -f "$LAST_PRUNE_FILE" ]]; then
    echo "2024-07-09-15-47" > "$LAST_PRUNE_FILE"
    chmod 644 "$LAST_PRUNE_FILE"
fi

# Ensure file /etc/scredits/next_prune exists and has correct permissions
NEXT_PRUNE_FILE="$SCREDITS_DIR/next_prune"
if [[ ! -f "$NEXT_PRUNE_FILE" ]]; then
    echo "2024-10-31-23-59" > "$NEXT_PRUNE_FILE"
    chmod 644 "$NEXT_PRUNE_FILE"
fi

# Read values from /etc/scredits/last_prune and /etc/scredits/next_prune
SCREDITS_LAST_PRUNE=$(cat "$LAST_PRUNE_FILE")
SCREDITS_NEXT_PRUNE=$(cat "$NEXT_PRUNE_FILE")

# Check format of SCREDITS_LAST_PRUNE and SCREDITS_NEXT_PRUNE
if ! [[ $SCREDITS_LAST_PRUNE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}$ && $SCREDITS_NEXT_PRUNE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "SCREDITS_LAST_PRUNE and SCREDITS_NEXT_PRUNE in $SCREDITS_DIR must be in the format yyyy-mm-dd-hh-mm."
    exit 1
fi

# Execute "sacctmgr list account -P" and save account names in ACCOUNT_LIST variable
ACCOUNT_LIST=$(sacctmgr list account -P | awk -F'|' '{print $1}')

# Estrai anno, mese, giorno, ora e minuti dalla data
YEAR=$(echo "$SCREDITS_NEXT_PRUNE" | cut -d'-' -f1)
MONTH=$(echo "$SCREDITS_NEXT_PRUNE" | cut -d'-' -f2)
DAY=$(echo "$SCREDITS_NEXT_PRUNE" | cut -d'-' -f3)
HOUR=$(echo "$SCREDITS_NEXT_PRUNE" | cut -d'-' -f4)
MINUTE=$(echo "$SCREDITS_NEXT_PRUNE" | cut -d'-' -f5)

# Costruisci la data in formato Unix timestamp
SCREDITS_NEXT_PRUNE_TIMESTAMP=$(date -d "${YEAR}-${MONTH}-${DAY} ${HOUR}:${MINUTE}:00" +'%s')

echo "Timestamp Unix per SCREDITS_NEXT_PRUNE: $NEXT_PRUNE_TIMESTAMP"
# Loop over each account retrieved
for account in $ACCOUNT_LIST; do
    # Skip the header "Account"
    if [[ "$account" == "Account" ]]; then
        continue
    fi

    # Get current timestamp
    CURRENT_TIMESTAMP=$(date +'%s')

    # Compare current timestamp with SCREDITS_NEXT_PRUNE timestamp
    if [[ "$CURRENT_TIMESTAMP" -ge "$SCREDITS_NEXT_PRUNE_TIMESTAMP" ]]; then
        verbose_echo "Modifying account $account"

        # Create temporary file for 'y' input
        TMPFILE=$(mktemp)
        echo "y" > "$TMPFILE"

        # Execute command to modify account for each cluster, feeding 'y' from TMPFILE
        if [[ "$CLUSTER_SPECIFIED" == "true" ]]; then
            IFS=',' read -r -a CLUSTERS <<< "$CLUSTER"
            for cl in "${CLUSTERS[@]}"; do
                verbose_echo "  in cluster $cl"
                sacctmgr modify account $account cluster="$cl" set RawUsage= < "$TMPFILE"
            done
        else
            sacctmgr modify account $account set RawUsage= < "$TMPFILE"
        fi

        # Remove temporary file
        rm "$TMPFILE"
    else
        verbose_echo "Skipping modification of account $account because current date is not yet at SCREDITS_NEXT_PRUNE or has passed"
    fi
done
# Set SCREDITS_LAST_PRUNE to current date and time
SCREDITS_LAST_PRUNE=$(date +'%Y-%m-%d-%H-%M')

# Calculate the date N months ahead from the first day of the current month
CURRENT_MONTH=$(date +'%Y-%m')
NEXT_PRUNE=$(date -d "$CURRENT_MONTH-01 +$((MONTHS-1)) months" +'%Y-%m-%d')

# Calculate the last day of the month for the NEXT_PRUNE
LAST_DAY=$(date -d "$NEXT_PRUNE +1 month -1 day" +'%Y-%m-%d')

# Format SCREDITS_NEXT_PRUNE as yyyy-mm-dd-hh-mm
SCREDITS_NEXT_PRUNE=$(date -d "$LAST_DAY 23:59" +'%Y-%m-%d-%H-%M')

# Update /etc/scredits/last_prune and /etc/scredits/next_prune with new values
echo "$SCREDITS_LAST_PRUNE" > "$LAST_PRUNE_FILE"
echo "$SCREDITS_NEXT_PRUNE" > "$NEXT_PRUNE_FILE"

# Output the set variables
verbose_echo "SCREDITS_LAST_PRUNE set to: $SCREDITS_LAST_PRUNE"
verbose_echo "SCREDITS_NEXT_PRUNE set to: $SCREDITS_NEXT_PRUNE"

# Exit the script
exit 0
