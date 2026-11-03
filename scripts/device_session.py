"""Capture bounded, read-only Android diagnostics before/after a manual workload."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from editorial import atomic_json

SCENARIOS = ('idle', 'browse', 'first-discovery', 'repeat-discovery', 'narration', 'background-lock')


def capture(adb, serial):
    prefix = [adb] + (['-s', serial] if serial else [])
    commands = {
        'model': ['getprop', 'ro.product.model'], 'os': ['getprop', 'ro.build.version.release'],
        'battery': ['dumpsys', 'battery'], 'power': ['dumpsys', 'power'],
        'thermal': ['dumpsys', 'thermalservice'], 'process': ['pidof', 'org.vitadex.vitadex'],
        'package': ['dumpsys', 'package', 'org.vitadex.vitadex'],
        'display': ['settings', 'get', 'system', 'screen_brightness'],
        'battery_stats': ['dumpsys', 'batterystats', 'org.vitadex.vitadex'],
    }
    results = {}
    for name, args in commands.items():
        try:
            result = subprocess.run(prefix + ['shell'] + args, capture_output=True, text=True, timeout=15)
            results[name] = {'returncode': result.returncode, 'output': result.stdout[-100000:],
                             'error': result.stderr[-1000:]}
        except subprocess.TimeoutExpired:
            results[name] = {'returncode': None, 'error': 'Timed out after 15 seconds.'}
    return {'captured_at': datetime.now(timezone.utc).isoformat(), 'diagnostics': results}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('before', 'after'))
    parser.add_argument('--session', type=Path, required=True)
    parser.add_argument('--scenario', choices=SCENARIOS)
    parser.add_argument('--serial')
    parser.add_argument('--notes', default='')
    args = parser.parse_args()
    adb = shutil.which('adb')
    if not adb:
        parser.error('adb is not installed. Install Android platform-tools; no device evidence was collected.')
    if args.stage == 'before':
        if not args.scenario or args.session.exists():
            parser.error('Choose a scenario and a new session file.')
        data = {'version': 1, 'scenario': args.scenario, 'serial': args.serial,
                'notes': args.notes, 'result': 'unassessed',
                'conditions': {'connectivity': '', 'brightness': '', 'thermal_state': '',
                               'battery_saver': '', 'cache_state': '', 'charging_state': ''}}
    else:
        data = json.loads(args.session.read_text())
        if 'after' in data or data.get('serial') != args.serial:
            parser.error('Use the same serial and a session without an after capture.')
    data[args.stage] = capture(adb, args.serial)
    atomic_json(args.session, data)
    print(f'Saved {args.stage} diagnostics. Result remains unassessed; this is not an energy estimate.')


if __name__ == '__main__':
    main()
