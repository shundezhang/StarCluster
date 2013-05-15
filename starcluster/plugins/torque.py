from starcluster import clustersetup
from starcluster.templates import torque
from starcluster.logger import log
import random
import string

MUNGE_KEY = '/etc/munge/munge.key'
SERVER_NAME = '/etc/torque/server_name'
MOM_CONFIG = '/etc/torque/mom/config'
MAUI_CONFIG = '/var/spool/maui/maui.cfg'

class TorquePlugin(clustersetup.DefaultClusterSetup):

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
	mom_config=node.ssh.remote_file(MOM_CONFIG, 'w')
        mom_config.write(torque.mom_config_tmpl)
        mom_config.close()
        node.ssh.execute('service pbs_mom start')

    def _config_maui(self, node):
        maui_config=node.ssh.remote_file(MAUI_CONFIG, 'w')
        maui_config.write(torque.maui_config_tmpl)
        maui_config.close()
        node.ssh.execute('service maui start')

    def _setup_master(self, node):
	self._config_server_name(node)

	munge_key=node.ssh.remote_file(MUNGE_KEY, 'w')
	munge_key.write(self._generate_munge_key(1024))
	munge_key.close()
	node.ssh.execute('chown munge:munge '+MUNGE_KEY)
	node.ssh.execute('chmod 600 '+MUNGE_KEY)
	node.ssh.execute('service munge start')

	node.ssh.execute('service pbs_server start')
	node.ssh.execute('qmgr -c "create queue batch"')
	node.ssh.execute('qmgr -c "set queue batch queue_type = Execution"')
	node.ssh.execute('qmgr -c "set queue batch enabled = True"')
	node.ssh.execute('qmgr -c "set queue batch started = True"')
	node.ssh.execute('qmgr -c "set server default_queue = batch"')
	node.ssh.execute('qmgr -c "set server resources_default.cput = 01:00:00"')
	node.ssh.execute('qmgr -c "set server resources_default.neednodes = 1"')
	node.ssh.execute('qmgr -c "set server auto_node_np = True"')
	#node.ssh.execute('qmgr -c "set server authorized_users = *@master"')
	
	node.ssh.execute('qmgr -c "create node master"')
	self._config_mom(node)

	self._config_maui(node)

    def _setup_worker_node(self, node):
	self._config_server_name(node)
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
        self._setup_master(master)
        log.info("Starting Torque worker nodes")
	
        for node in nodes:
	    master.ssh.execute('qmgr -c "create node '+node.alias+'"')
            self.pool.simple_job(self._setup_worker_node, (node,),
                                 jobid=node.alias)
        self.pool.wait(numtasks=len(nodes))

    def run(self, nodes, master, user, user_shell, volumes):
        try:
            self._nodes = nodes
            self._master = master
            self._user = user
            self._user_shell = user_shell
            self._volumes = volumes
            self._setup_torque()
        finally:
            self.pool.shutdown()

    def on_add_node(self, node, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Adding %s to Torque" % node.alias)
	master.ssh.execute('qmgr -c "create node '+node.alias+'"')
        self._setup_worker_node(node)

    def on_remove_node(self, node, nodes, master, user, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Removing %s from Torque peacefully..." % node.alias)
	master.ssh.execute('pbsnodes -o '+node.alias)
	master.ssh.execute('qmgr -c "delete node '+node.alias+'"')
        node.ssh.execute("service pbs_mom stop")
