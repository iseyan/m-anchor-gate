"""Stdlib environment receipt plus import/version probe. No schema checks here."""
import importlib.metadata
import json
import platform
import sys
import traceback


def block_network(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo'}:
        raise RuntimeError('environment_probe_network_disabled')


sys.addaudithook(block_network)
record = {'python_executable': sys.executable, 'python_prefix': sys.prefix,
          'python_base_prefix': sys.base_prefix, 'python_version': sys.version,
          'platform': platform.platform(), 'validator_ready': False,
          'validator_version': None, 'validator_class': None,
          'schema_checks_performed': False, 'model_api_calls': 0}
try:
    record['installed_distributions'] = sorted(
        ({'name': d.metadata['Name'], 'version': d.version} for d in importlib.metadata.distributions()),
        key=lambda row: str(row['name']).lower())
    record['validator_version'] = importlib.metadata.version('jsonschema')
    from jsonschema import Draft202012Validator
    import jsonschema
    record.update(validator_class=Draft202012Validator.__module__ + '.' + Draft202012Validator.__name__,
                  validator_module_path=jsonschema.__file__)
    record['validator_ready'] = record['validator_version'] == '4.26.0'
except Exception as error:
    record.update(error_type=type(error).__name__, error=str(error))
    traceback.print_exc(file=sys.stderr)
print(json.dumps(record, ensure_ascii=False))
sys.exit(0 if record['validator_ready'] else 2)
