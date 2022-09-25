#!/bin/bash -x

# Live here
cd /wallet

if [ "$NET_FLAG" = "--floonet" ]; then
    # Set Network Flag in TOML Config
    sed -i 's/chain_type = .*/chain_type = \"Floonet\"/' /usr/src/mugle/mugle-wallet.toml
fi

# Copy in updated config
cp /usr/src/mugle/mugle-wallet.toml /wallet/mugle-wallet.toml


# Restore or Create new wallet if needed
if [ ! -f /wallet/wallet_data/wallet.seed ]; then
    # Create new
    echo ${WALLET_PASSWORD} > /password.txt
    echo ${WALLET_PASSWORD} >> /password.txt
    mugle-wallet ${NET_FLAG} init < /password.txt
    rm /password.txt
elif [ ! -e /wallet/wallet_data/db ]; then
    # Restore from seed
    mugle-wallet ${NET_FLAG} -p ${WALLET_PASSWORD} restore 
fi

# Run as Public or Private listener based run argument
MODE="public"
if [ $# -ne 0 ]; then
    MODE=$1
fi


if [ $MODE == "private" ]; then
    mkdir -p /root/.mugle/
    echo ${WALLET_OWNER_API_PASSWORD} > /root/.mugle/.api_secret
    chmod 600 /root/.mugle/.api_secret
    echo "Waiting for public wallet to start"
    sleep 120 # Let the public wallet start first
    keybase login
    echo "Starting wallet owner_api"
    mugle-wallet ${NET_FLAG} -p ${WALLET_PASSWORD} owner_api
else
    if [ -e /wallet/RUN_BACKUP ]; then
        echo "Backup Wallet DB"
        tar czf wallet_db.backup.$(date "+%F-%T" |tr : '_').tgz wallet_data
    fi
    if [ -e /wallet/RUN_CHECK ]; then
        echo "Running wallet check"
        mugle-wallet ${NET_FLAG} -p ${WALLET_PASSWORD} check
    fi
    echo "Starting public wallet listener"
    mugle-wallet ${NET_FLAG} -p ${WALLET_PASSWORD} listen
fi
