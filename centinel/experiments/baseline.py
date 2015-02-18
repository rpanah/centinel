#
# Abbas Razaghpanah (arazaghpanah@cs.stonybrook.edu)
# February 2015, Stony Brook University
#
# baseline.py: baseline experiment that runs through
# lists of URLs and does HTTP + DNS + traceroute for
# every URL in the list.
#
# Input files can be either simple URL lists or CSV
# files. In case of CSV input, the first column is
# assumed to be the URL and the rest of the columns
# are included in the results as metadata.


import os
import logging
import urlparse

from centinel.experiment import Experiment
from centinel.primitives import dnslib
import centinel.primitives.http as http
import centinel.primitives.traceroute as traceroute


class BaselineExperiment(Experiment):
    name = "baseline"
    # country-specific, world baseline
    # this can be overridden by the main thread
    input_files = ['country', 'world']

    def __init__(self, input_files):
        self.input_files = input_files
        self.results = []

        if os.geteuid() != 0:
            logging.info("Centinel is not running as root, "
                         "traceroute will be limited to UDP.")
            self.traceroute_methods = ["udp"]
        else:
            self.traceroute_methods = ["icmp", "udp", "tcp"]

    def run(self):
        for input_file in self.input_files.items():
            logging.info("Testing input file %s..." % (input_file[0]))
            self.results.append(self.run_file(input_file))

    def run_file(self, input_file):
        file_name, file_contents = input_file

        # Initialize the results for this input file.
        # This can be anything from file name to version
        # to any useful information.
        result = {}
        result["file_name"] = file_name

        http_results = {}
        dns_results = {}
        traceroute_results = {}
        metadata_results = {}

        # we may want to make this threaded and concurrent
        for line in file_contents:
            line = line.strip()
            url = line
            meta = ''

            # if the list entry has comma separated meta-data
            if len(line.split(',')) > 1:
                url, meta = line.split(',', 1)
                # remove trailing spaces
                url = url.strip()

            # remove quotes, if any
            # this may not be the best way to do this.
            # therefore, clean input files are preferred.
            if url[0] == '"' or url[0] == "'":
                url = url[1:-1]

            # parse the URL to extract netlocation, HTTP path, domain name,
            # and HTTP method (SSL or plain)
            try:
                http_netloc = ''.join(urlparse.urlparse(url).netloc)

                # if netloc is not urlparse-able, add // to the start
                # of URL
                if http_netloc == '':
                    url = '//' + url
                    http_netloc = ''.join(urlparse.urlparse(url).netloc)

                http_path = urlparse.urlparse(url).path
                if http_path == '':
                    http_path = '/'

                # we assume scheme is either empty, or "http", or "https"
                # other schemes (e.g. "ftp") are out of the scope of this
                # measuremnt
                http_ssl = False
                if urlparse.urlparse(url).scheme == "https":
                    http_ssl = True
            except Exception as exp:
                logging.warning("%s: failed to parse URL: %s" %(url, str(exp)))
                http_netloc = url
                http_ssl    = False
                http_path   = '/'

            domain_name = http_netloc.split(':')[0]

            # HTTP GET
            logging.info("%s: HTTP" % (url))
            try:
                http_results[url] = http.get_request(http_netloc,
                                                     http_path,
                                                     ssl=http_ssl)
            except Exception as exp:
                logging.info("%s: HTTP test failed: %s" %
                             (url, str(exp)))
                http_results[url] = { "exception" : str(exp) }

            # DNS Lookup
            logging.info("%s: DNS" % (domain_name))
            try:
                dns_results[domain_name] = dnslib.lookup_domain(domain_name)
            except Exception as exp:
                logging.info("%s: DNS lookup failed: %s" %
                             (domain_name, str(exp)))
                dns_results[domain_name] = { "exception" : str(exp) }

            # Traceroute
            for method in self.traceroute_methods:
                try:
                    logging.info("%s: Traceroute (%s)"
                                 % (domain_name, method.upper()))
                    traceroute_results[domain_name] = traceroute.traceroute(domain_name, method=method)
                except Exception as exp:
                    logging.info("%s: Traceroute (%s) failed: %s" %
                                    (domain_name, method.upper(), str(exp)))
                    traceroute_results[domain_name] = { "exception" : str(exp) }

            # Meta-data
            metadata_results[url] = meta

        result["http"] = http_results
        result["dns"] = dns_results
        result["traceroute"] = traceroute_results
        result["metadata"] = metadata_results
        return result
