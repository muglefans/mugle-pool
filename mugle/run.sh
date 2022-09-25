#!/bin/bash

# Live here
cd /server

# Put config file in place
cp /usr/src/mugle/mugle-server.toml /server/mugle-server.toml

# Update mugle-server config
if [ "$NET_FLAG" = "--floonet" ]; then
    # Set Network Flag in TOML Config
    sed -i 's/chain_type = .*/chain_type = \"Floonet\"/' /server/mugle-server.toml
fi
if [  "$NET_FLAG" == "--floonet" ]; then
    # disable mainnet preferred peers
    sed -i 's/peers_preferred = .*$/#peers_preferred = []/' /server/mugle-server.toml
fi
if [ ! -z "$WALLETPORT" ]; then
    # Update Wallet Port for remote stratum
    sed -i "s/^wallet_listener_url = .*$/wallet_listener_url = \"http:\/\/wallet:${WALLETPORT}\"/" /server/mugle-server.toml
fi

#echo "Backup Chain Data"
#tar czf mugle.backup.$(date "+%F-%T" |tr : '_').tgz .mugle

mugle ${NET_FLAG} server run
