#!/usr/bin/env python3
"""
Create GitHub milestones, labels, and issues for RE:GENESIS hackathon pipeline.

Prerequisites:
  brew install gh   # or see https://cli.github.com
  gh auth login     # or export GH_TOKEN=<pat with repo scope>

Usage:
  python3 scripts/github_bootstrap_issues.py
  python3 scripts/github_bootstrap_issues.py --repo mitra9917/ReGenesis --dry-run
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from typing import List, Optional

REPO_DEFAULT = "mitra9917/ReGenesis"

MILESTONES = [
    ("M0 Tooling & MCP", "CLI, SAM, Cursor AWS MCP"),
    ("M1 Foundation green", "Deploy + E2E without SageMaker"),
    ("M2 ML model", "YOLO dataset, train, SageMaker endpoint"),
    ("M3 AWS integration", "Vision fallback, Textract, metrics, hardening"),
    ("M4 Product completeness", "RVS, audit, golden R740 run"),
    ("M5 Frontend multipage", "Sleek multipage UI after functional"),
    ("M6 Demo & submit", "Video, Builder Center, submission"),
]

LABELS = {
    # Phases (milestone sub-stages)
    "phase-0.1": "1d76db",
    "phase-0.2": "1d76db",
    "phase-1.1": "1d76db",
    "phase-1.2": "1d76db",
    "phase-1.3": "1d76db",
    "phase-2.1": "1d76db",
    "phase-2.2": "1d76db",
    "phase-2.3": "1d76db",
    "phase-3.1": "1d76db",
    "phase-3.2": "1d76db",
    "phase-3.3": "1d76db",
    "phase-4": "1d76db",
    "phase-5": "1d76db",
    "phase-6": "1d76db",
    # Work type
    "ml-model": "0e8a16",
    "aws-integration": "fbca04",
    "infra-sam": "5319e7",
    "backend": "c5def5",
    "frontend": "d4c5f9",
    "devops-deploy": "006b75",
    "data-catalog": "bfdadc",
    "security-kms": "b60205",
    "demo-video": "e99695",
    "docs": "0075ca",
    # Priority & flow
    "priority-p0": "d73a4a",
    "priority-p1": "f9d0c4",
    "priority-p2": "fef2c0",
    "blocker": "b60205",
    "parallel-ok": "a2eeef",
    "blocked-by-ml": "d876e3",
    "blocked-by-aws": "d876e3",
    # Owners (assign manually on GitHub if needed)
    "owner-you": "1f883d",
    "owner-friend": "2da44e",
    "owner-both": "3fb950",
    # AWS services
    "service-lambda": "ff9900",
    "service-step-functions": "ff9900",
    "service-api-gateway": "ff9900",
    "service-s3": "ff9900",
    "service-dynamodb": "ff9900",
    "service-kms": "ff9900",
    "service-sagemaker": "ff9900",
    "service-textract": "ff9900",
    "service-sns": "ff9900",
    "service-cloudwatch": "ff9900",
    "service-cloudfront": "ff9900",
}


@dataclass
class IssueSpec:
    issue_id: str
    milestone: str
    phase: str
    title: str
    owner: str
    labels: List[str]
    parallel: str
    skip: str
    done_when: str
    extra_labels: List[str] = field(default_factory=list)

    def all_labels(self) -> List[str]:
        owner_label = {
            "You": "owner-you",
            "Friend": "owner-friend",
            "Both": "owner-both",
            "You + Friend": "owner-both",
            "Friend + You": "owner-both",
            "Friend/You": "owner-both",
            "Either": "owner-both",
            "You or Friend": "owner-both",
        }.get(self.owner, "owner-both")
        return sorted(set([self.phase, owner_label] + self.labels + self.extra_labels))

    def gh_title(self) -> str:
        m = self.milestone.split()[0]  # M0, M1, ...
        return f"[{m}][{self.issue_id}] {self.title}"

    def body(self) -> str:
        return f"""## Pipeline issue `{self.issue_id}`

| Field | Value |
|-------|-------|
| **Milestone** | {self.milestone} |
| **Phase** | `{self.phase}` |
| **Owner** | {self.owner} |
| **Parallel?** | {self.parallel} |
| **Skip?** | {self.skip} |

### Done when
{self.done_when}

---
See [docs/HACKATHON_PIPELINE.md](docs/HACKATHON_PIPELINE.md).
"""


def build_issues() -> List[IssueSpec]:
    """All issues from HACKATHON_PIPELINE.md."""
    specs: List[IssueSpec] = []

    def add(
        issue_id: str,
        milestone: str,
        phase: str,
        title: str,
        owner: str,
        labels: List[str],
        parallel: str,
        skip: str,
        done_when: str,
        services: Optional[List[str]] = None,
    ):
        extra = [f"service-{s}" for s in (services or [])]
        specs.append(
            IssueSpec(
                issue_id=issue_id,
                milestone=milestone,
                phase=phase,
                title=title,
                owner=owner,
                labels=labels,
                parallel=parallel,
                skip=skip,
                done_when=done_when,
                extra_labels=extra,
            )
        )

    M0, M1, M2, M3, M4, M5, M6 = [m[0] for m in MILESTONES]

    # M0
    add("I-0.1.1", M0, "phase-0.1", "AWS account, credits, billing alarm ($25/$50)", "You", ["devops-deploy", "priority-p0"], "Yes for Friend", "No", "Alarm exists; region chosen (e.g. ap-south-1)", ["cloudwatch"])
    add("I-0.1.2", M0, "phase-0.1", "Install AWS CLI v2; aws configure (profile regenesis)", "Both", ["devops-deploy"], "Yes", "No", "`aws sts get-caller-identity` works")
    add("I-0.1.3", M0, "phase-0.1", "Install SAM CLI + Docker (optional local)", "You", ["infra-sam", "devops-deploy"], "Yes", "Skippable if cloud-only", "`sam --version` works")
    add("I-0.1.4", M0, "phase-0.1", "Install Node 20+, Python 3.12+, git; clone repo", "Both", ["devops-deploy"], "Yes", "No", "npm / python3 available")
    add("I-0.2.1", M0, "phase-0.2", "Add AWS MCP to Cursor (mcp.json) + restart", "Both", ["devops-deploy", "docs"], "Yes", "Nice-to-have", "aws-api MCP connected in Cursor")
    add("I-0.2.2", M0, "phase-0.2", "Smoke-test MCP: verify caller identity / region", "You", ["aws-integration"], "Yes", "Yes", "Agent returns correct account/region")

    # M1 Phase 1.1
    add("I-1.1.1", M1, "phase-1.1", "Review device + component catalog for R740 demo", "Both", ["data-catalog", "priority-p0"], "Yes", "No", "Catalog matches demo story")
    add("I-1.1.2", M1, "phase-1.1", "Run unit tests (pytest tests/unit)", "Both", ["backend", "data-catalog"], "Yes", "No", "All tests green")
    add("I-1.1.3", M1, "phase-1.1", "Generate synthetic devices JSONL", "Friend", ["data-catalog", "parallel-ok"], "Yes", "Yes", "JSONL exists for demos")

    # M1 Phase 1.2
    add("I-1.2.1", M1, "phase-1.2", "samconfig.toml: region + DetectionMode=mock", "You", ["infra-sam", "priority-p0"], "Friend trains ML", "No", "Config ready (no secrets in git)", ["lambda"])
    add("I-1.2.2", M1, "phase-1.2", "First SAM deploy (sam build && sam deploy)", "You", ["infra-sam", "devops-deploy", "priority-p0", "blocker"], "parallel-ok", "No", "Stack CREATE_COMPLETE", ["lambda", "step-functions", "api-gateway", "s3", "dynamodb", "kms"])
    add("I-1.2.3", M1, "phase-1.2", "Record stack outputs (ApiUrl, buckets, CloudFront, KMS)", "You", ["devops-deploy", "docs"], "Yes", "No", "Shared with teammate")
    add("I-1.2.4", M1, "phase-1.2", "Smoke POST /devices (poweredge_r740)", "You", ["backend", "aws-integration", "priority-p0"], "Yes", "No", "202 + execution_arn", ["api-gateway", "lambda", "step-functions"])
    add("I-1.2.5", M1, "phase-1.2", "Confirm RecoveryFlow Step Functions SUCCEEDED", "You", ["aws-integration", "backend", "priority-p0"], "Yes", "No", "Green execution in console", ["step-functions"])
    add("I-1.2.6", M1, "phase-1.2", "Confirm DynamoDB rows + S3 passport objects", "You", ["aws-integration", "security-kms"], "Yes", "No", "Devices/Components/Passports + S3 JSON", ["dynamodb", "s3", "kms"])
    add("I-1.2.7", M1, "phase-1.2", "Confirm GET /passports/{id}/verify valid=true", "You", ["security-kms", "priority-p0"], "Yes", "No", "KMS signature verifies", ["kms", "lambda", "api-gateway"])

    # M1 Phase 1.3
    add("I-1.3.1", M1, "phase-1.3", "Set frontend VITE_API_URL to ApiUrl", "You", ["frontend", "devops-deploy", "priority-p0"], "Yes", "No", "Run button enabled", ["api-gateway"])
    add("I-1.3.2", M1, "phase-1.3", "Complete one UI recovery end-to-end", "You", ["frontend", "priority-p0"], "Friend: ML", "No", "Plan + impact + passports on results page")
    add("I-1.3.3", M1, "phase-1.3", "Deploy UI build to S3 + CloudFront", "You", ["devops-deploy", "frontend", "priority-p1"], "Yes", "Can wait for M5", "Public UI URL works", ["s3", "cloudfront"])

    # M2
    add("I-2.1.1", M2, "phase-2.1", "Collect PCB + server interior images", "Friend", ["ml-model", "data-catalog"], "Yes vs M1", "Soft-skip", "≥50 labeled images or plan")
    add("I-2.1.2", M2, "phase-2.1", "Label YOLO classes (CPU GPU RAM SSD …)", "Friend", ["ml-model"], "Yes", "Soft-skip", "YOLO labels ready")
    add("I-2.1.3", M2, "phase-2.1", "Write ml/training/data/data.yaml", "Friend", ["ml-model"], "Yes", "Soft-skip", "Train script finds data")
    add("I-2.2.1", M2, "phase-2.2", "Train YOLO (train_yolo.py or notebook)", "Friend", ["ml-model", "priority-p1"], "Yes", "Soft-skip", "best.pt exists")
    add("I-2.2.2", M2, "phase-2.2", "Record mAP / precision-recall for blog", "Friend", ["ml-model", "docs"], "Yes", "Soft-skip", "Metrics for slides")
    add("I-2.2.3", M2, "phase-2.2", "Local inference JSON matches API schema", "Friend", ["ml-model", "backend"], "Yes", "Soft-skip", "detections[] + normalized bbox")
    add("I-2.3.1", M2, "phase-2.3", "Build model.tar.gz for SageMaker", "Friend", ["ml-model", "aws-integration"], "Needs AWS", "Soft-skip", "Artifact in S3", ["sagemaker", "s3"])
    add("I-2.3.2", M2, "phase-2.3", "Create SageMaker endpoint (small/serverless)", "Friend + You", ["ml-model", "aws-integration", "devops-deploy"], "After M1", "Soft-skip", "Endpoint InService", ["sagemaker"])
    add("I-2.3.3", M2, "phase-2.3", "Document delete endpoint when idle (cost guard)", "Both", ["devops-deploy", "docs", "priority-p0"], "Yes", "No", "Teardown note shared")
    add("I-2.3.4", M2, "phase-2.3", "Redeploy SAM: SageMakerEndpointName + DetectionMode=auto", "You", ["infra-sam", "blocked-by-ml"], "Blocked until 2.3.2", "Soft-skip", "Lambda env updated", ["lambda", "sagemaker"])

    # M3
    add("I-3.1.1", M3, "phase-3.1", "Test DETECTION_MODE=auto with real endpoint", "You + Friend", ["aws-integration", "ml-model"], "After 2.3.4", "Soft-skip", "detection_source=vision", ["sagemaker", "lambda"])
    add("I-3.1.2", M3, "phase-3.1", "Verify catalog-assisted fallback path", "You", ["aws-integration", "backend", "priority-p0"], "Yes", "No", "Fallback badge + audit work", ["lambda"])
    add("I-3.1.3", M3, "phase-3.1", "Textract model-plate path on sample photo", "You", ["aws-integration", "priority-p1"], "Yes", "Soft-skip", "OCR confirms model key", ["textract", "lambda"])
    add("I-3.2.1", M3, "phase-3.2", "Step Functions screenshot for demo", "You", ["aws-integration", "demo-video"], "Yes", "No", "Clean success screenshot", ["step-functions"])
    add("I-3.2.2", M3, "phase-3.2", "Verify S3 key prefixes (images/logs/passports)", "You", ["aws-integration"], "Yes", "No", "Matches ARCHITECTURE.md", ["s3"])
    add("I-3.2.3", M3, "phase-3.2", "Tamper passport JSON → verify fails", "You", ["security-kms", "priority-p1"], "Yes", "Soft-skip", "Invalid signature demo", ["kms"])
    add("I-3.2.4", M3, "phase-3.2", "SNS job-complete notification", "You", ["aws-integration", "priority-p2"], "Yes", "Yes", "Optional subscription works", ["sns"])
    add("I-3.2.5", M3, "phase-3.2", "CloudWatch custom metrics visible", "You", ["aws-integration", "priority-p1"], "Yes", "Soft-skip", "ComponentsRecovered / CO2e graphs", ["cloudwatch"])
    add("I-3.3.1", M3, "phase-3.3", "GET /devices/{id} returns plan + audit + impact", "You", ["backend", "priority-p0"], "Yes", "No", "Matches UI needs", ["api-gateway", "dynamodb"])
    add("I-3.3.2", M3, "phase-3.3", "GET /jobs execution_arn polling stable", "You", ["backend", "frontend"], "Yes", "No", "UI status updates", ["step-functions", "api-gateway"])
    add("I-3.3.3", M3, "phase-3.3", "Image upload base64 → S3 → detection", "You", ["backend", "aws-integration"], "Yes", "Soft-skip", "image_s3_key used", ["s3", "lambda"])

    # M4
    add("I-4.1", M4, "phase-4", "RVS ordering clear in plan timeline", "Both", ["backend", "data-catalog"], "Yes", "No", "High-value parts prioritized")
    add("I-4.2", M4, "phase-4", "Completeness audit flags under-detection", "You", ["backend", "ml-model"], "Yes", "Soft-skip", "Gaps array meaningful")
    add("I-4.3", M4, "phase-4", "Deterministic diagnostics per component_id", "You", ["backend"], "Yes", "No", "Repeatable demo")
    add("I-4.4", M4, "phase-4", "Impact panel uses catalog factors + ranges", "Both", ["data-catalog", "docs"], "Yes", "No", "Honest CO2e ranges")
    add("I-4.5", M4, "phase-4", "PipelineEvents table debuggable", "You", ["aws-integration", "backend"], "Yes", "Soft-skip", "Events per pipeline stage", ["dynamodb"])
    add("I-4.6", M4, "phase-4", "Stretch: second device type (laptop/switch)", "Friend/You", ["data-catalog", "priority-p2"], "Yes", "Yes", "Optional second demo path")

    # M5
    add("I-5.1", M5, "phase-5", "IA + route map for multipage UI", "Both", ["frontend", "docs"], "After M1", "Soft-skip", "Routes agreed")
    add("I-5.2", M5, "phase-5", "Layout, nav, design tokens (minimal sleek)", "You or Friend", ["frontend", "priority-p1"], "After M1", "Soft-skip", "Consistent look")
    add("I-5.3", M5, "phase-5", "Landing page (problem + CTA)", "Either", ["frontend"], "After M1", "Soft-skip", "Strong first viewport")
    add("I-5.4", M5, "phase-5", "Recovery + dashboard polish (loading/errors)", "Either", ["frontend", "priority-p0"], "After M1", "No", "Frictionless demo path")
    add("I-5.5", M5, "phase-5", "Passports list + verify UX", "Either", ["frontend", "security-kms"], "After M1", "Soft-skip", "One-click verify")
    add("I-5.6", M5, "phase-5", "Impact page / section", "Either", ["frontend"], "After M1", "Soft-skip", "Clear judge metrics")
    add("I-5.7", M5, "phase-5", "Redeploy UI to CloudFront", "You", ["devops-deploy", "frontend"], "After I-5.x", "Soft-skip", "Prod URL", ["cloudfront", "s3"])

    # M6
    add("I-6.1", M6, "phase-6", "Rehearse DEMO_SCRIPT.md (≤3 min)", "Both", ["demo-video"], "After golden run", "No", "Timing fits")
    add("I-6.2", M6, "phase-6", "Record hackathon screencast", "Both", ["demo-video", "priority-p0"], "After M1+", "No", "Video uploaded")
    add("I-6.3", M6, "phase-6", "Capture architecture + Step Functions assets", "You", ["demo-video", "aws-integration"], "Yes", "Soft-skip", "Screenshots ready", ["step-functions"])
    add("I-6.4", M6, "phase-6", "Publish Builder Center blog", "Both", ["docs", "priority-p0"], "Parallel", "No", "Post live + linked")
    add("I-6.5", M6, "phase-6", "Submit Waste and Energy track (repo, URL, video)", "Both", ["docs", "priority-p0"], "Last", "No", "Form submitted")
    add("I-6.6", M6, "phase-6", "Teardown SageMaker endpoint / costly resources", "You", ["devops-deploy", "priority-p0"], "After video", "No", "Credits protected", ["sagemaker"])

    return specs


def run_gh(args: List[str], repo: str, dry_run: bool) -> subprocess.CompletedProcess:
    cmd = ["gh"] + args
    if "--repo" not in args and repo:
        cmd.extend(["--repo", repo])
    if dry_run:
        print("DRY-RUN:", " ".join(cmd))
        return subprocess.CompletedProcess(cmd, 0, "", "")
    return subprocess.run(cmd, capture_output=True, text=True)


def ensure_auth() -> None:
    r = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
    if r.returncode != 0:
        print("GitHub CLI not authenticated. Run:\n  gh auth login\nor:\n  export GH_TOKEN=<token with repo scope>\n", file=sys.stderr)
        sys.exit(1)


def create_labels(repo: str, dry_run: bool) -> None:
    for name, color in LABELS.items():
        r = run_gh(["label", "create", name, "--color", color, "--force"], repo, dry_run)
        if not dry_run and r.returncode != 0 and "already exists" not in (r.stderr or "").lower():
            if r.returncode != 0:
                print(r.stderr or r.stdout, file=sys.stderr)


def get_milestone_numbers(repo: str, dry_run: bool) -> dict[str, int]:
    if dry_run:
        return {m[0]: i + 1 for i, m in enumerate(MILESTONES)}
    r = subprocess.run(
        ["gh", "api", f"repos/{repo}/milestones", "--paginate"],
        capture_output=True,
        text=True,
    )
    existing = {item["title"]: item["number"] for item in json.loads(r.stdout or "[]")}
    numbers = {}
    for title, desc in MILESTONES:
        if title in existing:
            numbers[title] = existing[title]
            continue
        create = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{repo}/milestones",
                "-f",
                f"title={title}",
                "-f",
                f"description={desc}",
            ],
            capture_output=True,
            text=True,
        )
        if create.returncode != 0:
            print(create.stderr, file=sys.stderr)
            sys.exit(1)
        numbers[title] = json.loads(create.stdout)["number"]
        print(f"Created milestone: {title} (#{numbers[title]})")
    return numbers


def existing_issue_titles(repo: str) -> set[str]:
    r = subprocess.run(
        ["gh", "issue", "list", "--repo", repo, "--limit", "500", "--json", "title"],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        return set()
    return {item["title"] for item in json.loads(r.stdout)}


def create_issues(repo: str, dry_run: bool) -> None:
    milestone_nums = get_milestone_numbers(repo, dry_run)
    titles = existing_issue_titles(repo) if not dry_run else set()
    created = skipped = 0
    for spec in build_issues():
        title = spec.gh_title()
        if title in titles:
            skipped += 1
            continue
        labels = ",".join(spec.all_labels())
        # gh expects milestone *title*, not numeric id
        milestone_title = spec.milestone
        if milestone_title not in milestone_nums and not dry_run:
            print(f"WARN: milestone missing: {milestone_title}", file=sys.stderr)
        args = [
            "issue",
            "create",
            "--title",
            title,
            "--body",
            spec.body(),
            "--label",
            labels,
            "--milestone",
            milestone_title,
        ]
        r = run_gh(args, repo, dry_run)
        if dry_run:
            created += 1
            continue
        if r.returncode != 0:
            print(f"FAILED {title}:\n{r.stderr}", file=sys.stderr)
        else:
            created += 1
            print(f"Created: {title}")
    print(f"\nDone. Created: {created}, skipped (existing): {skipped}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=REPO_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not args.dry_run:
        ensure_auth()
    create_labels(args.repo, args.dry_run)
    create_issues(args.repo, args.dry_run)


if __name__ == "__main__":
    main()
