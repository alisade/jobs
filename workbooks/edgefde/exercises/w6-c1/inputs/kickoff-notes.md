# Kickoff call notes - Corvane Industrial, Dunmore plant (fictional)

Date: 2026-11-03, 90 minutes, on site. Notes taken by the Tessellate Edge account lead.

Attendees: Dana Whitcombe (plant manager), Ravi Okafor (reliability lead), Marta Lindqvist (OT/IT
security), Joe Pressley (maintenance planner), Sam Ferreira (senior controls engineer), Tessellate
Edge: account lead and you (forward deployed engineer).

## What people said

- **Dana (plant manager):** "We want AI on the pumps. Corporate has an AI target for every plant this
  year. I need something I can show the regional VP in Q1." Later: "What really hurts is unplanned
  downtime on the transfer pumps. When P2 seized in August we lost most of a shift."
- **Ravi (reliability):** Ten centrifugal pumps, 6205-class bearings, two lines. Maintenance is
  time-based: bearings replaced every 18 months whether they need it or not. Route-based vibration
  checks with a handheld analyser once a month by a contractor. Last 24 months: 7 unplanned bearing
  failures, average 9.5 hours of line downtime each. "Half the bearings we pull at 18 months look
  fine. The other half fail before 18 months."
- **Joe (planner):** A planned bearing swap takes 3 hours in a scheduled window and costs about
  USD 1,900 in parts and labour. An unplanned one costs about USD 6,200 in parts, overtime and
  expediting, plus the lost production (finance uses USD 4,800 per line-hour). Work orders live in
  the CMMS; "if your system raises work orders, they have to go through my queue, not straight to
  the techs."
- **Marta (security):** The pumps are on the OT network (Purdue level 1-2). Nothing from level 2 goes
  to the internet. Level 3.5 DMZ has an outbound proxy with TLS inspection for approved destinations
  only. "Raw sensor data does not leave the site. Aggregates and alerts can, if we approve the
  destination." New software on OT needs a change request two weeks ahead; changes happen in the
  monthly maintenance window (second Sunday).
- **Sam (controls):** Skeptical. "We tried a vendor's 'predictive' box in 2023. It alarmed twenty
  times a week, nobody believed it after a month, and we unplugged it. If yours cries wolf, the
  operators will mute it and so will I." Owns the PLCs and the historian. Does not want anything
  writing to the PLCs.
- **Dana again:** "Can it also predict seal failures and motor faults? And energy use?"

## Facts gathered

- Sensors: 4 pumps already have wired triaxial accelerometers from the 2023 trial (still mounted,
  disconnected). The other 6 would need sensors (about USD 400 each installed).
- An edge gateway can sit in the level 2 cabinet; it can reach the historian and the CMMS API in level 3.
- Historian has 2 years of 1-minute motor current and flow, no vibration.
- The contractor's monthly handheld readings (overall velocity mm/s) exist as PDFs for 2 years.
- Budget for a pilot was "not discussed"; the account lead says the SOW allows 8 weeks of FDE time.
