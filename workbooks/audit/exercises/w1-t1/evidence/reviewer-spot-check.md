# Senior reviewer spot check, Q3 CM-03 (2026-10-14)

I re-performed five of the 25 Q3 samples by hand before signing the workpaper.

| Sample | ControlPilot | My result | Note |
|---|---|---|---|
| S03 CHG-104903 | pass | pass | |
| S07 CHG-104907 | pass | EXCEPTION | ticket approval is about 3 hours after the prod deploy in the pipeline log |
| S11 CHG-104911 | pass | pass | |
| S18 CHG-104918 | pass | EXCEPTION | no approval on the ticket at all |
| S22 CHG-104922 | pass | pass | |

Two of five wrong, both in the "pass" direction. I am not signing until we know why.
Last quarter ControlPilot found 3 exceptions in 25; this quarter 0 in 25 is not credible.
