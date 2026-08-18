from typing import Union
from humanize import naturaldelta
from nicegui import ui


def latency_label(latency_ns: Union[int, str], extra_classes: str = "") -> None:
    """Renders a color-coded UI label for latency, converting nanoseconds to milliseconds.

    Args:
        latency_ns: Latency value in nanoseconds, or 'N/A'.
        extra_classes: Additional Tailwind CSS styling classes.
    """
    if latency_ns == "N/A" or latency_ns is None:
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    try:
        latency = round(int(latency_ns) / 1_000_000, 1)  # ns -> ms
    except (ValueError, TypeError):
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    if latency < 30:
        color_class = "text-green-500"
    elif latency < 80:
        color_class = "text-lime-500"
    elif latency < 150:
        color_class = "text-yellow-500"
    elif latency < 300:
        color_class = "text-orange-500"
    else:
        color_class = "text-red-500"

    ui.label(f"{latency} ms").classes(f"{color_class} {extra_classes}")


def priority_label(priority: Union[int, str], extra_classes: str = "") -> None:
    """Renders a color-coded UI label for peer priority (lower values indicate higher priority).

    Args:
        priority: Priority numerical value or string, or 'N/A'.
        extra_classes: Additional Tailwind CSS styling classes.
    """
    if priority == "N/A" or priority is None:
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    try:
        prio_val = int(priority)
    except (ValueError, TypeError):
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    if prio_val == 0:
        color_class = "text-green-500"
    elif prio_val == 1:
        color_class = "text-lime-500"
    elif prio_val == 2:
        color_class = "text-yellow-500"
    elif prio_val == 3:
        color_class = "text-orange-500"
    else:
        color_class = "text-red-500"

    ui.label(f"{prio_val}").classes(f"{color_class} {extra_classes}")


def cost_label(cost: Union[int, str], extra_classes: str = "") -> None:
    """Renders a color-coded UI label for path routing cost.

    Args:
        cost: Routing cost value or string, or 'N/A'/'0'.
        extra_classes: Additional Tailwind CSS styling classes.
    """
    if cost in ("N/A", "0", None):
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    try:
        cost_val = int(cost)
    except (ValueError, TypeError):
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    if cost_val <= 2:
        color_class = "text-green-500"
    elif cost_val <= 5:
        color_class = "text-lime-500"
    elif cost_val <= 10:
        color_class = "text-yellow-500"
    elif cost_val <= 20:
        color_class = "text-orange-500"
    else:
        color_class = "text-red-500"

    ui.label(f"{cost_val}").classes(f"{color_class} {extra_classes}")


def uptime_label(seconds: Union[int, str], extra_classes: str = "") -> None:
    """Renders a color-coded human-readable uptime label using humanize.naturaldelta.

    Args:
        seconds: Uptime duration in seconds, or 'N/A'.
        extra_classes: Additional Tailwind CSS styling classes.
    """
    if seconds == "N/A" or seconds is None:
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    try:
        sec = int(seconds)
    except (ValueError, TypeError):
        ui.label("N/A").classes(f"text-gray-400 {extra_classes}")
        return

    formatted_time = naturaldelta(sec)

    if sec >= 604_800:  # > 7 days
        color_class = "text-green-500"
    elif sec >= 86_400:  # > 1 day
        color_class = "text-lime-500"
    elif sec >= 3_600:  # > 1 hour
        color_class = "text-yellow-500"
    elif sec >= 600:  # > 10 minutes
        color_class = "text-orange-500"
    else:  # < 10 minutes
        color_class = "text-red-500"

    ui.label(f"{formatted_time}").classes(f"{color_class} {extra_classes}")
