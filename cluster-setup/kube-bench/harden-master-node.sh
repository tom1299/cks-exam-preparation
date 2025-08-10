#!/bin/bash
set -e
# Create etcd user and group
if ! getent group etcd > /dev/null; then
  groupadd etcd
fi
if ! id etcd > /dev/null; then
  useradd -r -g etcd -s /sbin/nologin etcd
fi
# Change ownership of etcd data directory
chown -R etcd:etcd /var/lib/etcd

# Create audit log directory
mkdir -p /var/log/kubernetes/audit
