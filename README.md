# mugle-pool

## What it is:
An Open Source Mining Pool for [Mugle](https://github.com/mugleproject/mugle) MimbleWimble Cryptocurrency Implementation

### The architecture:
* Microservices

### The components:
* Pool Stratum Proxy: Rust
* Pool data processing jobs: Python3/SQLAlchemy
* Pool API: Python3/Flask/gunicorn
* Pool Web UI: NodeJS/Electron/Bootstrap/React
* Database: MariaDB/Redis
* Build/Packaging: Docker
* Deploy: Kubernetes/Docker-compose
* Orchestration: Kubernetes
* Log collection: Splunk
* Load Balancer/Certificates: NGINX/LetsEncrypt
* Monitoring & Alerting: ?? NotYet (Icinga?)

#### To run the pool yourself use: [docker-compose/README.md](docker-compose/README.md)

### Current Status:
* This project is under development.
* Please contribute!
* Join the discussion on [Gitter](https://gitter.im/mugle-pool/Lobby)

Install dependences
sudo apt-get update
sudo apt-get install git curl libssl-dev pkg-config clang
Install rust
curl https://sh.rustup.rs -sSf | sh
Use rust 1.40.0 stable
rustup default 1.40.0
Build
git clone https://github.com/mugleproject/mugle-pool.git
cd mugle-pool/stratum
cargo build