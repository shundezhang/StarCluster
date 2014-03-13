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

dt_config_tmpl = """\
[global]
job_mode: active
qstat_command: /opt/shared/system/torque/3.0.5-cpu/bin/qstat -x -t
pbsnodes_command: /opt/shared/system/torque/3.0.5-cpu/bin/pbsnodes {0} {1}
add_node_command: /opt/shared/system/torque/3.0.5-cpu/bin/qmgr -c "create node {0}"
check_node_command: /opt/shared/system/maui/3.3-gpu-torque-3.0.5/bin/checknode {0}
remove_node_command: /opt/shared/system/torque/3.0.5-cpu/bin/qmgr -c "delete node {0}"
set_node_command: /opt/shared/system/torque/3.0.5-cpu/bin/qmgr -c "set node {0} {1} {2} {3}"
diagnose_p_command: /opt/shared/system/maui/3.3-gpu-torque-3.0.5/bin/diagnose -p

[cloud]
cloud_username: %(CLOUD_USERNAME)s
cloud_password: %(CLOUD_PASSWORD)s
cloud_tenant_name: %(CLOUD_TENANT_NAME)s
cloud_image_uuid: %(CLOUD_IMAGE_UUID)s
cloud_auth_url: https://keystone.rc.nectar.org.au:5000/v2.0/
cloud_key_name: %(CLOUD_KEY_NAME)s
cloud_security_groups: %(CLOUD_SECURITY_GROUP)s
cloud_private_key_location: /etc/dynamictorque/%(CLOUD_KEY_NAME)s.pem
cloud_availability_zone: %(CLOUD_AVAILABILITY_ZONE)s
cloud_vm_prefix: %(CLOUD_SECURITY_GROUP)s-
cloud_vm_init_file:
cloud_vm_userdata_file: /etc/dynamictorque/userdata.sh
#static_core_number: 
max_number_cores_per_vm: 2
dynamic_core_number: %(DYNAMIC_CORE_NUMBER)s
cloud_vm_init_finish_file: /var/run/vmpool/alive

[torque]
torque_queue_to_monitor: batch
node_property: cloud
node_location_property: CLOUD:%(CLOUD_AVAILABILITY_ZONE)s
default_location: 0

[logging]
log_level: DEBUG
log_location: /var/log/dynamictorque/dynamictorque.log
"""

dt_userdata_tmpl = """\
#!/bin/bash

/bin/sed -i 's/^SELINUX=.*$/SELINUX=disabled/' /etc/selinux/config
/usr/sbin/setenforce Permissive

PBS_SERVER=master

sed -i '/master/d' /etc/hosts
cat << EOF >> /etc/hosts
%(MASTER_IP_ADDR)s master
EOF

# figure out correct hostname
IP=$(/sbin/ifconfig eth0 | grep 'inet addr:' | cut -d: -f2 | cut -d' ' -f1)
NAME=$(nslookup $IP | grep "name =" | cut -d" " -f3)
HOSTNAME=$(echo $NAME | sed - -e "s/\.$//")
if [ ! "$(hostname)" = "$HOSTNAME" ]; then
    # set hostname in system files
    /bin/hostname $HOSTNAME
    echo "$IP $HOSTNAME" >> /etc/hosts
    /bin/sed -i -e "s/^HOSTNAME=.*$/HOSTNAME=$HOSTNAME/" /etc/sysconfig/network
fi

groupadd -o -g %(GROUP_ID)s %(GROUP_NAME)s
useradd -o -u %(USER_ID)s -g %(GROUP_ID)s -s `which bash` -m %(USER_NAME)s

yum -d 0 -e 0 -y install nfs-utils nfs-utils-lib
/etc/init.d/rpcbind start

%(MOUNTS)s

/sbin/service pbs_server stop
cat << EOF > /etc/torque/mom/config
\$pbsserver   master
\$logevent    0x1ff
%(USECP)s
EOF

if [ ! -d /var/run/vmpool ]; then
    mkdir -p /var/run/vmpool
fi
touch /var/run/vmpool/alive
"""
