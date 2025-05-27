import requests
import time
import socket
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import RequestException
from log.log import logger


class Proxy(object):
    """
    Proxy class that provides a requests session object with SOCKS5 proxy support.
    Automatically renews Tor circuit when encountering 403 errors.
    Adapted from https://github.com/erdiaker/torrequest
    """

    DEFAULT_TIMEOUT = 0

    def __init__(
        self,
        proxy_port=5566,
        hostname="gluetun",
        tor_control_port=9051,
        tor_password="tor_p_hash",
    ):
        """
        Initialize Proxy object with the given proxy port and hostname.

        Args:
            proxy_port (int): Proxy port number
            hostname (str): Proxy hostname
            tor_control_port (int): Tor control port for sending commands
            tor_password (str): Password for Tor control authentication (if required)
        """
        self.proxy_port = proxy_port
        self.hostname = hostname
        self.tor_control_port = tor_control_port
        self.tor_password = tor_password
        self.max_retries = 3

        # Setup retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=30,
            allowed_methods=["HEAD", "GET", "POST"],
            status_forcelist=[
                500,
                502,
                503,
                504,
            ],  # Don't include 403 here as we handle it specially
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session = requests.Session()
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.proxies.update(
            {
                "http": f"socks5://{hostname}:{self.proxy_port}",
                "https": f"socks5://{hostname}:{self.proxy_port}",
            }
        )

    def renew_tor_circuit(self):
        """
        Send a signal to Tor to generate a new circuit.
        """
        try:
            # Create a socket connection to the Tor control port
            s = socket.socket()
            print(
                f"Connecting to Tor control port at {self.hostname}:{self.tor_control_port}"
            )
            s.connect((self.hostname, self.tor_control_port))

            # Authenticate with the password from the env/config
            auth_command = f'AUTHENTICATE "{self.tor_password}"\r\n'
            s.send(auth_command.encode())

            try:
                response = s.recv(1024).decode()
                print(f"Initial response: {response}")
            except Exception as e:
                print(f"Error receiving initial response: {e}")
                s.close()
                return False

            # If we have authentication error, try cookie auth
            if "515" in response:  # Authentication required
                print("Authentication required, trying cookie auth...")
                s.send(b"AUTHENTICATE\r\n")
                response = s.recv(1024).decode()
                print(f"Auth response: {response}")

                if "250 OK" not in response:
                    # Cookie auth failed, try with empty password
                    print("Cookie auth failed, trying empty password...")
                    s.send(b'AUTHENTICATE ""\r\n')
                    response = s.recv(1024).decode()
                    print(f"Empty password auth response: {response}")

            # Send the NEWNYM signal to request a new identity
            print("Sending SIGNAL NEWNYM...")
            s.send(b"SIGNAL NEWNYM\r\n")
            response = s.recv(1024).decode()
            print(f"NEWNYM response: {response}")
            s.close()

            if "250 OK" in response:
                print("Successfully renewed Tor circuit")
                # Wait a moment for the new circuit to be established
                time.sleep(2)
                return True
            else:
                print(f"Failed to renew Tor circuit: {response}")
                return False

        except Exception as e:
            logger.exception(f"Error renewing Tor circuit: {e}")
            return False

    def request_with_retry(self, method, *args, **kwargs):
        """
        Make a request and retry with a new Tor circuit if we get a 403.
        """
        retries = 0

        while retries < self.max_retries:
            if self.DEFAULT_TIMEOUT != 0:
                kwargs.setdefault("timeout", self.DEFAULT_TIMEOUT)

            # Make the request
            response = getattr(self.session, method)(*args, **kwargs)

            # If we get a 403, try renewing the Tor circuit
            if response.status_code == 403:
                logger.warning(
                    f"Received 403 error, attempting to renew Tor circuit (attempt {retries+1}/{self.max_retries})"
                )
                success = self.renew_tor_circuit()
                if success:
                    retries += 1
                    continue
                else:
                    # If we can't renew the circuit, just return the response
                    return response

            # For any other status code, return the response immediately
            return response

        # If we've exhausted all retries, return the last response
        return response

    def get(self, *args, **kwargs):
        return self.request_with_retry("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self.request_with_retry("post", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self.request_with_retry("put", *args, **kwargs)

    def patch(self, *args, **kwargs):
        return self.request_with_retry("patch", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.request_with_retry("delete", *args, **kwargs)

    def close(self):
        """
        Close the requests session.
        """
        try:
            self.session.close()
        except RequestException:
            logger.exception("Error occurred while closing the session")
        except Exception:
            logger.exception("Unknown error occurred while closing the session")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
