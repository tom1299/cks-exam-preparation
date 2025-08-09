#!/bin/bash

# Create etcd user and group
if ! getent group etcd >/dev/null; then
  groupadd etcd
fi
if ! id -u etcd >/dev/null 2>&1; then
  useradd -r -g etcd -s /bin/false etcd
fi

# Fix etcd data directory ownership
chown -R etcd:etcd /var/lib/etcd
