# Reference: edgefde/w6-c1

The model brief is `.grading/solution/BRIEF.md`. What a strong answer has, in order of weight:

1. A problem framed as unplanned bearing failures with a cost computed from the inputs:
   3.5 failures/year x (6,200 + 9.5 x 4,800) = about USD 181k, plus about USD 6k of unneeded planned
   swaps. The "AI target" is Dana's motive, not the problem.
2. False alarms as a first-class, signed metric (Sam), measured in a shadow period before alerts go
   live. Recall measured on replayed labelled failures, lead time in days.
3. Scope cut to the 4 pumps with sensors; seals, motors, energy and the chatbot deferred with reasons;
   a better VP story built from measured numbers.
4. Architecture with raw data on the gateway, outbound only through the proxy allow-list, no PLC
   writes, change requests in week 1, model updates as a standard change with rollback.
5. A thin slice end to end in two weeks, then a weekly plan.
6. Handoff assets with named client owners, matching Ravi's "without calling you".

Common misses: accepting "all ten pumps by January"; no baseline arithmetic; false alarms not
measured; a cloud design that uploads waveforms; work orders that bypass Joe; no owner for assets.
