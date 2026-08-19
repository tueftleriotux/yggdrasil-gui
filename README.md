# Yggdrasil GUI

A modern web-based user interface to manage and monitor your Yggdrasil network node.

---

## Requires

* Yggdrasil Network node running

Currently only tested with yggdrasil-go.

## Features

* Overview of connected peers and active links
* Real-time status and information of your Yggdrasil node
* Adding and removing peers
* NiceGUI web interface

---

## Quick Start with Docker (Recommended)

The easiest way to run the Yggdrasil GUI is using Docker Compose.

### 1. Create a `docker-compose.yml` file
Create a file named `docker-compose.yml` with the following content:

```yaml
services:
  yggdrasil-gui:
    image: ghcr.io/tueftleriotux/yggdrasil-gui:main
    container_name: yggdrasil-gui
    restart: unless-stopped
    ports:
      - "127.0.0.1:9999:9999"
    volumes:
      - /var/run/yggdrasil.sock:/var/run/yggdrasil.sock # Linux host setup
    environment:
      YGG_ADMIN_URI: "unix:///var/run/yggdrasil.sock" # For Windows/macOS: use tcp://host.docker.internal:9001
      PORT: 9999
      WEBROOT: "/" # Must end with a trailing slash
    extra_hosts:
      - "host.docker.internal:host-gateway" # Enables host.docker.internal on Linux/Windows
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

```

### 2. Start the container
Run the following command in your terminal:

```bash
docker compose up -d
```

The GUI will be available at **`http://localhost:9999`**

---

## 🔄 Updating the Container

To pull the latest changes and update your running container:

```bash
docker compose pull
docker compose up -d --remove-orphans
```

---

## 📄 License

Distributed under the Affero General Public License v3. See `LICENSE` for more information.
