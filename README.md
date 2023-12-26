# ovh-dns-updater Microservice Migration

## Overview

The `ovh-dns-updater` script has been migrated to a microservice architecture to enhance scalability, maintainability, and flexibility. This README provides an overview of the changes and instructions for deploying and managing the ovh-dns-updater microservice.

## Table of Contents

- [Changes](#changes)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Scaling](#scaling)
- [Maintenance and Updates](#maintenance-and-updates)
- [Contributing](#contributing)
- [License](#license)

## Changes

### Microservice Components

The ovh-dns-updater has been refactored into the following microservice components:

1. **Updater Service:**
   - Core logic for updating A/AAAA DNS records at OVH.
   - Manages interactions with the OVH API.
   - Periodically checks and updates DNS records.

2. **Config Service:**
   - Handles configuration management.
   - Retrieves domain/subdomain configurations from a centralized configuration store.
   - Supports dynamic updates to configuration.

3. **IP Service:**
   - Retrieves the current public IPV4 and IPV6 addresses.
   - Ensures the availability of IP addressing information.

### Communication

Microservices communicate via HTTP RESTful APIs. The Updater Service exposes endpoints for triggering updates, and the Config and IP Services provide configuration and IP information, respectively.

### Dockerization

Each microservice is containerized using Docker, enabling easy deployment and orchestration.

## Prerequisites

Before deploying the ovh-dns-updater microservice, ensure you have the following:

- Docker installed on the target machine.
- Access to the centralized configuration store for domain/subdomain configurations.
- API access keys for the OVH API.

## Configuration

### Config Service

Configure the Config Service with the connection details to the centralized configuration store.

### IP Service

No additional configuration is required for the IP Service.

### Updater Service

Configure the Updater Service with the following:

- OVH API access keys.
- Endpoints for the Config and IP Services.
- Polling interval for checking and updating DNS records.

## Deployment

Deploy each microservice using Docker. Sample Docker Compose files are provided in the `docker-compose` directory.

1. Build Docker images:

   ```bash
   docker-compose build
   docker-compose up -d
   ```
   
## Monitoring and Logging
Microservices emit logs to standard output. Configure a centralized logging solution for log aggregation.

### Updater Service Metrics
Enable monitoring and metrics using Prometheus and Grafana. Sample configurations are available in the monitoring directory.

## Scaling
Scale microservices independently based on demand. Use container orchestration tools like Kubernetes for dynamic scaling.

## Maintenance and Updates
Regularly update microservice containers with new releases. Follow the update instructions in the CHANGELOG.

## Contributing
Please follow the Contributing Guidelines for contributing to the ovh-dns-updater microservice.

## License
This project is licensed under the GNU General Public License.