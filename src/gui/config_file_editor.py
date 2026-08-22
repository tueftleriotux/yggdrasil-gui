from nicegui import ui
from os import getenv
import config_file_parser


hjson_parser = config_file_parser.HJSON_CONFIG_FILE()


def manual_edit_tab() -> None:
    ui.label("Manual Editor").classes("text-h5 font-bold text-white mb-2")
    ui.label("Directly edit the raw HJSON configuration text.").classes("text-slate-400 text-sm mb-4")

    # Monospace textarea for code editing
    config_area = ui.textarea(value=hjson_parser.read_config_raw()).props('rows=40').classes("w-full font-mono text-sm bg-slate-800 text-slate-100")

    # Confirmation Dialog for Permanent Changes
    with ui.dialog() as confirm_dialog, ui.card().classes("bg-slate-800 text-white p-6 max-w-md"):
        with ui.row().classes("items-center gap-3 mb-2"):
            ui.icon("warning", size="32px").classes("text-amber-400")
            ui.label("Permanent Configuration Change").classes("text-h6 font-bold")

        ui.label(
            "This action will permanently modify the Yggdrasil configuration file and cannot be undone!\n\n"
            "Please note: You will need to manually restart the Yggdrasil service after saving "
            "for the new configuration changes to take effect."
        ).classes("text-slate-300 text-sm mb-6")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=confirm_dialog.close).props("outline color=grey-5")

            def execute_save():
                confirm_dialog.close()

                hjson_parser.write_config_raw(config_area.value)
                ui.notify("Configuration successfully saved!", type="positive")

            ui.button("Proceed & Save", on_click=execute_save).props("color=red-700 font-bold")

    with ui.row().classes("mt-4 gap-2"):
        # Opens the warning dialog
        ui.button("Save Changes", on_click=confirm_dialog.open, icon="save").props("color=cyan-700")


def gui_input_line(label, value) -> object:
    input_field = ui.input(
            label=label,
            value=value
        ).classes("w-full")
    return input_field


def create_interface_peers_editor(config_file_dict):
    if "InterfacePeers" not in config_file_dict or not isinstance(config_file_dict["InterfacePeers"], dict):
        config_file_dict["InterfacePeers"] = {}

    interface_peers = config_file_dict["InterfacePeers"]

    with ui.card().classes("w-full bg-slate-800 p-4 mt-4"):
        ui.label("Interface Peers Configuration").classes("text-white font-bold text-lg mb-3")

        container = ui.column().classes("w-full gap-4")

        def refresh_ui():
            container.clear()
            with container:
                if not interface_peers:
                    ui.label("No interface-specific peers configured.").classes("text-slate-400 italic text-sm")

                for iface_name, peers_list in list(interface_peers.items()):
                    with ui.card().classes("w-full bg-slate-900 p-3 border border-slate-700"):

                        # Header for each Interface block
                        with ui.row().classes("w-full items-center gap-2 mb-2"):
                            ui.label(f"Interface: {iface_name}").classes("text-cyan-400 font-bold flex-1")

                            def make_del_iface(name=iface_name):
                                return lambda: delete_interface(name)
                            ui.button(icon="delete", on_click=make_del_iface()).props("flat color=red-400 dense")

                        # Peers inside this interface
                        for p_idx, peer in enumerate(peers_list):
                            with ui.row().classes("w-full items-center gap-2"):
                                ui.input(
                                    value=peer,
                                    on_change=lambda e, iname=iface_name, idx=p_idx: update_peer(iname, idx, e.value)
                                ).classes("flex-1").props("dense outlined")

                                def make_del_peer(iname=iface_name, idx=p_idx):
                                    return lambda: delete_peer(iname, idx)
                                ui.button(icon="delete", on_click=make_del_peer()).props("flat color=red-400 dense")

                        # Add peer to this specific interface
                        with ui.row().classes("w-full items-center gap-2 mt-2 pt-2 border-t border-slate-800"):
                            new_p_input = ui.input(placeholder=f"Add peer for {iface_name}...").classes("flex-1").props("dense outlined")

                            def make_add_peer(iname=iface_name, inp=new_p_input):
                                return lambda: add_peer_to_interface(iname, inp)

                            ui.button("Add Peer", icon="add", on_click=make_add_peer()).props("color=cyan-700 dense")

        def update_peer(iname, idx, val):
            if iname in interface_peers and idx < len(interface_peers[iname]):
                interface_peers[iname][idx] = val

        def delete_peer(iname, idx):
            if iname in interface_peers and idx < len(interface_peers[iname]):
                interface_peers[iname].pop(idx)
                refresh_ui()

        def delete_interface(iname):
            if iname in interface_peers:
                del interface_peers[iname]
                refresh_ui()

        def add_peer_to_interface(iname, inp):
            val = inp.value.strip()
            if val:
                interface_peers[iname].append(val)
                inp.value = ""
                refresh_ui()

        # Section to add a completely new interface key (e.g. eth0)
        with ui.row().classes("w-full items-center gap-2 mt-4 pt-3 border-t border-slate-700"):
            new_iface_input = ui.input(placeholder="New Interface Name (e.g. eth0)").classes("flex-1").props("dense outlined")

            def add_interface():
                iname = new_iface_input.value.strip()
                if iname and iname not in interface_peers:
                    interface_peers[iname] = []
                    new_iface_input.value = ""
                    refresh_ui()

            ui.button("Add Interface", icon="add", on_click=add_interface).props("color=cyan-700")

        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
Like `Peers` above, but sorted into sections representing the outbound network interface used to establish the peering connection. This is only useful on hosts that require a special multi-homed configuration, otherwise you should use `Peers` instead.
""")

        refresh_ui()


def create_multicast_interfaces_editor(config_file_dict):
    if "MulticastInterfaces" not in config_file_dict or not isinstance(config_file_dict["MulticastInterfaces"], list):
        config_file_dict["MulticastInterfaces"] = []

    mcast_list = config_file_dict["MulticastInterfaces"]

    with ui.card().classes("w-full bg-slate-800 p-4 mt-4"):
        ui.label("Multicast Interfaces Configuration").classes("text-white font-bold text-lg mb-3")

        container = ui.column().classes("w-full gap-4")

        def refresh_ui():
            container.clear()
            with container:
                if not mcast_list:
                    ui.label("No multicast interfaces configured.").classes("text-slate-400 italic text-sm")

                for index, mcast in enumerate(mcast_list):
                    with ui.card().classes("w-full bg-slate-900 p-3 border border-slate-700"):

                        # Header with delete button for this entry
                        with ui.row().classes("w-full items-center gap-2 mb-2"):
                            ui.label(f"Multicast Rule #{index + 1} ({mcast.get('Regex', 'All')})").classes("text-cyan-400 font-bold flex-1")

                            def make_del_mcast(idx=index):
                                return lambda: delete_mcast(idx)
                            ui.button(icon="delete", on_click=make_del_mcast()).props("flat color=red-400 dense")

                        # Line 1: Regex, Port, Priority
                        with ui.row().classes("w-full items-center gap-2 mb-2"):
                            ui.input(
                                label="Regex",
                                value=mcast.get("Regex", ".*"),
                                on_change=lambda e, idx=index: update_mcast(idx, "Regex", e.value)
                            ).classes("flex-1").props("dense outlined")

                            ui.input(
                                label="Port",
                                value=str(mcast.get("Port", 0)),
                                on_change=lambda e, idx=index: update_mcast(idx, "Port", int(e.value) if e.value.isdigit() else 0)
                            ).classes("w-28").props("dense outlined")

                            ui.input(
                                label="Priority",
                                value=str(mcast.get("Priority", 0)),
                                on_change=lambda e, idx=index: update_mcast(idx, "Priority", int(e.value) if e.value.isdigit() else 0)
                            ).classes("w-28").props("dense outlined")

                        # Line 2: Password
                        with ui.row().classes("w-full items-center gap-2 mb-2"):
                            ui.input(
                                label="Password",
                                value=mcast.get("Password", ""),
                                on_change=lambda e, idx=index: update_mcast(idx, "Password", e.value)
                            ).classes("flex-1").props("dense outlined")

                        # Line 3: Checkboxes for Beacon & Listen
                        with ui.row().classes("w-full items-center gap-6 mt-1 text-slate-300"):
                            ui.checkbox(
                                text="Beacon",
                                value=mcast.get("Beacon", True),
                                on_change=lambda e, idx=index: update_mcast(idx, "Beacon", e.value)
                            ).props("color=cyan-400")

                            ui.checkbox(
                                text="Listen",
                                value=mcast.get("Listen", True),
                                on_change=lambda e, idx=index: update_mcast(idx, "Listen", e.value)
                            ).props("color=cyan-400")

        def update_mcast(index, field, val):
            if index < len(mcast_list):
                mcast_list[index][field] = val

        def delete_mcast(index):
            if index < len(mcast_list):
                mcast_list.pop(index)
                refresh_ui()

        # Button to add a new rule
        with ui.row().classes("w-full items-center gap-2 mt-4 pt-3 border-t border-slate-700"):
            def add_mcast():
                mcast_list.append({
                    "Regex": "eth.*",
                    "Beacon": True,
                    "Listen": True,
                    "Port": 0,
                    "Password": "",
                    "Priority": 0
                })
                refresh_ui()

            ui.button("Add Multicast Rule", icon="add", on_click=add_mcast).props("color=cyan-700")

        # Documentation box with exact text
        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700 mt-4"):
            ui.markdown("""
Controls which interfaces to enable or disable multicast peer discovery on. The default varies by platform.

Each multicast interface block has the following options:

* `Regex` — match the names of specific interfaces, i.e. `eth.*` for matching all network interfaces starting with `eth`
* `Beacon` — controls whether this node should advertise its presence to nearby devices
* `Listen` — controls whether this node should attempt to connect to other nearby nodes that are advertising their presence
* `Port` — sets the port number for the TLS listener that is automatically opened for each matched interface, or `0` for a random port
* `Password` — optionally sets a password, only other nodes that have the same password configured will discover and connect to each other automatically
* `Priority` — controls whether peerings made to a node over this interface should take precedence over peerings made to the same node over other interfaces, lower numbers are higher priority, i.e. for preferring ethernet over Wi-Fi
""")

        refresh_ui()


def create_list_editor(config_file_dict: dict, key: str, title: str, placeholder: str):
    """Generic editor for lists such as peers or listeners."""
    items = config_file_dict.setdefault(key, [])

    ui.label(title).classes("text-white font-bold text-lg mb-3")

    container = ui.column().classes("w-full gap-2")

    def refresh_ui():
        container.clear()
        with container:
            if not items:
                ui.label(f"No {title.lower()} configured.").classes("text-slate-400 italic text-sm")

            for index, item in enumerate(items):
                with ui.row().classes("w-full items-center gap-2"):

                    ui.input(
                        value=item,
                        on_change=lambda e, idx=index: update_item(idx, e.value)
                    ).classes("flex-1").props("dense outlined")

                    # Delete button for this row
                    ui.button(icon="delete", on_click=lambda idx=index: delete_item(idx)).props("flat color=red-400 dense")

    def update_item(index, new_value):
        if index < len(items):
            items[index] = new_value

    def delete_item(index):
        if index < len(items):
            items.pop(index)
            refresh_ui()

    # Input field to add items at the end
    with ui.row().classes("w-full items-center gap-2 mt-4 pt-3 border-t border-slate-700"):
        new_input = ui.input(placeholder=placeholder).classes("flex-1").props("dense outlined")

        def add_item():
            val = new_input.value.strip()
            if val:
                items.append(val)
                new_input.value = ""
                refresh_ui()

        ui.button("Add", icon="add", on_click=add_item).props("color=cyan-700")

    refresh_ui()


def create_node_info_editor(config_file_dict):
    if "NodeInfo" not in config_file_dict or not isinstance(config_file_dict["NodeInfo"], dict):
        config_file_dict["NodeInfo"] = {}

    node_info = config_file_dict["NodeInfo"]

    with ui.card().classes("w-full bg-slate-800 p-4 mt-4"):
        ui.label("Node Info Configuration").classes("text-white font-bold text-lg mb-3")

        container = ui.column().classes("w-full gap-3")

        def refresh_ui():
            container.clear()
            with container:
                # 1. Standard fields (Name, Location, Contact)
                with ui.row().classes("w-full items-center gap-2"):
                    ui.input(
                        label="Name",
                        value=node_info.get("name", ""),
                        on_change=lambda e: update_field("name", e.value)
                    ).classes("flex-1").props("dense outlined")

                with ui.row().classes("w-full items-center gap-2"):
                    ui.input(
                        label="Location",
                        value=node_info.get("location", ""),
                        on_change=lambda e: update_field("location", e.value)
                    ).classes("flex-1").props("dense outlined")

                with ui.row().classes("w-full items-center gap-2"):
                    ui.input(
                        label="Contact",
                        value=node_info.get("contact", ""),
                        on_change=lambda e: update_field("contact", e.value)
                    ).classes("flex-1").props("dense outlined")

                ui.separator().classes("bg-slate-700 my-2")
                ui.label("Custom Fields").classes("text-slate-300 font-semibold text-sm")

                # 2. Custom fields (everything beyond name, location, and contact)
                custom_keys = {k: v for k, v in node_info.items() if k not in ["name", "location", "contact"]}

                if not custom_keys:
                    ui.label("No custom fields configured.").classes("text-slate-400 italic text-sm")

                for k, v in list(custom_keys.items()):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.input(value=k, label="Key").classes("w-1/3").props("readonly dense outlined")
                        ui.input(
                            value=str(v),
                            label="Value",
                            on_change=lambda e, key=k: update_field(key, e.value)
                        ).classes("flex-1").props("dense outlined")

                        def make_del_custom(key=k):
                            return lambda: delete_custom_field(key)
                        ui.button(icon="delete", on_click=make_del_custom()).props("flat color=red-400 dense")

        def update_field(key, val):
            val_str = val.strip()
            if val_str == "":
                # If empty, completely remove from dict for clean code
                node_info.pop(key, None)
            else:
                node_info[key] = val_str

        def delete_custom_field(key):
            node_info.pop(key, None)
            refresh_ui()

        # Row to add additional custom fields
        with ui.row().classes("w-full items-center gap-2 mt-2 pt-2 border-t border-slate-700"):
            new_key_input = ui.input(placeholder="Key (e.g. website)").classes("w-1/3").props("dense outlined")
            new_val_input = ui.input(placeholder="Value").classes("flex-1").props("dense outlined")

            def add_custom_field():
                k = new_key_input.value.strip()
                v = new_val_input.value.strip()
                if k:
                    node_info[k] = v
                    new_key_input.value = ""
                    new_val_input.value = ""
                    refresh_ui()

            ui.button("Add Field", icon="add", on_click=add_custom_field).props("color=cyan-700")

        # Documentation box
        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700 mt-4"):
            ui.markdown("""
A free-form section that the node operator can use to put JSON-formatted metadata that may be made available to other nodes.
""")

        refresh_ui()


def gui_edit_tab_elements(hjson_config: dict) -> object:
    config_file_dict = hjson_parser.read_config_hjson()

    def execute_save():
        if switch_private_key.value:
            config_file_dict.pop("PrivateKey", None)
            config_file_dict["PrivateKeyPath"] = input_private_key_path.value
        else:
            config_file_dict.pop("PrivateKeyPath", None)
            config_file_dict["PrivateKey"] = input_private_key.value

        config_file_dict["IfName"] = input_interface_name.value
        config_file_dict["IfMTU"] = input_interface_mtu.value
        config_file_dict["NodeInfoPrivacy"] = "true" if input_node_info_privacy.value else "false"

        hjson_parser.write_config_hjson(config_file_dict)
        ui.notify("Configuration successfully saved!", type="positive")

    # 1. Private-Key
    with ui.card().classes("w-full bg-slate-800 p-4"):
        ui.label("Private-Key (inline <---> extra file):").classes("text-white font-bold text-lg mb-3")
        with ui.row().classes("w-full items-center no-wrap"):
            input_private_key = gui_input_line("Private-Key", config_file_dict.get("PrivateKey", ""))
            switch_private_key = ui.switch(value=config_file_dict.get("PrivateKey", "") == "").props("color=cyan-400 text-white")
            input_private_key_path = gui_input_line("Private-Key Path", config_file_dict.get("PrivateKeyPath", ""))

        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""### `PrivateKey`

The private key for this node, specified as a hexadecimal string. If not specified, a random private key will be generated on startup.


### `PrivateKeyPath`

The path to a file containing the private key for this node. This allows storing the private key in an external file instead of embedding it directly in the configuration file.

If both `PrivateKey` and `PrivateKeyPath` are specified, `PrivateKeyPath` takes precedence.

A key or keypair can be generated with:

```bash
openssl genpkey -algorithm Ed25519 -out private.key -outputkey public.key
```
""")

    # 2. Peers
    with ui.card().classes("w-full bg-slate-800 p-4"):
        create_list_editor(config_file_dict, "Peers", "Peers Configuration", "e.g. quic://example.com:12345")
        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
A list of outbound peering connections to make. Peers are specified in URL format. The following types of peers are supported:

* `tcp://1.1.1.1:1234` (TCP)
* `tls://1.1.1.1:1234` (TCP+TLS)
* `quic://1.1.1.1:1234` (QUIC+TLS)
* `socks://2.2.2.2:2345/1.1.1.1:1234` (TCP via SOCKS, i.e. `tcp://1.1.1.1:1234` via the proxy at `2.2.2.2:2345`)
* `sockstls://2.2.2.2:2345/1.1.1.1:1234` (TCP+TLS via SOCKS, i.e. `tls://1.1.1.1:1234` via the proxy at `2.2.2.2:2345`)
* `unix:///path/to/sock.sock` (UNIX)
* `ws://1.1.1.1:1234` or `ws://1.1.1.1:1234/path` (WebSockets, Yggdrasil 0.5.7 or later only)
* `wss://1.1.1.1:1234` or `wss://1.1.1.1:1234/path` (WebSockets+TLS, Yggdrasil 0.5.7 or later only)

Additional settings can optionally be added as query-string parameters to the end of the URL:

* `password=PASSWORD` — set this only for peers that require a shared secret/password to connect, the password must match the remote side or the connection will fail, limited to 64 characters
* `key=PUBLICKEY` — pin the specified public key for this peer, this will cause the connection to fail if the remote side’s public key does not match what you expect
* `maxbackoff=DURATION` — control what the maximum backoff/retry time will be if the peering goes down, format like `30s` for seconds or `1m` for minutes
* `sni=domainname.com` - set the Server Name Indication (SNI) for TLS peering connections to a different name (TLS and QUIC only)
    """)
            # Clean Public Peers Footer Links
            with ui.row().classes(
                "items-center gap-2 pt-1 text-xs text-slate-400"
            ):
                ui.icon("public", size="xs").classes("text-slate-400")
                ui.label("Find public peers:").classes(
                    "font-medium text-slate-300"
                )
                ui.link(
                    "Yggdrasil Peer List ↗",
                    target="http://[200:2688:699a:ce30:5897:cd3d:f999:8782]/",
                    new_tab=True,
                ).classes("text-sky-400 hover:text-sky-300 underline font-mono")
                ui.label("•").classes("text-slate-600")
                ui.link(
                    "publicpeers.neilalexander.dev ↗",
                    target="https://publicpeers.neilalexander.dev/",
                    new_tab=True,
                ).classes("text-sky-400 hover:text-sky-300 underline font-mono")

    # 3. Interface Peers
    create_interface_peers_editor(config_file_dict)

    # 4. Listener
    with ui.card().classes("w-full bg-slate-800 p-4"):
        create_list_editor(config_file_dict, "Listen", "Listener Configuration", "e.g. quic://[::]:12001?priority=3")
        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
A list of listeners to open for accepting incoming connections. Instead of supplying the remote address, you should instead supply a bind address. This would either be `0.0.0.0` for IPv4, `::` for IPv4+IPv6 or the IP address of a network interface on your machine. The following listener types are supported:

* `tcp://[::]:1234` (TCP)
* `tls://[::]:1234` (TCP+TLS)
* `quic://[::]:1234` (QUIC+TLS)
* `unix:///path/to/sock.sock` (UNIX)
* `ws://[::]:444` (WebSockets, Yggdrasil 0.5.7 or later only)

Additional settings can optionally be added as query-string parameters to the end of the URL:

* `password=PASSWORD` — optionally require a password to connect to this listener, the connecting node’s password must match or the connection will fail, limited to 64 characters
""")

    # 5. Multicast Interfaces
    create_multicast_interfaces_editor(config_file_dict)

    # 6. Allowed Public Keys
    with ui.card().classes("w-full bg-slate-800 p-4"):
        create_list_editor(config_file_dict, "AllowedPublicKeys", "Allowed public keys", "e.g. a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0")
        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
A list of public keys from which your node will allow incoming peering connections.

If public keys are specified, whitelisting is enabled and only nodes with those public keys will be able to peer. If no public keys are specified in this section then peering connections will be allowed as per the `Listen` and/or `MulticastInterfaces` configuration.

**NOTE:** This is not a firewall and does not control who can send you traffic over the Yggdrasil Network or reach open ports and services on your machine. For that you need an IPv6 firewall.
""")

    # 7. Interface name
    with ui.card().classes("w-full bg-slate-800 p-4"):
        ui.label("Interface name:").classes("text-white font-bold text-lg mb-3")
        with ui.row().classes("w-full items-center no-wrap"):
            input_interface_name = gui_input_line("Interface name", config_file_dict.get("IfName", ""))

        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
Determines which TUN interface to use. The default is set to `auto` which will try to set up a TUN automatically. If set to `none`, TUN will be disabled and the node will run in headless router-only mode.

On Linux, you can use this setting to give your Yggdrasil TUN interface a unique/persistent name, i.e. `ygg0`, if desired.
""")

    # 8. Interface MTU
    with ui.card().classes("w-full bg-slate-800 p-4"):
        ui.label("Interface MTU:").classes("text-white font-bold text-lg mb-3")
        with ui.row().classes("w-full items-center no-wrap"):
            input_interface_mtu = gui_input_line("Interface MTU", config_file_dict.get("IfMTU", ""))

        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700"):
            ui.markdown("""
The MTU of the interface.

Set to `65353` for max. possible MTU.
""")

    # 8. Node Info Privacy
    with ui.card().classes("w-full bg-slate-800 p-4"):
        ui.label("Node-Info Privacy:").classes("text-white font-bold text-lg mb-3")

        with ui.row().classes("w-full items-center justify-between no-wrap bg-slate-900/40 p-3 rounded border border-slate-700"):
            ui.label("Hide build information, operating system, architecture, and version.").classes("text-slate-300 text-sm")
            input_node_info_privacy = ui.switch(
                value=bool(config_file_dict.get("NodeInfoPrivacy", False))
            ).props("color=cyan-400 text-white")

        with ui.expansion("Documentation", icon="help_outline").classes("w-full text-slate-300 bg-slate-900/50 rounded mb-3 border border-slate-700 mt-3"):
            ui.markdown("""
Whether or not the node info should automatically include build information, i.e. the operating system and architecture and the Yggdrasil build version. If privacy is enabled, the node info will not contain this information.
""")

    # 9. Node Infos
    create_node_info_editor(config_file_dict)

    return execute_save


def gui_edit_tab() -> None:
    ui.label("GUI Editor").classes("text-h5 font-bold text-white mb-2")

    execute_save_callback = gui_edit_tab_elements(hjson_parser.read_config_hjson())

    # Confirmation Dialog for Permanent Changes
    with ui.dialog() as confirm_dialog, ui.card().classes("bg-slate-800 text-white p-6 max-w-md"):
        with ui.row().classes("items-center gap-3 mb-2"):
            ui.icon("warning", size="32px").classes("text-amber-400")
            ui.label("Permanent Configuration Change").classes("text-h6 font-bold")

            ui.label(
            "This action will permanently modify the Yggdrasil configuration file and cannot be undone!\n\n"
            "Please note: THIS WILL REMOVE ALL COMMENTS IN YOUR CONFIG FILE and you will need to manually restart the Yggdrasil service after saving."
            ).classes("text-slate-300 text-sm mb-6")

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Cancel", on_click=confirm_dialog.close).props("outline color=grey-5")

            def save_button():
                confirm_dialog.close()
                execute_save_callback()

            ui.button("Proceed & Save", on_click=save_button).props("color=red-700 font-bold")

    with ui.row().classes("mt-4 gap-2"):
        # Opens the warning dialog
        ui.button("Save Changes", on_click=confirm_dialog.open, icon="save").props("color=cyan-700")


def config_file_editor_page() -> None:
    # Check if the configuration file path environment variable is defined
    if getenv("YGG_CONFIG_FILE_PATH", "N/A") == "N/A":
        # Display a warning card instructing the user to set up the required environment variable
        with ui.column().classes("w-full max-w-xl mx-auto p-6 mt-10 items-center text-center"):
            ui.icon("warning", size="48px").classes("text-amber-400 mb-2")
            ui.label("Configuration File Path Not Defined").classes("text-h5 font-bold text-white")
            ui.label(
                "The configuration file path has not been defined for this container. "
                "Please make sure to set the 'YGG_CONFIG_FILE_PATH' environment variable "
                "and map the corresponding volume in your docker-compose.yml file."
            ).classes("text-slate-400 mb-4 text-sm")
        return

    else:
        # Render the full configuration editor layout if the environment variable is available
        with ui.column().classes("w-full p-2"):
            # Create sub-tabs header to toggle between Manual Edit and GUI Edit modes
            with ui.tabs().props(
                'dense align="left" active-color="cyan-400" indicator-color="cyan-400"'
            ).classes("w-full bg-slate-800 text-slate-300 px-4") as sub_tabs:
                manual_tab = ui.tab("Manual Edit", icon="edit_note")
                gui_tab = ui.tab("GUI Edit", icon="dashboard_customize")

            # Configure tab panels container linking to each respective tab view
            with ui.tab_panels(sub_tabs, value=gui_tab).classes("w-full bg-slate-900 p-6"):
                # Panel 1: Raw HJSON text editor view
                with ui.tab_panel(manual_tab).classes("w-full"):
                    manual_edit_tab()

                # Panel 2: Structured form-based GUI editor view
                with ui.tab_panel(gui_tab).classes("w-full"):
                    gui_edit_tab()
