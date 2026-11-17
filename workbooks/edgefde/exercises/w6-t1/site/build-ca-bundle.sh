#!/usr/bin/env bash
# Assemble the CA bundle every client on the build box uses.
# Usage: CERT_DIR=/opt/corvane/certs/src OUT=/opt/corvane/certs/ca-bundle.pem build-ca-bundle.sh
set -euo pipefail
cert_dir="${CERT_DIR:-/opt/corvane/certs/src}"
out="${OUT:-/opt/corvane/certs/ca-bundle.pem}"
cat "${cert_dir}/corvane-root-g2.pem" > "${out}"
echo "wrote ${out}"
