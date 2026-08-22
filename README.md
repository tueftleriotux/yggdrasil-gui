# Yggdrasil GUI

A web-based user interface to manage and monitor your Yggdrasil network node.

---

## Requires

* Yggdrasil Network (yggdrasil-go) node running

Currently only tested on Arch and Debian Linux.  
Should also work with other distributions and MS Windows.

## Features

* Overview of connected peers and active links
* Real-time status and information of your Yggdrasil node
* Adding and removing peers while runtime
* Editing config file in text editor or with gui editor.

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
      - "127.0.0.1:9999:8080"

    volumes:
      - /var/run/yggdrasil.sock:/var/run/yggdrasil.sock  # Arch Linux
      # - /run/yggdrasil/yggdrasil.sock:/run/yggdrasil/yggdrasil.sock  # Debian Linux
      - /etc/yggdrasil.conf:/etc/yggdrasil.conf # Arch Linux
      # - /etc/yggdrasil/yggdrasil.conf:/etc/yggdrasil/yggdrasil.conf  # Debian Linux
      # - C:\\ProgramData\\Yggdrasil\\yggdrasil.conf:C:\\ProgramData\\Yggdrasil\\yggdrasil.conf  # MS Windows

    environment:
      YGG_ADMIN_URI: "unix:///var/run/yggdrasil.sock"  # Arch Linux
      # YGG_ADMIN_URI: "unix:///run/yggdrasil/yggdrasil.sock"  # Debian Linux
      # YGG_ADMIN_URI: "tcp://host.docker.internal:9001"  # MS Windows
      YGG_CONFIG_FILE_PATH: "/etc/yggdrasil.conf" # Arch Linux
      # YGG_CONFIG_FILE_PATH: "/etc/yggdrasil/yggdrasil.conf" # Debian Linux
      # YGG_CONFIG_FILE_PATH: "C:\\ProgramData\\Yggdrasil\\yggdrasil.conf"  # MS Windows
      # Only supports HJSON formatted config files in gui edit mode!
      # If you have a JSON formatted config, convert it with this command:
      # "yggdrasil -normaliseconf -useconffile /etc/yggdrasil.conf"  # Arch Linux
      # "yggdrasil -normaliseconf -useconffile /etc/yggdrasil/yggdrasil.conf"  # Debian Linux
      # "yggdrasil -normaliseconf -useconffile C:\\ProgramData\\Yggdrasil\\yggdrasil.conf"  # MS Windows
      # HTTP_BASIC_AUTH_USERNAME: "admin"
      # HTTP_BASIC_AUTH_PASSWORD: "changeme"

    # extra_hosts:
    #   - "host.docker.internal:host-gateway"  # MS Windows

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

## Security Best Practice: External Private Key Storage

For enhanced security, it is recommended to store your Yggdrasil private key in a separate external file rather than keeping it embedded directly in your main configuration file. 

You can extract your private key from an existing configuration file and secure it with the appropriate permissions by running the following commands:

```bash
# Export the private key and save it to an external file
sudo yggdrasil -useconffile /etc/yggdrasil.conf -exportkey | sudo tee /etc/yggdrasil.key

# Secure the key file permissions and ownership
sudo chown root:yggdrasil /etc/yggdrasil.key
sudo chmod 740 /etc/yggdrasil.key
```

> **Important:** After exporting the key, remember to remove the inline private key from your configuration file. You can then reference it using `PrivateKeyPath` instead.

### Default Configuration Paths

* **Arch Linux:** `"/etc/yggdrasil.conf"`
* **Debian Linux:** `"/etc/yggdrasil/yggdrasil.conf"`
* **MS Windows:** `"C:\\ProgramData\\Yggdrasil\\yggdrasil.conf"`

---

## Screenshots

![Local node overview](./docs/images/local-node-overview.avif)
![Peers](./docs/images/peers.avif)
![Peer overview](./docs/images/peer-overview.avif)
![Tree](./docs/images/tree.avif)
![Config file manal edit](./docs/images/config_file_manual_edit.avif)
![Config file gui edit 1](./docs/images/config_file_gui_edit_1.avif)
![Config file gui edit 2](./docs/images/config_file_gui_edit_2.avif)
![Config file gui edit 3](./docs/images/config_file_gui_edit_3.avif)
![Config file gui edit 4](./docs/images/config_file_gui_edit_4.avif)

## 📄 License

Distributed under the Affero General Public License v3. See `LICENSE` for more information.
