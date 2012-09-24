import sys
import time
from optparse import OptionParser
from psphere.client import Client
from psphere.managedobjects import HostSystem

class Host_info:

    def __init__(self, host_ins):

        self.host = host_ins
        self.total_memory = (self.host.summary.hardware.memorySize) / (1024*1024)
        self.total_cpu = self.host.summary.hardware.cpuMhz * self.host.summary.hardware.numCpuCores

class Moniter:

    def __init__(self, options):


        self.hosts = []
        if options.server_ip:
            self.server_ip = options.server_ip
        else:
            print "Please provide server ip"
            sys.exit(1)
        if options.username:
            self.username = options.username
        else:
            print "Please provide user name"
            sys.exit(1)
        if options.password:
            self.password = options.password
        else:
            print "Please provide password"
            sys.exit(1)
        if options.host_system_ips:
            hosts = options.host_system_ips.split(",")
            self.hosts.extend(hosts)
            print "Moniter hosts:", self.hosts
        else:
            print "Please provide Host Sytem IPs to moniter"
            sys.exit(1)

        self.hostsconn_fds = []

    def start(self, interval):

        self.client = self.connect_server()
        self.initialize_hosts()
        self.collect_data(interval)

    def connect_server(self):
        try:
            client = Client(self.server_ip, self.username, self.password)
	    print "connection established"
            return client
        except Exception, e:
            print "exception:", e
            sys.exit(1)

    def create_log(self, h):
        fd = open(str(h)+".log", "w")
        fd.write("=" * 100 + "\n")
        fd.write("START TIME:" + str(time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime()))+ "\n")
        fd.write("=" * 100 + "\n")
        val = "TIME".ljust(18)
        fd.write(val)
        val = "OverallCPU usage".ljust(18)
        fd.write(val)
        val = "OverallMem usage".ljust(18)
        fd.write(val)
        return fd

    def initialize_hosts(self):
        for h in self.hosts:
            fd = self.create_log(h)
            host_ins = HostSystem.get(self.client, name=h)
            host_obj = Host_info(host_ins)
            self.hostsconn_fds.append((fd, host_obj))

    def collect_data(self, interval):
        try:
            for fd,host_obj in self.hostsconn_fds:
                total_mem = str(host_obj.total_memory)
                total_cpu = str(host_obj.total_cpu)
                fd.write("(TOTAL MEMORY:" + total_mem + " TOTAL CPU:" + total_cpu + ")" + "\n")
                fd.write("*" * 100 + "\n")

            initial_time = time.time()
            while True:
		temp_fds = []
                if (time.time() - initial_time) > int(interval):
                    for fd,host_obj in self.hostsconn_fds:
                        host_obj.host.update()
                        cpu = str(host_obj.host.summary.quickStats.overallCpuUsage).ljust(18)
                        mem = str(host_obj.host.summary.quickStats.overallMemoryUsage).ljust(18)
                        cur_time = str(time.strftime("%H:%M:%S", time.gmtime())).ljust(18)
                        #print "cpu:", cpu
                        #print "mem:", mem
			#print "fd:", fd
                        fd.write(cur_time + cpu + mem + "\n")
			fd.close()
			fd = open(str(host_obj.host.name)+".log", "a")
			temp_fds.append((fd, host_obj))
		    initial_time =  time.time()
		if temp_fds:
		    self.hostsconn_fds = []
		    self.hostsconn_fds = temp_fds

        except Exception, e:
            print "Exception in collect_data", str(e)
            sys.exit(1)
	finally:
	    #self.client.logout()
	    fd.close()	

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option( "-i", "--server_ip",
                       action="store",
                       type="string",
                       dest="server_ip",
                       default="",
                       help="Vcenter IP Address")

    parser.add_option( "-u", "--username",
                       action="store",
                       type="string",
                       dest="username",
                       default="",
                       help="Vcenter User name")

    parser.add_option( "-p", "--password",
                       action="store",
                       type="string",
                       dest="password",
                       default="",
                       help="Vcenter Password")

    parser.add_option( "-n", "--interval",
                       action="store",
                       type="string",
                       dest="interval",
                       default="300",
                       help="Time interval to collect data, default is 300(in secs)")

    parser.add_option( "-s", "--host_system_ips",
                        action="store",
                        type="string",
                        dest="host_system_ips",
                        default="",
                        help="Host System IPs")

    options, remainder = parser.parse_args()


    moniter = Moniter(options)
    moniter.start(options.interval)
