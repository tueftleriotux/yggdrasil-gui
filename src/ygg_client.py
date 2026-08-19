from json import dumps, loads
from os import getenv
from nicegui.ui import notify
from socket import AF_INET, AF_UNIX, SOCK_STREAM, socket
from typing import Any, Dict, Tuple, Union


def show_error(error_string: str) -> None:
    """Shows errors as toast on the bottom of the site and in the logs."""
    print(error_string)
    notify(error_string,
           type='negative',
           timeout=20_000
           )


def create_default_node(key: str) -> Dict[str, Any]:
    """Creates a default peer dictionary structure populated with 'N/A' placeholder values.

    Args:
        key: The public key or placeholder string for the node.

    Returns:
        Dict[str, Any]: Default peer state dictionary.
    """
    return {
        "key": key,
        "remote": "N/A",
        "up": "N/A",
        "inbound": "N/A",
        "port": "N/A",
        "priority": "N/A",
        "cost": "N/A",
        "last_error": "N/A",
        "last_error_time": "N/A",
        "address": "N/A",
        "bytes_recvd": "N/A",
        "bytes_sent": "N/A",
        "uptime": "N/A",
        "latency": "N/A",
        "path": "N/A",
        "sequence": "N/A",
    }


class YggClient:
    """Client for communicating with the Yggdrasil daemon via Unix Domain Sockets or TCP Admin Sockets."""

    def __init__(self) -> None:
        """Initializes socket endpoint settings from the environment configuration."""
        endpoint = getenv("YGG_ADMIN_URI", "unix:///var/run/yggdrasil.sock")
        self.endpoint = self._parse_endpoint(endpoint)
        self.endpoint_type = "inet" if isinstance(self.endpoint, tuple) else "unix"

    @staticmethod
    def _parse_endpoint(endpoint: Union[str, Tuple[str, int]]) -> Union[str, Tuple[str, int]]:
        """Parses URI strings or tuples into standard socket targets.

        Examples:
            - 'unix:///var/run/yggdrasil.sock' -> '/var/run/yggdrasil.sock' (str)
            - 'tcp://host.docker.internal:9001' -> ('host.docker.internal', 9001) (tuple)
            - ('127.0.0.1', 9001) -> ('127.0.0.1', 9001) (tuple)
        """
        if isinstance(endpoint, tuple):
            return (str(endpoint[0]), int(endpoint[1]))

        endpoint_str = str(endpoint).strip()

        # Handle unix:// URI scheme
        if endpoint_str.startswith("unix://"):
            return endpoint_str[7:]

        # Handle tcp:// URI scheme
        if endpoint_str.startswith("tcp://"):
            endpoint_str = endpoint_str[6:]

        # Handle host:port string format
        if ":" in endpoint_str:
            host, port = endpoint_str.rsplit(":", 1)
            return (host, int(port))

        # Return raw file path string for Unix sockets
        return endpoint_str

    def request(self, req_type: str, **kwargs: Any) -> Dict[str, Any]:
        """Sends a JSON-RPC request to the Yggdrasil socket interface and returns the decoded response.

        Args:
            req_type: Yggdrasil API request method name (e.g., 'getPeers', 'getSelf').
            **kwargs: Arguments to pass alongside the request payload.

        Returns:
            Dict[str, Any]: Parsed JSON response payload from the Yggdrasil daemon.
        """
        try:
            family = AF_UNIX if self.endpoint_type == "unix" else AF_INET
            payload = {"request": req_type, "arguments": kwargs}

            with socket(family, SOCK_STREAM) as s:
                s.connect(self.endpoint)
                s.sendall(dumps(payload).encode("utf-8") + b"\n")

                data = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    data += chunk

                json_object = loads(data.decode("utf-8"))

                if not json_object:
                    return {}

                if json_object.get("status") == "error":
                    show_error(f"[Yggdrasil] Request error:\nRequest: {payload}\nAnswer: {json_object}")

                return json_object

        except (ConnectionRefusedError, FileNotFoundError, OSError) as e:
            show_error(f"[Yggdrasil] Failed to connect to admin socket ({self.endpoint}): {e}")

    def get_peer_dict(self) -> Dict[str, Dict[str, Any]]:
        """Aggregates active peer metrics by merging output from 'getPeers', 'getPaths', and 'getSessions'.

        Returns:
            Dict[str, Dict[str, Any]]: Unified map of peer identifiers to their merged statistics.
        """
        ygg_peer_dict: Dict[str, Dict[str, Any]] = {}
        key_to_id: Dict[str, str] = {}
        addr_to_id: Dict[str, str] = {}

        # 1. Fetch connected Peers
        peers_res = self.request("getPeers")
        peers = peers_res.get("response", {}).get("peers", []) if isinstance(peers_res, dict) else []

        for i, peer in enumerate(peers):
            key = peer.get("key", "")
            remote = peer.get("remote", "N/A")
            address = peer.get("address", "N/A")

            peer_id = f"{key}_{remote}" if key else f"nokey_{remote}_{i}"
            node = create_default_node(key if key else "N/A (No Key)")

            node.update({
                "remote": remote,
                "up": peer.get("up", "N/A"),
                "inbound": peer.get("inbound", "N/A"),
                "port": peer.get("port", "N/A"),
                "priority": peer.get("priority", "N/A"),
                "cost": peer.get("cost", "N/A"),
                "last_error": peer.get("last_error", "N/A"),
                "last_error_time": peer.get("last_error_time", "N/A"),
                "address": address,
                "bytes_recvd": peer.get("bytes_recvd", "N/A"),
                "bytes_sent": peer.get("bytes_sent", "N/A"),
                "uptime": peer.get("uptime", "N/A"),
                "latency": peer.get("latency", "N/A"),
            })

            ygg_peer_dict[peer_id] = node

            if key:
                key_to_id[key] = peer_id
            if address and address != "N/A":
                addr_to_id[address] = peer_id

        def get_or_create_node(key: str, address: str) -> Dict[str, Any]:
            """Helper to resolve an existing peer record or create a fallback entry."""
            if key and key in key_to_id:
                return ygg_peer_dict[key_to_id[key]]
            if address and address in addr_to_id:
                return ygg_peer_dict[addr_to_id[address]]

            lookup_key = key if key else (address if address else f"unknown_{len(ygg_peer_dict)}")
            if lookup_key not in ygg_peer_dict:
                ygg_peer_dict[lookup_key] = create_default_node(key if key else "N/A")
                if key:
                    key_to_id[key] = lookup_key
                if address:
                    addr_to_id[address] = lookup_key

            return ygg_peer_dict[lookup_key]

        # 2. Merge routing Paths
        paths_res = self.request("getPaths")
        paths = paths_res.get("response", {}).get("paths", []) if isinstance(paths_res, dict) else []

        for path in paths:
            key = path.get("key", "")
            address = path.get("address", "")

            node = get_or_create_node(key, address)
            node["path"] = path.get("path", "N/A")
            node["sequence"] = path.get("sequence", "N/A")
            if address and node.get("address") == "N/A":
                node["address"] = address

        # 3. Merge active Sessions
        sessions_res = self.request("getSessions")
        sessions = sessions_res.get("response", {}).get("sessions", []) if isinstance(sessions_res, dict) else []

        for session in sessions:
            key = session.get("key", "")
            address = session.get("address", "")

            node = get_or_create_node(key, address)
            if address and node.get("address") == "N/A":
                node["address"] = address
            if session.get("bytes_recvd") is not None:
                node["bytes_recvd"] = session.get("bytes_recvd")
            if session.get("bytes_sent") is not None:
                node["bytes_sent"] = session.get("bytes_sent")
            if session.get("uptime") is not None:
                node["uptime"] = session.get("uptime")

        return ygg_peer_dict
