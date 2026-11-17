# modernize/w5-c1 -- PolicyPortal.Rating: .NET Framework 4.8 to .NET 10. Needs the .NET 10 SDK.
SHELL := /bin/bash
TEST_PROJ := tests/PolicyPortal.Rating.Tests/PolicyPortal.Rating.Tests.csproj
export DOTNET_CLI_TELEMETRY_OPTOUT := 1
export DOTNET_NOLOGO := 1

.PHONY: setup test clean

setup:       ## check the SDK and restore NuGet packages once (online) so grading can restore offline
	@command -v dotnet >/dev/null 2>&1 || { echo "dotnet SDK not found: see tools/doctor.sh modernize (brew install --cask dotnet-sdk)"; exit 1; }
	@dotnet --version
	@dotnet restore $(TEST_PROJ) >/dev/null
	@echo "w5-c1 ready. Start with: make test (the library will not build on this machine yet)"

test:        ## build and run the visible characterization tests
	@dotnet test $(TEST_PROJ)

clean:
	@rm -rf src/*/bin src/*/obj tests/*/bin tests/*/obj tests/*/TestResults
	@echo "w5-c1 clean (NuGet cache kept)"
