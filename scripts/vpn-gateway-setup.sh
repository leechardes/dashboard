#!/bin/bash
# Script para configurar o servidor como gateway VPN

# Habilitar IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Limpar regras antigas de NAT para VPN
iptables -t nat -D POSTROUTING -o tun0 -j MASQUERADE 2>/dev/null

# Configurar NAT para interface VPN
iptables -t nat -A POSTROUTING -o tun0 -j MASQUERADE

# Permitir forwarding entre interfaces
iptables -A FORWARD -i enp6s18 -o tun0 -j ACCEPT
iptables -A FORWARD -i tun0 -o enp6s18 -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "Gateway VPN configurado com sucesso!"
echo "Interfaces ativas:"
ip addr show tun0 2>/dev/null | grep inet || echo "VPN não conectada"