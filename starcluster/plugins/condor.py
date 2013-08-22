# Copyright 2009-2013 Justin Riley
#
# This file is part of StarCluster.
#
# StarCluster is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# StarCluster is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with StarCluster. If not, see <http://www.gnu.org/licenses/>.

from starcluster import clustersetup
from starcluster.templates import condor
from starcluster.logger import log

CONDOR_CFG = '/etc/condor/config.d/40starcluster'
FS_REMOTE_DIR = '/home/._condor_tmp'


class CondorPlugin(clustersetup.DefaultClusterSetup):

    def _add_condor_node(self, node):
        if node.package_provider == "yum":
	    if node.ssh.get_remote_file_lines('/etc/issue', '5.', True):
            	node.ssh.execute('curl http://research.cs.wisc.edu/htcondor/yum/repo.d/htcondor-stable-rhel5.repo -o /etc/yum.repos.d/htcondor-stable-rhel5.repo')
	    if node.ssh.get_remote_file_lines('/etc/issue', '6.', True):
            	node.ssh.execute('curl http://research.cs.wisc.edu/htcondor/yum/repo.d/htcondor-stable-rhel6.repo -o /etc/yum.repos.d/htcondor-stable-rhel6.repo')
            node.ssh.execute('yum install -y condor')
        if node.package_provider == "apt":
            node.ssh.execute('echo "deb http://research.cs.wisc.edu/htcondor/debian/stable/ squeeze contrib" >> /etc/apt/sources.list')
            node.ssh.execute('apt-get -y update')
            node.ssh.execute('apt-get -y --force-yes install condor')
        condorcfg = node.ssh.remote_file(CONDOR_CFG, 'w')
        daemon_list = "MASTER, STARTD"
        if node.is_master():
            daemon_list += ", SCHEDD, COLLECTOR, NEGOTIATOR"
        ctx = dict(CONDOR_HOST='master', DAEMON_LIST=daemon_list,
                   FS_REMOTE_DIR=FS_REMOTE_DIR)
        condorcfg.write(condor.condor_tmpl % ctx)
        condorcfg.close()
        node.ssh.execute('pkill condor', ignore_exit_status=True)
        node.ssh.execute('/etc/init.d/condor start')

    def _setup_condor(self, master=None, nodes=None):
        log.info("Setting up Condor grid")
        master = master or self._master
        if not master.ssh.isdir(FS_REMOTE_DIR):
            # TODO: below should work but doesn't for some reason...
            #master.ssh.mkdir(FS_REMOTE_DIR, mode=01777)
            master.ssh.mkdir(FS_REMOTE_DIR)
            master.ssh.chmod(01777, FS_REMOTE_DIR)
        nodes = nodes or self.nodes
        log.info("Starting Condor master")
        print master.__dict__
        self._add_condor_node(master)
        log.info("Starting Condor nodes")
        for node in nodes:
            self.pool.simple_job(self._add_condor_node, (node,),
                                 jobid=node.alias)
        self.pool.wait(numtasks=len(nodes))

    def run(self, nodes, master, user, user_id, group_id, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        self._setup_condor()

    def on_add_node(self, node, nodes, master, user, user_id, group_id, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Adding %s to Condor" % node.alias)
        self._add_condor_node(node)

    def on_remove_node(self, node, nodes, master, user, user_id, group_id, user_shell, volumes):
        self._nodes = nodes
        self._master = master
        self._user = user
        self._user_shell = user_shell
        self._volumes = volumes
        log.info("Removing %s from Condor peacefully..." % node.alias)
        master.ssh.execute("condor_off -peaceful %s" % node.alias)
        node.ssh.execute("pkill condor", ignore_exit_status=True)
