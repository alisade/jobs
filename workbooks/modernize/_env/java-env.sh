# Source me: puts JDK 21 and Maven on PATH (Homebrew openjdk@21 by default; override JAVA_HOME).
# Returns non-zero with a message when the toolchain is missing.
if [ -z "${JAVA_HOME:-}" ] || [ ! -x "${JAVA_HOME}/bin/java" ]; then
  for c in /opt/homebrew/opt/openjdk@21 /usr/local/opt/openjdk@21 /usr/lib/jvm/java-21-openjdk-amd64 /usr/lib/jvm/java-21-openjdk; do
    if [ -x "${c}/bin/java" ]; then JAVA_HOME="${c}"; break; fi
  done
fi
if [ -z "${JAVA_HOME:-}" ] || [ ! -x "${JAVA_HOME}/bin/java" ]; then
  echo "java-env: JDK 21 not found -> brew install openjdk@21 (or set JAVA_HOME)" >&2
  return 2 2>/dev/null || exit 2
fi
export JAVA_HOME
export PATH="${JAVA_HOME}/bin:${PATH}"
if ! command -v mvn >/dev/null 2>&1; then
  echo "java-env: Maven not found -> brew install maven" >&2
  return 2 2>/dev/null || exit 2
fi
