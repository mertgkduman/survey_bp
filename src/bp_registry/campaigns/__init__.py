"""Strict, evidence-preserving campaign execution primitives."""

from .contracts import (
    CampaignArmV1, CampaignPlanV1, CampaignSpecV1, CampaignWorkSpecV1,
    MaterializedPhysicalSampleV1, SharedSamplerContractV1, build_one_unit_plan,
)
from .execution import run_canonical_work_plan, run_one_unit, verify_canonical_attempt
from .planning import CampaignWorkPlan, freeze_campaign_work_spec
from .shards import reconstruct_fixed_shot, verify_shard

__all__ = [
    "CampaignPlanV1",
    "CampaignSpecV1",
    "CampaignArmV1",
    "CampaignWorkPlan",
    "CampaignWorkSpecV1",
    "MaterializedPhysicalSampleV1",
    "SharedSamplerContractV1",
    "build_one_unit_plan",
    "freeze_campaign_work_spec",
    "reconstruct_fixed_shot",
    "run_one_unit",
    "run_canonical_work_plan",
    "verify_canonical_attempt",
    "verify_shard",
]
