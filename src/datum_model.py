"""Structural layer of LB-QPS validation (D-035): field names and types only.

Controlled vocabularies, units and cross-references are checked in the semantic
layer (src/quantitative.py), because they are defined in YAML and can change
without code changes. Unknown fields are rejected (extra="forbid") so a misspelled
field name cannot silently drop information.
"""
from typing import Any, List, Optional, Union

from pydantic import BaseModel, ConfigDict, StrictBool, StrictFloat, StrictInt, StrictStr

Number = Union[StrictInt, StrictFloat]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Target(Strict):
    entity_ids: List[StrictStr]
    anatomical_scope: Optional[StrictStr] = None
    laterality: Optional[StrictStr] = None
    computational_representation: Optional[StrictStr] = None


class Uncertainty(Strict):
    type: Optional[StrictStr] = None
    value: Optional[Number] = None
    unit: Optional[StrictStr] = None
    confidence_level: Optional[Number] = None
    distribution: Optional[StrictStr] = None


class Method(Strict):
    name: Optional[StrictStr] = None
    description: Optional[StrictStr] = None
    direct_measurement: Optional[StrictBool] = None
    derived_from: List[StrictStr] = []


class CoordinateContext(Strict):
    frame_id: Optional[StrictStr] = None
    coordinate_id: Optional[StrictStr] = None
    convention_source_id: Optional[StrictStr] = None
    axis: Optional[StrictStr] = None
    reference_pose: Optional[StrictStr] = None


class SourceClaim(Strict):
    source_id: Optional[StrictStr] = None
    supports: List[StrictStr] = []
    evidence_domain: Optional[StrictStr] = None
    claim_scope: Optional[StrictStr] = None
    value_directly_reported: Optional[StrictBool] = None
    notes: Optional[StrictStr] = None


class TransformationStep(Strict):
    operation: StrictStr
    input_value: Optional[Number] = None
    input_unit: Optional[StrictStr] = None
    output_value: Optional[Number] = None
    output_unit: Optional[StrictStr] = None
    formula: Optional[StrictStr] = None


class Provenance(Strict):
    source_claims: List[SourceClaim] = []
    source_value_location: Optional[StrictStr] = None
    retrieval_date: Optional[StrictStr] = None
    transformation_history: List[TransformationStep] = []


class Applicability(Strict):
    level: Optional[StrictStr] = None
    population: Optional[StrictStr] = None
    sample_size: Optional[StrictInt] = None
    age: Optional[StrictStr] = None
    sex: Optional[StrictStr] = None
    body_mass_kg: Optional[Number] = None
    stature_m: Optional[Number] = None
    pathology_or_condition: Optional[StrictStr] = None
    inclusion_notes: Optional[StrictStr] = None
    model_id: Optional[StrictStr] = None
    subject_id: Optional[StrictStr] = None


class ValueComparison(Strict):
    """A documented difference between this datum's inputs and another value (D-027)."""
    related_observation: Optional[StrictStr] = None
    this_value: StrictStr
    other_value: StrictStr
    relationship: StrictStr
    comparability: StrictStr
    selection_rationale: StrictStr
    downstream_effect: StrictStr
    decision: Optional[StrictStr] = None


class Quality(Strict):
    validation_status: Optional[StrictStr] = None
    limitations: List[StrictStr] = []
    conflicts_with: List[StrictStr] = []
    value_comparisons: List[ValueComparison] = []
    reviewer_notes: Optional[StrictStr] = None


class SymmetryPolicy(Strict):
    baseline_assumption: Optional[StrictStr] = None
    shared_baseline_group: Optional[StrictStr] = None
    independent_override_supported: Optional[StrictBool] = None


class DerivationInput(Strict):
    name: StrictStr
    value: Optional[Number] = None
    unit: Optional[StrictStr] = None
    source_id: Optional[StrictStr] = None
    role: Optional[StrictStr] = None


class Derivation(Strict):
    inputs: List[Union[DerivationInput, StrictStr]] = []
    formula: Optional[StrictStr] = None
    assumptions: List[StrictStr] = []


class Normalization(Strict):
    """Normalizing length of a normalized quantity (D-055 C3)."""
    length_property: StrictStr
    reference_observation: Optional[StrictStr] = None
    basis: Optional[StrictStr] = None


class Datum(Strict):
    target: Target
    property_id: StrictStr
    property_definition: Optional[StrictStr]
    property_role: Optional[StrictStr] = None
    value_form: Optional[StrictStr]
    value: Union[Number, dict, list, None] = None
    unit: Optional[StrictStr]
    uncertainty: Optional[Uncertainty] = None
    datum_kind: Optional[StrictStr]
    method: Optional[Method] = None
    coordinate_context: Optional[CoordinateContext] = None
    provenance: Provenance
    applicability: Applicability
    quality: Optional[Quality] = None
    symmetry_policy: Optional[SymmetryPolicy] = None
    derivation: Optional[Derivation] = None
    normalization: Optional[Normalization] = None
    status: StrictStr


__all__ = ["Datum", "Any"]
