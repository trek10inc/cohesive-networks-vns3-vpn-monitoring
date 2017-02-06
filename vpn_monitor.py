#!/usr/bin/env python
# -*- coding: utf-8 -*-
# DOM 28.09.2015

import os, sys

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "vendored"))

from base64 import b64encode
import httplib
import json
from datadog import initialize, api
import ssl
from datetime import datetime

ssl._create_default_https_context = ssl._create_unverified_context
options = {
    'api_key': os.environ['DD_API_KEY'],
    'app_key': os.environ['DD_APP_KEY']
}

initialize(**options)

def check_tunnels(*args):

    MANAGER_SERVERS = []
    for varName, varValue in os.environ.iteritems():
        if varName.startswith('VPN_'):
            varSplit = varValue.split( )

            MANAGER_SERVERS.append(
             {
                varSplit[0].split('=')[0]: varSplit[0].split('=')[1],
                varSplit[1].split('=')[0]: varSplit[1].split('=')[1],
                varSplit[2].split('=')[0]: varSplit[2].split('=')[1]
             }
            )

    for manager_server in MANAGER_SERVERS:
        userAndPass = b64encode(b""+manager_server['VNS3_API_USER']+":"+manager_server['VNS3_API_PASSWD']+"").decode("ascii")
        headers = { 'Authorization' : 'Basic %s' %  userAndPass }

        headers.update({"Content-Type" : "application/json"})
        conn_api = httplib.HTTPSConnection(manager_server['VNS3_HOST'], 8000, timeout=10)
        json_req = '{"extended_output":"true"}'
        conn_api.request("GET", "/api/status/connected_subnets", json_req, headers)
        resp = conn_api.getresponse()
        networks_json = json.loads(resp.read())
        ips = []
        for net in networks_json['response']:
            # skip subnets with remote_manager origin ot local_*
            if not (net['origin'] == 'remote_manager' or 'local_' in net['origin']):
                ips.append(net['network'])
        conn_api.request("GET", "/api/status/ipsec", json_req, headers)
        resp = conn_api.getresponse()
        tunnels_json = json.loads(resp.read())
        tunnel_keys = tunnels_json['response'].keys()

        for tunnel_key in tunnel_keys:
            tunnel_name = str(tunnels_json['response'][tunnel_key]['description'])
            tunnel_ip = tunnels_json['response'][tunnel_key]['remote_subnet'].split("/")[0]
            tunnel_connected_status = tunnels_json['response'][tunnel_key]['connected']
            if not tunnel_connected_status:
                # Tunnel DOWN, send alarm
                print ("%s tunnel %s is DOWN" % (datetime.today(), tunnel_name))
                api.Metric.send(metric='vpn.tunnel.status', points=0, tags=["tunnel:"+tunnel_name,"vpn_environment:"+os.environ['VPNENV']])
            else:
                # Tunnel UP and OK
                print ("%s tunnel %s is UP" % (datetime.today(), tunnel_name))
                api.Metric.send(metric='vpn.tunnel.status', points=1, tags=["tunnel:"+tunnel_name,"vpn_environment:"+os.environ['VPNENV']])

        for ip in ips:
            ip_exist = False
            for tunnel_key in tunnel_keys:
                if ip == tunnels_json['response'][tunnel_key]['remote_subnet'].split("/")[0]:
                    ip_exist = True
            if not ip_exist:
                # IP address from connected_networks is not exist into tunnel status
                # send alert
                print "%s IP address %s does not exist in tunnel status" % (datetime.today(), ip)
                text = "IP address %s does not exist in tunnel status" % ip
                title = "Problem with VPN"
                tags = ['ip:'+ip, 'application:vpn_monitor']
                api.Event.create(title=title, text=text, tags=tags)

    return "OK"

if __name__ == "__main__":
    check_tunnels()