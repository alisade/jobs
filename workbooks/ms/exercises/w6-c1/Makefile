# ms/w6-c1 - Tailspin work-order plug-ins
SHELL := /bin/bash
TEST_PROJ := tests/Tailspin.Plugins.Tests/Tailspin.Plugins.Tests.csproj
export DOTNET_CLI_TELEMETRY_OPTOUT := 1
export DOTNET_NOLOGO := 1

.PHONY: setup test clean

setup:
	@command -v dotnet >/dev/null 2>&1 || { echo "dotnet SDK not found: see tools/doctor.sh ms (brew install --cask dotnet-sdk)"; exit 1; }
	dotnet restore $(TEST_PROJ)
	dotnet build $(TEST_PROJ) --no-restore -v q

test:
	dotnet test $(TEST_PROJ)

clean:
	rm -rf src/*/bin src/*/obj tests/*/bin tests/*/obj tests/*/TestResults
