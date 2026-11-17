# Design: ICD-10-CM code suggestion for PA intake

## Decision and summary

<!-- Which option ships first (A, B, or a combination), in three sentences, with the numbers that decided it. -->

## Cost per 1,000 notes and per month

<!-- Show the arithmetic from inputs/costs.csv for both options at 38,000 notes/month, including idle endpoint cost. -->

## Quality analysis

<!-- Read results.csv: where B wins, where it loses (rare codes, invalid codes, parse failures), and why that matters here. -->

## Architecture on Agent Platform

<!-- Serving, endpoint type (private), VPC-SC, CMEK, logging; how the PA graph calls it; a diagram. -->

## Evaluation and release gates

<!-- Held-out set, slices (rare codes, code-set update), thresholds, CI gate, shadow mode, drift monitoring. -->

## Code-set updates and retraining

<!-- October 1 updates: how each option handles new/deleted codes; validation against the code file. -->

## PHI and compliance

<!-- Training data provenance, de-identification, BAA scope, audit, minimum necessary in the prompt. -->
