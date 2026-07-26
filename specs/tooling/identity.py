"""Validation and computation for the GVE unified identity framework."""
from __future__ import annotations
import hashlib, json, re
from collections.abc import Sequence
from typing import Any, Mapping

class IdentityFrameworkError(ValueError): pass

def _fail(message:str)->None: raise IdentityFrameworkError(message)

def _unique_ids(records,label):
    ids=set()
    for record in records:
        identity=record.get('id')
        if not isinstance(identity,str) or not identity: _fail(f"{label} requires a non-empty id")
        if identity in ids: _fail(f"duplicate {label} id {identity}")
        ids.add(identity)
    return ids

_REQUIRED_FAMILIES={'gve-spec-document','gve-spec-revision','gve-governance-composition','gve-effect','gve-plan','gve-contract','gve-production','gve-evidence','gve-execution-record','gve-authoritative-result','gve-finalization'}
_REQUIRED_FAIL_CLOSED={'missing-family','unknown-family','missing-domain-prefix','cross-domain-substitution','missing-canonicalization-version','unsupported-canonicalization-version','missing-digest-algorithm','unsupported-digest-algorithm','ambiguous-reference-semantics','implicit-embedded-identity-handling','incomplete-aggregate-membership','self-referential-identity','circular-aggregate-identity','mismatched-identity-family','unverifiable-identity'}
_REQUIRED_INVARIANTS={'one_semantic_domain_per_family','one_canonical_preimage_per_family','one_domain_prefix_per_family','domain_prefixes_unique','canonicalization_version_explicit','digest_algorithm_explicit','future_families_must_derive_from_framework','cross_domain_substitution_prohibited','circular_construction_prohibited'}

def validate_identity_framework(framework):
    authority=framework['authority']
    if authority['governing_specification']!='GVE-LEVEL-2-DOCUMENT-AUTHORITY': _fail('identity framework has incorrect governing specification')
    if authority['status']!='normative-framework-core': _fail('identity framework status is not normative-framework-core')
    rep=framework['representation']
    if rep['syntax']!='<family>-<algorithm>:<digest>': _fail('identity representation syntax is not canonical')
    try: pat=re.compile(rep['family_pattern'])
    except re.error as exc: _fail(f'identity family pattern is invalid: {exc}')
    for valid in ('gve-effect','gve-spec-document','gve-authoritative-result'):
        if pat.fullmatch(valid) is None: _fail(f'identity family pattern rejects {valid}')
    for invalid in ('sha256','GVE-effect','gve_effect'):
        if pat.fullmatch(invalid) is not None: _fail(f'identity family pattern admits {invalid}')
    cids=_unique_ids(framework['canonicalization_versions'],'canonicalization version')
    if 'gve-canonical-json-v1' not in cids: _fail('gve-canonical-json-v1 is required')
    aids=_unique_ids(framework['digest_algorithms'],'digest algorithm')
    if 'sha256' not in aids: _fail('sha256 is required')
    sha=next(x for x in framework['digest_algorithms'] if x['id']=='sha256')
    if (sha['digest_bits'],sha['encoded_length'],sha['encoding'])!=(256,64,'lowercase-hex'): _fail('sha256 declaration is inconsistent')
    pre=framework['canonical_preimage']
    if pre['construction']!='domain-prefix-bytes || canonical-value-bytes': _fail('canonical preimage construction is not explicit')
    for flag in ('canonicalization_version_required','digest_algorithm_required','family_definition_required'):
        if pre[flag] is not True: _fail(f'canonical preimage must require {flag}')
    if set(framework['fail_closed_conditions'])!=_REQUIRED_FAIL_CLOSED: _fail('fail-closed condition inventory is incomplete')
    inv=framework['framework_invariants']
    if set(inv)!=_REQUIRED_INVARIANTS: _fail('framework invariant inventory is incomplete')
    if any(v is not True for v in inv.values()): _fail('every framework invariant must be enabled')
    if framework['embedded_identity_rules']['implicit_handling_prohibited'] is not True: _fail('implicit embedded identity handling must be prohibited')
    if framework['reference_semantics']['ambiguous_reference_prohibited'] is not True: _fail('ambiguous reference semantics must be prohibited')
    kinds=framework.get('object_kinds')
    if not isinstance(kinds,Mapping) or kinds.get('permitted_kinds')!=['object','ordered-aggregate','unordered-aggregate']: _fail('v1 object kinds must exclude transitive closure')
    if kinds.get('v1_aggregate_closure_boundary')!='direct': _fail('v1 aggregate closure boundary must be direct')
    ctx=framework.get('identity_verification_context')
    if not isinstance(ctx,Mapping): _fail('identity verification context authority is required')
    expected_ctx={
        'representation':'caller-supplied sequence of identity records',
        'record_fields':['identity','family_id','accepted'],
        'identity_field':'identity',
        'family_field':'family_id',
        'acceptance_field':'accepted',
        'accepted_value':True,
        'external_to_canonical_preimage':True,
        'missing_context_policy':'reject',
        'missing_identity_policy':'reject',
        'unknown_family_policy':'reject',
        'family_conflict_policy':'reject',
        'unaccepted_identity_policy':'reject',
        'duplicate_identity_policy':'reject',
    }
    for key,expected in expected_ctx.items():
        if ctx.get(key)!=expected: _fail(f'identity verification context has invalid {key}')
    req={'membership','ordering_significance','duplicate_policy','closure_boundary','member_reference_mode','empty_aggregate_rule','cycle_policy','membership_path','member_identity_path','member_value_path'}
    if set(framework['aggregate_semantics']['required_for_aggregate_kinds'])!=req: _fail('aggregate semantic inventory is incomplete')
    if framework['aggregate_semantics']['cycle_policy']!='reject': _fail('aggregate cycles must be rejected')
    if framework['aggregate_semantics']['incomplete_membership_policy']!='reject': _fail('incomplete aggregate membership must be rejected')
    validate_identity_family_registry(framework)

def validate_identity_family_registry(framework):
    families=framework.get('identity_families')
    if not isinstance(families,list) or not families: _fail('identity family registry is required')
    ids=_unique_ids(families,'identity family')
    if ids!=_REQUIRED_FAMILIES: _fail('identity family registry is incomplete')
    cids={x['id'] for x in framework['canonicalization_versions']}; aids={x['id'] for x in framework['digest_algorithms']}
    prefixes=set(); adjacency={}
    for family in families:
        fid=family['id']; prefix=family['domain_separation_prefix']
        if not isinstance(family['semantic_domain'],str) or not family['semantic_domain'].strip(): _fail(f'identity family {fid} requires one semantic domain')
        if prefix in prefixes: _fail(f'duplicate domain-separation prefix {prefix!r}')
        prefixes.add(prefix)
        if not prefix.endswith('\0'): _fail(f'identity family {fid} prefix must end in NUL')
        if family['canonicalization_version'] not in cids: _fail(f'identity family {fid} uses unknown canonicalization version')
        if family['digest_algorithm'] not in aids: _fail(f'identity family {fid} uses unknown digest algorithm')
        if prefix!=fid.replace('gve-','gve/',1)+'/v1\0': _fail(f'identity family {fid} prefix does not match its domain')
        p=family.get('preimage')
        if not isinstance(p,Mapping): _fail(f'identity family {fid} requires an exact machine-readable preimage')
        if p.get('value_source')!='complete-object': _fail(f'identity family {fid} has unknown value source')
        own=p.get('own_identity_paths'); refs=p.get('reference_paths')
        if not isinstance(own,list) or not own or len(set(own))!=len(own): _fail(f'identity family {fid} has unknown own-identity paths')
        if any(not isinstance(x,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*',x) for x in own): _fail(f'identity family {fid} has unknown own-identity paths')
        if not isinstance(refs,list) or len(set(refs))!=len(refs): _fail(f'identity family {fid} has ambiguous reference paths')
        if p.get('reference_encoding') not in {'by-value','by-identity','identity-plus-value'}: _fail(f'identity family {fid} has ambiguous reference semantics')
        verification=p.get('identity_verification')
        if not isinstance(verification,Mapping): _fail(f'identity family {fid} requires identity verification semantics')
        expected_verification={
            'by-value':('not-applicable',False,'none','not-applicable'),
            'by-identity':('verified-identity-set',True,'caller-supplied','external-to-canonical-preimage'),
            'identity-plus-value':('embedded-value-recomputation',True,'embedded-value','not-applicable'),
        }[p['reference_encoding']]
        actual_verification=(verification.get('mode'),verification.get('required'),verification.get('context_source'),verification.get('context_binding'))
        if actual_verification!=expected_verification: _fail(f'identity family {fid} has inconsistent identity verification semantics')
        vb=p.get('version_bindings')
        if not isinstance(vb,Mapping) or set(vb)!={'canonicalization','governing_specification_revision'}: _fail(f'identity family {fid} has incomplete version bindings')
        canonical_binding=vb.get('canonicalization')
        revision_binding=vb.get('governing_specification_revision')
        if not isinstance(canonical_binding,Mapping) or set(canonical_binding)!={'required','source'}: _fail(f'identity family {fid} has incomplete canonicalization binding')
        if canonical_binding.get('source')!='family-definition' or not isinstance(canonical_binding.get('required'),bool): _fail(f'identity family {fid} has invalid canonicalization binding')
        if not isinstance(revision_binding,Mapping) or set(revision_binding)!={'required','source','family_id','comparison'}: _fail(f'identity family {fid} has incomplete governing revision binding')
        required_revision=revision_binding.get('required')
        if not isinstance(required_revision,bool): _fail(f'identity family {fid} has invalid governing revision binding')
        expected_revision_binding=(
            ('verification-context','gve-spec-revision','exact')
            if required_revision else
            ('not-applicable',None,'not-applicable')
        )
        actual_revision_binding=(revision_binding.get('source'),revision_binding.get('family_id'),revision_binding.get('comparison'))
        if actual_revision_binding!=expected_revision_binding: _fail(f'identity family {fid} has invalid governing revision binding')
        kind=family['object_kind']; agg=family['aggregate']
        if kind=='transitive-closure': _fail(f'identity family {fid} selects unsupported transitive closure')
        if kind=='object':
            if agg is not None: _fail(f'object identity family {fid} must not define aggregate rules')
            if p.get('aggregate_encoding') is not None: _fail(f'object identity family {fid} must not define aggregate encoding')
            adjacency[fid]=[]
        else:
            if not isinstance(agg,Mapping): _fail(f'aggregate identity family {fid} requires aggregate rules')
            if agg.get('closure_boundary')!='direct': _fail(f'identity family {fid} must use direct aggregate closure')
            if p.get('aggregate_encoding')!='member-references': _fail(f'aggregate identity family {fid} requires member-references encoding')
            aggregate_verification=agg.get('identity_verification')
            if not isinstance(aggregate_verification,Mapping): _fail(f'aggregate identity family {fid} requires identity verification semantics')
            expected_aggregate_verification={
                'by-value':('not-applicable',False,'none','not-applicable'),
                'by-identity':('verified-identity-set',True,'caller-supplied','external-to-canonical-preimage'),
                'identity-plus-value':('embedded-value-recomputation',True,'embedded-value','not-applicable'),
            }[agg['member_reference_mode']]
            actual_aggregate_verification=(aggregate_verification.get('mode'),aggregate_verification.get('required'),aggregate_verification.get('context_source'),aggregate_verification.get('context_binding'))
            if actual_aggregate_verification!=expected_aggregate_verification: _fail(f'aggregate identity family {fid} has inconsistent identity verification semantics')
            members=agg['member_family_ids']
            if not members: _fail(f'aggregate identity family {fid} requires members')
            for mid in members:
                if mid not in ids: _fail(f'aggregate identity family {fid} references unknown member')
                if mid==fid: _fail(f'identity family {fid} is self-referential')
            adjacency[fid]=list(members)
    visiting=set(); visited=set()
    def visit(fid):
        if fid in visiting: _fail('identity family registry contains a circular aggregate')
        if fid in visited: return
        visiting.add(fid)
        for mid in adjacency.get(fid,[]): visit(mid)
        visiting.remove(fid); visited.add(fid)
    for fid in ids: visit(fid)

def validate_identity_context(framework,identity_context):
    """Return a fail-closed identity-to-family map for authoritative records."""
    families=framework.get('identity_families')
    if not isinstance(families,list):
        _fail('identity family registry is required')
    known={family.get('id') for family in families if isinstance(family,Mapping)}
    if identity_context is None:
        _fail('identity verification context is required')
    if not isinstance(identity_context,Sequence) or isinstance(identity_context,(str,bytes,bytearray)):
        _fail('identity verification context must be a sequence of records')
    verified={}
    for index,record in enumerate(identity_context):
        if not isinstance(record,Mapping):
            _fail(f'identity verification context record {index} is malformed')
        if set(record)!={'identity','family_id','accepted'}:
            _fail(f'identity verification context record {index} is malformed')
        identity=record['identity']; family_id=record['family_id']; accepted=record['accepted']
        parsed_family=_identity_family(identity)
        if family_id not in known:
            _fail('identity verification context contains unknown family')
        if parsed_family!=family_id:
            _fail('identity verification context family conflicts with identity')
        if accepted is not True:
            _fail('identity verification context contains unaccepted identity')
        if identity in verified:
            _fail('identity verification context contains duplicate identity')
        verified[identity]=family_id
    return verified

def _require_verified_identity(framework,identity,expected_family,identity_context):
    verified=validate_identity_context(framework,identity_context)
    actual=verified.get(identity)
    if actual is None:
        _fail('identity is absent from authoritative verification context')
    if actual!=expected_family:
        _fail('identity verification context family does not match')
    return identity

def canonical_json_bytes(value):
    def norm(item):
        if item is None or isinstance(item,bool): return item
        if isinstance(item,int) and not isinstance(item,bool):
            if item<-(2**63) or item>2**63-1: _fail('integer is outside the signed 64-bit canonical range')
            return item
        if isinstance(item,float): _fail('floating-point values are not canonicalizable')
        if isinstance(item,str):
            if any(0xD800<=ord(c)<=0xDFFF for c in item): _fail('surrogate code points are not canonicalizable')
            return item
        if isinstance(item,list): return [norm(x) for x in item]
        if isinstance(item,Mapping):
            out={}
            for k,v in item.items():
                if not isinstance(k,str): _fail('non-string object member names are not canonicalizable')
                out[k]=norm(v)
            return out
        _fail(f'value of type {type(item).__name__} is not canonicalizable')
    return json.dumps(norm(value),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf-8')

def _family_map(framework):
    validate_identity_framework(framework)
    return {f['id']:f for f in framework['identity_families']}

def _delete_path(value,path):
    if not isinstance(value,Mapping): return value
    result=dict(value); parts=path.split('.'); cursor=result
    for part in parts[:-1]:
        if part not in cursor: return result
        child=cursor[part]
        if not isinstance(child,Mapping): _fail(f'own-identity path {path} traverses a non-object')
        child=dict(child); cursor[part]=child; cursor=child
    cursor.pop(parts[-1],None); return result

def _identity_family(identity):
    if not isinstance(identity,str) or '-sha256:' not in identity: _fail('reference identity is missing or malformed')
    family,digest=identity.rsplit('-sha256:',1)
    if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest): _fail('reference identity is missing or malformed')
    return family

def _assert_acyclic(value,stack=()):
    if not isinstance(value,(Mapping,list)): return
    marker=id(value)
    if marker in stack: _fail('circular object identity construction')
    next_stack=stack+(marker,)
    members=value.values() if isinstance(value,Mapping) else value
    for member in members: _assert_acyclic(member,next_stack)

def _enter_construction(value,stack):
    if not isinstance(value,(Mapping,list)): return stack
    marker=id(value)
    if marker in stack: _fail('circular object identity construction')
    return stack+(marker,)

def _encode_references(framework,family,value,stack,claimed_identity=None,identity_context=None):
    pre=family['preimage']; paths=pre['reference_paths']; mode=pre['reference_encoding']; allowed=set(pre['allowed_reference_family_ids'])
    prepared=value
    encoded={}
    for path in paths:
        if '.' in path: _fail('reference paths deeper than one member are not supported')
        if not isinstance(prepared,Mapping) or path not in prepared: continue
        raw=prepared[path]
        if not isinstance(raw,list): _fail('reference representation must be a list')
        out=[]
        for ref in raw:
            if not isinstance(ref,Mapping): _fail('reference representation is missing or ambiguous')
            if mode=='by-value':
                if set(ref)!={'value'}: _fail('by-value reference representation is missing or ambiguous')
                _enter_construction(ref['value'],stack)
                out.append({'value':ref['value']})
            elif mode=='by-identity':
                if set(ref)!={'identity'}: _fail('by-identity reference representation is missing or ambiguous')
                ident=ref['identity']; rf=_identity_family(ident)
                if claimed_identity is not None and ident==claimed_identity: _fail('self-referential identity')
                if allowed and rf not in allowed: _fail('reference identity family does not match')
                _require_verified_identity(framework,ident,rf,identity_context)
                out.append({'identity':ident})
            else:
                if set(ref)!={'identity','value'}: _fail('identity-plus-value reference representation is missing or ambiguous')
                ident=ref['identity']; rf=_identity_family(ident)
                if claimed_identity is not None and ident==claimed_identity: _fail('self-referential identity')
                if allowed and rf not in allowed: _fail('reference identity family does not match')
                verify_identity(framework,rf,ident,ref['value'],identity_context=identity_context,_construction_stack=stack)
                out.append({'identity':ident,'value':ref['value']})
        encoded[path]=out
        prepared=dict(prepared); prepared.pop(path,None)
    return prepared,encoded

def _path_value(value,path,label):
    cursor=value
    for part in path.split('.'):
        if not isinstance(cursor,Mapping) or part not in cursor:
            _fail(f'{label} path {path} is missing')
        cursor=cursor[part]
    return cursor

def _replace_path(value,path,replacement):
    if not isinstance(value,Mapping): _fail(f'aggregate membership path {path} traverses a non-object')
    result=dict(value); parts=path.split('.'); cursor=result
    for part in parts[:-1]:
        if part not in cursor or not isinstance(cursor[part],Mapping):
            _fail(f'aggregate membership path {path} is missing')
        child=dict(cursor[part]); cursor[part]=child; cursor=child
    cursor[parts[-1]]=replacement
    return result

def _direct_aggregate_members(framework,family,value,stack,identity_context=None):
    agg=family['aggregate']
    raw=_path_value(value,agg['membership_path'],'aggregate membership')
    if not isinstance(raw,list): _fail('aggregate membership must be a list')
    allowed=set(agg['member_family_ids']); mode=agg['member_reference_mode']
    encoded=[]; identities=[]
    for index,member in enumerate(raw):
        if not isinstance(member,Mapping): _fail(f'aggregate member {index} is malformed')
        if mode=='by-value':
            if agg['member_value_path'] is None or agg['member_identity_path'] is not None:
                _fail('by-value aggregate declaration is malformed')
            value_part=_path_value(member,agg['member_value_path'],f'aggregate member {index}')
            _enter_construction(value_part,stack)
            encoded.append({'value':value_part})
            continue
        if agg['member_identity_path'] is None:
            _fail('aggregate member identity path is missing')
        identity=_path_value(member,agg['member_identity_path'],f'aggregate member {index}')
        member_family=_identity_family(identity)
        if member_family not in allowed: _fail('aggregate member identity family does not match')
        if member_family not in _family_map(framework): _fail('aggregate member identity family is unknown')
        identities.append(identity)
        if mode=='by-identity':
            _require_verified_identity(framework,identity,member_family,identity_context)
            encoded.append({'identity':identity})
        else:
            if agg['member_value_path'] is None:
                _fail('identity-plus-value aggregate member value path is missing')
            value_part=_path_value(member,agg['member_value_path'],f'aggregate member {index}')
            verify_identity(framework,member_family,identity,value_part,identity_context=identity_context,_construction_stack=stack)
            encoded.append({'identity':identity,'value':value_part})
    return raw,encoded,identities

def _aggregate_members(framework,family,value,member_identities,stack,identity_context=None):
    agg=family['aggregate']
    if member_identities is None: _fail('aggregate identity requires complete member identities')
    supplied=list(member_identities)
    if len(supplied)!=len(set(supplied)) and agg['duplicate_policy']=='reject':
        _fail('aggregate identity contains duplicate members')
    if agg['closure_boundary']!='direct': _fail('v1 aggregate closure boundary must be direct')
    raw,encoded,identities=_direct_aggregate_members(framework,family,value,stack,identity_context)
    raw_count=len(raw)
    mode=agg['member_reference_mode']
    if mode=='by-value':
        if supplied: _fail('by-value aggregate does not accept member identities')
    else:
        if sorted(supplied)!=sorted(identities):
            _fail('aggregate membership is incomplete or inconsistent')
        if agg['ordering_significance']=='ordered' and supplied!=identities:
            by_identity={item['identity']:item for item in encoded}
            encoded=[by_identity[identity] for identity in supplied]
    if raw_count==0 and agg['empty_aggregate_rule']=='reject': _fail('aggregate identity rejects empty membership')
    duplicate_basis=identities if mode!='by-value' else [canonical_json_bytes(x).hex() for x in encoded]
    if len(duplicate_basis)!=len(set(duplicate_basis)) and agg['duplicate_policy']=='reject':
        _fail('aggregate identity contains duplicate members')
    if agg['ordering_significance']=='unordered':
        encoded.sort(key=lambda item: canonical_json_bytes(item))
    return encoded

def _canonical_family_value(framework,family,value,member_identities=None,version_bindings=None,construction_stack=(),claimed_identity=None,identity_context=None,governing_specification_revision=None):
    _assert_acyclic(value,construction_stack)
    stack=_enter_construction(value,construction_stack)
    prepared=value
    for path in family['preimage']['own_identity_paths']: prepared=_delete_path(prepared,path)
    prepared,refs=_encode_references(framework,family,prepared,stack,claimed_identity,identity_context)
    vb=family['preimage']['version_bindings']; supplied=dict(version_bindings or {})
    if 'canonicalization' in supplied and supplied['canonicalization']!=family['canonicalization_version']: _fail('stale canonicalization binding')
    bindings={}
    if vb['canonicalization']['required']: bindings['canonicalization']=family['canonicalization_version']
    if vb['governing_specification_revision']['required']:
        revision=supplied.get('governing_specification_revision')
        if not isinstance(revision,str):
            _fail('governing specification revision binding is required')
        try:
            revision_family=_identity_family(revision)
        except IdentityFrameworkError:
            _fail('stale governing specification revision binding')
        if revision_family!='gve-spec-revision':
            _fail('governing specification revision binding has wrong identity family')
        if governing_specification_revision is None:
            _fail('authoritative governing specification revision is required')
        authoritative_family=_identity_family(governing_specification_revision)
        if authoritative_family!='gve-spec-revision':
            _fail('authoritative governing specification revision has wrong identity family')
        if revision!=governing_specification_revision:
            _fail('stale governing specification revision binding')
        _require_verified_identity(
            framework,
            governing_specification_revision,
            'gve-spec-revision',
            identity_context,
        )
        bindings['governing_specification_revision']=revision
    kind=family['object_kind']
    if kind=='object':
        if member_identities is not None: _fail('object identity does not accept aggregate member identities')
        if not refs and not bindings.get('governing_specification_revision'): return prepared
        return {'value':prepared,'references':refs,'version_bindings':bindings}
    members=_aggregate_members(framework,family,prepared,member_identities,stack,identity_context)
    agg=family['aggregate']
    if agg['member_reference_mode']=='by-identity':
        identities=[member['identity'] for member in members]
        if agg['ordering_significance']=='unordered':
            raw_members=_path_value(prepared,agg['membership_path'],'aggregate membership')
            identity_path=agg['member_identity_path']
            raw_members=sorted(raw_members,key=lambda member:canonical_json_bytes(_path_value(member,identity_path,'aggregate member')))
            prepared=_replace_path(prepared,agg['membership_path'],raw_members)
        result={'value':prepared,'member_identities':identities}
    else:
        aggregate_value=dict(prepared)
        aggregate_value.pop(agg['membership_path'],None)
        result={'value':aggregate_value,'members':members}
    if refs: result['references']=refs
    if bindings.get('governing_specification_revision'): result['version_bindings']=bindings
    return result

def compute_identity(framework,family_id,value,*,member_identities=None,version_bindings=None,identity_context=None,governing_specification_revision=None,_construction_stack=(),_claimed_identity=None):
    families=_family_map(framework); family=families.get(family_id)
    if family is None: _fail(f'unknown identity family {family_id}')
    canonical=_canonical_family_value(framework,family,value,member_identities,version_bindings,_construction_stack,_claimed_identity,identity_context,governing_specification_revision)
    algorithm=family['digest_algorithm']
    if algorithm!='sha256': _fail(f'unsupported digest algorithm {algorithm}')
    digest=hashlib.sha256(family['domain_separation_prefix'].encode()+canonical_json_bytes(canonical)).hexdigest()
    return f'{family_id}-{algorithm}:{digest}'

def verify_identity(framework,family_id,claimed_identity,value,*,member_identities=None,version_bindings=None,identity_context=None,governing_specification_revision=None,_construction_stack=()):
    family=_family_map(framework).get(family_id)
    if family is None: _fail(f'unknown identity family {family_id}')
    expected_prefix=f"{family_id}-{family['digest_algorithm']}:"
    if not isinstance(claimed_identity,str) or not claimed_identity.startswith(expected_prefix): _fail('claimed identity family does not match the required family')
    expected=compute_identity(framework,family_id,value,member_identities=member_identities,version_bindings=version_bindings,identity_context=identity_context,governing_specification_revision=governing_specification_revision,_construction_stack=_construction_stack,_claimed_identity=claimed_identity)
    if claimed_identity!=expected: _fail('claimed identity does not match its canonical preimage')

def _negative_vector_scenario(vector):
    scenario=vector.get('scenario')
    if scenario is None:
        return vector.get('value'), vector.get('member_identities')
    if scenario=='generic-self-graph-cycle':
        value={'identity':'ignored','references':[]}
        value['references'].append({'value':value})
        return value,None
    if scenario=='generic-mutual-graph-cycle':
        first={'identity':'ignored','references':[]}
        second={'identity':'ignored','references':[]}
        first['references'].append({'value':second})
        second['references'].append({'value':first})
        return first,None
    if scenario=='identity-self-reference':
        claimed=vector['claimed_identity']
        value={
            'identity':'ignored',
            'references':[{'identity':claimed}],
        }
        return value,None
    if scenario=='direct-aggregate-cycle':
        member_identity='gve-contract-sha256:'+'0'*64
        value={'identity':'ignored','composition':'cycle','members':[]}
        value['members'].append({
            'identity':member_identity,
            'value':value,
        })
        return value,[member_identity]
    _fail(f"unknown negative vector scenario {scenario}")

def validate_fixed_identity_vectors(framework,vectors):
    if vectors.get('schema_version')!=1: _fail('identity vectors schema_version must be 1')
    pos=vectors.get('positive'); neg=vectors.get('negative')
    if not isinstance(pos,list) or not pos: _fail('positive identity vectors are required')
    if not isinstance(neg,list) or not neg: _fail('negative identity vectors are required')
    families={family['id'] for family in framework['identity_families']}
    covered={vector.get('family_id') for vector in pos}
    if covered!=families:
        missing=sorted(families-covered); extra=sorted(covered-families)
        _fail(f"fixed positive vector family coverage is incomplete; missing={missing}, extra={extra}")
    required_categories={'omitted-prefix','stale-version','mismatched-family','ambiguous-reference','incomplete-membership','generic-in-memory-graph-cycle','identity-self-reference','direct-aggregate-cycle'}
    categories={vector.get('category') for vector in neg}
    if not required_categories.issubset(categories):
        _fail('required negative vector category coverage is incomplete')
    seen=set()
    for vector in pos:
        if vector['id'] in seen: _fail(f"duplicate identity vector id {vector['id']}")
        seen.add(vector['id'])
        actual=compute_identity(framework,vector['family_id'],vector['value'],member_identities=vector.get('member_identities'),version_bindings=vector.get('version_bindings'),identity_context=vector.get('identity_context'),governing_specification_revision=vector.get('governing_specification_revision'))
        if actual!=vector['expected_identity']: _fail(f"fixed identity vector {vector['id']} does not match")
    for vector in neg:
        if vector['id'] in seen: _fail(f"duplicate identity vector id {vector['id']}")
        seen.add(vector['id'])
        value,members=_negative_vector_scenario(vector)
        try:
            verify_identity(framework,vector['family_id'],vector['claimed_identity'],value,member_identities=members,version_bindings=vector.get('version_bindings'),identity_context=vector.get('identity_context'),governing_specification_revision=vector.get('governing_specification_revision'))
        except IdentityFrameworkError as exc:
            if vector['expected_error'] not in str(exc): _fail(f"negative identity vector {vector['id']} failed for the wrong reason")
        else: _fail(f"negative identity vector {vector['id']} was accepted")

def render_identity_framework_markdown(framework):
    validate_identity_framework(framework)
    context=framework['identity_verification_context']
    lines=['# GVE Unified Domain-Separated Identity Framework','', '> This Markdown is a deterministic projection of `GVE-IDENTITY-FRAMEWORK.json`. The JSON is normative.','','## Authority','',f"- Governing specification: `{framework['authority']['governing_specification']}`",f"- Integration state: `{framework['authority']['integration_state']}`",'','## Representation','',f"- Syntax: `{framework['representation']['syntax']}`",f"- Digest encoding: `{framework['representation']['digest_encoding']}`",'','## Identity Verification Context','',f"- Representation: `{context['representation']}`",f"- External to canonical preimage: `{str(context['external_to_canonical_preimage']).lower()}`",f"- Missing context policy: `{context['missing_context_policy']}`",f"- Missing identity policy: `{context['missing_identity_policy']}`",f"- Family conflict policy: `{context['family_conflict_policy']}`",f"- Unaccepted identity policy: `{context['unaccepted_identity_policy']}`",f"- Duplicate identity policy: `{context['duplicate_identity_policy']}`",'','## V1 Aggregate Boundary','',f"- Permitted object kinds: `{', '.join(framework['object_kinds']['permitted_kinds'])}`",f"- Aggregate closure boundary: `{framework['object_kinds']['v1_aggregate_closure_boundary']}`","- Transitive closure: `deferred to a successor issue`",'','## Identity Families','']
    for family in framework['identity_families']:
        pre=family['preimage']
        verification=pre['identity_verification']
        revision_binding=pre['version_bindings']['governing_specification_revision']
        lines += [f"### `{family['id']}`",'',f"- Semantic domain: `{family['semantic_domain']}`",f"- Domain prefix: `{family['domain_separation_prefix'][:-1]}\\0`",f"- Canonicalization: `{family['canonicalization_version']}`",f"- Digest: `{family['digest_algorithm']}`",f"- Reference encoding: `{pre['reference_encoding']}`",f"- Identity verification: `{verification['mode']}`",f"- Verification context source: `{verification['context_source']}`",f"- Governing revision required: `{str(revision_binding['required']).lower()}`",f"- Governing revision source: `{revision_binding['source']}`",f"- Governing revision comparison: `{revision_binding['comparison']}`",f"- Own identity paths: `{', '.join(pre['own_identity_paths'])}`",f"- Reference paths: `{', '.join(pre['reference_paths']) or '(none)'}`",f"- Object kind: `{family['object_kind']}`",'']
    lines += ['## Fail-Closed Conditions','']+[f'- `{c}`' for c in framework['fail_closed_conditions']]+['','## Canonical Normative JSON','','```json',json.dumps(framework,ensure_ascii=False,sort_keys=True,indent=2),'```','']
    return '\n'.join(lines)
