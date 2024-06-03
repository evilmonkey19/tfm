"""
This file generates the following topology within Mininet.

        h1 --- swa1 --- swc1 --- swc2 --- swa2 ---- h2
                         |        |
                         |        |
                         |        |
        h3 --- swa3 --- swc3 --- swc4 --- swa4 --- swa5 --- h4

"""

from mininet.topo import Topo
from mininet.cli import CLI
from mininet.log import setLogLevel
from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch

class Experiment1( Topo ):
    """ Experiment SDN topology. """
    def build(self):
        # switch core
        sw_core_1 = self.addSwitch('swc1')
        sw_core_2 = self.addSwitch('swc2')
        sw_core_3 = self.addSwitch('swc3')
        sw_core_4 = self.addSwitch('swc4')

        # switch access
        sw_access_1 = self.addSwitch('swa1')
        sw_access_2 = self.addSwitch('swa2')
        sw_access_3 = self.addSwitch('swa3')
        sw_access_4 = self.addSwitch('swa4')
        sw_access_5 = self.addSwitch('swa5')

        # Hosts
        host_1 = self.addHost('h1', ip='10.0.0.1/24')
        host_2 = self.addHost('h2', ip='10.0.0.2/24')
        host_3 = self.addHost('h3', ip='10.0.0.3/24')
        host_4 = self.addHost('h4', ip='10.0.0.4/24')

        # Add links
        self.addLink(sw_core_1, sw_core_2)
        self.addLink(sw_core_2, sw_core_3)
        self.addLink(sw_core_3, sw_core_4)
        self.addLink(sw_core_4, sw_core_1)
        self.addLink(sw_core_1, sw_access_1)
        self.addLink(sw_core_2, sw_access_2)
        self.addLink(sw_core_3, sw_access_3)
        self.addLink(sw_core_4, sw_access_4)
        self.addLink(sw_access_4, sw_access_5)
        self.addLink(sw_access_1, host_1)
        self.addLink(sw_access_2, host_2)
        self.addLink(sw_access_3, host_3)
        self.addLink(sw_access_5, host_4)

def allow_all(net):
    for switch in net.switches:
        if isinstance(switch, OVSSwitch):
            switch.dpctl('add-flow', 'priority=0,actions=normal')

def runExperiment1():
    topo = Experiment1()
    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController( name, ip='127.0.0.1', port=6653),
        switch=OVSSwitch,
        autoSetMacs=True
        )
    
    net.start()
    h1_pcap = h1.popen('tcpdump -w h1.pcap')
    h1_pcap.terminate()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    runExperiment1()

topos = { 'experiment1': Experiment1 }