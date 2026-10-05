"""Rescore an unchanged native geometry on/off pair without simulating."""
import argparse
import json
from pathlib import Path

import numpy as np

from dexlab.contact_archive import read_contacts
from dexlab.contact_indent_run import verify
from dexlab.contact_transfer import native_box_observation_matches


def report(root):
    receipts = {name: json.loads((root/name/'run.json').read_text()) for name in ('off','on')}
    outcomes = {name: verify(root/name) for name in receipts}
    with np.load(root/'off/states.npz', allow_pickle=False) as off, np.load(root/'on/states.npz', allow_pickle=False) as on:
        complete = set(off.files) == set(on.files)
        arrays = {key: key in on.files and bool(np.array_equal(off[key],on[key])) for key in off.files}
    contacts = read_contacts(root/'off',receipts['off']) == read_contacts(root/'on',receipts['on'])
    geometry = native_box_observation_matches(receipts['on'].get('native',{}).get('native_geometry',{}),receipts['on']['case']['half_size'])
    config = all(receipts['off'].get(key) == receipts['on'].get(key) for key in ('case','engine','normal_parameters','limits','source_sha256'))
    config = config and receipts['off'].get('record_native_geometry') is False and receipts['on'].get('record_native_geometry') is True
    required = ('artifact_hashes_match','native_run_completed','clean_shutdown','source_unchanged','archived_source_hashes_match')
    integrity = all(all(outcome['checks'].get(key) is True for key in required) for outcome in outcomes.values())
    result = {'state_arrays_equal':arrays,'complete_arrays':complete,'contacts_equal':contacts,
              'same_configuration_except_queries':config,'geometry_matches':geometry,
              'archive_integrity':integrity,'original_engineering_passed':{name:r['passed'] for name,r in outcomes.items()},
              'original_failures':{name:[key for key,value in r['checks'].items() if not value] for name,r in outcomes.items()}}
    result['observation_noninterference_passed']=all((complete,all(arrays.values()),contacts,config,geometry,integrity))
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    args=parser.parse_args()
    print(json.dumps(report(args.directory),indent=2))
