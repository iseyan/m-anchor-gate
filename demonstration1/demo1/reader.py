"""Fresh-process entry point: only case ID and store location are case inputs."""

import argparse
import json
from demo1 import resume


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", required=True)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()
    print(json.dumps(resume(args.store, args.case_id), ensure_ascii=True))
