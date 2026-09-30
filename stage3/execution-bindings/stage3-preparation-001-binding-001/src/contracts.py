"""Pinned contracts. Offline structural checks never authorize HTTP dispatch."""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re

BINDING = Path(__file__).resolve().parents[1]
ROOT = BINDING.parents[2]
CONDITIONS = ROOT / 'stage3/run-forms/stage3-preparation-001'
FORM_SHA256 = '96ace90ed5c1f7f781bd5a5b3c7a256b9fc26b0595b7640a311044b6333db5e3'

def now():
    return datetime.now(timezone.utc).isoformat()

def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def digest(value):
    return hashlib.sha256(value if isinstance(value, bytes) else encode(value)).hexdigest()

def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate_json_key:' + key)
        result[key] = value
    return result

def _constant(value):
    raise ValueError('non_json_number:' + value)

def decode(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')
    return json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)

def read_pinned(path, expected):
    raw = Path(path).read_bytes()
    if digest(raw) != expected:
        raise ValueError('reference_hash_mismatch:' + str(path))
    return decode(raw)

def frozen():
    form = read_pinned(CONDITIONS / 'official-run-form.json', FORM_SHA256)
    ev = form['evidence_authority']
    admissions = read_pinned(ROOT / ev['case_admission_manifest_path'], ev['case_admission_manifest_sha256'])
    plan = form['trial_plan']
    trials = read_pinned(ROOT / plan['condition_manifest_path'], plan['condition_manifest_sha256'])
    registry = read_pinned(ROOT / ev['registry_path'], ev['registry_sha256'])
    return form, admissions, trials, registry

def verify_runtime_manifest():
    path = BINDING / 'runtime-manifest.json'
    manifest = decode(path.read_bytes())
    for item in manifest['files']:
        target = (BINDING / item['path']).resolve()
        if not target.is_relative_to(BINDING) or digest(target.read_bytes()) != item['sha256']:
            raise ValueError('runtime_binding_hash_mismatch:' + item['path'])
    return digest(path.read_bytes())

def structural_check(schema, value, path='$'):
    """Fixture-only check of the keywords present in the pinned schemas.

    Not a Draft 2020-12 validator, not a replacement for jsonschema 4.26.0.
    Used only when explicitly requested for offline development checks.
    """
    if 'anyOf' in schema:
        for branch in schema['anyOf']:
            try:
                structural_check(branch, value, path)
                return
            except ValueError:
                pass
        raise ValueError('structural_anyOf:' + path)
    expected = schema.get('type')
    types = {'object': dict, 'array': list, 'string': str, 'integer': int, 'null': type(None), 'boolean': bool}
    if expected and type(value) is not types[expected]:
        raise ValueError('structural_type:' + path)
    if 'const' in schema and (value != schema['const'] or type(value) is not type(schema['const'])):
        raise ValueError('structural_const:' + path)
    if 'enum' in schema and value not in schema['enum']:
        raise ValueError('structural_enum:' + path)
    if isinstance(value, dict):
        if not set(schema.get('required', [])) <= value.keys():
            raise ValueError('structural_required:' + path)
        props = schema.get('properties', {})
        if schema.get('additionalProperties') is False and not value.keys() <= props.keys():
            raise ValueError('structural_extra_field:' + path)
        for key in value:
            if key in props:
                structural_check(props[key], value[key], path + '.' + key)
    if isinstance(value, list):
        if len(value) > schema.get('maxItems', len(value)):
            raise ValueError('structural_maxItems:' + path)
        if schema.get('uniqueItems') and len({encode(x) for x in value}) != len(value):
            raise ValueError('structural_uniqueItems:' + path)
        for i, item in enumerate(value):
            structural_check(schema.get('items', {}), item, f'{path}[{i}]')
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0) or ('pattern' in schema and not re.search(schema['pattern'], value)):
            raise ValueError('structural_string:' + path)
    if type(value) is int and value < schema.get('minimum', value):
        raise ValueError('structural_minimum:' + path)

class Contracts:
    def __init__(self, *, offline_structural=False):
        self.runtime_manifest_sha256 = verify_runtime_manifest()
        self.form, self.admissions, self.trials, self.registry = frozen()
        self.schemas = {name: read_pinned(ROOT / item['path'], item['sha256']) for name, item in self.form['schemas']['files'].items()}
        self.offline_structural = bool(offline_structural)
        self.validators = {}
        if self.offline_structural:
            self.validation_status = 'external_schema_not_performed_offline_structural_only'
        else:
            if importlib.metadata.version('jsonschema') != '4.26.0':
                raise RuntimeError('required_jsonschema_version_unavailable')
            from jsonschema import Draft202012Validator
            for name, schema in self.schemas.items():
                Draft202012Validator.check_schema(schema)
                self.validators[name] = Draft202012Validator(schema)
            self.validation_status = 'jsonschema_4.26.0_Draft202012Validator'

    def validate(self, name, value):
        if self.offline_structural:
            structural_check(self.schemas[name], value)
        else:
            errors = sorted(self.validators[name].iter_errors(value), key=lambda x: str(list(x.path)))
            if errors:
                raise ValueError('schema_invalid:' + name + ':' + str(list(errors[0].path)) + ':' + errors[0].validator)

    def case_row(self, case_id, trial_id=None):
        if trial_id:
            trial = next((x for x in self.trials['calls'] if x['trial_id'] == trial_id), None)
            if not trial or trial['case_id'] != case_id:
                raise ValueError('trial_case_mismatch')
            rows = [x for x in self.admissions['case_rows'] if x['case_id'] == case_id and x['condition_id'] == trial['condition_id']]
            if trial['condition_id'] == 'R5':
                rows = [x for x in rows if x['variant'] == trial['variant']]
        else:
            rows = [x for x in self.admissions['case_rows'] if x['case_id'] == case_id and x['condition_id'] != 'R5']
        if len(rows) != 1:
            raise ValueError('unknown_or_ambiguous_case')
        return rows[0]
