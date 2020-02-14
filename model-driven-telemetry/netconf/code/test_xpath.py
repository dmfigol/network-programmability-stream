from ncclient import manager

import constants
import utils

#   filter xpath /platform-sw-ios-xe-oper:cisco-platform-software/control-processes/control-process[fru="fru-rp" and slot=0 and bay=0 and chassis=-1]/per-core-stats
# XPATH_FILTER = "access-lists/access-list/access-list-entries/access-list-entry[rule-name='20']/access-list-entries-oper-data/match-counter"
# XPATH_FILTER = "cisco-platform-software/control-processes/control-process[fru='fru-rp' and slot=0 and bay=0 and chassis=-1]/per-core-stats"
XPATH_FILTER = "cisco-platform-software/control-processes/control-process[fru='fru-rp'][slot='0'][bay='0'][chassis='-1']/per-core-stats/per-core-stat[name='1']"

def main():
    with manager.connect(**constants.NC_CONN_PARAMS) as m:
        nc_reply = m.get(filter=('xpath', XPATH_FILTER))
        print(utils.prettify_xml(nc_reply.xml))

if __name__ == "__main__":
    main()