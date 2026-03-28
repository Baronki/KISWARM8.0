#!/usr/bin/env python3
"""
🌐 HEXSTRIKE DNS SERVICE DISCOVERY v1.0
Purpose: Discover services via DNS and mDNS
Capabilities: DNS enumeration, mDNS/Bonjour discovery, internal DNS scanning
"""

import logging
import socket
import subprocess
import dns.resolver
import dns.reversename
from datetime import datetime
from typing import Dict, List, Optional
import struct

logging.basicConfig(level=logging.INFO, format='%(asctime)s [DNS-DISCOVERY] %(message)s')
logger = logging.getLogger('DNS_DISCOVERY')

class DNSServiceDiscovery:
    """Discover services via DNS protocols"""
    
    # Common KI-related DNS patterns
    KI_DNS_PATTERNS = [
        'ollama', 'llama', 'gpt', 'chat', 'api', 'model',
        'kiswarm', 'hexstrike', 'inference', 'ml', 'ai',
        'vllm', 'openai', 'anthropic', 'claude',
        'llm', 'embedding', 'vector', 'rag',
    ]
    
    # Common internal DNS suffixes to try
    INTERNAL_DNS_SUFFIXES = [
        '.internal',
        '.local',
        '.cluster.local',
        '.svc.cluster.local',
        '.kubernetes',
        '.docker',
        '.home',
        '.lan',
    ]
    
    # Service record types
    SRV_SERVICES = [
        '_ollama._tcp',
        '_http._tcp',
        '_https._tcp',
        '_api._tcp',
        '_grpc._tcp',
        '_kubernetes._tcp',
        '_etcd-server-ssl._tcp',
        '_etcd-client-ssl._tcp',
    ]
    
    # mDNS/Bonjour service types
    MDNS_SERVICES = [
        '_ollama._tcp.local.',
        '_http._tcp.local.',
        '_workstation._tcp.local.',
        '_ssh._tcp.local.',
        '_sftp-ssh._tcp.local.',
    ]
    
    def __init__(self):
        self.discovered_hosts = {}
        self.discovered_services = {}
        
    def dns_lookup(self, hostname: str) -> Dict:
        """Perform DNS lookup for hostname"""
        result = {
            'hostname': hostname,
            'timestamp': datetime.now().isoformat(),
            'addresses': [],
            'aliases': [],
            'errors': [],
        }
        
        try:
            answers = dns.resolver.resolve(hostname, 'A')
            for rdata in answers:
                result['addresses'].append(str(rdata))
        except Exception as e:
            result['errors'].append(f"A lookup: {str(e)}")
        
        try:
            answers = dns.resolver.resolve(hostname, 'AAAA')
            for rdata in answers:
                result['addresses'].append(str(rdata))
        except:
            pass
        
        return result
    
    def reverse_dns(self, ip: str) -> Dict:
        """Perform reverse DNS lookup"""
        result = {
            'ip': ip,
            'timestamp': datetime.now().isoformat(),
            'hostnames': [],
        }
        
        try:
            addr = dns.reversename.from_address(ip)
            answers = dns.resolver.resolve(addr, 'PTR')
            for rdata in answers:
                hostname = str(rdata).rstrip('.')
                result['hostnames'].append(hostname)
                
                # Check for KI patterns
                hostname_lower = hostname.lower()
                for pattern in self.KI_DNS_PATTERNS:
                    if pattern in hostname_lower:
                        result['is_ki_related'] = True
                        result['ki_pattern'] = pattern
                        logger.info(f"🌐 KI hostname found: {hostname}")
                        break
                        
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def scan_internal_dns(self, base_name: str, suffixes: List[str] = None) -> List[Dict]:
        """Scan for internal DNS entries"""
        suffixes = suffixes or self.INTERNAL_DNS_SUFFIXES
        results = []
        
        for suffix in suffixes:
            hostname = f"{base_name}{suffix}"
            
            try:
                result = self.dns_lookup(hostname)
                if result['addresses']:
                    result['suffix'] = suffix
                    results.append(result)
                    logger.info(f"🌐 DNS found: {hostname} -> {result['addresses']}")
            except:
                pass
        
        return results
    
    def discover_srv_records(self, domain: str) -> List[Dict]:
        """Discover SRV records for services"""
        results = []
        
        for service in self.SRV_SERVICES:
            try:
                query = f"{service}.{domain}"
                answers = dns.resolver.resolve(query, 'SRV')
                
                for rdata in answers:
                    result = {
                        'service': service,
                        'domain': domain,
                        'target': str(rdata.target).rstrip('.'),
                        'port': rdata.port,
                        'priority': rdata.priority,
                        'weight': rdata.weight,
                        'timestamp': datetime.now().isoformat(),
                    }
                    results.append(result)
                    logger.info(f"🌐 SRV: {service}.{domain} -> {result['target']}:{result['port']}")
                    
            except:
                pass
        
        return results
    
    def mdns_scan(self, timeout: int = 5) -> List[Dict]:
        """Perform mDNS/Bonjour scan"""
        results = []
        
        try:
            # Use avahi-browse if available
            result = subprocess.run(
                ['avahi-browse', '-a', '-t', '-r'],
                capture_output=True, text=True, timeout=timeout
            )
            
            if result.returncode == 0:
                current_service = None
                
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    
                    if '=' in line and 'IPv4' in line:
                        parts = line.split(';')
                        if len(parts) >= 4:
                            service_info = {
                                'type': 'mdns',
                                'service': parts[0] if parts else '',
                                'hostname': parts[3] if len(parts) > 3 else '',
                                'address': parts[7] if len(parts) > 7 else '',
                                'port': parts[8] if len(parts) > 8 else '',
                                'timestamp': datetime.now().isoformat(),
                            }
                            
                            # Check for KI patterns
                            for field in ['service', 'hostname']:
                                val = service_info.get(field, '').lower()
                                for pattern in self.KI_DNS_PATTERNS:
                                    if pattern in val:
                                        service_info['is_ki_related'] = True
                                        service_info['ki_pattern'] = pattern
                                        logger.info(f"🌐 mDNS KI service: {service_info['hostname']}")
                                        break
                            
                            results.append(service_info)
                            
        except FileNotFoundError:
            logger.info("avahi-browse not installed, using socket-based mDNS")
            results = self._socket_mdns_scan()
        except Exception as e:
            logger.debug(f"mDNS scan error: {e}")
        
        return results
    
    def _socket_mdns_scan(self) -> List[Dict]:
        """Socket-based mDNS scan (fallback)"""
        results = []
        MDNS_ADDR = "224.0.0.251"
        MDNS_PORT = 5353
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', MDNS_PORT))
            
            # Join mDNS group
            mreq = struct.pack("4sl", socket.inet_aton(MDNS_ADDR), socket.INADDR_ANY)
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            sock.settimeout(5)
            
            # Listen for a few seconds
            start = datetime.now()
            while (datetime.now() - start).seconds < 5:
                try:
                    data, addr = sock.recvfrom(4096)
                    results.append({
                        'type': 'mdns_traffic',
                        'source_ip': addr[0],
                        'source_port': addr[1],
                        'data_size': len(data),
                        'timestamp': datetime.now().isoformat(),
                    })
                except socket.timeout:
                    break
                    
        except Exception as e:
            logger.debug(f"Socket mDNS error: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
        
        return results
    
    def scan_subnet_dns(self, base_ip: str, range_size: int = 20) -> Dict:
        """Scan subnet with reverse DNS"""
        results = {
            'scan_time': datetime.now().isoformat(),
            'base_ip': base_ip,
            'hosts_found': 0,
            'ki_hosts': [],
            'entries': [],
        }
        
        parts = base_ip.split('.')
        if len(parts) != 4:
            return results
        
        base = '.'.join(parts[:3])
        start = int(parts[3])
        
        for i in range(start, min(start + range_size, 255)):
            ip = f"{base}.{i}"
            
            rdns = self.reverse_dns(ip)
            if rdns.get('hostnames'):
                results['entries'].append(rdns)
                results['hosts_found'] += 1
                
                if rdns.get('is_ki_related'):
                    results['ki_hosts'].append(rdns)
        
        return results
    
    def get_status(self):
        return {
            "hosts_discovered": len(self.discovered_hosts),
            "services_discovered": len(self.discovered_services),
            "ki_patterns_tracked": len(self.KI_DNS_PATTERNS),
        }


# Flask API
from flask import Flask, jsonify, request

app = Flask(__name__)
dns_discovery = DNSServiceDiscovery()

@app.route('/')
def index():
    return jsonify({
        "name": "HEXSTRIKE-DNS-Discovery",
        "version": "1.0",
        "capabilities": [
            "DNS lookup",
            "Reverse DNS",
            "SRV record discovery",
            "mDNS/Bonjour scan",
            "Internal DNS enumeration"
        ],
        "endpoints": {
            "/": "This info",
            "/status": "Status",
            "/lookup/<hostname>": "DNS lookup",
            "/reverse/<ip>": "Reverse DNS",
            "/mdns": "mDNS scan",
            "/scan/<base_ip>": "Scan subnet DNS"
        }
    })

@app.route('/status')
def status():
    return jsonify(dns_discovery.get_status())

@app.route('/lookup/<hostname>')
def lookup(hostname):
    result = dns_discovery.dns_lookup(hostname)
    return jsonify(result)

@app.route('/reverse/<ip>')
def reverse(ip):
    result = dns_discovery.reverse_dns(ip)
    return jsonify(result)

@app.route('/mdns')
def mdns():
    result = dns_discovery.mdns_scan()
    return jsonify({"services": result})

@app.route('/scan/<path:base_ip>')
def scan_subnet(base_ip):
    range_size = request.args.get('range', 20, type=int)
    result = dns_discovery.scan_subnet_dns(base_ip, range_size)
    return jsonify(result)


if __name__ == '__main__':
    logger.info("🌐 DNS Discovery starting on port 5016")
    app.run(host='127.0.0.1', port=5016)
