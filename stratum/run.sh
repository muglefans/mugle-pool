#!/bin/bash

# Update API Port for remote stratum
if [ ! -z "$APIPORT" ]; then
    sed -i "s/^api_port = .*$/api_port = ${APIPORT}/" /usr/local/bin/mugle-pool.toml
fi


echo "Starting MuglePool Stratum Server"
cp /usr/local/bin/mugle-pool.toml /stratum/
/usr/local/bin/mugle-pool
