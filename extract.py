#!/usr/bin/env python2

import argparse
import errno
import os

import update_payload
from update_payload import applier


def list_content(payload_file_name):
    with open(payload_file_name, 'rb') as payload_file:
        payload = update_payload.Payload(payload_file)
        payload.Init()

        for part in payload.manifest.partitions:
            print("{} ({} bytes)".format(part.partition_name,
                                         part.new_partition_info.size))


def extract(payload_file_name, output_dir="output", source_dir="source", partition_names=None):
    try:
        os.makedirs(output_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

    with open(payload_file_name, 'rb') as payload_file:
        payload = update_payload.Payload(payload_file)
        payload.Init()

        helper = applier.PayloadApplier(payload)

        if payload.IsDelta():
            print("Delta payload Detected")
            if not os.path.isdir(source_dir):
                raise SystemExit("Source directory not found")

            for part in payload.manifest.partitions:
                if partition_names and part.partition_name not in partition_names:
                    continue
                source_file = os.path.join(source_dir, part.partition_name + ".img")
                if not os.path.isfile(source_file):
                    print("Source for partition " + part.partition_name + " not found, skipping...")
                    continue
                print("Patching {}".format(part.partition_name))
                output_file = os.path.join(output_dir, part.partition_name + ".img")
                helper._ApplyToPartition(
                    part.operations, part.partition_name,
                    'install_operations', output_file,
                    part.new_partition_info, source_file)
        else:
            for part in payload.manifest.partitions:
                if partition_names and part.partition_name not in partition_names:
                    continue
                print("Extracting {}".format(part.partition_name))
                output_file = os.path.join(output_dir, part.partition_name + ".img")
                helper._ApplyToPartition(
                    part.operations, part.partition_name,
                    'install_operations', output_file,
                    part.new_partition_info)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("payload", metavar="payload.bin",
                        help="Path to the payload.bin")
    parser.add_argument("--output_dir", default="output",
                        help="Output directory")
    parser.add_argument("--source_dir", default="source",
                        help="Source directory (For delta payloads)")
    parser.add_argument("--partitions", type=str, nargs='+',
                        help="Name of the partitions to extract")
    parser.add_argument("--list_partitions", action="store_true",
                        help="List the partitions included in the payload.bin")

    args = parser.parse_args()
    if args.list_partitions:
        list_content(args.payload)
    else:
        extract(args.payload, args.output_dir, args.source_dir, args.partitions)
