#!/usr/bin/env bash

# Define interfaces
main_iface="enp6s0"
bridge_iface="br0"

# Save current IP and route before modifying the network
ip_addr=$(ip addr show "$main_iface" | awk '/inet / {print $2}')
gateway=$(ip route | awk '/default/ {print $3}')

# Create the bridge
sudo ip link add name "$bridge_iface" type bridge

# Move the main interface into the bridge
sudo ip link set "$main_iface" master "$bridge_iface"

# Bring up interfaces
sudo ip link set "$bridge_iface" up
sudo ip link set "$main_iface" up

# Assign previous IP manually to avoid DHCP issues
sudo ip addr add "$ip_addr" dev "$bridge_iface"
sudo ip route add default via "$gateway"

echo "Bridge successfully created. Use 'ip addr show' and 'ip route' to check."
