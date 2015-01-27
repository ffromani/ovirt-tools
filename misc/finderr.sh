#!/bin/bash

cat /var/log/vdsm/vdsm.log |\
        grep -v disable_after_error_count |\
        grep -v abortOnError |\
        grep -v 'in bridge with' |\
        grep -v 'vmMigrationCreate' |\
        grep -v 'error_policy' |\
        grep -v 'looking for unfetched domain' |\
        grep -v 'looking for domain' |\
        grep -i error

