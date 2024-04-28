import requests
import random
import time

from codecarbon import EmissionsTracker
from os import getenv
from http.server import HTTPServer
from prometheus_client import MetricsHandler, Counter
from string import Template
from util import artificial_503, artificial_latency

# load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()


HOST_NAME = "0.0.0.0"  # This will map to available port in docker
PORT_NUMBER = 8001
ELECTRICITY_MAP_API_KEY = getenv("ELECTRICITY_MAP_API_KEY")

# GIVEN ZONE - FEEL FREE TO CHANGE
ZONE = "DE"
carbon_intensity_url = (
    f"https://api.electricitymap.org/v3/carbon-intensity/latest?zone={ZONE}"
)
# Prometheus counter to count number of requests by status and endpoint
requestCounter = Counter(
    "requests_total", "total number of requests", ["status", "endpoint"]
)
# Tracker for carbon emissions
tracker = EmissionsTracker(
    project_name="python-app",
    save_to_prometheus=True,
    prometheus_url="http://pushgateway:9091",
)

with open("./templates/treeCounter.html", "r") as f:
    html_string = f.read()
html_template = Template(html_string)


def fetch_carbon_intensity():
    tracker.start()
    r = (
        requests.get(carbon_intensity_url, auth=("auth-token", ELECTRICITY_MAP_API_KEY))
        if random.random() > 0.15
        else artificial_503()
    )
    requestCounter.labels(status=r.status_code, endpoint="/upstream").inc()
    _ = tracker.stop()
    if r.status_code == 200:
        return r.json()["carbonIntensity"]
    return 0


class HTTPRequestHandler(MetricsHandler):
    @artificial_latency
    def get_carbon_intensity(self):
        self.do_HEAD()
        carbon_intensity = fetch_carbon_intensity()
        bytes_template = bytes(
            html_template.substitute(counter=carbon_intensity), "utf-8"
        )
        requestCounter.labels(status="200", endpoint="/carbon_intensity").inc()
        self.wfile.write(bytes_template)

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_GET(self):
        endpoint = self.path
        if endpoint == "/carbon_intensity":
            return self.get_carbon_intensity()
        elif endpoint == "/metrics":
            return super(HTTPRequestHandler, self).do_GET()
        else:
            self.send_error(404)


if __name__ == "__main__":
    myServer = HTTPServer((HOST_NAME, PORT_NUMBER), HTTPRequestHandler)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        myServer.serve_forever()
    except KeyboardInterrupt:
        pass
    myServer.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
