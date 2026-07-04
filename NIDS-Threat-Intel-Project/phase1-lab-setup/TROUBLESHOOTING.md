# Phase 1 - Troubleshooting Log

##Issue 1: Baseline traffic generation (sudo apt update / ping) stopped during 48-hour run
- **Symptom**: Baseline traffic (Victim's 'sudo apt update' and Kali's 'ping') was not being generated consistently throughout the 48-hour capture window
- **Root cause**: Both commands were originally being run manually in a foreground terminal session:
  - On Victim, 'sudo apt update' prompted for a password each time it was run, so it could not repeated unattened
  - On Kali, 'ping' was running as a foreground process in a terminal session; when Kali auto-logged out due to inactivity, the session closed and killed the 'ping' process along with it.
- **Diagnosis**: Noticed baseline results were missing expected TCP/UDP traffic and review how the traffic-generating commands were being run -both were interactive foreground commands with no automation, dependent on an active login session

 - **Fix**: Replaced both manual commands with systemd timers so they run independently of any login session or password prompt.

On Victim Vm - allowed 'apt update' to run without a password prompt:
,,,bash
  sudo visudo -f /etc/sudoers.d/apt-update
...

UbuntuVictim All=(All) NOPASSWD: /usr/bin/apt update
Note: UbuntuVictim is the username of the Virtual Machine.

Created a oneshot service and timer:
'''bash
  sudo nano /etc/systemd/system/apt-update.service
'''
'''ini
  [Unit]
  Decription=Periodic apt update for NIDS baseline traffic

  [Service]
  Type=oneshot
  ExecStart=/usr/bin/apt update
'''
'''bash
  sudo nano /etc/systemd/system/apt-update.timer
'''ini
  [Unit]
  Description=Run apt update every 15 minutes

  [Timer]
  OnbootSec=2min
  OnUnitActiveSec=15min

  [Instal]
  WantedBy=timers.target
'''
'''bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now apt-update.timer
'''
On Kali VM - same pattern for 'ping', so it no longer depends on a logged-in terminal session
'''bash
  sudo nano /etc/systemd/system/ping-victim.service
'''
'''ini
  [Unit]
  Description=Periodic ping burst for NIDS baseline traffic

  [Service]
  Type=oneshot
  ExecStart=/bin/ping -c 5 192.168.56.20
'''
'''bash
  sudo nano /etc/systemd/system/ping-victim.timer
'''
'''ini
  [Unit]
  Description=Run ping burst every 20 minutes

  [Timer]
  OnBootSec=5min
  OnUnitActiveSec=20min

  [Install]
  WantedBy=timers.target
'''
'''bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now ping-victim.timer
'''

- **Verification**:
'''bash
  systemctl list-timers apt-update.timer
  systemctl list-timers ping-victim.timer
'''

  Both showed a recent "LAST" run and a scheduled "NEXT" run, confirming they fire automatically regardless of login state or session timeout.

- **Note**: This fix ensures both traffic sources are now fully automated and independent of session state, matching the resilience already built into 'packet-capture.service' on the Monitor VM.


##Issue 2: Kali VM had no internet access (NAT adapter no carrier)
- **Symtom**: 'apt update' failed with "Temporary failure resolving http.kali.org", then 'ping 8.8.8.8' return "Network is unreachable"
- **Diagnosis**: 'ip addr show' revealed eth0 (NAT) in state DOWN with NO-CARRIER; 'ip route show' confirmed no default route existed
- **Root cause**: "Virtual Cable Connected" was unchecked on Adapter 1 in VirtualBox settings
- **Fix**: enabled Virtual Cable Connected, adapter came up immediately
- **Verification**: 'ip addr show eth0' show state UP with LOWER_up and a DHCP-assigned IP; 'ping -c 8.8.8.8' succeeded afterward

##Issue 3: Kali apt update failing with 404 errors on every package
- **Symptom**: all packages returned 404 Not Found from the mirror
- **Diagnosis**: 'sudo apt update' output show "NO_PUBKEY ED65462EC8D5E4C5" and a GPG signature verification warning, indicating apt was rejecting the current repo index and falling back to stale cached data -which explained why installs were falling with 404s even though the network itself was working
- **Root cause**: stale package index caused by an untrusted repo signature (NO_PUBKEY ED65462EC8D5E4C5) - apt was silently using old cached index data
- **Fix**: installed kali-archive-keyring / re-imported the archive signing key
- **Verification**: 'sudo apt update' completed with no GPG warnings 
