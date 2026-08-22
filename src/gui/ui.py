from datetime import timedelta
from pathlib import Path
from os import getenv
from asyncio import sleep

import base64
from fastapi import Request
from starlette.responses import Response

from gui import labels, peer_infos, config_file_editor
from humanize import naturaldelta, naturalsize
from nicegui import run, ui, app
from ygg_client import YggClient


AUTH_USER = getenv("HTTP_BASIC_AUTH_USERNAME", "")
AUTH_PASS = getenv("HTTP_BASIC_AUTH_PASSWORD", "")

if AUTH_USER != "":
    @app.middleware("http")
    async def basic_auth_middleware(request: Request, call_next):
        """Add headers and check the http basic auth."""
        auth_header = request.headers.get("Authorization")

        if auth_header:
            try:
                scheme, credentials = auth_header.split(" ")
                if scheme.lower() == "basic":
                    decoded = base64.b64decode(credentials).decode("utf-8")
                    user, password = decoded.split(":", 1)
                    if user == AUTH_USER and password == AUTH_PASS:
                        return await call_next(request)
            except Exception:
                pass

        # Löst das native Browser-Login-Fenster aus
        return Response(
            "Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Yggdrasil GUI"'},
        )


def start() -> None:
    """Initialize the Yggdrasil client and start the NiceGUI web application server."""
    global ygg
    ygg = YggClient()

    favicon_path = Path(__file__).parent / "images" / "favicon.avif"
    ui.run(
        title="Yggdrasil GUI",
        favicon=favicon_path,
        dark=True,
        reload=False,
    )


def render_tabs(active_route: str) -> None:
    """Render the top navigation tabs bar and highlight the active route."""
    routes = {
        "/": "General",
        "/peers": "Peers",
        "/tree": "Tree",
        "/config_file": "Config file",
        "/restart": "Restart",
    }

    with ui.tabs().props(
        'active-color="white" active-bg-color="transparent" indicator-color="cyan-5"'
    ).classes("w-full bg-slate-900 border-b border-slate-800 shadow-md") as tabs:
        ui.tab("General", icon="info").on("click", lambda: ui.navigate.to("/"))
        ui.tab("Peers", icon="people").on("click", lambda: ui.navigate.to("/peers"))
        ui.tab("Tree", icon="account_tree").on("click", lambda: ui.navigate.to("/tree"))
        ui.tab("Config file", icon="data_object").on("click", lambda: ui.navigate.to("/config_file"))
        ui.tab("Restart", icon="restart_alt").on("click", lambda: ui.navigate.to("/restart"))

    tabs.value = routes.get(active_route, "General")


def build_tree_hierarchy(flat_tree: list) -> list:
    """Transform a flat list of network node dictionaries into a nested tree hierarchy.

    Args:
        flat_tree: A list of dicts representing network nodes with parent-child links.

    Returns:
        A list of root node dictionaries, each containing nested 'children' list references.
    """
    if not flat_tree:
        return []

    nodes_by_key = {}

    for item in flat_tree:
        key = item.get("key")
        if not key:
            continue

        seq = item.get("sequence", 0)

        nodes_by_key[key] = {
            "id": key,
            "key": key,
            "address": item.get("address", "N/A"),
            "sequence": seq,
            "parent_key": item.get("parent"),
            "children": [],
        }

    roots = []
    for key, node in nodes_by_key.items():
        parent_key = node["parent_key"]

        if parent_key == key or parent_key not in nodes_by_key:
            roots.append(node)
        else:
            nodes_by_key[parent_key]["children"].append(node)

    return roots


@ui.page("/tree")
async def tree_page() -> None:
    """Render the Network Topology Tree page UI."""
    render_tabs("/tree")

    with ui.column().classes("w-full p-4 gap-4"):
        # Header / Action Bar
        with ui.row().classes("w-full justify-between items-center px-1"):
            ui.label("Network Topology Tree").classes(
                "text-sm font-bold text-slate-300 uppercase tracking-wider"
            )
            ui.button(
                "Refresh Tree",
                icon="refresh",
                on_click=lambda: render_tree_view.refresh(),
            ).classes("bg-lime-500 hover:bg-lime-400 text-black font-bold")

        @ui.refreshable
        async def render_tree_view():
            """Fetch network topology asynchronously and render the tree UI component."""
            res = await run.io_bound(ygg.request, "getTree")
            tree_list = (
                res.get("response", {}).get("tree", [])
                if isinstance(res, dict)
                else []
            )

            with ui.card().classes(
                "w-full p-4 border border-slate-700/60 bg-slate-800/40 shadow-sm overflow-x-auto"
            ):
                if not tree_list:
                    ui.label("No tree data available from Yggdrasil.").classes(
                        "text-slate-400 italic"
                    )
                    return

                tree_nodes = build_tree_hierarchy(tree_list)

                # Create tree widget
                tree_widget = (
                    ui.tree(
                        tree_nodes,
                        node_key="id",
                    )
                    .classes("text-slate-200 font-mono text-sm")
                    .props("dark dense")
                )

                # Custom header template: Full key as link + sequence
                tree_widget.add_slot(
                    "default-header",
                    f"""
                    <div class="flex items-center gap-2 py-1 flex-wrap">
                        <span class="text-cyan-400 font-mono text-xs shrink-0">[{{{{ props.node.address }}}}]</span>
                        <a :href="`/peer/${{props.node.key}}`"
                        class="font-mono text-sm text-white underline hover:text-slate-300 break-all">
                            {{{{ props.node.key }}}}
                        </a>
                        <span class="text-slate-400 text-xs shrink-0">(Seq: {{{{ props.node.sequence }}}})</span>
                    </div>
                    """,
                )

                # Expand all nodes on initial render
                tree_widget.expand()

                # Expand / Collapse controls
                with ui.row().classes(
                    "mt-4 gap-2 border-t border-slate-700/60 pt-3"
                ):
                    ui.button(
                        "Expand All",
                        icon="unfold_more",
                        on_click=tree_widget.expand,
                    ).props("dense outline color=cyan-5")
                    ui.button(
                        "Collapse All",
                        icon="unfold_less",
                        on_click=tree_widget.collapse,
                    ).props("dense outline color=slate")

        # Call asynchronous render
        await render_tree_view()


@ui.page("/")
def general_page() -> None:
    """Render the main Overview page showing local Yggdrasil node details and build info."""
    render_tabs("/")

    self_res = ygg.request("getSelf") or {}
    self_data = self_res.get("response") or {}
    self_key = self_data.get("key", "").strip()

    address = self_data.get("address", "N/A")
    subnet = self_data.get("subnet", "N/A")
    pub_key = self_data.get("key", "N/A")
    routing_entries = self_data.get("routing_entries", "N/A")

    initial_name = self_data.get("build_name", "Loading...")
    initial_version = self_data.get("build_version", "Loading...")

    with ui.card().classes("m-4 p-6 shadow-sm border border-slate-700/60"):
        ui.label("Local Node Overview").classes(
            "text-xl font-bold mb-4 border-b border-slate-700 pb-2 text-slate-100"
        )

        with ui.grid(columns=2).classes("w-full gap-4 mb-6"):
            with ui.column().classes("gap-0"):
                ui.label("Public Key:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                ui.label(pub_key).classes(
                    "font-mono text-sm text-slate-200 break-all"
                )

            with ui.column().classes("gap-0"):
                ui.label("Yggdrasil Address:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                if address and address != "N/A":
                    clean_ip = address.strip("[]")
                    ui.link(
                        address, target=f"http://[{clean_ip}]", new_tab=True
                    ).classes("font-mono text-sm text-white underline")
                else:
                    ui.label(address).classes("font-mono text-sm text-slate-200")

            with ui.column().classes("gap-0"):
                ui.label("Subnet:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                ui.label(subnet).classes("font-mono text-sm text-slate-200")

            with ui.column().classes("gap-0"):
                ui.label("Routing Entries:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                ui.label(str(routing_entries)).classes(
                    "font-mono text-sm text-slate-200"
                )

        ui.label("System & Build Information").classes(
            "font-bold text-sm text-slate-300 mb-2"
        )
        with ui.grid(columns=2).classes(
            "w-full gap-4 mb-4 bg-slate-800/60 p-4 rounded-lg border border-slate-700/50"
        ):
            with ui.column().classes("gap-0"):
                ui.label("Software Name:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                lbl_name = ui.label(str(initial_name)).classes(
                    "text-sm font-mono text-slate-200"
                )

            with ui.column().classes("gap-0"):
                ui.label("Build Version:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                lbl_version = ui.label(str(initial_version)).classes(
                    "text-sm font-mono text-slate-200"
                )

            with ui.column().classes("gap-0"):
                ui.label("Platform:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                lbl_platform = ui.label("Loading...").classes(
                    "text-sm font-mono text-slate-200"
                )

            with ui.column().classes("gap-0"):
                ui.label("Architecture:").classes(
                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                )
                lbl_arch = ui.label("Loading...").classes(
                    "text-sm font-mono text-slate-200"
                )

        metadata_container = ui.column().classes("w-full gap-0")

    async def fetch_node_info():
        """Asynchronously query detailed node metadata and update the general UI components."""
        retry_container = ui.column().classes("w-full gap-0 mt-2")

        if not self_key:
            lbl_name.set_text(self_data.get("build_name", "N/A"))
            lbl_version.set_text(self_data.get("build_version", "N/A"))
            lbl_platform.set_text("N/A")
            lbl_arch.set_text("N/A")
            return

        try:
            info_res = (
                await run.io_bound(ygg.request, "getNodeInfo", key=self_key) or {}
            )
            response_data = info_res.get("response") or {}
            node_info = response_data.get(self_key) or {}

            lbl_name.set_text(str(node_info.get("buildname", "N/A")))
            lbl_version.set_text(str(node_info.get("buildversion", "N/A")))
            lbl_platform.set_text(str(node_info.get("buildplatform", "N/A")))
            lbl_arch.set_text(str(node_info.get("buildarch", "N/A")))

            custom_metadata = {
                k: v for k, v in node_info.items() if not k.startswith("build")
            }
            if custom_metadata:
                with metadata_container:
                    ui.label("Node Metadata").classes(
                        "font-bold text-sm text-slate-300 mt-2 mb-2"
                    )
                    with ui.grid(columns=2).classes(
                        "w-full gap-4 border-t border-slate-700/60 pt-3"
                    ):
                        for key, val in custom_metadata.items():
                            with ui.column().classes("gap-0"):
                                ui.label(f"{key.capitalize()}:").classes(
                                    "font-bold text-xs text-slate-400 uppercase tracking-wider"
                                )
                                ui.label(str(val)).classes(
                                    "text-sm text-slate-200"
                                )

        except Exception:
            lbl_name.set_text(str(self_data.get("build_name", "N/A")))
            lbl_version.set_text(str(self_data.get("build_version", "N/A")))
            lbl_platform.set_text("N/A (Timeout)")
            lbl_arch.set_text("N/A (Timeout)")

            with retry_container:
                with ui.row().classes("items-center gap-2 mt-2"):
                    ui.label("Failed to fetch node info.").classes("text-xs text-red-400")
                    # Klick lädt die Seite komplett neu:
                    ui.button("Retry", on_click=ui.navigate.reload).classes(
                        "bg-slate-700 text-white hover:bg-slate-600 text-xs px-3 py-1"
                    ).props("dense")

    ui.timer(0.05, fetch_node_info, once=True)


def get_sort_key(peer: dict, field: str) -> tuple:
    """Generate a comparison tuple to sort peer records safely.

    Ensures missing or 'N/A' values are consistently placed at the bottom of the list.

    Args:
        peer: Peer dictionary containing property values.
        field: The key in the peer dictionary to extract values for.

    Returns:
        A tuple of (priority, value) formatted for Python sorting.
    """
    val = peer.get(field)
    if val is None or val == "N/A":
        return (1, 0)

    # Sort numeric fields as floats
    if field in (
        "latency",
        "priority",
        "cost",
        "uptime",
        "bytes_recvd",
        "bytes_sent",
        "last_error_time",
    ):
        try:
            return (0, float(val))
        except (ValueError, TypeError):
            return (1, 0)

    # Sort text fields as strings
    return (0, str(val).lower())


def table_column(checkbox, name, internal_name, ygg_peer_dict) -> None:
    """Render a single column in the peers table if its visibility checkbox is checked.

    Args:
        checkbox: NiceGUI checkbox instance controlling visibility.
        name: Column header title displayed to the user.
        internal_name: Key string corresponding to peer attributes.
        ygg_peer_dict: Mapping of index/identifiers to peer data dictionaries.
    """
    if not checkbox.value:
        return

    with ui.column().classes("gap-0 shrink-0 min-w-max"):
        ui.label(name).classes(
            "h-9 flex items-center font-bold text-xs text-slate-400 uppercase tracking-wider border-b border-slate-700 whitespace-nowrap px-2"
        )

        for peer in ygg_peer_dict.values():
            with ui.element("div").classes(
                "h-9 flex items-center whitespace-nowrap px-2"
            ):
                label_text = peer.get(internal_name, "N/A")

                LIMIT_100MB = 100 * 1024 * 1024

                if internal_name == "key":
                    key = peer.get("key", "N/A")
                    if key and key != "N/A (No Key)":
                        ui.link(str(key), target=f"/peer/{key}").classes(
                            "font-mono text-sm text-white underline hover:text-slate-300"
                        )
                        continue
                    else:
                        ui.label("N/A (No Key)").classes(
                            "font-mono text-sm text-slate-500"
                        )
                        continue

                elif internal_name == "address":
                    address = peer.get("address", "N/A")
                    if address and address != "N/A":
                        clean_ip = address.strip("[]")
                        ui.link(
                            address, target=f"http://[{clean_ip}]", new_tab=True
                        ).classes(
                            "font-mono text-sm text-white underline hover:text-slate-300"
                        )
                        continue
                    else:
                        ui.label("N/A").classes(
                            "font-mono text-sm text-slate-500"
                        )
                        continue

                elif internal_name == "latency":
                    latency_ns = peer.get("latency", "N/A")
                    labels.latency_label(latency_ns)
                    continue

                elif internal_name == "priority":
                    priority = peer.get("priority", "N/A")
                    labels.priority_label(priority)
                    continue

                elif internal_name == "cost":
                    cost = peer.get("cost", "N/A")
                    labels.cost_label(cost)
                    continue

                elif internal_name == "uptime":
                    uptime = peer.get("uptime", "N/A")
                    labels.uptime_label(uptime)
                    continue

                elif internal_name == "inbound":
                    is_inbound = peer.get("inbound", False)
                    text_color = (
                        "text-cyan-400 font-semibold"
                        if is_inbound is True
                        else "text-slate-200"
                    )
                    ui.label(str(is_inbound)).classes(
                        f"font-mono text-sm {text_color}"
                    )
                    continue

                elif internal_name == "last_error_time":
                    last_error_time = peer.get("last_error_time")
                    if last_error_time is not None and last_error_time != "N/A":
                        seconds_ago = int(last_error_time) / 1e9
                        delta = timedelta(seconds=seconds_ago)
                        label_text = naturaldelta(delta)
                    else:
                        label_text = "N/A"

                elif internal_name == "bytes_recvd":
                    bytes_recvd = peer.get("bytes_recvd", "N/A")
                    if bytes_recvd != "N/A":
                        color = (
                            "text-cyan-400 font-bold"
                            if isinstance(bytes_recvd, (int, float))
                            and bytes_recvd > LIMIT_100MB
                            else "text-slate-200"
                        )
                        ui.label(
                            naturalsize(bytes_recvd, binary=True, format="%.1f")
                        ).classes(f"font-mono text-sm {color}")
                    else:
                        ui.label("N/A").classes(
                            "font-mono text-sm text-slate-200"
                        )
                    continue

                elif internal_name == "bytes_sent":
                    bytes_sent = peer.get("bytes_sent", "N/A")
                    if bytes_sent != "N/A":
                        color = (
                            "text-cyan-400 font-bold"
                            if isinstance(bytes_sent, (int, float))
                            and bytes_sent > LIMIT_100MB
                            else "text-slate-200"
                        )
                        ui.label(
                            naturalsize(bytes_sent, binary=True, format="%.1f")
                        ).classes(f"font-mono text-sm {color}")
                    else:
                        ui.label("N/A").classes(
                            "font-mono text-sm text-slate-200"
                        )
                    continue

                ui.label(str(label_text)).classes(
                    "font-mono text-sm text-slate-200"
                )


@ui.page("/peers")
def peers_page() -> None:
    """Render the Connected Peers table page, including column settings and peer addition form."""
    render_tabs("/peers")

    with ui.column().classes("w-full p-4 gap-4"):
        # 1. Action bar with manual refresh button above table
        with ui.row().classes("w-full justify-between items-center px-1"):
            ui.label("Connected Peers").classes(
                "text-sm font-bold text-slate-300 uppercase tracking-wider"
            )
            ui.button(
                "Refresh Table",
                icon="refresh",
                on_click=lambda: render_peer_card.refresh(),
            ).classes("bg-lime-500 hover:bg-lime-400 text-black font-bold")

        # 2. Column Visibility & Sorting Controls
        with ui.card().classes(
            "w-full p-0 border border-slate-700/60 bg-slate-800/20 shadow-sm"
        ):
            with ui.expansion(
                "Column & Sorting Settings", icon="tune"
            ).classes("w-full text-slate-300 font-bold"):
                with ui.column().classes(
                    "p-4 gap-4 w-full border-t border-slate-700/60"
                ):
                    # Sort Options Row
                    with ui.row().classes(
                        "items-center gap-4 border-b border-slate-700/40 pb-3 w-full flex-wrap"
                    ):
                        ui.label("Sort By:").classes(
                            "text-xs font-bold uppercase tracking-wider text-slate-400"
                        )
                        sort_by = (
                            ui.select(
                                options={
                                    "default": "Default (Unsorted)",
                                    "key": "Public Key",
                                    "address": "Yggdrasil Address",
                                    "remote": "Remote Address",
                                    "latency": "Latency",
                                    "priority": "Priority",
                                    "cost": "Cost",
                                    "uptime": "Uptime",
                                    "bytes_recvd": "Received Bytes",
                                    "bytes_sent": "Sent Bytes",
                                },
                                value="default",
                            )
                            .props("dense outlined dark")
                            .classes("w-48")
                        )

                        sort_direction = (
                            ui.select(
                                options={
                                    "asc": "Ascending (▲)",
                                    "desc": "Descending (▼)",
                                },
                                value="asc",
                            )
                            .props("dense outlined dark")
                            .classes("w-36")
                        )

                    # Checkbox Grid
                    ui.label("Visible Columns:").classes(
                        "text-xs font-bold uppercase tracking-wider text-slate-400"
                    )
                    with ui.grid().classes(
                        "grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2 w-full"
                    ):
                        cb_key = ui.checkbox("Public Key", value=True)
                        cb_address = ui.checkbox("Yggdrasil-Address", value=True)
                        cb_remote = ui.checkbox("Remote", value=True)
                        cb_latency = ui.checkbox("Latency", value=True)
                        cb_priority = ui.checkbox("Priority")
                        cb_cost = ui.checkbox("Cost")
                        cb_uptime = ui.checkbox("Uptime")
                        cb_path = ui.checkbox("Path")
                        cb_sequence = ui.checkbox("Sequence")
                        cb_inbound = ui.checkbox("Inbound")
                        cb_received = ui.checkbox("Received")
                        cb_sent = ui.checkbox("Sent")
                        cb_last_error = ui.checkbox("Last Error")
                        cb_last_error_time = ui.checkbox("Last Error Time")

        # Map sort dropdown fields directly to their corresponding checkbox instances
        sort_to_cb = {
            "key": cb_key,
            "address": cb_address,
            "remote": cb_remote,
            "latency": cb_latency,
            "priority": cb_priority,
            "cost": cb_cost,
            "uptime": cb_uptime,
            "bytes_recvd": cb_received,
            "bytes_sent": cb_sent,
        }

        def handle_sort_change(e):
            """Ensure selected sort field column is automatically set to visible and trigger table refresh."""
            if e.value in sort_to_cb:
                sort_to_cb[e.value].value = True
            render_peer_card.refresh()

        # Connect sort update handlers
        sort_by.on_value_change(handle_sort_change)
        sort_direction.on("update:model-value", lambda: render_peer_card.refresh())

        all_checkboxes = [
            cb_key,
            cb_address,
            cb_remote,
            cb_latency,
            cb_priority,
            cb_cost,
            cb_uptime,
            cb_path,
            cb_sequence,
            cb_inbound,
            cb_received,
            cb_sent,
            cb_last_error,
            cb_last_error_time,
        ]
        for cb in all_checkboxes:
            cb.on("update:model-value", lambda: render_peer_card.refresh())

        # 3. Peer Table Container
        @ui.refreshable
        def render_peer_card():
            """Fetch peer data, apply active sorting, and render the peers table view."""
            ygg_peer_dict = ygg.get_peer_dict() or {}

            # Sort dictionary values if a sort option is selected
            if sort_by.value != "default":
                reverse = sort_direction.value == "desc"
                sorted_peers = sorted(
                    ygg_peer_dict.values(),
                    key=lambda p: get_sort_key(p, sort_by.value),
                    reverse=reverse,
                )
                ygg_peer_dict = {i: peer for i, peer in enumerate(sorted_peers)}

            with ui.card().classes(
                "w-full max-h-[70vh] overflow-auto p-4 border border-slate-700/60 bg-slate-800/40 shadow-sm"
            ):
                if not ygg_peer_dict:
                    ui.label("No peers connected.").classes(
                        "text-slate-400 italic p-2"
                    )
                    return

                with ui.row().classes("flex-nowrap min-w-max gap-4"):
                    table_column(cb_key, "Public Key", "key", ygg_peer_dict)
                    table_column(
                        cb_address, "Yggdrasil-Address", "address", ygg_peer_dict
                    )
                    table_column(
                        cb_remote, "Remote-Address", "remote", ygg_peer_dict
                    )
                    table_column(
                        cb_latency, "Latency (ms)", "latency", ygg_peer_dict
                    )
                    table_column(cb_priority, "Priority", "priority", ygg_peer_dict)
                    table_column(cb_cost, "Cost", "cost", ygg_peer_dict)
                    table_column(
                        cb_uptime, "Connection Uptime", "uptime", ygg_peer_dict
                    )
                    table_column(cb_path, "Path", "path", ygg_peer_dict)
                    table_column(
                        cb_sequence, "Sequence", "sequence", ygg_peer_dict
                    )
                    table_column(cb_inbound, "Inbound", "inbound", ygg_peer_dict)
                    table_column(
                        cb_received, "Received", "bytes_recvd", ygg_peer_dict
                    )
                    table_column(cb_sent, "Sent", "bytes_sent", ygg_peer_dict)
                    table_column(
                        cb_last_error, "Last Error", "last_error", ygg_peer_dict
                    )
                    table_column(
                        cb_last_error_time,
                        "Last Error Time",
                        "last_error_time",
                        ygg_peer_dict,
                    )

        render_peer_card()

        # 4. Add Peer Card
        with ui.card().classes(
            "w-full p-4 border border-slate-700/60 bg-slate-800/40 shadow-sm gap-3"
        ):
            ui.label("Add New Peer").classes(
                "text-sm font-bold text-slate-200 uppercase tracking-wider"
            )

            async def add_peer():
                """Send request to add a new peer URI to Yggdrasil and refresh the interface."""
                uri = peer_input.value.strip()
                if not uri:
                    ui.notify("Please enter a peer URI!", type="warning")
                    return
                btn_add.props("loading")
                try:
                    res = await run.io_bound(ygg.request, "addPeer", uri=uri)
                    if res and res.get("status") == "success":
                        ui.notify(
                            f"Peer added successfully: {uri}", type="positive"
                        )
                        peer_input.value = ""
                        render_peer_card.refresh()
                    else:
                        err_msg = (
                            res.get("error", "N/A")
                            if isinstance(res, dict)
                            else "N/A"
                        )
                        ui.notify(
                            f"Failed to add peer: ({err_msg})", type="negative"
                        )
                except Exception as e:
                    ui.notify(f"Error: {e}", type="negative")
                finally:
                    btn_add.props(remove="loading")

            with ui.row().classes("w-full items-center gap-3"):
                peer_input = (
                    ui.input(
                        placeholder="e.g. tls://192.168.1.1:5678 or quic://[2001:db8:85a3::8a2e:370:7334]:1234"
                    )
                    .classes("flex-grow")
                    .props("dense outlined dark")
                    .on("keydown.enter", add_peer)
                )
                btn_add = ui.button(
                    "Connect Peer", icon="add", on_click=add_peer
                ).classes("bg-sky-600 hover:bg-sky-500 text-white font-bold")

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


@ui.page("/peer/{subpath:path}/")
def peer_page(subpath: str) -> None:
    """Render details page for a specific peer matching the given public key subpath.

    Args:
        subpath: Public key path identifying the peer node.
    """
    peer_dict = ygg.get_peer_dict()
    matching_peers = [
        peer for peer in peer_dict.values() if peer.get("key") == subpath
    ]

    if not matching_peers:
        peer_infos._render_not_found(subpath)
        return

    peer_info = ygg.request("getNodeInfo", key=subpath)
    ui.page_title(
        peer_info.get("response", {})
        .get(subpath, {})
        .get("name", f"Peer: {subpath}")
    )

    peer_infos._render_peer_overview(subpath, matching_peers, ygg)
    peer_infos._render_node_info(subpath, peer_info)


@ui.page("/config_file/")
def config_file_page():
    render_tabs("/config_file")

    config_file_editor.config_file_editor_page()


@ui.page("/restart/")
def restart_page() -> None:
    """Render the restart page to trigger a graceful container reboot."""
    render_tabs("/restart")

    with ui.column().classes("w-full max-w-xl mx-auto p-6 mt-10 items-center text-center"):
        ui.icon("restart_alt", size="64px").classes("text-cyan-400 mb-2")
        ui.label("Yggdrasil-GUI Restart").classes("text-h4 font-bold text-white")

        # Informational text explaining when to use it
        ui.label(
            "Here you can restart the application or the container. "
            "Use this feature if you have changed your Docker configuration "
            "(such as volumes or environment variables like admin URIs) "
            ", edited the config file external "
            "or if the socket connection to the Yggdrasil service has dropped."
        ).classes("text-slate-400 mb-6 text-sm")

        async def trigger_restart() -> None:
            ui.notify("GUI is restarting... The container will be back up shortly.", type="warning", timeout=3000)
            await sleep(2)
            # Docker will automatically spin it back up.
            exit(0)

        ui.button("Restart GUI / Container Now", on_click=trigger_restart).props("color=red-700").classes("font-bold")
