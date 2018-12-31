from ats import topology
from genie.conf import Genie
from genie.abstract import Lookup
from genie.libs import ops 

pyats_testbed = topology.loader.load('testbed.yaml')
genie_testbed = Genie.init(pyats_testbed)

csr_dev = genie_testbed.devices['CSR-DEV']
csr_dev.connect(via='netconf')
csr3 = genie_testbed.devices['CSR3']
csr3.connect(via='console')
abstract = Lookup.from_device(csr_dev)
# lookup = Lookup(device.os, device.context)
interfaces = abstract.ops.interface.interface.Interface(csr_dev)
interfaces.learn()
interfaces.info
static_routes = abstract.ops.static_routing.static_routing.StaticRoute(csr_dev)
static_routes.learn()
static_routes.info

show_version = abstract.ops.platform.platform.show_platform.ShowVersion(csr_dev)
show_version.parse()

show_boot = abstract.ops.platform.platform.show_platform.ShowBoot(csr_dev)
show_boot.parse()

show_cpu_ram = abstract.ops.platform.platform.show_platform.ShowPlatformSoftwareStatusControl(csr_dev)
show_cpu_ram.parse()


acl = abstract.ops.acl.acl.Acl(csr_dev)
acl.learn()
acl.info
acl_stats = abstract.ops.acl.acl.ShowAccessLists(csr_dev)
acl_stats.parse()
