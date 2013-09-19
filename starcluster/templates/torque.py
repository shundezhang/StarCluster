mom_config_tmpl = """\
$pbsserver   master
$logevent    255
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
