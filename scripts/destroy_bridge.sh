#!/usr/bin/env bash

# Script that manually destroys the bridge network created

main_iface="enp6s0"
bridge_iface="br0"

## Bring the bridge interface down
sudo ip link set "$bridge_iface" down

## Set interface to original state
sudo ip link set "$main_iface" nomaster

## Bring the interface back up
sudo ip link set "$main_iface" up

## Delete the bridge
sudo ip link delete "$bridge_iface"

echo "Bridge destroyed. Use 'ip link show' to confirm it"
