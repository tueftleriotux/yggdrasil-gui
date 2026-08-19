from datetime import timedelta
from typing import Any, Dict, List

from humanize import naturaldelta, naturalsize
from nicegui import ui

from gui import labels


def _render_info_field(
    label: str,
    value: str,
    is_mono: bool = False,
    is_semibold: bool = False,
    is_break_all: bool = False,
) -> None:
    """Helper component to render a standardized labeled metadata item."""
    with ui.column().classes("gap-0"):
        ui.label(label).classes(
            "font-bold text-xs text-slate-400 uppercase tracking-wider"
        )

        css_classes = ["text-sm", "text-slate-200"]
        if is_mono:
            css_classes.append("font-mono")
        if is_semibold:
            css_classes.append("font-semibold")
        if is_break_all:
            css_classes.append("break-all")

        if label == "Yggdrasil Address:":
            ui.link(
                value, target=f"http://[{value.strip()}]", new_tab=True
            ).classes(" ".join(css_classes))
        else:
            ui.label(value).classes(" ".join(css_classes))


def _render_not_found(subpath: str) -> None:
    """Renders the error state if a peer is not found."""
    with ui.card().classes(
        "w-full p-6 text-center border border-red-900/50 bg-red-950/30"
    ):
        ui.label(f"Peer with Public Key: {subpath} not found.").classes(
            "text-red-400 font-semibold"
        )


def _render_active_connections(
    peers: List[Dict[str, Any]], subpath: str, ygg_instance: Any
) -> None:
    """Renders the table/grid of active peer connections with individual disconnect action buttons."""
    ui.label("Active Connections").classes(
        "font-bold text-sm text-slate-300 mt-2 mb-2"
    )

    def disconnect_single_peer(peer: Dict[str, Any]) -> None:
        """Handles disconnect confirmation and API call for a single peer entry."""
        target = peer.get("remote", f"Port {peer.get('port', 'N/A')}")

        with (
            ui.dialog() as dialog,
            ui.card().classes("bg-slate-800 border border-slate-700 p-6"),
        ):
            ui.label("Disconnect?").classes(
                "text-lg font-bold text-slate-100 mb-1"
            )
            ui.label(
                f"Are you sure you want to disconnect from: {target} ?"
            ).classes("text-sm text-slate-400 mb-4")

            def execute_disconnect():
                dialog.close()
                if "remote" in peer:
                    response = ygg_instance.request(
                        "removePeer", endpoint=peer["remote"]
                    )
                else:
                    response = ygg_instance.request("removePeer", key=subpath)

                if response.get("status", {}) != "error":
                    ui.notify(
                        f"{target} disconnected!",
                        type="positive",
                        color="lime-600",
                        icon="link_off",
                    )

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props(
                    "flat text-color=slate-300"
                )
                ui.button("Disconnect", on_click=execute_disconnect).classes(
                    "bg-red-600 hover:bg-red-700 text-white font-bold"
                )

        dialog.open()

    with ui.row().classes(
        "w-full overflow-x-auto gap-6 bg-slate-800/60 p-4 rounded-lg border border-slate-700/50"
    ):
        with ui.column().classes("gap-3"):
            ui.label("Remote Address").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                ui.label(peer.get("remote", "N/A")).classes(
                    "text-sm font-mono text-slate-200"
                )

        with ui.column().classes("gap-3"):
            ui.label("Latency").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                labels.latency_label(
                    peer.get("latency", "N/A"), extra_classes="text-sm"
                )

        with ui.column().classes("gap-3"):
            ui.label("Priority").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                labels.priority_label(
                    peer.get("priority", "N/A"), extra_classes="text-sm"
                )

        with ui.column().classes("gap-3"):
            ui.label("Cost").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                labels.cost_label(
                    peer.get("cost", "N/A"), extra_classes="text-sm"
                )

        with ui.column().classes("gap-3"):
            ui.label("Uptime").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                labels.uptime_label(
                    peer.get("uptime", "N/A"), extra_classes="text-sm"
                )

        with ui.column().classes("gap-3"):
            ui.label("Inbound").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                is_inbound = peer.get("inbound", False)
                text_color = (
                    "text-cyan-400" if is_inbound is True else "text-slate-200"
                )
                ui.label(str(is_inbound)).classes(
                    f"text-sm font-mono {text_color}"
                )

        # High-volume traffic highlight threshold: 100 MB in bytes
        LIMIT_100MB = 100 * 1024 * 1024

        with ui.column().classes("gap-3"):
            ui.label("Received").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                bytes_recvd = peer.get("bytes_recvd", "N/A")
                if bytes_recvd == "N/A":
                    ui.label("N/A").classes("text-sm text-slate-200")
                else:
                    color = (
                        "text-cyan-400 font-bold"
                        if isinstance(bytes_recvd, (int, float))
                        and bytes_recvd > LIMIT_100MB
                        else "text-slate-200"
                    )
                    ui.label(
                        naturalsize(bytes_recvd, binary=True, format="%.1f")
                    ).classes(f"text-sm font-mono {color}")

        with ui.column().classes("gap-3"):
            ui.label("Sent").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                bytes_sent = peer.get("bytes_sent", "N/A")
                if bytes_sent == "N/A":
                    ui.label("N/A").classes("text-sm text-slate-200")
                else:
                    color = (
                        "text-cyan-400 font-bold"
                        if isinstance(bytes_sent, (int, float))
                        and bytes_sent > LIMIT_100MB
                        else "text-slate-200"
                    )
                    ui.label(
                        naturalsize(bytes_sent, binary=True, format="%.1f")
                    ).classes(f"text-sm font-mono {color}")

        error_occurred = False
        with ui.column().classes("gap-3"):
            ui.label("Last Error").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                last_error = peer.get("last_error")
                if last_error and last_error != "N/A":
                    ui.label(str(last_error)).classes("text-sm text-red-400")
                    error_occurred = True
                else:
                    ui.label("N/A").classes("text-sm text-slate-500")

        if error_occurred:
            with ui.column().classes("gap-3"):
                ui.label("Last Error Time").classes(
                    "font-bold text-xs text-slate-400"
                )
                for peer in peers:
                    error_time = peer.get("last_error_time")
                    if error_time is not None and error_time != "N/A":
                        seconds_ago = int(error_time) / 1e9  # ns -> s
                        delta = timedelta(seconds=seconds_ago)
                        ui.label(naturaldelta(delta)).classes(
                            "text-sm text-red-400"
                        )
                    else:
                        ui.label("N/A").classes("text-sm text-slate-500")

        # Action column with individual disconnect buttons
        with ui.column().classes("gap-2 items-center"):
            ui.label("Action").classes("font-bold text-xs text-slate-400")
            for peer in peers:
                ui.button(
                    icon="link_off",
                    on_click=lambda p=peer: disconnect_single_peer(p),
                ).props("dense flat color=red-400 size=sm").classes(
                    "hover:bg-red-950/50 rounded"
                ).tooltip("Disconnect")


def _render_peer_overview(
    subpath: str, peers: List[Dict[str, Any]], ygg_instance: Any
) -> None:
    """Renders the top overview card for a peer."""
    first_peer = peers[0]
    latest_peer = peers[-1]

    with ui.card().classes(
        "w-full p-6 shadow-sm border border-slate-700/60 mb-4"
    ):
        ui.label("Peer Overview").classes(
            "text-xl font-bold mb-4 border-b border-slate-700 pb-2 text-slate-100"
        )

        with ui.grid(columns=2).classes("w-full gap-4 mb-4"):
            _render_info_field(
                "Public Key:", subpath, is_mono=True, is_break_all=True
            )
            _render_info_field(
                "Yggdrasil Address:",
                first_peer.get("address", "N/A"),
                is_mono=True,
            )
            _render_info_field(
                "Path:", str(latest_peer.get("path", "N/A")), is_mono=True
            )
            _render_info_field(
                "Sequence:",
                str(latest_peer.get("sequence", "N/A")),
                is_mono=True,
            )

        _render_active_connections(peers, subpath, ygg_instance)


def _render_node_info(subpath: str, response_data: Dict[str, Any]) -> None:
    """Renders the node system and custom metadata card."""
    with ui.card().classes("w-full p-6 shadow-sm border border-slate-700/60"):
        ui.label("Node Information").classes(
            "text-xl font-bold mb-4 border-b border-slate-700 pb-2 text-slate-100"
        )

        node_info = response_data.get("response", {}).get(subpath, {})

        arch = node_info.get("buildarch", "N/A")
        platform = node_info.get("buildplatform", "N/A")
        version = node_info.get("buildversion", "N/A")
        name = node_info.get("buildname", "N/A")

        # Static system & build info
        with ui.grid(columns=2).classes(
            "w-full gap-4 mb-4 bg-slate-800/60 p-4 rounded-lg border border-slate-700/50"
        ):
            _render_info_field("Software Name:", str(name), is_mono=True)
            _render_info_field("Build Version:", str(version), is_mono=True)
            _render_info_field("Platform:", str(platform), is_mono=True)
            _render_info_field("Architecture:", str(arch), is_mono=True)

        # Dynamic custom metadata (NodeInfo fields from yggdrasil.conf)
        custom_metadata = {
            k: v for k, v in node_info.items() if not k.startswith("build")
        }

        if custom_metadata:
            ui.label("Node Metadata").classes(
                "font-bold text-sm text-slate-300 mt-2 mb-2"
            )
            with ui.grid(columns=2).classes(
                "w-full gap-4 border-t border-slate-700/60 pt-3"
            ):
                for key, val in custom_metadata.items():
                    _render_info_field(f"{key.capitalize()}:", str(val))
        else:
            ui.label("No custom metadata available for this node.").classes(
                "text-sm text-slate-500 italic mt-2"
            )
