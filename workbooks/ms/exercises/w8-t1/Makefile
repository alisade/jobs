# ms/w8-t1 - credit ledger does not reconcile
SHELL := /bin/bash
TEST_PROJ := tests/Fabrikam.Plugins.Tests/Fabrikam.Plugins.Tests.csproj
GEN_PROJ := tools/IncidentGen/IncidentGen.csproj
export DOTNET_CLI_TELEMETRY_OPTOUT := 1
export DOTNET_NOLOGO := 1

.PHONY: setup test clean

setup:
	@command -v dotnet >/dev/null 2>&1 || { echo "dotnet SDK not found: see tools/doctor.sh ms (brew install --cask dotnet-sdk)"; exit 1; }
	dotnet restore $(TEST_PROJ)
	dotnet restore $(GEN_PROJ)
	dotnet build $(TEST_PROJ) --no-restore -v q
	dotnet run --project $(GEN_PROJ) --no-restore -- incident

test:
	dotnet test $(TEST_PROJ)

clean:
	rm -rf incident src/*/bin src/*/obj sim/*/bin sim/*/obj tools/*/bin tools/*/obj tests/*/bin tests/*/obj tests/*/TestResults
