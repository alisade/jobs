"""Build the incident/ evidence bundle for the failed FieldOps 1.4.0.0 UAT release (run by `make setup`)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INC = ROOT / "incident"


def w(rel: str, text: str) -> None:
    p = INC / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def missing_block() -> str:
    """The MissingDependencies payload the platform echoes back, built from the packed Solution.xml."""
    xml = (ROOT / "solutions" / "FieldOps" / "src" / "Other" / "Solution.xml").read_text()
    m = re.search(r"<MissingDependencies>.*?</MissingDependencies>", xml, re.S)
    block = m.group(0) if m else "<MissingDependencies />"
    # The service only reports dependencies it cannot resolve in the target (ContosoCore 2.0.3.0 is there).
    entries = re.findall(r"<MissingDependency>.*?</MissingDependency>", block, re.S)
    keep = [e for e in entries if "ContosoCore (2.1.0.0)" in e]
    compact = "".join(re.sub(r">\s+<", "><", e.strip()) for e in keep)
    compact = compact.replace("<MissingDependency>", '<MissingDependency canResolveMissingDependency="True">')
    return "<MissingDependencies>" + compact + "</MissingDependencies>"


def main() -> None:
    if INC.exists():
        shutil.rmtree(INC)
    INC.mkdir()
    md = missing_block()
    err = (
        "Solution manifest import: FAILURE: The following solution cannot be imported: FieldOps. "
        "Some dependencies are missing. The missing dependencies are : " + md + " , ProductUpdatesOnly : False"
    )

    w("github-actions-release-uat-run-5512.log", f"""2026-10-08T15:02:11.4120000Z ##[group]Run microsoft/powerplatform-actions/actions-install@v1
2026-10-08T15:02:19.9910000Z Installed Power Platform CLI (pac) 1.46.1
2026-10-08T15:02:20.0020000Z ##[endgroup]
2026-10-08T15:02:20.1030000Z ##[group]Solution checker (pac solution check) FieldOps_1_4_0_0_managed.zip
2026-10-08T15:03:41.5520000Z Rule meta-remove-dup-reg       : 0 issues
2026-10-08T15:03:41.5530000Z Rule web-use-client-context    : 2 issues (Medium)  contoso_/js/asset.form.js line 41, 88: Xrm.Page is deprecated, use formContext
2026-10-08T15:03:41.5540000Z Rule il-avoid-specialized-update-ops : 0 issues
2026-10-08T15:03:41.5550000Z Solution checker: 0 Critical, 0 High, 2 Medium, 0 Low. Threshold (High) not exceeded.
2026-10-08T15:03:41.5560000Z ##[endgroup]
2026-10-08T15:03:41.7010000Z ##[group]Import FieldOps 1.4.0.0 (managed) into https://contoso-fs-uat.crm.dynamics.com
2026-10-08T15:03:41.7020000Z > pac solution import --path out/FieldOps_1_4_0_0_managed.zip --activate-plugins --stage-and-upgrade --async --max-async-wait-time 60
2026-10-08T15:03:43.1180000Z Connected as svc-pp-release@contoso.onmicrosoft.com
2026-10-08T15:03:43.6020000Z Connected to... Contoso FS UAT
2026-10-08T15:03:44.0300000Z Solution Importing...
2026-10-08T15:03:44.0310000Z Solution Import Requested with Stage and Upgrade Mode...
2026-10-08T15:04:12.5520000Z Asynchronous operation 6b2e8d41-91c3-f011-bbd3-000d3a8c2f10 completed with status Failed.
2026-10-08T15:04:12.5530000Z Error: {err}
2026-10-08T15:04:12.6710000Z ##[error]Process completed with exit code 1.
2026-10-08T15:04:12.6720000Z ##[endgroup]
""")

    w("import-job-6b2e8d41.xml", f"""<!-- Solution history / import job data for contoso-fs-uat (Settings > Solution history > FieldOps). Trimmed. -->
<importexportxml start="2026-10-08T15:03:45Z" stop="2026-10-08T15:04:11Z" progress="0" processed="false">
  <solutionManifests>
    <solutionManifest languagecode="1033" id="FieldOps" LocalizedName="Field Operations" processed="false">
      <UniqueName>FieldOps</UniqueName>
      <Version>1.4.0.0</Version>
      <Managed>1</Managed>
      <Publisher>contoso</Publisher>
      <result result="failure" errortext="{err.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')}" datetime="15:04:11.20" datetimeticks="639249170512000000" />
    </solutionManifest>
  </solutionManifests>
  <upgradeSolutionPackageInformation>
    <upgradeRequired>1</upgradeRequired>
    <upgradeValid>1</upgradeValid>
    <fileVersion>9.2.25092.170</fileVersion>
    <currentVersion>9.2.25092.170</currentVersion>
  </upgradeSolutionPackageInformation>
</importexportxml>
""")

    w("maker-portal-missing-dependencies.txt", """Power Apps > Solutions > Import > FieldOps (contoso-fs-uat), 2026-10-08 15:20, retried manually by Jordan Lee

  Import failed due to missing dependencies.

  [Show dependencies]
  Managed Solutions (1)
    ContosoCore (2.1.0.0)
      Region Code (Column) on Asset   required by   Asset - Field Ops (Form)
      Region Code (Column) on Asset   required by   Assets by Region (View)
""")

    w("pac-solution-list-uat.txt", """> pac solution list --environment https://contoso-fs-uat.crm.dynamics.com
Unique Name                 Friendly Name               Version      Managed
ContosoCore                 Contoso Core                2.0.3.0      True
ContosoPortal               Contoso Customer Portal     3.2.1.0      True
FieldOps                    Field Operations            1.3.0.0      True
msdynce_AppCommon           Dynamics 365 App Common     9.0.25073.1  True
""")

    w("pac-solution-list-dev.txt", """> pac solution list --environment https://contoso-fs-dev.crm.dynamics.com
Unique Name                 Friendly Name               Version      Managed
ContosoCore                 Contoso Core                2.1.0.0      False
ContosoPortal               Contoso Customer Portal     3.2.1.0      True
FieldOps                    Field Operations            1.4.0.0      False
""")

    w("component-layers-account-main-form-uat.txt", """Solution layers: Account (table) > Forms > Account - Main, environment contoso-fs-uat

Order  Solution            Publisher   Type        Version     Modified
3      Active              Default     Unmanaged   n/a         2026-09-30 (jordan.lee@contoso.com)
2      ContosoPortal       contoso     Managed     3.2.1.0     2026-07-14
1      System              Microsoft   Managed     9.2         n/a
""")

    w("teams-thread.txt", """#fieldops-release  Thu 2026-10-08
[15:06] Release bot: release-uat run 5512 FAILED at "Import FieldOps 1.4.0.0".
[15:11] Jordan (QA): Probably that unmanaged change I made on the Account main form in UAT last week? There is an
        Active layer on top now. Can someone just remove the Active layer and rerun?
[15:14] Sam (dev): Solution checker also flagged Xrm.Page in asset.form.js, maybe that is it.
[15:18] Jordan: I retried the import from the maker portal, same error, it lists Region Code.
[15:22] Alex (lead): Can we pass --skip-dependency-check and move on? UAT sign-off is tomorrow 10:00.
[15:30] Priya (platform): Holding the release. Assigning to platform on-call.
""")

    w("README.txt", """Evidence for the failed FieldOps 1.4.0.0 release to contoso-fs-uat (generated by make setup)

github-actions-release-uat-run-5512.log   release workflow output (solution checker + pac solution import)
import-job-6b2e8d41.xml                   import job record from Solution history
maker-portal-missing-dependencies.txt     manual retry from the maker portal
pac-solution-list-uat.txt / -dev.txt      what is installed where
component-layers-account-main-form-uat.txt  solution layers of the Account main form in UAT
teams-thread.txt                          the conversation so far
""")
    print("incident bundle written to incident/")


if __name__ == "__main__":
    main()
