# External Provenance Request

## Purpose

`test_benchmark_source_resolution`이 blocked였기 때문에, 3DSSG relation test
benchmark를 열기 위해 필요한 외부 증빙 요청 packet을 만들었다.

이 단계의 목적은 metric runner 실행이 아니라 다음을 확인하기 위한 문의/증빙
자료를 고정하는 것이다.

```text
official evaluation server or independent 3DSSG relation-test label provenance
```

## Result

```text
artifact_root = artifacts/compatibility_dataset_v3_test_benchmark_external_provenance_request_after_source_resolution/
status = h002_test_benchmark_external_provenance_request_after_source_resolution_ready
selected_path = external_request_packet_ready_keep_test_benchmark_blocked
validation_errors = 0
next_todo = compatibility_dataset_v3_test_benchmark_external_response_ingestion_after_request
```

## Generated Packet

| File | Role |
| --- | --- |
| `request_packet.md` | maintainer/contact request draft |
| `request_questions.csv` | exact questions and what each answer unblocks |
| `source_evidence.csv` | official/local source evidence used in the request |
| `readiness_matrix.csv` | checkpoint/source-prediction readiness vs relation-GT readiness |
| `next_contract.json` | required response/provenance before test benchmark |

## Decision

| 항목 | 판단 |
| --- | --- |
| request packet ready | true |
| test benchmark execution allowed | false |
| checkpoint reproduction sufficient | false |
| prediction-only test scan export sufficient | false |
| validation table position | appendix / secondary analysis only |

## Interpretation

VL-SAT checkpoint route와 Open3DSG test execution route가 존재하더라도, 이것만으로
test `Recall@K`를 계산할 수 없다. Checkpoint는 prediction을 만들 수 있지만,
GT를 만들지는 못한다.

H002 test benchmark가 열리려면 다음 중 하나가 필요하다.

- official hidden evaluation server.
- official/independent `relationships_test.json` provenance.
- official statement that validation split is the intended reporting split.

## Next

다음 단계는 `external_response_ingestion`이다. 외부 응답 또는 공식 문서 증빙이
들어오기 전까지 test benchmark metric runner를 실행하지 않는다.

