#!/usr/bin/env bash
# Assemble the CA bundle every client on the build box uses: the OS public roots (for pinned,
# uninspected hosts such as models.tessellate-edge.example), the corporate root, and both corporate
# issuing CAs. The inspecting proxy sends only its leaf, so "Corvane Inspection Issuing CA 2" must
# be in the bundle for any proxied destination to verify.
# Usage: CERT_DIR=/opt/corvane/certs/src OUT=/opt/corvane/certs/ca-bundle.pem build-ca-bundle.sh
set -euo pipefail
cert_dir="${CERT_DIR:-/opt/corvane/certs/src}"
out="${OUT:-/opt/corvane/certs/ca-bundle.pem}"
parts=(public-roots.pem corvane-root-g2.pem corvane-inspection-issuing-ca2.pem corvane-internal-issuing-ca1.pem)
for p in "${parts[@]}"; do
  if [ ! -s "${cert_dir}/${p}" ]; then echo "missing ${cert_dir}/${p}" >&2; exit 1; fi
done
tmp="${out}.tmp"
: > "${tmp}"
for p in "${parts[@]}"; do cat "${cert_dir}/${p}" >> "${tmp}"; echo >> "${tmp}"; done
mv "${tmp}" "${out}"
echo "wrote ${out} ($(grep -c 'BEGIN CERTIFICATE' "${out}") certificates)"
