"""python -m tools.run_phase_b --commit-sha FULL_SHA --output results/phase_b/<date>_phase_b_runs_<shortsha>.json

Runs are demonstrations; physiological and clinical validity are not established.
"""
import argparse
from pathlib import Path
from src.hip_phase_b import ROOT, resolve_inputs, simulate, run_manifest, serialize_manifest

def main():
    p=argparse.ArgumentParser(description="Right-hip data-to-dynamics demonstration (D-053)")
    p.add_argument("--commit-sha",required=True,help="40-character revision identifier")
    p.add_argument("--config",type=Path,default=ROOT/"config/phase_b_hip.yaml")
    p.add_argument("--baseline",type=Path,default=ROOT/"config/phase_b_scenario_baseline.yaml")
    p.add_argument("--perturbed",type=Path,default=ROOT/"config/phase_b_scenario_perturbed.yaml")
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    runs=[]
    for scenario_path in (args.baseline,args.perturbed):
        inputs=resolve_inputs(args.config,scenario_path)
        runs.append(run_manifest(inputs,simulate(inputs),args.commit_sha))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(serialize_manifest(runs),encoding="utf-8")
    print("Demonstration manifest (validity not established) written to",args.output)

if __name__=="__main__":
    main()
