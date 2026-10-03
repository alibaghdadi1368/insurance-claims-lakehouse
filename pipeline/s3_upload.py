"""
Upload landing files to S3.

    python -m pipeline.s3_upload                    # everything in data/landing + postcodes
    python -m pipeline.s3_upload --date 2026-10-01  # only that day's files
    python -m pipeline.s3_upload --date latest      # the last day the generator made

The folder layout in the bucket mirrors data/landing, under a landing/ prefix:
    s3://<bucket>/landing/customers/customers_2026-10-01.csv
"""
import argparse

import boto3

from pipeline.settings import ROOT, env, last_business_day

LANDING = ROOT / "data" / "landing"
POSTCODES = ROOT / "generator" / "reference" / "postcodes.csv"


def upload(day=None):
    s3 = boto3.client("s3", region_name=env("AWS_DEFAULT_REGION"))
    bucket = env("S3_BUCKET")

    files = sorted(LANDING.rglob(f"*{day}*" if day else "*.*"))
    files = [f for f in files if f.is_file()]
    targets = [(f, f"landing/{f.relative_to(LANDING).as_posix()}") for f in files]
    if not day:
        targets.append((POSTCODES, "landing/reference/postcodes.csv"))

    for path, key in targets:
        s3.upload_file(str(path), bucket, key)
        print(f"  s3://{bucket}/{key}")
    print(f"Uploaded {len(targets)} files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="only upload files for this day (YYYY-MM-DD or 'latest')")
    day = parser.parse_args().date
    upload(last_business_day() if day == "latest" else day)