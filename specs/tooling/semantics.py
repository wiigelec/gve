"""Semantic graph and hierarchy validation for GVE level specifications."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence




class SemanticValidationError(ValueError):
    """Raised when a structurally valid level specification is inconsistent."""


def _fail(specification_id: str, message: str) -> None:
    raise SemanticValidationError(f"{specification_id}: {message}")


def _metadata(document: Mapping[str, Any]) -> dict[str, Any]:
    specification_id = document["specification"]["id"]
    metadata = document.get("document")
    if metadata is None:
        return {"role": "root", "root": specification_id, "imports": []}
    return dict(metadata)




_EFFECT_STATE_DIMENSIONS = {
    "request": {"requested", "not-requested"},
    "authorization": {"authorized", "refused", "indeterminate"},
    "execution": {
        "unattempted",
        "attempted",
        "partial",
        "completed",
        "failed",
        "cancelled",
        "timed-out",
        "indeterminate",
    },
    "observation": {"unobserved", "observed", "contradicted", "indeterminate"},
    "verification": {
        "unverified",
        "verified",
        "failed",
        "contradicted",
        "indeterminate",
    },
}

_REQUIRED_NON_IMPLICATIONS = {
    (("observation", "observed"), ("execution", "completed")),
    (("execution", "completed"), ("authorization", "authorized")),
    (("authorization", "authorized"), ("execution", "attempted")),
    (("execution", "attempted"), ("execution", "completed")),
}

_REQUIRED_ASSERTION_FIELDS = {
    "assertion_id",
    "effect_id",
    "dimension",
    "value",
    "governing_actor",
    "governing_authority",
    "admitted_evidence_ids",
    "asserted_at",
    "uncertainty",
    "supersedes_assertion_id",
    "correction_reason",
}


def _state_ref(
    specification_id: str,
    state: Mapping[str, Any],
    inventory: Mapping[str, set[str]],
    *,
    label: str,
) -> tuple[str, str]:
    dimension = state["dimension"]
    value = state["value"]
    if dimension not in inventory:
        _fail(specification_id, f"{label} references unknown dimension {dimension}")
    if value not in inventory[dimension]:
        _fail(
            specification_id,
            f"{label} references value {value} outside dimension {dimension}",
        )
    return dimension, value


def validate_effect_state_model(
    specification_id: str, model: Mapping[str, Any]
) -> None:
    """Validate the structured normative governed effect-state model."""
    if model["schema_version"] != 1:
        _fail(specification_id, "effect_state_model schema_version must be 1")
    if model["effect_identity_required"] is not True:
        _fail(specification_id, "effect_state_model must require exact effect identity")

    inventory: dict[str, set[str]] = {}
    authorities: dict[str, str] = {}
    for dimension in model["dimensions"]:
        dimension_id = dimension["id"]
        if dimension_id in inventory:
            _fail(specification_id, f"duplicate effect-state dimension {dimension_id}")
        values: set[str] = set()
        for value in dimension["values"]:
            value_id = value["id"]
            if value_id in values:
                _fail(
                    specification_id,
                    f"duplicate effect-state value {dimension_id}.{value_id}",
                )
            values.add(value_id)
            if not value["evidence_requirement"].strip():
                _fail(
                    specification_id,
                    f"effect-state value {dimension_id}.{value_id} has empty "
                    "evidence requirement",
                )
            expected_uncertainty = value_id == "indeterminate"
            if value["uncertainty_required"] is not expected_uncertainty:
                _fail(
                    specification_id,
                    f"effect-state value {dimension_id}.{value_id} has invalid "
                    "uncertainty requirement",
                )
        inventory[dimension_id] = values
        authority = dimension["assertion_authority"].strip()
        if not authority:
            _fail(specification_id, f"dimension {dimension_id} has empty authority")
        authorities[dimension_id] = authority

    if inventory != _EFFECT_STATE_DIMENSIONS:
        _fail(
            specification_id,
            "effect_state_model dimensions or permitted values do not match the "
            "normative inventory",
        )

    implications = set()
    for index, implication in enumerate(model["implications"]):
        source = _state_ref(
            specification_id, implication["source"], inventory,
            label=f"implication {index} source",
        )
        target = _state_ref(
            specification_id, implication["target"], inventory,
            label=f"implication {index} target",
        )
        implications.add((source, target))
        if implication["same_effect"] is not True:
            _fail(specification_id, "every implication must be scoped to one effect")
    required_implication = (
        ("verification", "verified"),
        ("observation", "observed"),
    )
    if implications != {required_implication}:
        _fail(
            specification_id,
            "effect_state_model must define only verified-implies-observed",
        )
    verified_implication = model["implications"][0]
    if verified_implication["same_evidence_context"] is not True:
        _fail(
            specification_id,
            "verified-implies-observed must require the same evidence context",
        )

    non_implications = set()
    for index, rule in enumerate(model["non_implications"]):
        source = _state_ref(
            specification_id, rule["source"], inventory,
            label=f"non-implication {index} source",
        )
        target = _state_ref(
            specification_id, rule["target"], inventory,
            label=f"non-implication {index} target",
        )
        non_implications.add((source, target))
    if not _REQUIRED_NON_IMPLICATIONS.issubset(non_implications):
        _fail(specification_id, "effect_state_model omits a required non-implication")

    prohibited: set[frozenset[tuple[str, str]]] = set()
    for index, combination in enumerate(model["prohibited_combinations"]):
        states = [
            _state_ref(
                specification_id, state, inventory,
                label=f"prohibited combination {index}",
            )
            for state in combination["states"]
        ]
        if len(states) != len(set(states)):
            _fail(specification_id, "prohibited combination repeats a state")
        if len({dimension for dimension, _value in states}) != len(states):
            _fail(
                specification_id,
                "prohibited combination asserts multiple values in one dimension",
            )
        if not combination["reason"].strip():
            _fail(specification_id, "prohibited combination has empty reason")
        prohibited.add(frozenset(states))
    for observation_value in ("unobserved", "contradicted", "indeterminate"):
        required = frozenset(
            {
                ("verification", "verified"),
                ("observation", observation_value),
            }
        )
        if required not in prohibited:
            _fail(
                specification_id,
                f"missing prohibited verified plus {observation_value} combination",
            )

    assertion_record = model["assertion_record"]
    if set(assertion_record["required_fields"]) != _REQUIRED_ASSERTION_FIELDS:
        _fail(specification_id, "assertion_record required_fields are incomplete")
    for flag in (
        "one_current_head_per_effect_dimension",
        "immutable_history",
        "verification_claim_identity_required",
        "verification_evidence_identity_required",
    ):
        if assertion_record[flag] is not True:
            _fail(specification_id, f"assertion_record must enable {flag}")

    lineage = model["lineage"]
    if set(lineage["statuses"]) != {"current", "superseded"}:
        _fail(specification_id, "lineage statuses must be current and superseded")
    if lineage["correction_disposition"] != "corrected":
        _fail(specification_id, "lineage correction disposition must be corrected")
    for flag in (
        "supersession_same_effect_required",
        "supersession_same_dimension_required",
        "correction_reason_required",
        "new_evidence_basis_required",
    ):
        if lineage[flag] is not True:
            _fail(specification_id, f"lineage must enable {flag}")

    for flag in (
        "admitted_evidence_bound",
        "preserve_adverse_facts",
        "conflict_or_incompleteness_fails_closed",
    ):
        if model["result_constraints"][flag] is not True:
            _fail(specification_id, f"result_constraints must enable {flag}")


def validate_effect_state_record(
    model: Mapping[str, Any], record: Mapping[str, Any]
) -> None:
    """Validate one explicit effect-state assertion record fail closed."""
    specification_id = "GVE-EFFECT-STATE-RECORD"
    dimensions = {dimension["id"]: dimension for dimension in model["dimensions"]}
    assertions = record.get("assertions")
    if not isinstance(assertions, list) or not assertions:
        _fail(specification_id, "record must contain at least one assertion")

    by_id: dict[str, Mapping[str, Any]] = {}
    current_heads: set[tuple[str, str]] = set()
    current_states: dict[str, dict[str, str]] = defaultdict(dict)
    for assertion in assertions:
        missing = sorted(_REQUIRED_ASSERTION_FIELDS - set(assertion))
        if missing:
            _fail(specification_id, f"assertion omits required fields {missing}")
        assertion_id = assertion["assertion_id"]
        if assertion_id in by_id:
            _fail(specification_id, f"duplicate assertion id {assertion_id}")
        by_id[assertion_id] = assertion
        effect_id = assertion["effect_id"]
        if not isinstance(effect_id, str) or not effect_id:
            _fail(specification_id, "assertion has invalid effect identity")
        dimension_id = assertion["dimension"]
        if dimension_id not in dimensions:
            _fail(specification_id, f"assertion uses unknown dimension {dimension_id}")
        dimension = dimensions[dimension_id]
        values = {value["id"]: value for value in dimension["values"]}
        value_id = assertion["value"]
        if value_id not in values:
            _fail(
                specification_id,
                f"assertion uses value {value_id} outside dimension {dimension_id}",
            )
        if assertion["governing_authority"] != dimension["assertion_authority"]:
            _fail(
                specification_id,
                f"assertion authority conflicts for dimension {dimension_id}",
            )
        evidence = assertion["admitted_evidence_ids"]
        if not isinstance(evidence, list) or not evidence or len(evidence) != len(set(evidence)):
            _fail(specification_id, "assertion requires distinct admitted evidence")
        uncertainty = assertion["uncertainty"]
        if values[value_id]["uncertainty_required"]:
            if not isinstance(uncertainty, str) or not uncertainty.strip():
                _fail(specification_id, "indeterminate assertion requires uncertainty")
        elif uncertainty is not None:
            _fail(specification_id, "determinate assertion must not claim uncertainty")
        status = assertion.get("lineage_status", "current")
        if status not in model["lineage"]["statuses"]:
            _fail(specification_id, f"invalid lineage status {status}")
        supersedes = assertion["supersedes_assertion_id"]
        correction_reason = assertion["correction_reason"]
        if supersedes is None:
            if correction_reason is not None:
                _fail(specification_id, "non-correction assertion has correction reason")
        else:
            prior = by_id.get(supersedes)
            if prior is None:
                _fail(specification_id, "correction references missing prior assertion")
            if prior["effect_id"] != effect_id or prior["dimension"] != dimension_id:
                _fail(specification_id, "correction crosses effect or dimension")
            if not isinstance(correction_reason, str) or not correction_reason.strip():
                _fail(specification_id, "correction requires a reason")
            if set(evidence) == set(prior["admitted_evidence_ids"]):
                _fail(specification_id, "correction requires a new evidence basis")
        if dimension_id == "verification" and value_id == "verified":
            claim_id = assertion.get("verified_claim_id")
            verification_evidence = assertion.get("verification_evidence_ids")
            if not isinstance(claim_id, str) or not claim_id:
                _fail(specification_id, "verified assertion requires claim identity")
            if not isinstance(verification_evidence, list) or not verification_evidence:
                _fail(specification_id, "verified assertion requires evidence identity")
            if not set(verification_evidence).issubset(set(evidence)):
                _fail(
                    specification_id,
                    "verification evidence must be admitted by the assertion",
                )
        if status == "current":
            head = (effect_id, dimension_id)
            if head in current_heads:
                _fail(specification_id, "multiple current heads for effect dimension")
            current_heads.add(head)
            current_states[effect_id][dimension_id] = value_id

    prohibited = [
        {(state["dimension"], state["value"]) for state in combination["states"]}
        for combination in model["prohibited_combinations"]
    ]
    for effect_id, states in current_states.items():
        realized = set(states.items())
        for combination in prohibited:
            if combination.issubset(realized):
                _fail(
                    specification_id,
                    f"effect {effect_id} contains a prohibited state combination",
                )
        if states.get("verification") == "verified" and states.get("observation") != "observed":
            _fail(
                specification_id,
                f"effect {effect_id} violates verified-implies-observed",
            )


def _identifier_inventory(
    document: Mapping[str, Any],
) -> tuple[set[str], set[str], set[str]]:
    specification_id = document["specification"]["id"]
    classes = {
        "definition": [item["id"] for item in document["definitions"]],
        "requirement": [item["id"] for item in document["requirements"]],
        "relationship": [item["id"] for item in document["relationships"]],
    }
    owners: dict[str, str] = {}
    for class_name, identifiers in classes.items():
        seen: set[str] = set()
        for identifier in identifiers:
            if identifier in seen:
                _fail(
                    specification_id,
                    f"duplicate {class_name} identifier {identifier}",
                )
            seen.add(identifier)
            prior = owners.get(identifier)
            if prior is not None:
                _fail(
                    specification_id,
                    f"ambiguous identifier {identifier} occurs as both "
                    f"{prior} and {class_name}",
                )
            owners[identifier] = class_name
    return set(classes["definition"]), set(classes["requirement"]), set(
        classes["relationship"]
    )


def validate_semantics(
    document: Mapping[str, Any],
    path: Path,
    *,
    levels_root: Path | None = None,
) -> None:
    """Validate one document's identity, governed path, and local identifiers."""
    specification = document["specification"]
    specification_id = specification["id"]
    level = specification["level"]
    prefix = f"GVE-LEVEL-{level}"
    if specification_id != prefix and not specification_id.startswith(prefix + "-"):
        _fail(
            specification_id,
            f"specification id does not match numeric level {level}; "
            f"expected {prefix} or {prefix}-<DOCUMENT>",
        )
    expected_name = f"{specification_id}.json"
    if path.name != expected_name:
        _fail(
            specification_id,
            f"filename {path.name!r} does not match specification identity; "
            f"expected {expected_name}",
        )
    root = (
        Path(__file__).resolve().parents[1] / "levels"
        if levels_root is None
        else levels_root
    )
    expected_path = root / f"level-{level}" / expected_name
    if path.resolve() != expected_path.resolve():
        _fail(
            specification_id,
            f"path {path} does not match authoritative path {expected_path}",
        )
    if "effect_state_model" in document:
        validate_effect_state_model(specification_id, document["effect_state_model"])
    _identifier_inventory(document)


def _visit_graph(
    graph: Mapping[str, Sequence[str]],
    *,
    label: str,
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            _fail(identifier, f"{label} cycle includes {identifier}")
        visiting.add(identifier)
        for target in graph.get(identifier, ()):
            visit(target)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(graph):
        visit(identifier)


def validate_hierarchy(
    specifications: Sequence[tuple[Path, Mapping[str, Any]]],
    *,
    levels_root: Path,
) -> None:
    """Validate document sets, inheritance, imports, and semantic resolution."""
    by_id: dict[str, tuple[Path, Mapping[str, Any]]] = {}
    by_level: dict[int, list[str]] = defaultdict(list)
    metadata: dict[str, dict[str, Any]] = {}
    inventories: dict[str, tuple[set[str], set[str], set[str]]] = {}

    for path, document in specifications:
        validate_semantics(document, path, levels_root=levels_root)
        specification_id = document["specification"]["id"]
        if specification_id in by_id:
            _fail(
                specification_id,
                f"duplicate specification identifier {specification_id}",
            )
        by_id[specification_id] = (path, document)
        by_level[document["specification"]["level"]].append(specification_id)
        metadata[specification_id] = _metadata(document)
        inventories[specification_id] = _identifier_inventory(document)

    roots_by_level: dict[int, str] = {}
    exact_membership_levels: set[int] = set()
    for level, identifiers in sorted(by_level.items()):
        roots = [
            identifier
            for identifier in identifiers
            if metadata[identifier]["role"] == "root"
        ]
        if len(roots) != 1:
            _fail(
                f"GVE-LEVEL-{level}",
                f"level {level} must contain exactly one root document; "
                f"found {len(roots)}",
            )
        root_id = roots[0]
        roots_by_level[level] = root_id
        if root_id != f"GVE-LEVEL-{level}":
            _fail(
                root_id,
                f"root document identity must be GVE-LEVEL-{level}",
            )
        if metadata[root_id]["root"] != root_id:
            _fail(root_id, f"root document must name itself as set root {root_id}")
        if metadata[root_id]["imports"]:
            _fail(root_id, "root document must not import subordinate documents")

        declared_members = metadata[root_id].get("members")
        if len(identifiers) > 1 and declared_members is None:
            _fail(
                root_id,
                "decomposed specification-set root must declare document.members",
            )
        if declared_members is not None:
            for identifier in declared_members:
                if identifier not in by_id:
                    _fail(
                        root_id,
                        f"unresolved specification-set member {identifier}",
                    )
                declared_role = metadata[identifier]["role"]
                if declared_role == "root" and identifier != root_id:
                    _fail(
                        root_id,
                        f"declared specification-set member {identifier} "
                        "is another specification-set root",
                    )
            expected_members = set(declared_members)
            discovered_members = set(identifiers)
            if discovered_members != expected_members:
                missing = sorted(expected_members - discovered_members)
                unexpected = sorted(discovered_members - expected_members)
                _fail(
                    root_id,
                    f"specification-set membership mismatch; missing={missing}, "
                    f"unexpected={unexpected}",
                )
            exact_membership_levels.add(level)
            for identifier in sorted(expected_members):
                status = by_id[identifier][1]["specification"]["status"]
                if status != "normative":
                    _fail(
                        identifier,
                        "accepted specification-set member must have normative "
                        f"status; found {status}",
                    )

        for identifier in identifiers:
            item = metadata[identifier]
            if item["root"] != root_id:
                _fail(
                    identifier,
                    f"unresolved specification-set root {item['root']}; "
                    f"expected {root_id}",
                )
            if identifier != root_id and item["role"] != "subordinate":
                _fail(identifier, "non-root document must have subordinate role")
            if identifier != root_id and "members" in item:
                _fail(identifier, "subordinate document must not declare members")

    inheritance: dict[str, list[str]] = {}
    imports: dict[str, list[str]] = {}
    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        level = specification["level"]
        parent = specification["parent"]
        role = metadata[specification_id]["role"]

        if level == 0:
            if parent is not None:
                _fail(specification_id, f"Level 0 must not declare parent {parent}")
        elif parent is None:
            _fail(specification_id, "nonzero level has unresolved parent None")
        elif parent == specification_id:
            _fail(specification_id, f"self-parenting is invalid: {parent}")
        elif parent not in by_id:
            _fail(specification_id, f"unresolved parent specification {parent}")
        else:
            parent_level = by_id[parent][1]["specification"]["level"]
            if role == "subordinate":
                expected_parent = roots_by_level[level]
                if parent != expected_parent:
                    _fail(
                        specification_id,
                        f"subordinate parent must be specification-set root "
                        f"{expected_parent}; found {parent}",
                    )
            elif level in exact_membership_levels:
                expected_parent = roots_by_level.get(level - 1)
                if parent != expected_parent:
                    _fail(
                        specification_id,
                        "root parent must be immediate prior-level root "
                        f"{expected_parent}; found {parent}",
                    )
        inheritance[specification_id] = [] if parent is None else [parent]

        targets = list(metadata[specification_id]["imports"])
        imports[specification_id] = targets
        for target in targets:
            if target == specification_id:
                _fail(specification_id, f"self import is invalid: {target}")
            if target not in by_id:
                _fail(specification_id, f"unresolved import target {target}")
            target_level = by_id[target][1]["specification"]["level"]
            if target_level != level:
                _fail(
                    specification_id,
                    f"import target {target} is outside level {level}",
                )

    _visit_graph(inheritance, label="inheritance")
    _visit_graph(imports, label="import")

    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        parent = specification["parent"]
        if parent is None or metadata[specification_id]["role"] == "subordinate":
            continue
        parent_level = by_id[parent][1]["specification"]["level"]
        if parent_level >= specification["level"]:
            _fail(
                specification_id,
                f"invalid parent level ordering: parent {parent} is level "
                f"{parent_level}, child is level {specification['level']}",
            )

    global_owner: dict[str, tuple[str, str]] = {}
    for specification_id in sorted(by_id):
        definitions, requirements, relationships = inventories[specification_id]
        for class_name, identifiers in (
            ("definition", definitions),
            ("requirement", requirements),
            ("relationship", relationships),
        ):
            for identifier in sorted(identifiers):
                prior = global_owner.get(identifier)
                if prior is not None:
                    _fail(
                        specification_id,
                        f"cross-document identifier conflict {identifier}: "
                        f"{prior[0]} declares {prior[1]}, "
                        f"{specification_id} declares {class_name}",
                    )
                global_owner[identifier] = (specification_id, class_name)

    def visible_documents(specification_id: str) -> set[str]:
        visible = {specification_id}
        pending = list(imports[specification_id])
        while pending:
            target = pending.pop()
            if target in visible:
                continue
            visible.add(target)
            pending.extend(imports[target])
        return visible

    for specification_id, (_path, document) in by_id.items():
        visible = visible_documents(specification_id)
        visible_definitions: set[str] = set()
        visible_requirements: set[str] = set()
        for target in visible:
            definitions, requirements, _relationships = inventories[target]
            visible_definitions.update(definitions)
            visible_requirements.update(requirements)

        for requirement in document["requirements"]:
            for reference in requirement["references"]:
                if reference not in visible_definitions:
                    _fail(
                        specification_id,
                        f"requirement {requirement['id']} has unresolved definition "
                        f"reference {reference} in visible imports",
                    )

        permitted_endpoints = visible_definitions | visible_requirements
        for relationship in document["relationships"]:
            for field in ("source", "target"):
                endpoint = relationship[field]
                if endpoint not in permitted_endpoints:
                    _fail(
                        specification_id,
                        f"relationship {relationship['id']} has unresolved "
                        f"{field} endpoint {endpoint} in visible imports",
                    )
