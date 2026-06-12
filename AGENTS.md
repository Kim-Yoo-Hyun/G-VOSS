# Research Agent Harness

이 저장소는 3D Scene Graph 분야의 석사 연구를 위해 문헌 조사, 동향 파악, 기여 가능성 탐색을 누적하는 작업 공간이다.

## Current Scope

- 현재 하네스는 `literature` 조사에서 `hypothesis` 준비 및 scoped experiment 단계로 확장되었다.
- 논문 본문용 실제 experiment 구현은 Docker 기반으로 진행한다.
- 현재 active experiment root는 `experiments/H001_geom_reliability/`이다.
- 연구 목표와 방향성은 AI, ML, CV, Robotics top-tier journal/conference를 타겟으로 판단한다.
- `docs/hypothesis.md`는 hypothesis workflow와 작성 규칙을 관리한다.
- `docs/literature.md`는 literature workflow와 작성 규칙을 관리한다.
- `docs/experiments.md`는 Docker experiment workflow와 promotion 규칙을 관리한다.
- `docs/paper.md`는 top-tier paper framing, novelty standard, reviewer-defense rule을 관리한다.
- 실제 문헌 조사 결과는 루트의 `literature/` 폴더에 저장한다.
- 실제 hypothesis 산출물은 루트의 `hypothesis/` 폴더에 저장한다.
- 논문 하나는 `literature/<paper-folder>/` 하나로 관리한다.

## Instruction Strategy

`AGENTS.md`는 작업 전에 읽히는 project instruction이며, 세부 연구 로그가 아니라 에이전트용 상위 운영 규칙이다. OpenAI Codex guidance처럼 repo-level instruction에는 setup/rules/expectations, file responsibilities, verification expectations만 두고, 상세 지침은 가까운 하위 문서나 nested instruction으로 분리한다.

- 이 repo의 기본 구조는 `AGENTS.md = 상위 규칙과 파일 책임`, `docs/*.md` 및 각 폴더 `README.md = 세부 runbook/state`이다.
- 이 파일에는 변하지 않는 rule, document ownership, claim boundary, experiment safety rule만 둔다.
- 최신 실험 상태, 긴 artifact 목록, 실행 명령, row count, recovery checklist는 `docs/reproducibility.md`, `docs/index.md`, `summary.md`, `TODO.md`, `experiments/**/README.md`에 둔다.
- 특정 폴더의 세부 규칙은 그 폴더의 `README.md` 또는 필요 시 nested `AGENTS.md`로 분리한다.
- `AGENTS.md`를 run log, paper draft, artifact inventory, download checklist, or metric table로 사용하지 않는다.
- Codex의 project instruction size limit을 고려해 이 파일은 간결하게 유지한다. 긴 목록은 owning document로 이동한다.

## Reading Protocol

작업 시작 시에는 `AGENTS.md`를 최상위 project instruction으로 먼저 읽고,
이어서 현재 상태와 우선순위를 재구성한다. 이후 작업 유형에 맞는 대표
문서를 읽고 필요한 폴더의 `README.md`로 내려간다.

1. Global instruction: `AGENTS.md`
2. Orientation: `README.md`, `TODO.md`, `docs/index.md`
3. Global rules: `docs/paper.md`, `docs/experiments.md`, `docs/reproducibility.md`
4. Research state: `summary.md`, `hypothesis/README.md`, relevant H-folder canonical files
5. Literature tasks: `docs/literature.md`, `literature/README.md`, `literature/PAPER.md`
6. Hypothesis tasks: `docs/hypothesis.md`, `hypothesis/README.md`, relevant H-folder canonical files
7. Experiment tasks: `docs/experiments.md`, relevant `experiments/**/README.md`, `commands.md`, `compose*.yaml`, and reports
8. Paper-writing tasks: `paper/README.md`, `paper/preview.md`, `paper/risk.md`, `paper/appendix.md`, `paper/outline.md`, `paper/draft.md`, `paper/figures.md`, and venue folder README

H001 resume, upload, deletion, or other-computer recovery work must start from `docs/reproducibility.md`. That file owns the exact artifact lists, transfer paths, verification commands, and recovery order.

## Repository File Role Map

- `AGENTS.md`: agent-facing operating contract. Owns stable rules, file-role map, documentation ownership, experiment safety, novelty/claim guardrails, and update protocol.
- `README.md`: human-facing project overview and current high-level phase. It should summarize where the work stands, not duplicate runbooks.
- `TODO.md`: mutable task board. Owns `Now`, `Next`, and recently completed items. It should not contain long literature notes, full metrics, or large command logs.
- `summary.md`: consolidated research summary. Owns problem definition, hypothesis, contribution, metric/baseline plan, current evidence, and top-level paper direction.
- `docs/index.md`: state dashboard. Owns current status, active questions, and pointers to working files.
- `docs/literature.md`: literature workflow rulebook. Owns how to create paper cards, trend synthesis, and contribution scans.
- `docs/hypothesis.md`: hypothesis workflow rulebook. Owns candidate/hypothesis stages, gate criteria, and hypothesis artifact conventions.
- `docs/experiments.md`: Docker experiment workflow rulebook. Owns experiment promotion criteria, root-creation checklist, source adapter expectations, metric-freeze gates, and paper-result boundary rules.
- `docs/paper.md`: paper-framing rulebook. Owns top-tier novelty standard, claim boundary, reviewer-risk checklist, and table/ablation/failure-analysis requirements.
- `docs/reproducibility.md`: recovery and reproducibility runbook. Owns dataset/checkpoint/model locations, artifact bundles, Docker commands, verification commands, transfer guidance, and cleanup implications.
- `literature/`: paper evidence base. Owns source-grounded paper cards, field maps, cross-paper synthesis, reading queue, and contribution candidates.
- `hypothesis/`: pre-paper validation workspace. Owns hypothesis statements, method sketches, smoke tests, audits, scoped results, and experiment-transition gates.
- `experiments/`: Docker-based paper experiment workspace. Owns executable experiment code, compose files, locked manifests, paper-facing reports, metric outputs, and source-specific adapters.
- `paper/`: manuscript workspace. `paper/README.md` owns the folder map; the folder owns paper preview, progress rationale, outline, draft prose, risk register, appendix/supplement plan, venue-specific LaTeX source, references, and figure plans.
- `logs/`: timestamped logs for long-running or verification jobs. Inspect with `tail`, `head`, targeted `rg`, summaries, or exit files.
- `local_dataset/`: ignored local dataset/cache/runtime root. Never treat it as a tracked artifact source.
- `release/`: ignored external artifact bundle staging area. Use checksums and row/file-count verification before relying on it.

## Documentation Ownership Rules

- If a change adds or changes a rule, update `AGENTS.md`.
- If a change updates current status, active work, or completion history, update `TODO.md` and possibly `docs/index.md`.
- If a change affects research framing, contribution, novelty, or reviewer defense, update `docs/paper.md`, `summary.md`, and the relevant `paper/` planning file.
- If a change affects commands, datasets, checkpoints, model caches, artifact transfer, or cleanup safety, update `docs/reproducibility.md` and the relevant experiment README.
- If a change affects a folder-local workflow, update that folder's `README.md`; do not expand `AGENTS.md` with folder-local details.
- When a new root-level research/workflow folder is created or activated, create or update the matching `docs/<folder>.md` workflow rulebook before substantive work in that folder. Also add it to `docs/index.md` and the relevant README role map. This rule applies to durable workflow roots such as `experiments/`, `paper/`, `literature/`, or `hypothesis/`, not transient/ignored roots such as `logs/`, `local_dataset/`, or `release/`.
- If a detailed list appears in more than one place, keep the authoritative copy in the owning document and replace other copies with a pointer.

## Working Language

- 사용자에게는 한국어로 답한다.
- 논문 제목, 방법명, 데이터셋명, metric, benchmark 이름은 영어 원문을 유지한다.
- "사실", "논문 주장", "에이전트 추론", "사용자 판단 필요"를 섞지 말고 구분한다.

## Paper Novelty Standard

H001/CAND를 논문으로 정리할 때 motivation만으로 novelty를 주장하지 않는다. Top-tier 기준에서는 "기존 방법이 안 된다"가 아니라, "왜 안 되는가"와 "그 원인 때문에 왜 이 방법 형태가 필요해지는가"가 핵심이다.

- Top-tier claim은 기존 3DSSG/3D Scene Graph relation method의 구체적 failure mode를 정의하고, 그 failure가 실제라는 증거를 보이고, 원인 mechanism/assumption을 설명하고, 그 원인을 직접 바꾸는 method를 제안해야 한다.
- Novelty를 "geometry를 추가했다", "semantic과 geometry를 결합했다", "VLM을 사용했다", "verifier를 만들었다", "중요한 task다"로 쓰지 않는다. 이 표현들은 failure cause와 design necessity에 연결되지 않으면 motivation 또는 implementation detail이다.
- H001의 선호 claim pattern은 다음과 같다: existing relation predictors can produce semantically plausible but geometrically inconsistent 3D scene graph relations because semantic confidence is not calibrated to relation-level physical consistency; H001 introduces calibrated geometry-consistency evaluation/re-ranking to expose, quantify, and reduce this failure while tracking recall tradeoffs.
- 모든 paper claim은 falsifiable evidence를 가져야 한다: semantic-only vs geometry re-ranking, calibration variants, family-specific controls, wrong-pair/shuffled-geometry controls, Open3DSG second-source evidence, qualitative failure taxonomy.
- Method contribution은 `verifier script`가 아니라 calibrated geometry-consistency evaluation/re-ranking framework로 명명한다. Verifier, calibration, metric, failure-analysis schema는 이 framework를 구성하는 요소로 둔다.
- Evidence가 single source의 scoped reliability에 머물면 claim도 scoped reliability로 제한한다. Broad open-vocabulary 3DSSG improvement 주장은 second-source metrics, denominator caveat, failure analysis가 완료되기 전에는 사용하지 않는다.
- Reviewer가 물을 "왜 더 단순한 방법으로 안 되는가?", "왜 이 relation family인가?", "왜 이 geometry rule/calibration인가?", "recall tradeoff는 무엇인가?"에 대한 답을 table, ablation, error taxonomy 중 하나로 연결한다.
- 논문화 과정은 원하는 가설을 증명하기 위해 결과를 끼워 맞추는 방식이 아니라, 문제의 원리에서 method가 자연스럽게 도출되고 그 method가 falsifiable evidence로 검증되는 방식이어야 한다. Claim 또는 실험을 추가할 때마다 `failure mechanism -> design necessity -> fixed protocol -> evidence -> claim boundary` chain을 확인한다.
- Evidence가 기대보다 약하거나 부정적이면 method를 사후 조정해 성공처럼 만들지 말고 claim을 좁히거나 appendix/limitation/future-work로 내린다. Relation family, source, metric, threshold, recovery branch를 main claim에 승격하려면 사전 고정된 protocol과 controls를 먼저 통과해야 한다.

## H001 Claim Boundary And Extension Rules

- H001의 현재 paper claim은 broad SOTA가 아니라 scoped relation reliability layer다. Claim을 "open-vocabulary 3DSSG 전체 성능 향상", "baseline-agnostic improvement", "Open3DSG SOTA/reproduction benchmark"로 넓히려면 별도 source metrics, denominator caveat, controls, and audit evidence가 먼저 있어야 한다.
- Open3DSG는 현재 main open-vocabulary relation-source case study로 lock한다. 논문에서는 averaged-BLIP variant, filtered train/dev split, covered H001 scope, exact-label denominator, `validation_missing_preprocessed:11`, and residual calibration-risk caveat를 Table/results/provenance wording에서 숨기지 않는다.
- Open3DSG 관련 필수 실험은 현재 scoped H001 claim 기준으로 완료된 것으로 본다. 추가 Open3DSG 실험은 claim을 넓히거나 full reproduction 자체를 목표로 바꿀 때만 진행한다.
- Qwen-VL은 VL-SAT/Open3DSG를 대체하는 main baseline이 아니라 third semantic source / modern VLM extension이다. Qwen 결과는 sharded inference, parser validation, adapter export, geometry join, metrics, controls, bootstrap CI if reported, and audit가 Docker로 완료되기 전까지 paper metric evidence가 아니다.
- Cross-source results, failure rows, qualitative inspection, and Qwen extension은 세 번째/네 번째 contribution으로 부풀리지 말고, calibrated geometry-consistency framework를 검증하는 empirical evidence로 둔다.
- `relative_horizontal`, `attachment_deferred`, Qwen-VL, or any other expansion must not be added to the main AAAI claim without explicit final confirmation from the user after the required evidence gates are complete.

## Long-running and Background Tasks

Dataset/model/checkpoint downloads, Docker pulls/builds, decompression, indexing, preprocessing, and other long-running I/O-heavy jobs must not keep Codex blocked.

- Launch long jobs in a separate `tmux` session, `nohup` process, or background job, then return to the main research task.
- Prefer resumable commands: `aria2c`, `wget -c`, `rsync --partial`, or `huggingface-cli download` with a fixed cache/local-dir.
- Always write logs under `logs/` with a timestamped filename.
- Record the exact command, working directory, output path, expected files, and verification command.
- Check progress only when explicitly requested or when a dependent task needs the result.
- Never scan or print huge logs; inspect only `tail`, `head`, or targeted `grep` errors.
- Verify completion with file counts, expected directory layout, checksums when available, or a lightweight sanity script.
- Update `TODO.md` or the relevant hypothesis README with job status: `launched`, `running`, `completed`, `failed`, or `needs_verification`.
- If a guarded loop stops because of a resource guard such as GPU utilization, treat it as a resumable stop rather than a scientific failure. Record the exact blocker, completed shards/rows, clean resume shard, exit file, and next resume command before taking any other action.

Template:

```bash
mkdir -p logs
ts=$(date +%Y%m%d_%H%M%S)
tmux new-session -d -s <job_name> "cd <workdir> && <resumable command> > logs/<job_name>_${ts}.log 2>&1"
```

## Artifact Handoff And Cleanup Rules

- Always distinguish three goals before advising uploads or deletion: paper-result preservation, current experiment resume, and full reproduction. Each goal requires a different artifact set.
- GitHub should carry source, Dockerfiles/compose files, scripts, runbooks, paper source, compact manifests, reports, table summaries, and metric summaries. Large `local_dataset/` payloads, model caches, feature caches, and row-level JSONL outputs stay ignored and must be transferred separately or regenerated.
- Before deleting any local dataset, checkpoint, feature cache, model cache, or row-level JSONL, verify the external copy with checksums, file counts, expected directory layout, or a lightweight sanity script. Record the verification and deletion rationale in `TODO.md` or `docs/reproducibility.md`.
- Deleting uploaded Open3DSG checkpoint, feature caches, or row-level JSONL does not block Qwen-VL continuation, but it does block local Open3DSG re-eval, feature audit, raw-dump regeneration, and geometry-backed figure regeneration until those artifacts are restored.
- For Qwen-VL resume on another computer, preserve or transfer the fixed model cache, full-source crops, full-source input, inference plan, runtime shard outputs, status files, Qwen compose/Dockerfile, Qwen scripts, and the latest loop log/status/exit files.
- For Open3DSG full reproduction, preserve or transfer `local_dataset/Open3DSG_staged/`, `local_dataset/3RScan/`, `local_dataset/3DSSG/`, `local_dataset/3DSSG_subset/`, and relevant model caches such as `Salesforce/instructblip-vicuna-7b`, `jinaai/jina-embeddings-v2-base-en`, and CLIP cache. For paper-table regeneration only, the verified core result bundle plus source repo is sufficient.

## Naming Rules

- 파일명과 문서 제목은 직관적이고 핵심 단어 기반으로 짧게 작성한다.
- 부모 폴더나 workflow 이름을 파일명에 반복하지 않는다. 예: `visual_inspection/labels.jsonl`처럼 쓴다.
- 불필요한 긴 접두사, 중복된 candidate/hypothesis 이름, 설명문 형태의 파일명은 피한다.
- 번호가 필요한 workflow 문서는 기존 순서를 유지하되 제목은 짧게 둔다. 예: `01_overview.md`, `02_method.md`.
- 중복된 stage 문서는 하나의 짧은 stage log로 병합한다. 이미 병합한 오래된 번호 파일을 다시 만들지 않는다.

## Evidence Rules

3D Scene Graph의 최근 동향, 최신 논문, 연구 공백, 기여 가능성을 다룰 때는 반드시 최신 정보를 확인한다.

- 우선순위 소스: 논문 PDF, arXiv, CVF Open Access, OpenReview, 공식 프로젝트 페이지, 공식 코드 저장소.
- 블로그/뉴스/요약글은 보조 자료로만 사용한다.
- 논문을 인용할 때는 제목, 연도, venue 또는 preprint 상태, 링크를 기록한다.
- "최근", "최신", "SOTA", "트렌드"라고 말하려면 검색 날짜 또는 확인 날짜를 함께 남긴다.
- 근거가 약한 판단은 `Inference`로 표시한다.
- 출처를 확인하지 못한 항목은 확정된 사실처럼 쓰지 않는다.

## Update Protocol

모든 갱신은 "가장 작은 authoritative owner"에 기록한다.

- `AGENTS.md`: stable rule이나 file-role 책임이 바뀔 때만 수정한다.
- `TODO.md`: 시작할 작업은 `Now`, 바로 다음 작업은 `Next`, 완료한 작업은 `Recently Completed`에 둔다.
- `docs/index.md`: 연구 상태 dashboard와 active questions가 바뀔 때 갱신한다.
- `summary.md`: 문제 정의, 가설, contribution, metric, baseline, experiment setting, claim boundary가 바뀔 때 갱신한다.
- `docs/literature.md` / `literature/`: 문헌 조사 절차와 결과를 관리한다. 자세한 paper card와 trend synthesis는 `literature/`에 둔다.
- `docs/hypothesis.md` / `hypothesis/`: hypothesis gate, method sketch, smoke-test artifact convention, audit/evidence lock을 관리한다.
- `docs/experiments.md` / `experiments/`: Docker experiment promotion, source adapter, metric-freeze, and paper-result boundary를 관리한다.
- `docs/paper.md` / `paper/`: paper-level novelty, reviewer defense, outline, draft, figure/table plan, venue-specific source를 관리한다.
- `docs/reproducibility.md` / `experiments/**/README.md`: dataset, checkpoint, model cache, Docker command, artifact bundle, verification, cleanup safety를 관리한다.
- `logs/`: long-running job log와 exit/status file만 둔다. 중요한 결과는 owning report/README/TODO에 요약한다.

세부 파일명, artifact directory, row-level output, run command 목록은 `AGENTS.md`에 추가하지 않는다. 그런 정보는 `docs/reproducibility.md`, `docs/hypothesis.md`, `experiments/**/README.md`, or source-specific README가 소유한다.

Experiment implementation rule:

- 논문 본문에 들어갈 실제 experiment 구현은 Docker 기반으로만 진행한다.
- Host 환경에서 직접 패키지를 설치하거나 host-only script로 paper experiment를 확정하지 않는다.
- Experiment root를 만들 때는 Dockerfile 또는 compose file, pinned dependency record, mounted dataset/cache path, command entrypoint, and output manifest를 함께 둔다.
- `local_dataset/` 같은 큰 runtime/data root는 container에 mount하고 tracked artifact로 복사하지 않는다.
- Hypothesis-stage smoke test와 문서 검증은 기존 방식으로 가능하지만, paper experiment 결과로 승격하려면 Docker command로 재현 가능해야 한다.
- 중간 산출물이 더 구체적인 review/report artifact로 대체되면 오래된 queue 파일은 유지하지 않는다.

## Contribution Candidate Standard

기여 후보는 아래 조건을 만족해야 한다.

- 어떤 기존 한계에서 출발하는지 분명해야 한다.
- 왜 3D Scene Graph 문제인지 설명되어야 한다.
- 어떤 데이터셋, benchmark, metric으로 확인할 수 있는지 가늠 가능해야 한다.
- 석사 과정에서 3-6개월 단위로 시도 가능한 범위여야 한다.
- 실패했을 때 무엇을 배울 수 있는지 적어야 한다.

## Do Not Over-Structure

- 빈 paper folder를 미리 많이 만들지 않는다.
- 추가 `experiments/` root를 미리 만들지 않는다.
- `paper/`는 현재 H001 manuscript workspace로 존재한다. 새 paper/venue subtree는 실제 필요가 생길 때만 만든다.
- `decisions/` 같은 새 top-level workflow root는 아직 만들지 않는다.
- `experiments/`는 Docker 재현성을 전제로 최소 구조부터 만든다.
- hypothesis는 루트의 `hypothesis/` 폴더에서만 관리한다.
- 해당 단계가 실제로 필요해지면 먼저 새 workflow 문서 하나에서 시작한다.
- 구조는 연구가 커질 때 따라오게 한다.
