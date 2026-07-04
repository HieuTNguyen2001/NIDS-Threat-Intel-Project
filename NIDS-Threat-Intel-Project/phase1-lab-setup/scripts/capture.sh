#!/bin/bash
# Rotating packet capture script
# Saves a new file every 10 minutes, compresses old ones

CAPDIR="/home/$USER/captures"
mkdir -p $CAPDIR

tcpdump -i enp0s8 \
   -w "$CAPDIR/capture_%Y%m%d_%H%M%S.pcap" \
   -G 600 \
   -z gzip \
   -n -s 0
# -G 600  = rotate file every 600 seconds (10 minutes)
# -z gzip = compress each file after rotation
# -s 0    = capture the complete packet (no truncation)
 
