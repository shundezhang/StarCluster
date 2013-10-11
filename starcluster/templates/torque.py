mom_config_tmpl = """\
$pbsserver   master
$logevent    0x1ff
"""

maui_config_tmpl = """\
# 
# MAUI configuration example
# @(#)maui.cfg David Groep 20031015.1
# for MAUI version 3.2.5
# 
SERVERHOST              master
ADMIN1                  root
ADMINHOST               master
RMTYPE[0]           PBS
RMHOST[0]           master
RMSERVER[0]         master

SERVERPORT            40559
SERVERMODE            NORMAL

# Set PBS server polling interval. Since we have many short jobs
# and want fast turn-around, set this to 10 seconds (default: 2 minutes)
RMPOLLINTERVAL        00:00:10

# a max. 10 MByte log file in a logical location
LOGFILE               /var/log/maui.log
LOGFILEMAXSIZE        10000000
LOGLEVEL              3
"""

epel_repo = """\
[epel]
name=epel
baseurl=http://mirror.internode.on.net/pub/epel/6/$basearch
skip_if_unavailable=1
enabled=1
sslverify=0
gpgcheck=0
"""

umd_repo = """\
[UMD_3_base_SL6]
name=UMD 3 base SL6
baseurl=http://repository.egi.eu/sw/production/umd/3/sl6/$basearch/base
skip_if_unavailable=1
enabled=1
sslverify=0
gpgcheck=0
"""

