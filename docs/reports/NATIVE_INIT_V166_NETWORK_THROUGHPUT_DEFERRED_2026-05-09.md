# Native Init v166 Network Throughput / Impairment Report (Deferred, 2026-05-09)

## Result

- status: DEFERRED
- label: `v166 Network Throughput / Impairment`
- baseline build: `A90 Linux init 0.9.59 (v159)`
- objective: USB NCM throughput and impairment baseline.
- decision: do not run throughput in this Codex pass because host NCM IP assignment requires local sudo and the current approval policy is non-interactive.

## Evidence

Host interfaces:

```text
enx0000000005e1  UP  192.168.0.8/24 fe80::f944:4e7a:2cb2:efcd/64
```

No `192.168.7.1/24` host NCM interface was present in the current environment.

Device `netservice status`:

```text
netservice: flag=/cache/native-init-netservice enabled=no
netservice: if=ncm0 ip=192.168.7.2/255.255.255.0 tcp=2325 bind=192.168.7.2 idle=3600s max_clients=0 auth=required
netservice: helpers usbnet=yes tcpctl=yes toybox=yes
netservice: ncm0=absent tcpctl=stopped
```

Device `a90_usbnet status`:

```text
config b.1: f1,strings,bmAttributes,MaxPower
f1: ../../../../usb_gadget/g1/functions/acm.usb0
f2: <readlink:No such file or directory>
ncm.ifname: <read:No such device>
ncm.dev_addr: <read:No such device>
ncm.host_addr: <read:No such device>
```

`ncm_host_setup.py status --allow-auto-interface`:

```text
[ncm] NCM host_addr not present in helper status
```

## Deferral Reason

- v165 intentionally restored final state to ACM-only.
- v166 throughput requires enabling NCM and assigning host `192.168.7.1/24`.
- Host IP assignment requires `sudo ip addr replace ...`, and this run cannot request interactive sudo.
- Running a partial network throughput test without host IP configuration would produce misleading failure evidence.

## Operator Resume Steps

```bash
python3 scripts/revalidation/ncm_host_setup.py setup --allow-auto-interface

# If sudo is required, run manually:
sudo ip addr replace 192.168.7.1/24 dev <enx...>
sudo ip link set <enx...> up
ping -c 3 -W 2 192.168.7.2
```

After NCM is reachable, create the actual throughput report and replace this deferred report with measured direction/bytes/MB/s/checksum evidence.

## Next

- Continue to v167 FS Exerciser Mini.
