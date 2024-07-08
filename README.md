
# slurm-scredits
`scredits` is a Slurm utility for checking account balance. The utility calculates the remaining *service units* or *SU* left in the account.
The utility shows SU as an aggregate of cpu+gpu+mem usage.


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
```
pip install scredits
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
Account         | Allocation(SU)  | Remaining(SU)   | Used(SU)   | Used(%) |
-----------------------------------------------------------------------------
test_account    | 1000.0          | 1000.0          | 0          | 0.0
```

If you want more details use the ` -d` flag.
```
[test@localhost ~]$ scredits -d
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


https://pypi.org/project/scredits
