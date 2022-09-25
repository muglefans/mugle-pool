# Deploy Mugle-Pool to a single VM using docker-compose

## Provision a VM
* 2 vCPU 4G Mem minimum
* Install: git, Docker,  and docker-compose
* Static public IP address
* Open ports inbound: 80, 443, 2222, 3333
* Configure a Domain Name: Set DNS A records for .domain, api.domain, and stratum.domain

## Get the mugle-pool software
* git checkout git@github.com:mugle-pool/mugle-pool.git

## Edit Configuration (Yes, its a mess and needs to be improved)
* mugle-pool/docker-compose/.env
* mugle-pool/mugle-js/webui/src/config.js
* mugle-pool/mugle-py/services/config.ini
* mugle-pool/nginx/src/\*.conf
* mugle-pool/stratum/mugle-pool.toml
* Maybe a few others....

## Build and Run it
### Mugle Node
Build and start the mugle node first and give it an hour to sync
* cd mugle-pool/docker-compose
* docker-compose up -d --build mugle
* docker-compose logs -f

### The Pool
Build and start the pool
* cd mugle-pool/docker-compose
* docker-compose up -d --build
* docker-compose logs -f

### Bugs
* You will see lots of connection errors at first pool startup.  Its normal for a few minutes
* It may be necessary to restart the pool (docker-compose down/up) a few times for new installs
* Not all services are integrated with docker-compose yet - its missing: auditor, blockvalidator, dbbackup, paymentmaker, poolblockunlocker, and tidywallet
* Grasph Rate calculations have not been updated for latest cuckaroo fork
