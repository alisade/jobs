#!/usr/bin/env python3
"""snapshot-janitor: delete expired EBS snapshots owned by the platform account.

Runs nightly from a Jenkins box at Northwind Freight. Being retired in favour of a
static Go binary that runs as a Kubernetes CronJob with EKS Pod Identity.
"""
import argparse
import datetime as dt
import logging
import sys

import boto3
from botocore.exceptions import ClientError

log = logging.getLogger("snapshot-janitor")


def is_retained(snap, keep_tag):
    for tag in snap.get("Tags", []):
        if tag["Key"] == keep_tag and tag["Value"].lower() == "true":
            return True
    return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--owner-id", required=True)
    p.add_argument("--retention-days", type=int, default=30)
    p.add_argument("--keep-tag", default="retain")
    p.add_argument("--max-deletes", type=int, default=200)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    ec2 = boto3.client("ec2")
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=args.retention_days)

    candidates = []
    for page in ec2.get_paginator("describe_snapshots").paginate(OwnerIds=[args.owner_id]):
        for snap in page["Snapshots"]:
            if is_retained(snap, args.keep_tag):
                log.info("skip %s: retained by tag", snap["SnapshotId"])
                continue
            if snap.get("Description", "").startswith("Created by CreateImage("):
                log.info("skip %s: backs an AMI", snap["SnapshotId"])
                continue
            if snap["StartTime"] >= cutoff:
                continue
            candidates.append(snap)

    candidates.sort(key=lambda s: s["StartTime"])  # oldest first
    deleted, failed = 0, 0
    for snap in candidates:
        if deleted >= args.max_deletes:
            log.warning("max deletes reached, leaving %s", snap["SnapshotId"])
            continue
        try:
            ec2.delete_snapshot(SnapshotId=snap["SnapshotId"], DryRun=args.dry_run)
            deleted += 1
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code == "DryRunOperation":
                deleted += 1          # would have succeeded
            elif code == "InvalidSnapshot.InUse":
                log.info("skip %s: in use", snap["SnapshotId"])
            else:
                log.error("delete %s failed: %s", snap["SnapshotId"], e)
                failed += 1
    log.info("deleted=%d failed=%d", deleted, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sys.exit(main())
