#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

AS = 65000
CONFIG_DIR = Path("/root/bgp-orr/configs")
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

loopbacks = {
    "rr1": "10.0.0.1", "rr2": "10.0.0.2", "rr3": "10.0.0.3", "rr4": "10.0.0.4",
    "a1": "10.0.1.1", "a2": "10.0.1.2",
    "b1": "10.0.1.11", "b2": "10.0.1.12",
    "c1": "10.0.1.21", "c2": "10.0.1.22",
    "d1": "10.0.1.31", "d2": "10.0.1.32",
}

nets = {
    "rr1": "49.0001.0000.0000.0001.00",
    "rr2": "49.0001.0000.0000.0002.00",
    "rr3": "49.0001.0000.0000.0003.00",
    "rr4": "49.0001.0000.0000.0004.00",
    "a1":  "49.0001.0000.0000.0101.00",
    "a2":  "49.0001.0000.0000.0102.00",
    "b1":  "49.0001.0000.0000.0201.00",
    "b2":  "49.0001.0000.0000.0202.00",
    "c1":  "49.0001.0000.0000.0301.00",
    "c2":  "49.0001.0000.0000.0302.00",
    "d1":  "49.0001.0000.0000.0401.00",
    "d2":  "49.0001.0000.0000.0402.00",
}

# Link definitions: (node_a, if_a, ip_a, node_b, if_b, ip_b, metric)
links = [
    ("rr1","eth1","172.16.0.0/31","rr2","eth1","172.16.0.1/31",10),
    ("rr2","eth2","172.16.0.2/31","rr3","eth1","172.16.0.3/31",10),
    ("rr3","eth2","172.16.0.4/31","rr4","eth1","172.16.0.5/31",50),
    ("rr4","eth2","172.16.0.6/31","rr1","eth2","172.16.0.7/31",50),

    ("rr1","eth3","172.16.0.8/31","a1","eth1","172.16.0.9/31",5),
    ("rr4","eth5","172.16.0.10/31","a1","eth2","172.16.0.11/31",5),
    ("rr1","eth4","172.16.0.12/31","a2","eth1","172.16.0.13/31",5),
    ("rr4","eth6","172.16.0.14/31","a2","eth2","172.16.0.15/31",5),

    ("rr2","eth3","172.16.0.16/31","b1","eth1","172.16.0.17/31",5),
    ("rr1","eth5","172.16.0.18/31","b1","eth2","172.16.0.19/31",5),
    ("rr2","eth4","172.16.0.20/31","b2","eth1","172.16.0.21/31",5),
    ("rr1","eth6","172.16.0.22/31","b2","eth2","172.16.0.23/31",5),

    ("rr3","eth3","172.16.0.24/31","c1","eth1","172.16.0.25/31",5),
    ("rr2","eth5","172.16.0.26/31","c1","eth2","172.16.0.27/31",5),
    ("rr3","eth4","172.16.0.28/31","c2","eth1","172.16.0.29/31",5),
    ("rr2","eth6","172.16.0.30/31","c2","eth2","172.16.0.31/31",5),

    ("rr4","eth3","172.16.0.32/31","d1","eth1","172.16.0.33/31",5),
    ("rr3","eth5","172.16.0.34/31","d1","eth2","172.16.0.35/31",5),
    ("rr4","eth4","172.16.0.36/31","d2","eth1","172.16.0.37/31",5),
    ("rr3","eth6","172.16.0.38/31","d2","eth2","172.16.0.39/31",5),
]

node_ifaces = {n: [] for n in loopbacks}
for a, ifa, ipa, b, ifb, ipb, metric in links:
    node_ifaces[a].append((ifa, ipa, metric, b))
    node_ifaces[b].append((ifb, ipb, metric, a))

rrs = ["rr1","rr2","rr3","rr4"]
rr_clients = {
    "rr1": ["a1","a2"],
    "rr2": ["b1","b2"],
    "rr3": ["c1","c2"],
    "rr4": ["d1","d2"],
}
client_rr = {
    "a1":"rr1","a2":"rr1","b1":"rr2","b2":"rr2",
    "c1":"rr3","c2":"rr3","d1":"rr4","d2":"rr4",
}
client_prefixes = {
    "a1":["10.255.1.1/32"],
    "a2":["10.255.1.2/32"],
    "b1":["10.255.2.1/32"],
    "b2":["10.255.2.2/32"],
    "c1":["10.255.3.1/32","198.51.100.0/24"],
    "c2":["10.255.3.2/32"],
    "d1":["10.255.4.1/32","198.51.100.0/24"],
    "d2":["10.255.4.2/32"],
}

def write_cfg(node):
    lo = loopbacks[node]
    lines = []
    lines.append(f"set system host-name {node}")
    lines.append("set system services ssh")
    lines.append("set system services netconf ssh")
    lines.append(f"set interfaces lo0 unit 0 family inet address {lo}/32")

    for ifname, ip, metric, peer in node_ifaces[node]:
        lines.append(f"set interfaces {ifname} description \"to {peer}\"")
        lines.append(f"set interfaces {ifname} unit 0 family inet address {ip}")

    lines.append(f"set routing-options router-id {lo}")
    lines.append(f"set routing-options autonomous-system {AS}")

    lines.append(f"set protocols isis net {nets[node]}")
    lines.append("set protocols isis level 2 wide-metrics-only")
    lines.append("set protocols isis interface lo0.0 passive")
    for ifname, ip, metric, peer in node_ifaces[node]:
        lines.append(f"set protocols isis interface {ifname} point-to-point")
        lines.append(f"set protocols isis interface {ifname} level 2 metric {metric}")

    if node in rrs:
        lines.append("set protocols bgp group RR-PEERS type internal")
        lines.append(f"set protocols bgp group RR-PEERS local-address {lo}")
        lines.append("set protocols bgp group RR-PEERS family inet unicast")
        for peer in rrs:
            if peer != node:
                lines.append(f"set protocols bgp group RR-PEERS neighbor {loopbacks[peer]}")
        lines.append("set protocols bgp group CLIENTS type internal")
        lines.append(f"set protocols bgp group CLIENTS local-address {lo}")
        lines.append(f"set protocols bgp group CLIENTS cluster {lo}")
        lines.append("set protocols bgp group CLIENTS family inet unicast")
        lines.append("set protocols bgp group CLIENTS optimal-route-reflection")
        c1, c2 = rr_clients[node]
        lines.append(f"set protocols bgp group CLIENTS optimal-route-reflection igp-primary {loopbacks[c1]}")
        lines.append(f"set protocols bgp group CLIENTS optimal-route-reflection igp-backup {loopbacks[c2]}")
        for c in rr_clients[node]:
            lines.append(f"set protocols bgp group CLIENTS neighbor {loopbacks[c]}")
    else:
        rr = client_rr[node]
        lines.append("set policy-options policy-statement EXPORT-STATIC term STATIC from protocol static")
        lines.append("set policy-options policy-statement EXPORT-STATIC term STATIC then accept")
        lines.append("set policy-options policy-statement EXPORT-STATIC term DEFAULT then reject")
        for prefix in client_prefixes[node]:
            lines.append(f"set routing-options static route {prefix} discard")
        lines.append("set protocols bgp group RR type internal")
        lines.append(f"set protocols bgp group RR local-address {lo}")
        lines.append("set protocols bgp group RR family inet unicast")
        lines.append("set protocols bgp group RR export EXPORT-STATIC")
        lines.append(f"set protocols bgp group RR neighbor {loopbacks[rr]}")

    (CONFIG_DIR / f"{node}.conf").write_text("\n".join(lines) + "\n")

def run(cmd):
    subprocess.run(cmd, check=True)

def apply():
    nodes = list(loopbacks.keys())
    for n in nodes:
        run(["docker","cp",f"{CONFIG_DIR}/{n}.conf",f"clab-bgp-orr-4rr-{n}:/config/juniper.conf"])
        run(["docker","exec","-i",f"clab-bgp-orr-4rr-{n}","cli","-c",
             "configure; delete; load set /config/juniper.conf; commit and-quit"])

def main():
    for n in loopbacks:
        write_cfg(n)
    if "--apply" in sys.argv:
        apply()
    print("Configs regenerated.")
    if "--apply" in sys.argv:
        print("Configs applied.")

if __name__ == "__main__":
    main()
