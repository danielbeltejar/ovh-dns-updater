import json
import os
import ovh
import requests
import time
from kubernetes import client, config


def get_ovh_credentials():
    """
    Retrieve OVH API credentials from environment variables.
    """
    endpoint = os.environ.get("OVH_ENDPOINT", "ovh-eu")
    application_key = os.environ.get("OVH_APPLICATION_KEY", "")
    application_secret = os.environ.get("OVH_APPLICATION_SECRET", "")
    consumer_key = os.environ.get("OVH_CONSUMER_KEY", "")

    return {
        "endpoint": endpoint,
        "application_key": application_key,
        "application_secret": application_secret,
        "consumer_key": consumer_key
    }


def get_namespace():
    """
    Retrieve the namespace from the service account token mounted in the pod.
    """
    namespace_path = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
    with open(namespace_path, 'r') as f:
        namespace = f.read().strip()
    return namespace


def get_config_map():
    """
    Load in-cluster configuration and fetch ConfigMap data.
    """
    config.load_incluster_config()
    namespace = get_namespace()
    v1 = client.CoreV1Api()
    config_map_name = "ovh-dns-config"
    config_map = v1.read_namespaced_config_map(config_map_name, namespace)
    hosts_json = config_map.data.get("hosts.json", "[]")
    return json.loads(hosts_json)


def get_current_ip(v=4):
    """
    Retrieve the current IPv4 or IPv6 address.
    """
    if v == 4:
        url_list = ["https://api.ipify.org", "https://ipv4.lafibre.info/ip.php", "https://v4.ident.me"]
    else:
        url_list = ["https://api6.ipify.org", "https://ipv6.lafibre.info/ip.php", "https://v6.ident.me"]
    ip = ""
    message = ""
    for url in url_list:
        try:
            r = requests.get(url, timeout=30.0)
        except requests.exceptions.RequestException as e:
            message += f"failed getting ipv{v} address from {url} because {str(e)} occurred\n"
            continue
        if r.status_code == requests.codes.ok:
            ip = r.text
            break
        else:
            message += f"{time.asctime(time.localtime(time.time()))} : Cannot get IPv{v} from {url}: " \
                       f"requests.get returned status_code {r.status_code}.\n"
    if ip != "":
        return ip
    elif v in [4]:  # IPv4 is required
        message += f"Failed getting required IPv{v}. There is most likely a real connectivity problem. Aborting"
        print(message)
        quit()
    else:
        return False


def update_record(domain, subdomain, new_ip, _ttl=600):
    """
    Update the (A or AAAA) record with the provided IP.
    """
    global records_changed
    typ = 'AAAA' if ":" in new_ip else 'A'
    path = f"/domain/zone/{domain}/record"
    result = ovh_client.get(path, fieldType=typ, subDomain=subdomain)

    if len(result) != 1:
        result = ovh_client.post(path, fieldType=typ, subDomain=subdomain, target=new_ip, ttl=_ttl)
        ovh_client.post(f"/domain/zone/{domain}/refresh")
        result = ovh_client.get(path, fieldType=typ, subDomain=subdomain)
        record_id = result[0]
        records_changed += 1
        print(f"{time.asctime(time.localtime(time.time()))} : ### created new record {typ} for {subdomain}.{domain}")
    else:
        record_id = result[0]
        path = f"/domain/zone/{domain}/record/{record_id}"
        result = ovh_client.get(path)
        oldip = result['target']
        if oldip == new_ip:
            return
        else:
            result = ovh_client.put(path, subDomain=subdomain, target=new_ip, ttl=_ttl)
            ovh_client.post(f"/domain/zone/{domain}/refresh")
            records_changed += 1


def delete_record(domain, subdomain, typ):
    """
    Delete an A or AAAA record if it exists.
    """
    global records_changed
    result = ovh_client.get(f"/domain/zone/{domain}/record", fieldType=typ, subDomain=subdomain)
    if len(result) == 1:
        record_id = result[0]
        print(f"{time.asctime(time.localtime(time.time()))} : ### deleting record {typ} for {subdomain}.{domain}")
        ovh_client.delete(f"/domain/zone/{domain}/record/{record_id}")
        ovh_client.post(f"/domain/zone/{domain}/refresh")
        records_changed += 1


def timestamp():
    """
    Get the current timestamp.
    """
    return time.asctime(time.localtime(time.time()))


# Main script logic
credentials = get_ovh_credentials()
ovh_client = ovh.Client(**credentials)

# Use 'get_config_map()' to retrieve the hosts list
hosts = get_config_map()

checkDNS_interval_hrs = 12.1
current_ip_file = "/data/current_ip.json"

# Retrieve current IPv4 and IPv6
current_ipv4 = get_current_ip(4)
current_ipv6 = get_current_ip(6)

# Reload saved values & compare
try:
    with open(current_ip_file, 'r') as f:
        old_time, old_ipv4, old_ipv6 = json.load(f)
    need_update = (old_ipv4 != current_ipv4) or (old_ipv6 != current_ipv6) or (
            (old_time - time.time()) > 3600.0 * checkDNS_interval_hrs)
except IOError:
    need_update = True

if need_update:
    records_changed = 0
    default_ttl = 600
    try:
        for host in hosts:
            domain = host["domain"]
            subdomain = host["subdomain"]
            if ('ipv4' not in host) or (host['ipv4'] != False):
                if current_ipv4:
                    ttl = default_ttl if ('ttl' not in host) else host['ttl']
                    update_record(domain, subdomain, current_ipv4, _ttl=ttl)
                else:
                    delete_record(domain, subdomain, 'A')
            else:
                pass
            if ('ipv6' not in host) or (host['ipv6'] != False):
                if current_ipv6:
                    ttl = default_ttl if ('ttl' not in host) else host['ttl']
                    update_record(domain, subdomain, current_ipv6, _ttl=ttl)
                else:
                    delete_record(domain, subdomain, 'AAAA')
            else:
                pass
        print(f"{timestamp()} : new addresses {current_ipv4} ; {current_ipv6} -- {records_changed} records updates")
        with open(current_ip_file, 'w') as f:
            json.dump([time.time(), current_ipv4, current_ipv6], f)
    except Exception as e:
        msg = f"{timestamp()} : ### error {str(e)} while updating records!! {records_changed} records updated " \
              f"with new addresses {current_ipv4} ; {current_ipv6}"
        print(msg)
else:
    pass
