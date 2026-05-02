# Literature Workflow

Last updated: 2026-04-28

이 문서는 3D Scene Graph 문헌 조사를 수행하는 에이전트의 workflow와 규칙을 정의한다. 실제 조사 결과는 이 파일에 저장하지 않는다.

## Storage Rule

문헌 조사 결과는 루트의 `literature/` 폴더에 저장한다.

- 전체 문헌 조사 인덱스와 synthesis: `literature/README.md`
- paper registry와 reading queue: `literature/PAPER.md`
- contribution candidate 목록: `literature/Contribution Candidates.md`
- candidate별 상세 문서: `literature/CAND-<number>.md`
- 논문별 상세 정리: `literature/<paper-folder>/`
- 작업 계획과 진행 상태: `TODO.md`
- workflow와 작성 규칙: `docs/literature.md`

`docs/literature.md`는 절차와 기준만 관리한다. 논문 내용, paper registry, trend note, contribution candidate는 `literature/` 아래에 기록한다.

## Paper Folder Convention

논문 하나는 하나의 폴더로 관리한다.

```text
literature/
  <year>_<venue-or-arxiv>_<short-title>/
    paper.pdf
    01_metadata.md
    02_paper_card.md
    03_evaluation.md
    04_insights.md
```

예시:

```text
literature/
  2024_cvpr_open3dsg/
    paper.pdf
    01_metadata.md
    02_paper_card.md
    03_evaluation.md
    04_insights.md
```

폴더명 규칙:

- 소문자 사용
- 공백 대신 `-` 사용
- 가능한 형식: `<year>_<venue>_<short-title>`
- venue가 불명확하면 `arxiv` 또는 `preprint` 사용
- 같은 논문을 중복 생성하지 않는다. 먼저 `literature/PAPER.md`의 Paper Registry를 확인한다.
- 가능한 경우 논문 PDF를 `paper.pdf`라는 이름으로 저장한다.
- arXiv 등에서 버전이 중요한 경우 `01_metadata.md`에 확인한 버전과 다운로드 날짜를 적는다.

## File Roles

### `01_metadata.md`

논문의 식별 정보와 출처를 저장한다.

```md
# <Paper Title>

- Date checked:
- Year:
- Venue / status:
- Authors:
- Link:
- PDF:
- Local PDF: `paper.pdf`
- PDF version:
- PDF downloaded:
- Code:
- Project page:
- Dataset:
- Tags:
- Reading status: Queued / Skimmed / Read / Revisit
```

### `02_paper_card.md`

논문의 핵심 문제와 방법을 정리한다.

```md
# Paper Card

## Problem

## Core Idea

## Input / Output

## Method

## Main Claims

## Strengths

## Limitations

## Relevance to My Research

## Follow-up Questions
```

### `03_evaluation.md`

실험과 평가 가능성을 따로 본다. 석사 연구로 이어질 수 있는지 판단하는 핵심 파일이다.

```md
# Evaluation

## Dataset / Benchmark

## Splits

## Metrics

## Baselines

## Main Results

## Reproducibility Notes

## Evaluation Weaknesses
```

### `04_insights.md`

에이전트의 해석, trend 연결, 기여 가능성을 기록한다. 논문 사실과 추론을 분리한다.

```md
# Insights

## Facts

## Paper Claims

## Inferences

## Connection to Field Trends

## Possible Contribution Angles

## What Would Change This Assessment
```

## Global Literature Index

`literature/README.md`는 전체 문헌 조사 결과의 인덱스와 cross-paper synthesis를 관리한다.

포함해야 할 섹션:

- Field Map
- Trend Synthesis
- Cross-Paper Insights
- Open Questions

개별 논문 내용은 각 paper folder에 두고, `literature/README.md`에는 cross-paper synthesis만 남긴다.

## Literature Control Files

### `literature/PAPER.md`

paper registry와 reading queue를 관리한다.

- `Paper Registry`: 논문 목록, venue, folder, status, why it matters
- `Reading Queue`: 다음에 읽을 논문/주제, priority, status

### `literature/Contribution Candidates.md`

contribution candidate 목록을 관리한다.

- 후보를 간단히 비교할 수 있는 수준으로 유지한다.
- 특정 후보가 길어지면 별도 `literature/CAND-<number>.md`로 분리한다.
- 후보 목록에는 detail file 링크를 둔다.

### `literature/CAND-<number>.md`

특정 contribution candidate의 세부 문제 설정, feasibility, dataset/metric/baseline 판단을 관리한다.

현재 구조:

- `literature/CAND-001.md`: CAND-001 세부 문제 설정, closed-set 3DSG problem setting, feasibility notes

## Research Questions

문헌 조사는 아래 질문으로 수렴해야 한다.

1. 3D Scene Graph의 최근 주류 흐름은 무엇인가?
2. 기존 연구들이 공유하는 problem setting, dataset, metric은 무엇인가?
3. open-vocabulary, LLM/VLM, robotics, dynamic scene, 3D generation은 각각 어떤 한계를 해결하려는가?
4. 현재 연구 흐름에서 석사 연구로 기여 가능한 좁고 명확한 문제는 무엇인가?
5. 기여 후보를 검증하려면 어떤 baseline과 evaluation이 필요한가?

## Literature Workflow

문헌 조사 작업은 네 단계로 수행한다.

1. Field Survey
   - 최근 2-3년 연구 흐름을 조사한다.
   - 결과는 `literature/README.md`의 Field Map / Trend Synthesis와 `literature/PAPER.md`의 Reading Queue에 반영한다.

2. Paper Intake
   - 읽을 가치가 있는 논문마다 paper folder를 만든다.
   - `01_metadata.md`부터 작성한다.
   - `literature/PAPER.md`의 Paper Registry를 갱신한다.

3. Paper Analysis
   - `02_paper_card.md`, `03_evaluation.md`, `04_insights.md`를 작성한다.
   - 방법보다 evaluation을 반드시 따로 본다.

4. Contribution Scan
   - 여러 논문을 비교해 기여 가능성을 찾는다.
   - 결과는 `literature/Contribution Candidates.md`에 기록한다.
   - 후보가 구체화되면 `literature/CAND-<number>.md`로 분리한다.

## Evidence Rules

- 우선순위 소스: 논문 PDF, arXiv, CVF Open Access, OpenReview, 공식 프로젝트 페이지, 공식 코드 저장소.
- 블로그/뉴스/요약글은 보조 자료로만 사용한다.
- 논문을 인용할 때는 제목, 연도, venue 또는 preprint 상태, 링크를 기록한다.
- "최근", "최신", "SOTA", "트렌드"라고 말하려면 검색 날짜 또는 확인 날짜를 함께 남긴다.
- 근거가 약한 판단은 `Inference`로 표시한다.
- 출처를 확인하지 못한 항목은 확정된 사실처럼 쓰지 않는다.

## Agent Task Recipes

### Recipe 1: Field Survey Pass

```md
3D Scene Graph 분야의 최근 2-3년 흐름을 조사해줘.

반드시 최신 정보를 확인하고, primary source 중심으로 근거를 남겨.
결과는 `literature/README.md`의 Field Map / Trend Synthesis와
`literature/PAPER.md`의 Paper Registry / Reading Queue를 갱신해.

특히 다음 축을 비교해:
- open-vocabulary / open-world 3DSG
- LLM/VLM + 3D scene reasoning
- robotics / embodied AI
- dynamic / online / 4D scene graph
- scene graph controlled 3D generation
- 3DGS / NeRF + semantic graph

각 trend는 최소 2개 이상의 논문 근거가 있을 때만 trend로 기록하고,
근거가 약하면 Cross-Paper Insights에 낮은 confidence로 남겨.
```

### Recipe 2: Paper Intake Pass

```md
다음 논문을 literature paper folder 형식으로 정리해줘: <paper title or link>

`literature/PAPER.md`의 Paper Registry에서 중복 여부를 확인한 뒤,
`literature/<year>_<venue-or-arxiv>_<short-title>/` 폴더를 만들고
`01_metadata.md`, `02_paper_card.md`, `03_evaluation.md`, `04_insights.md`를 작성해.

단순 요약이 아니라 problem setting, dataset, metric, limitation,
내 3D Scene Graph 석사 연구와의 연결점을 중심으로 정리해.

마지막에 `literature/PAPER.md`의 Paper Registry와 Reading Queue status를 갱신해.
```

### Recipe 3: Contribution Scan Pass

```md
지금까지 `literature/`에 쌓인 문헌 조사 내용을 바탕으로
석사 연구로 시도 가능한 contribution candidate를 3-5개 제안해줘.

각 candidate는 반드시 다음을 포함해야 해:
- 기존 한계
- 연구 질문
- 가능한 접근
- 필요한 dataset/benchmark
- baseline
- 실패 조건
- 3-6개월 안에 가능한 범위인지

결과는 `literature/Contribution Candidates.md`에 기록해.
후보 중 하나가 primary candidate 수준으로 구체화되면 `literature/CAND-<number>.md`를 만들어 세부 feasibility를 분리해.
논문 근거가 부족한 candidate는 확정하지 말고 추가 조사 필요로 표시해.
```

### Recipe 4: Trend-to-Thesis Narrowing

```md
현재 `literature/README.md`, `literature/PAPER.md`, `literature/Contribution Candidates.md`,
그리고 `literature/CAND-*.md`에 정리된 내용을 비교해서,
내가 석사 논문 주제로 좁힐 만한 방향을 ranking해줘.

ranking 기준:
- 연구 공백의 명확성
- 평가 가능성
- 구현 난이도
- 데이터 접근성
- 3D Scene Graph 분야와의 직접성
- 논문 contribution으로 말할 수 있는 정도

결과는 결론부터 쓰지 말고,
각 방향의 evidence와 risk를 비교한 뒤 마지막에 추천 순위를 줘.
```

## Quality Gate

문헌 조사 결과가 아래 기준을 만족하지 않으면 contribution candidate를 확정하지 않는다.

- 최소 6개 이상의 primary source를 확인했다.
- 각 주요 trend는 2개 이상의 근거 논문을 가진다.
- dataset, benchmark, metric이 확인되어 있다.
- "이 분야에서 중요해 보인다"가 아니라 "왜 아직 풀리지 않았는지"가 설명되어 있다.
- 3D Scene Graph가 꼭 필요한 문제인지 설명할 수 있다.
- 석사 연구 범위에서 구현/검증 가능한지 판단할 수 있다.
