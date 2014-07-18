#!/usr/bin/python2.7

import argparse


from socket import socket
import sys
import time
from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.proto.rfc1902 import Integer, IpAddress, OctetString

hostname='172.17.9.7'
community='dog33show'
snmp_port=161
graphite_host='127.0.0.1'
graphite_port=2003
graphite_prefix='localhost.pdu'

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--host','-H', help='Hostname to connect to', required=True)
parser.add_argument('--snmp-community','-c', help='SNMP Community', required=True)
parser.add_argument('--snmp-port','-p', help='SNMP Port', default=snmp_port, type=int)
parser.add_argument('--graphite-host', help='Graphite host', default=graphite_host)
parser.add_argument('--graphite-port', help='Graphite port', default=graphite_port, type=int)
parser.add_argument('--graphite-prefix', help='Graphite prefix', default=graphite_prefix)
parser.add_argument('--use-graphite', help='Send stats to Graphite', action='store_true', default=False)
parser.add_argument('--use-collectd', help='Send stats to Collectd', action='store_true', default=False)

args = parser.parse_args()
# Namespace(graphite_host='127.0.0.1', graphite_port=2013, host='pdu-eth1', snmp_community='dog33show', snmp_port=161, use_collectd=False, use_graphite=False)

# rPDUIdentDeviceNumOutlets = 1.3.6.1.4.1.318.1.1.12.1.8
# rPDUOutletStatusOutletName = 1.3.6.1.4.1.318.1.1.12.3.5.1.1.2
value=(1,3,6,1,4,1,318,1,1,12,3,5,1,1,2)

generator = cmdgen.CommandGenerator()
comm_data = cmdgen.CommunityData('server', args.snmp_community, 1) # 1 means version SNMP v2c
transport = cmdgen.UdpTransportTarget((args.host, args.snmp_port))

real_fun = getattr(generator, 'nextCmd')
res = (errorIndication, errorStatus, errorIndex, varBinds)\
    = real_fun(comm_data, transport, value)

if not errorIndication is None  or errorStatus is True:
       print "Error: %s %s %s %s" % res
       sys.exit(1)

a=[]
# TODO Get number of outlets via SNMP
for i in range(0,23):
   a.append(varBinds[i][0][1])

# rPDU Outlet AMP (not documented) = .1.3.6.1.4.1.318.1.1.12.3.5.1.1.7 
value=(1,3,6,1,4,1,318,1,1,12,3,5,1,1,7)

res = (errorIndication, errorStatus, errorIndex, varBinds)\
    = real_fun(comm_data, transport, value)

if not errorIndication is None  or errorStatus is True:
       print "Error: %s %s %s %s" % res
       sys.exit(1)

output = []
unix_ts = int(time.time())

for i in range(0,23):
    # print "%s %s" %  (a[i],varBinds[i][0][1])
    output.append("%s.outlet_amp.%s %f %d" %  (args.graphite_prefix,a[i],(float(varBinds[i][0][1]))/10, unix_ts) )

output = set(output)

    
if args.use_graphite: 
# Send to graphite
  sock = socket()
  try:
     sock.connect(('localhost', 2013))
  except Exception:
     print "Couldn't connect to %s on port %d, is carbon running?" % ('localhost', 2013)
     sys.exit(1)
  #            
  message = '\n'.join(output) + '\n'
  sock.sendall(message)
  sock.close()
elif args.use_collectd:
  # collectd code goes here
  print 'collectd module not implemented'
else:
  print output

