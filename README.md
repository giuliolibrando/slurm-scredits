# slurm-scredits
`scredits` is a Slurm utility for checking account balance. The utility calculates the remaining *service units* or *SU* left in the account.
The utility shows SU as an aggregate of cpu+gpu+mem usage.

Also, there's a companion script ([scredits-crontab-script.sh](https://github.com/giuliolibrando/slurm-scredits/blob/main/scredits-crontab-script.sh)) that can automatically reset accounts credits each X months on clusters.


# Prerequisites
*  Slurm with Accounting enabled.
*  TRES resources enabled and GrpTRESMins billing set.
*  Optionally  gres/gpu enabled and configured.


# Usage
```
usage: scredits [-h] [-v] [-V] [-d] [-a ACCOUNT]

Retrieve and display Slurm usage data.

options:
  -h, --help            show this help message and exit
  -v, --verbose         Print debug messages
  -V, --version         Print program version
  -d, --detailed        Show detailed account and user association
  -a ACCOUNT, --account ACCOUNT
                        Account name to filter results
```


# Installation
Main commandlet
```
pip install scredits
```
To use the credits reset script automation
```
mkdir /etc/scredits && cd /etc/scredits
wget https://github.com/giuliolibrando/slurm-scredits/blob/main/scredits-crontab-script.sh
chmod +x scredits-crontab-script.sh
```
Add this string to crontab to run each midnight (add flags if you need them)
```
sudo crontab -e
0 0 * * * /etc/scredits/scredits-crontab-script.sh
```


# Setting up Slurm
`scredits` currently support the following setup.
* Balance is limited per account
* Account limit is set through  `GrpTRESMins` using `billing` parameter.

Following is an example setup

Creating account `test_account`  with billing balance of 1000
```
sacctmgr add account test_account set GrpTRESMins=billing=1000
```

Add `test_user` user to account `test_account`
```
sacctmgr add user test_user set Account=test_account
sacctmgr add user test_user2 set Account=test_account
```

Checking balance for all the Accounts
```
[test@localhost ~]$ scredits
Last credits reset: 09/07/2024 00:01
Next credits reset: 31/07/2024 23:59
Account         | Allocation(SU)  | Remaining(SU)   | Used(SU)   | Used(%) |
-----------------------------------------------------------------------------
test_account    | 1000.0          | 1000.0          | 0          | 0.0
```

If you want more details use the ` -d` flag.
```
[test@localhost ~]$ scredits -d
Last credits reset: 09/07/2024 00:01
Next credits reset: 31/07/2024 23:59
------------------------------------------------------------------------------------------
Account              | User            | Consumed (SU)   | % SU Usage      | Used Resources
------------------------------------------------------------------------------------------
root                 |                 |                 |                 |
                     | root            | 0               | 0.00%           | cpu=0, mem=0, gpu=0
                     |                 |                 |                 |
                     | Total:          | 0/0             | 0.00%           | cpu=0, mem=0, gpu=0
------------------------------------------------------------------------------------------
test_account         |                 |                 |                 |
                     | test_account    | 0               | 0.00%           | cpu=0, mem=0, gpu=0
                     | test_account2   | 0               | 0.00%           | cpu=0, mem=0, gpu=0
                     |                 |                 |                 |
                     | Total:          | 0/1000          | 0.00%           | cpu=0, mem=0, gpu=0
------------------------------------------------------------------------------------------
```
You can filter for Account with the ` -a` flag
```
[test@localhost ~]$ scredits -d -a test_account
Last credits reset: 09/07/2024 00:01
Next credits reset: 31/07/2024 23:59
------------------------------------------------------------------------------------------
Account              | User            | Consumed (SU)   | % SU Usage      | Used Resources
------------------------------------------------------------------------------------------
test_account         |                 |                 |                 |
                     | test_account    | 0               | 0.00%           | cpu=0, mem=0, gpu=0
                     | test_account2   | 0               | 0.00%           | cpu=0, mem=0, gpu=0
                     |                 |                 |                 |
                     | Total:          | 0/1000          | 0.00%           | cpu=0, mem=0, gpu=0
------------------------------------------------------------------------------------------
```
**N.B.  "Last credits reset" and "Next credits reset" are shown only if the companion crontab script is enabled**

# Crontab script
```
[test@localhost ~]$ /etc/scredits/scredits-crontab-script.sh -h
Usage: ./scredits-crontab-script.sh [-v] [-c CLUSTER] [-h] [-m MONTHS]

Options:
  -v          Enable verbose mode.
  -c CLUSTER  Specify the cluster name(s), separated by commas.
  -m MONTHS   Specify the number of months before the next prune.
  -h          Show this help message.

```
The script accepts multiple clusters with the -c parameter. 


```
root@master1:~/slurm-scredits# ./scredits-crontab-script.sh -v -c clusterA,clusterB
Modifying account aaaaaaa in cluster clusterA
Modifying account bbbbbbb in cluster clusterB
SCREDITS_LAST_PRUNE set to: 2024-07-09-14-39
SCREDITS_NEXT_PRUNE set to: 2024-07-31-23-59
```
The script resets credits each 3 months, if you want to set a different interval use `-m`
```
root@master1:~/slurm-scredits# ./scredits-crontab-script.sh -v -c clusterA,clusterB -m 5
Modifying account aaaaaaa in cluster clusterA
Modifying account bbbbbbb in cluster clusterB
SCREDITS_LAST_PRUNE set to: 2024-07-09-14-39
SCREDITS_NEXT_PRUNE set to: 2024-12-31-23-59
```

# Build yourself

Clone the repo
```
git clone https://github.com/giuliolibrando/slurm-scredits.git
```
enter into the folder
```
cd slurm-scredits
```
install via pip
```
pip install .
```
