#!/bin/bash

# Fetch and deploy the certificates
echo "${AUTH_SA}" > /serviceaccount.json
gcloud auth activate-service-account --key-file=/serviceaccount.json

# Fetch the keybase profile from Network Storage
gsutil cp gs://${MYDOMAIN}/keybase/mwfloopool_keybase_profile.tgz /mwfloopool_keybase_profile.tgz

while /bin/true
do
    # Clean up existing profile and re-deploy
    rm -rf /keybase/{*,.*}
    mkdir -p /keybase

    # Extract a fresh copy of the keybase profile
    cd /
    tar xzf /mwfloopool_keybase_profile.tgz

    # Go Home
    cd /keybase

    # Not sure if we need this
    if [ ! -e /keybase/.mugle ]; then
        ln -s /root/.mugle . 
    fi
    # Fix permissions
    chown -R keybase:keybase /keybase

    # Start keybase server
    su - keybase /usr/bin/run_keybase

    # Monitor the keybase server processes
    sleep 12h # Enhance this to monitor the daemon processes and fal through if any fail

    PIDLIST=$(ps -ef | grep ^keybase | awk '{print $2 }' | grep -v ^1$)
    for p in ${PIDLIST}
    do
        kill -9 $p
    done
    
    sleep 5
done
