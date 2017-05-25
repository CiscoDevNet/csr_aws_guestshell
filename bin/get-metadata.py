#!/usr/bin/env python
import json
from boto.utils import get_instance_metadata

metadata = get_instance_metadata(timeout=2, num_retries=2)
print json.dumps(metadata, sort_keys=True,indent=4)
