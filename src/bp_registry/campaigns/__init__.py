"""Strict, evidence-preserving campaign execution primitives."""

from .contracts import (
    CampaignArmV1, CampaignPlanV1, CampaignSpecV1, CampaignWorkSpecV1,
    MaterializedPhysicalSampleV1, SharedSamplerContractV1, build_one_unit_plan,
)
from .execution import run_canonical_work_plan, run_one_unit, verify_canonical_attempt
from .planning import CampaignWorkPlan, freeze_campaign_work_spec
from .reporting import CampaignReportV1, reconstruct_campaign_report, verify_campaign_report, verify_campaign_routes
from .shards import derive_resume_plan, reconstruct_fixed_shot, verify_shard
from .sizing import PairedDesignV1, paired_design_size

__all__ = [
    "CampaignPlanV1",
    "CampaignReportV1",
    "CampaignSpecV1",
    "CampaignArmV1",
    "CampaignWorkPlan",
    "CampaignWorkSpecV1",
    "MaterializedPhysicalSampleV1",
    "PairedDesignV1",
    "SharedSamplerContractV1",
    "build_one_unit_plan",
    "derive_resume_plan",
    "freeze_campaign_work_spec",
    "paired_design_size",
    "reconstruct_fixed_shot",
    "reconstruct_campaign_report",
    "run_one_unit",
    "run_canonical_work_plan",
    "verify_canonical_attempt",
    "verify_campaign_report",
    "verify_campaign_routes",
    "verify_shard",
]
