#!/usr/bin/env python3
"""
Baseline traffic analyzer for NIDS Phase 1
Extracts protocol breakdown and packets rate from pcap files
"""
import subprocess
import json
import os
from collections import defaultdict

CAPTURES_DIR = os.path.expanduser('~/captures')

def analyse_pcap (filepath):
	"""Extract protocol stats using tshark"""
	result = subprocess.run([
	    'tshark', '-r', filepath,
	    '-T', 'fields',
	    '-e', 'ip.proto',
	    '-e', 'frame.len',
	    '-e', 'tcp.dstport',
	    '-e', 'udp.dstport',
	], capture_output=True, text=True)
	
	proto_bytes = defaultdict(int)
	port_counts = defaultdict(int)
	total_packets = 0

	proto_names = {'6': 'TCP', '17': 'UDP', '1': 'ICMP'}

	for line in result.stdout.strip().split('\n'):
		if not line.strip():
			continue

		parts = line.split('\t')
		if len(parts) < 2: 
			continue

		proto = proto_names.get(parts[0], parts[0] or 'Other')

		size = int(parts[1]) if parts[1].isdigit() else 0
		proto_bytes[proto] += size
		total_packets += 1

		port = ''
		if len(parts) > 2 and parts[2]:
			port = parts[2]
		elif len(parts) > 3 and parts[3]:
			port = parts[3]

		if port.isdigit():
			port_counts[port] += 1

	return proto_bytes, port_counts, total_packets

# Analyze all pcap files

all_proto = defaultdict(int)
all_ports = defaultdict(int)
total_pkts = 0

files = [f for f in os.listdir(CAPTURES_DIR) if f.endswith('.pcap')]
print(f'Analysing {len(files)} capture files...')

for fname in files:
    path = os.path.join(CAPTURES_DIR, fname)
    pb, pc, tp = analyse_pcap(path)
    for k, v in pb.items(): all_proto[k] += v
    for k, v in pc.items(): all_ports[k] += v
    total_pkts += tp

print('\n=== BASELINE RESULTS ===')
print(f'Total packets captured: {total_pkts:,}')
print('\nTraffic by protocol (bytes):')
for proto, b in sorted(all_proto.items(), key=lambda x: -x[1]):
    print(f'  {proto:10s}: {b:>12,} bytes')
print('\nTop 10 destination ports:')
for port, count in sorted(all_ports.items(), key=lambda x: -x[1])[:10]:
    print(f'  Port {port:>6s}: {count:>8,} packets')

# Save to JSON for use in Phase 3
results = {'total_packets': total_pkts,
	   'proto_bytes': dict(all_proto),
           'top_ports': dict(all_ports)}
with open('baseline_results.json', 'w') as f:
    json.dump(results, f, indent =2)
print('\nResults saved to baseline_result.json') 

