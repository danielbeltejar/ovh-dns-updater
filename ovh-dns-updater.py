import json
import os
import ovh
import requests
import time

ovh_client = ovh.Client()
ip_versions_required = [4]  # MUST not be empty. Can be [4],[6] or [4,6]

default_ttl = 60  # seconds
checkDNS_interval_hrs = 12.1
current_ip_file = "/tmp/current_ip.json"
records_changed = 0

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


def get_config_map():
    """
    Load in-cluster configuration and fetch ConfigMap data.
    """
    return json.loads(os.environ.get("OVH_HOSTS", ""))


def get_current_ip(v=4):
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
            message += "failed getting ipv{} address from {} because {} occurred\n".format(v, url, str(e))
            continue
        if r.status_code == requests.codes.ok:
            ip = r.text
            break
        else:
            message += "{} : Cannot get IPv{} from {}: requests.get returned status_code {}.\n".format(timestamp(), v,
                                                                                                       url,
                                                                                                       r.status_code)
    if ip != "":
        return ip
    elif v in ip_versions_required:
        message += "Failed getting required IPv{}. There is most likely a real connectivity problem. Aborting".format(v)
        print(message)
        quit()
    else:
        return False


def timestamp():
    return time.asctime(time.localtime(time.time()))


def update_record(domain, subdomain, new_ip, _ttl=600):
    # Update the (A or AAAA) record with the provided IP

    global records_changed
    typ = 'AAAA' if ":" in new_ip else 'A'
    # print("checking record {} for {}.{}".format(typ,subdomain,domain))
    path = "/domain/zone/{}/record".format(domain)
    result = ovh_client.get(path,
                            fieldType=typ,
                            subDomain=subdomain
                            )

    if len(result) != 1:
        # creating NEW record
        result = ovh_client.post(path,
                                 fieldType=typ,
                                 subDomain=subdomain,
                                 target=new_ip,
                                 ttl=_ttl
                                 )
        ovh_client.post('/domain/zone/{}/refresh'.format(domain))
        result = ovh_client.get(path,
                                fieldType=typ,
                                subDomain=subdomain
                                )
        record_id = result[0]
        records_changed += 1
        print("{} : ### created new record {} for {}.{}".format(timestamp(), typ, subdomain, domain))
    else:
        # record exists
        record_id = result[0]
        path = "/domain/zone/{}/record/{}".format(domain, record_id)
        result = ovh_client.get(path)
        oldip = result['target']
        # print('record exists, with ip :',oldip)
        if oldip == new_ip:
            # print('nothing to do')
            return
        else:
            # print('updating to ', new_ip)
            result = ovh_client.put(path,
                                    subDomain=subdomain,
                                    target=new_ip,
                                    ttl=_ttl
                                    )
            ovh_client.post('/domain/zone/{}/refresh'.format(domain))
            records_changed += 1
    # checking changes
    result = ovh_client.get("/domain/zone/{}/record/{}".format(domain, record_id))
    if new_ip != result['target']:
        records_changed -= 1
        raise Exception("Error updating {}.{} with {}".format(subdomain, domain, new_ip))


def delete_record(domain, subdomain, typ):
    """
    if it exists, delete an A or AAAA record
    (because the corresponding IP is not available)
    """
    # print("checking record {} for {}.{}".format(typ,subdomain,domain))
    global records_changed
    result = ovh_client.get("/domain/zone/{}/record".format(domain),
                            fieldType=typ,
                            subDomain=subdomain
                            )
    if len(result) == 1:
        # record exists, delete it
        record_id = result[0]
        print("{} : ### deleting record {} for {}.{}".format(timestamp(), typ, subdomain, domain))
        ovh_client.delete("/domain/zone/{}/record/{}".format(domain, record_id))
        ovh_client.post('/domain/zone/{}/refresh'.format(domain))
        records_changed += 1


current_ipv4 = get_current_ip(4)
current_ipv6 = get_current_ip(6)
print('current ips: {} ; {}'.format(current_ipv4, current_ipv6))

hosts = get_config_map()
print(hosts)


def do():
    global records_changed
    try:
        with open(current_ip_file, 'r') as f:
            old_time, old_ipv4, old_ipv6 = json.load(f)
        need_update = (old_ipv4 != current_ipv4) or (old_ipv6 != current_ipv6) or (
                (old_time - time.time()) > 3600.0 * checkDNS_interval_hrs)
    except IOError:
        # print("No old ips recorded")
        need_update = True
    if need_update:
        records_changed = 0
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
                    # print("Not touching A record for {}.{}, as instructed".format(subdomain, domain))
                    pass
                if ('ipv6' not in host) or (host['ipv6'] != False):
                    if current_ipv6:
                        ttl = default_ttl if ('ttl' not in host) else host['ttl']
                        update_record(domain, subdomain, current_ipv6, _ttl=ttl)
                    else:
                        delete_record(domain, subdomain, 'AAAA')
                else:
                    # print("Not touching AAAA record for {}.{}, as instructed".format(subdomain, domain))
                    pass
            # all hosts records have been updated without errors, log change and save current addresses
            print("{} : new addresses {} ; {} -- {} records updates".format(timestamp(), current_ipv4, current_ipv6,
                                                                            records_changed))
            with open(current_ip_file, 'w') as f:
                json.dump([time.time(), current_ipv4, current_ipv6], f)
        except Exception as e:  # some error occured (API down, keys expired...?),
            msg = "{} : ### error {} while updating records!! {} records updated with new addresses {} ; {}".format(
                timestamp(), str(e), records_changed, current_ipv4, current_ipv6)
            print(msg)
            # not saving new addresses, so that update is attempted again.
    else:
        # print("nothing to do!")
        pass


while True:
    current_ipv4 = get_current_ip(4)
    current_ipv6 = get_current_ip(6)
    print('current ips: {} ; {}'.format(current_ipv4, current_ipv6))
    do()
    time.sleep(60)
