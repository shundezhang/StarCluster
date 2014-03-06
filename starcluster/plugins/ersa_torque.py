from starcluster import clustersetup
from starcluster.templates import torque
from starcluster.logger import log
from starcluster.config import StarClusterConfig
import random
import string
import time

MUNGE_KEY = '/etc/munge/munge.key'
SERVER_NAME = '/etc/torque/server_name'
MOM_CONFIG = '/var/lib/torque/mom_priv/config'
MAUI_CONFIG = '/var/spool/maui/maui.cfg'
DYNAMIC_TORQUE_CONFIG = '/etc/dynamictorque/dynamic_torque.conf'
DYNAMIC_TORQUE_USERDATA= '/etc/dynamictorque/userdata.sh'
DYNAMIC_TORQUE_DIR = '/etc/dynamictorque'

class ErsaTorquePlugin(clustersetup.DefaultClusterSetup):

    def __init__(self, enable_dynamic=False, os_username=None, os_password=None, os_tenant_name=None, os_image_uuid=None, os_key_name=None, dynamic_core_number="0"):
	super(ErsaTorquePlugin, self).__init__()
	self._enable_dynamic=enable_dynamic
        self._os_username=os_username
        self._os_password=os_password
        self._os_tenant_name=os_tenant_name
        self._os_image_uuid=os_image_uuid
        self._os_key_name=os_key_name
        self._dynamic_core_number=dynamic_core_number
        self._cfg=StarClusterConfig()
        self._cfg.load()
        log.debug("cfg: %s" % self._cfg)

    def _generate_munge_key(self, N):
	return ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(N))

    def _get_munge_key(self, master):
	munge_key=node.ssh.remote_file(MUNGE_KEY, 'r')
	content=munge_key.readlines()
	munge_key.close()
	return content

    def _config_server_name(self, node):
        server_name=node.ssh.remote_file(SERVER_NAME, 'w')
        server_name.write('master')
        server_name.close()

    def _config_mom(self, node):
	mount_map = node.get_mount_map()
	log.debug("mount_map %s"%mount_map)
	usecp_string = ""
	if node.is_master():
	    usecp_string = "$usecp *:/ /"
	else:
	    for mount_point in mount_map:
	        if ":" in mount_point:
		    dir_name=mount_point.split(":")[1]
		    usecp_string+="$usecp *:"+dir_name+"/ "+dir_name+"/\n"
	mom_config=node.ssh.remote_file(MOM_CONFIG, 'w')
        mom_config.write(torque.mom_config_tmpl + usecp_string)
        mom_config.close()
        node.ssh.execute('service pbs_mom restart')

    def _config_maui(self, node):
        maui_config=node.ssh.remote_file(MAUI_CONFIG, 'w')
        maui_config.write(torque.maui_config_tmpl)
        maui_config.close()
        node.ssh.execute('service maui restart')

    def _setup_master(self, node):
	#self._config_server_name(node)
	node.ssh.execute('yum install -y denyhosts', ignore_exit_status=True)

	#munge_key=node.ssh.remote_file(MUNGE_KEY, 'w')
	#munge_key.write(self._generate_munge_key(1024))
	#munge_key.close()
	#node.ssh.execute('chown munge:munge '+MUNGE_KEY)
	#node.ssh.execute('chmod 600 '+MUNGE_KEY)
	#node.ssh.execute('service munge restart')

	#node.ssh.execute('service pbs_server start')
	#node.ssh.execute('qmgr -c "create queue batch"')
	#node.ssh.execute('qmgr -c "set queue batch queue_type = Execution"')
	#node.ssh.execute('qmgr -c "set queue batch enabled = True"')
	#node.ssh.execute('qmgr -c "set queue batch started = True"')
	#node.ssh.execute('qmgr -c "set server default_queue = batch"')
	#node.ssh.execute('qmgr -c "set server resources_default.cput = 01:00:00"')
	#node.ssh.execute('qmgr -c "set server resources_default.neednodes = 1"')
	#node.ssh.execute('qmgr -c "set server auto_node_np = True"')
	#node.ssh.execute('qmgr -c "set server authorized_users = *@master"')
	
	#node.ssh.execute('qmgr -c "create node master"')
	#self._config_mom(node)

	#self._config_maui(node)

    def _setup_worker_node(self, node):
	#self._config_server_name(node)
	node.ssh.execute('/sbin/service pbs_server stop', ignore_exit_status=True)
	self._config_mom(node)

    def _setup_torque(self, master=None, nodes=None):
        log.info("Setting up Torque cluster")
        master = master or self._master
        #if not master.ssh.isdir(FS_REMOTE_DIR):
        #    # TODO: below should work but doesn't for some reason...
        #    #master.ssh.mkdir(FS_REMOTE_DIR, mode=01777)
        #    master.ssh.mkdir(FS_REMOTE_DIR)
        #    master.ssh.chmod(01777, FS_REMOTE_DIR)
        nodes = nodes or self.nodes
        log.info("Starting Torque headnode")
        log.debug('master %s' % master.__dict__)
        log.debug('master.instance %s' % master.instance.__dict__)
        self._setup_master(master)
        log.info("Starting Torque worker nodes")
	
        for node in nodes:
	    master.ssh.execute('qmgr -c "create node '+node.alias+'"')
            self.pool.simple_job(self._setup_worker_node, (node,),
                                 jobid=node.alias)
        self.pool.wait(numtasks=len(nodes))

    def _configure_dynamic_torque(self, master, user, user_id, group_id):
	master.ssh.execute('yum install -y git python-pip python-devel gcc-c++ make', ignore_exit_status=True)
	master.ssh.execute('pip install python-novaclient', ignore_exit_status=True)
	master.ssh.execute('cd /opt; git clone https://github.com/shundezhang/dynamictorque.git')
	master.ssh.execute('cp /opt/dynamictorque/scripts/dynamictorque /etc/init.d/')
	master.ssh.mkdir('/var/log/dynamictorque')
	master.ssh.mkdir('/etc/dynamictorque')
        dt_cfg = master.ssh.remote_file(DYNAMIC_TORQUE_CONFIG, 'w')
	log.debug("sg %s"%master.instance.groups[0].__dict__)
	log.debug("sg name %s"%master.instance.groups[0].name)
        ctx = dict(CLOUD_USERNAME=self._os_username, CLOUD_PASSWORD=self._os_password,
                   CLOUD_TENANT_NAME=self._os_tenant_name, CLOUD_IMAGE_UUID=self._os_image_uuid,
		   CLOUD_KEY_NAME=self._os_key_name, CLOUD_SECURITY_GROUP=master.instance.groups[0].id,
		   CLOUD_AVAILABILITY_ZONE=master.instance._placement, DYNAMIC_CORE_NUMBER=self._dynamic_core_number)
        dt_cfg.write(torque.dt_config_tmpl % ctx)
        dt_cfg.close()
	master.ssh.put(master.key_location, DYNAMIC_TORQUE_DIR+'/'+self._os_key_name+".pem")
        usecp_string = ""
	mount_string=""
	export_paths = self._get_nfs_export_paths()
	log.debug(export_paths)
        for path in export_paths:
            usecp_string+="\$usecp *:"+path+"/ "+path+"/\n"
            mount_string+="mkdir -p "+path+";mount -t nfs -o vers=3,user,rw,exec,noauto master:"+path+"/ "+path+"\n"

        dt_userdata = master.ssh.remote_file(DYNAMIC_TORQUE_USERDATA, 'w')
        ctx = dict(MASTER_IP_ADDR=master.instance.ip_address, USECP=usecp_string, MOUNTS=mount_string, GROUP_ID=group_id, GROUP_NAME=user, 
		   USER_ID=user_id, USER_NAME=user)
	dt_userdata.write(torque.dt_userdata_tmpl % ctx)
	dt_userdata.close()

    def run(self, nodes, master, user, user_id, group_id, user_shell, volumes):
        try:
            self._nodes = nodes
            self._master = master
            self._user = user
            self._user_shell = user_shell
            self._volumes = volumes
            self._setup_torque()
        finally:
            self.pool.shutdown()
	log.debug("cfg: %s" % self._cfg.aws)
	log.debug("cfg: %s" % self._cfg.__dict__)
        if self._enable_dynamic:
            log.info("Configure Dynamic Torque...")
            self._configure_dynamic_torque(master, user, user_id, group_id)

    def on_add_node(self, node, nodes, master, user, user_id, group_id, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Adding %s to Torque" % node.alias)
	master.ssh.execute('qmgr -c "create node '+node.alias+'"')
        self._setup_worker_node(node)

    def on_remove_node(self, node, nodes, master, user, user_id, group_id, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Removing %s from Torque peacefully..." % node.alias)
	master.ssh.execute('pbsnodes -o '+node.alias)
        worker_node_drained = False
	log.info("waiting for node to be drained in maui...")
        while not worker_node_drained:
            if master.ssh.execute('checknode '+node.alias+'|grep Drained', ignore_exit_status=True):
		worker_node_drained = True
	    time.sleep(2)
	log.info("node is drained in maui, go on to delete it in torque...")
	master.ssh.execute('qmgr -c "delete node '+node.alias+'"')
        node.ssh.execute("service pbs_mom stop")
	master.ssh.execute('service maui restart')
