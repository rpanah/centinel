import utils.http as http
import utils.dnslib as dns

SEARCH_STRING = "home network testbed will appear at"

class TurkeyExperiment:
    name = "turkey"

    def __init__(self, input_file):
        self.input_file = input_file
        self.results = []
        self.host = "twitter.com"
        self.path = "/feamster/status/452889624541921280"

    def run(self):
        ips = dns.get_ips(self.host)
        blocked_ips = filter(self.is_blocked, ips)

        if not blocked_ips:
            print "No censorship"
            return

        # let's try using Google's nameserver
        ips = dns.get_ips(self.host, nameserver="8.8.8.8")
        blocked_ips = filter(self.is_blocked, ips)

        if not blocked_ips:
            print "DNS blocking, use Google DNS"
            return


    def is_blocked(self, ip):
        headers = {
            "Host" : self.host
        }

        result = http.get_request(ip, self.path, headers, ssl=True)

        blocked = SEARCH_STRING not in result["response"]["body"]
        result["blocked"] = blocked

        self.results.append(result)

        return blocked
