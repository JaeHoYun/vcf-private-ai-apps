# 14 — 운영과 Day-2

[← 목차로](../README.md)

에이전트를 만들었다면 이제 운영입니다. 이 문서는 에이전트와 모델 워크로드를 어디에 배포하고, 무엇을 관측하며, 업그레이드 때 무엇을 조심하고, 어떤 알려진 이슈와 비용이 있는지를 다루고, 배치 워크로드의 운영, 모델 폐기 고지, 플랫폼 SLA, 서비스 퇴역까지 이어집니다. 용량과 TCO의 정밀 계산은 ⑥에, 플랫폼 Day-2 운영 전반은 ①에 위임하고, 여기서는 **서비스 워크로드와 직결된 운영**에 집중합니다.

> 본 문서의 수치와 동작은 VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0 기준입니다(작성 2026-06, 9.1.1과 3.0 GA 반영 2026-09). 2.1 환경에서는 "PAIS 3.0부터"로 표기한 대목만 건너뛰면 됩니다. 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

---

## 14.1 배포 토폴로지

- **실행 기반** — 모델 엔드포인트와 에이전트는 Supervisor의 vSphere Namespace에 프로비저닝된 **VKS 클러스터** 위에서 실행되며, ESXi 호스트의 GPU에 연결됩니다([01 1.4절](01-foundations.md)). PAIS 3.0은 VKr 1.34, ClusterClass builtin-generic-v3.5.0, NVIDIA GPU Operator 25.10.1(기본) 또는 26.3.1 기준으로 동작합니다(2.1은 VKr 1.33, 25.10.1).
- **두 경로** — 프로토타이핑과 노트북 작업은 **DLVM(Deep Learning VM)**, 프로덕션 모델 엔드포인트와 에이전트는 **VKS 클러스터**에 둡니다.
- **provider와 consumer(PAIS 3.0부터)** — 여러 사업부가 같은 기반 모델을 쓰는 조직은 모델 엔드포인트를 중앙 provider 인스턴스 한 곳에 두고, 에이전트는 각 사업부의 consumer 네임스페이스에서 그 공유 모델을 참조하는 토폴로지가 가능합니다. 에이전트, 지식베이스, MCP 도구, 세션은 consumer 쪽에 남으므로 에이전트 운영 단위는 그대로이고 GPU만 중앙으로 모입니다. 대신 provider 엔드포인트의 장애와 포화가 모든 consumer 에이전트에 번지므로, provider 쪽 레플리카와 쿼터를 에이전트 팀이 아니라 플랫폼 팀이 관리하는 책임 분리를 미리 정해 둡니다([① 06 6.4.1절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/06-production.md)).
- **고가용성** — 모델 엔드포인트는 서로 다른 워커 노드에 복제본 2 이상을 두기를 권장합니다. 단일 zone 배포에서는 VKS 컨트롤 플레인 등 핵심 구성요소가 단일 인스턴스로 배치돼 가용성 제약이 따릅니다.
- **사이징 위임** — 프로덕션 모델 서빙에 필요한 최소 GPU 호스트 수, GPU 메모리, 시스템 RAM 비율 등 용량 산정은 [⑥ VKS 클러스터 사이징](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/04-vks-cluster-sizing.md)에 위임합니다. 공식 디자인 문서도 구체 수치를 별도 사이징 자료로 위임합니다.
- **배포 실무 참조(공개)** — PAIS 활성화 절차와 Supervisor 네트워킹 구성은 공식 블로그가 실무 관점으로 다룹니다: [Activate VCF Private AI Services (2026-01)](https://blogs.vmware.com/cloud-foundation/2026/01/15/activate-vcf-private-ai-services/), [Navigating Supervisor Networking Stack (2026-06)](https://blogs.vmware.com/cloud-foundation/2026/06/11/deploying-vmware-cloud-foundation-private-ai-services-navigating-supervisor-networking-stack/).

## 14.2 관측성

PAIS는 2.1부터 추론, GPU, 에이전트를 아우르는 관측을 VCF Operations의 AI 지표 화면으로 제공하며, OpenTelemetry 기반 LLM 추적을 지원합니다([01 1.2.5절](01-foundations.md)).

**모델과 서비스 지표**

| 지표 | 의미 |
|------|------|
| Time to First Token (TTFT) | 첫 토큰까지 걸린 시간 — 체감 응답성 |
| Token throughput | 초당 토큰 처리량 — 처리 용량 |
| End-to-end latency | 요청 종단 지연 |
| Tokens per request | 요청당 토큰 수 — 비용과 길이 |
| Cache utilization | 캐시 활용도 |

**GPU 지표** — 사용률, 온도, 전력, 메모리 온도, 메모리 클럭 등.

**에이전트 추적** — OpenTelemetry LLM 추적으로 "사용자 ↔ 모델 ↔ 에이전트 ↔ 지식베이스" 상호작용을 따라갑니다. 백엔드는 Prometheus, Grafana를 씁니다. 추적이 보이지 않으면 구성 오류일 수 있습니다(14.4절).

> 평가([13](13-evaluation-guardrails.md))가 "출시 전 품질"이라면, 관측성은 "운영 중 품질과 비용"입니다. TTFT, 종단 지연, 토큰 처리량을 기준선으로 잡아 두고 이탈을 감시하십시오.

**PAIS 3.0에서 더해진 것** — 모델과 에이전트 메트릭을 PAIS UI에서 실시간 대시보드로 볼 수 있고, 조직이 배포한 Grafana에 올릴 예시 구성이 제공되며, 추론 백엔드 헬스가 실시간으로 노출되고, 트레이싱은 LLM 상호작용 전체로 넓어졌습니다. 에이전트 운영에 직접 닿는 변화는 두 가지입니다. 첫째, 원격 클라우드 모델을 쓰는 에이전트는 그 토큰 사용량이 별도로 추적되므로 실비와 반출 증빙으로 함께 남깁니다. 둘째, Prometheus 수집이 PAIS 관리 VKS 클러스터가 가용해진 뒤에 시작되도록 바뀌어 업그레이드 직후 기준선 지표가 비는 구간이 생기니, 그 구간의 알람은 유예합니다(14.3절). ([근거: PAIS 3.0 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html))

## 14.3 업그레이드 — 다운타임 주의

> **반드시 알아둘 운영 리스크** — PAIS 2.0.x → 2.1 업그레이드는 **모델 엔드포인트를 호스팅하는 VKS 클러스터를 삭제하고 재생성**합니다. 그 과정에서 노드가 재생성되고 모델을 다시 내려받는 동안 **다운타임**이 발생합니다. ([근거: PAIS 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-release-notes/vmware-private-ai-services-release-notes.html))

**2.1 → 3.0 업그레이드**는 릴리스 노트가 명시한 다운타임 범위가 다릅니다. 명시된 것은 **레플리카가 하나뿐인 모델 엔드포인트의 다운타임**이며, 2.0.x → 2.1 때와 같은 클러스터 삭제와 재생성은 문서에 없습니다(VKr가 1.33에서 1.34로 올라가므로 노드 재생성은 따를 수 있습니다). 그 밖에 세 가지가 에이전트 운영에 직접 닿습니다. 첫째, 에이전트 API의 `completion_role` 필드가 제거되고 non-chat completions가 deprecated되어 기존 클라이언트가 실패할 수 있습니다([08 8.8절](08-agent-builder.md)). 둘째, Prometheus 메트릭 수집이 VKS 클러스터가 가용해진 뒤에 시작되도록 바뀌어 업그레이드 직후 메트릭 공백이 생깁니다(14.2절). 셋째, vLLM이 0.20.0(CUDA 13.0)으로 올라가 GPU 드라이버 580 미만은 지원되지 않습니다([10 10.2절](10-models-serving.md)). ([근거: PAIS 3.0 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html))

대비:

- 3.0으로 올리기 전에 중요 에이전트가 쓰는 모델 엔드포인트는 레플리카를 2 이상으로 두고, `completion_role`과 non-chat completions를 쓰는 호출부를 먼저 고칩니다.
- 업그레이드 창(window)을 다운타임 전제로 계획하고 이해관계자에 사전 공지합니다.
- 모델 재다운로드 시간을 고려해 충분한 창을 잡습니다(모델 크기와 대역폭 의존).
- 업그레이드 후 모델 엔드포인트, 에이전트, 지식베이스, MCP 연결이 정상 복구되는지 검증 절차를 둡니다.
- 플랫폼 LCM 업그레이드 순서와 롤백 등 전반은 [① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md)의 10.1절 LCM 런북에 위임합니다.

## 14.4 알려진 이슈

릴리스별로 나눠 정리합니다([근거: PAIS 릴리스 노트 3.0, 2.1.2, 2.1](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html), 2026-09 기준, 변동 가능).

**PAIS 3.0에서 새로 보고된 이슈**

| 증상 | 방향 |
|------|------|
| UI로 PAIS를 활성화하면 API 토큰 발급이 켜지지 않음 | 활성화 후 설정에서 API 토큰 발급을 별도로 켬. 에이전트를 API 토큰으로 호출하거나 CLI를 쓰는 팀은 첫 배포 점검 항목에 포함 |
| UI로 활성화하면 로컬 계정의 기본 base URL을 설정할 수 없음 | 활성화 후 별도 설정 |

**PAIS 2.1에서 보고돼 3.0 시점에도 주의할 이슈**

| 증상 | 방향 |
|------|------|
| GPU 파드가 `CDI device injection failed`로 실패 | GPU Operator Helm 값 조정(CDI 관련 설정). 3.0 알려진 이슈 목록에는 없으나 GPU Operator 25.10.1을 그대로 쓰면 같은 조합이라 재현 가능성이 있음. 26.3.1을 고르면 별도 검증 |
| 업그레이드 후 모델 엔드포인트가 메모리 부족으로 실패 | 2.1에서 VRAM 요구량 증가, 3.0은 vLLM 0.20.0으로 다시 상향 — 자원 재산정([⑥ 컴퓨트와 메모리 사이징](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/03-compute-memory-sizing.md)) |
| OpenTelemetry LLM 추적이 표시되지 않음 | 추적 구성 점검(14.2절) |
| 네임스페이스당 모델 엔드포인트 복제본 상한(작성 시점 최대 15) | 복제본과 엔드포인트 수 설계 시 상한 고려 |

**2.1.2(2026-08-17)에서 해결된 것** — 로컬 레지스트리 미러와 5000 포트 충돌, 중간 CA 인증서 갱신 요구, CPU 추론에서 MCP 도구를 쓸 때 reasoning 모델 타임아웃, 패키지 다운로드 URL 오류. 2.1 라인을 유지한다면 최소 2.1.2로 올리는 것이 좋습니다.

증상→진단→조치 형태의 트러블슈팅 런북 패턴은 [① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md)의 10.2절 트러블슈팅 런북을 참조하십시오.

## 14.5 비용

에이전트 자체는 모델과 도구를 잇는 경량 계층이고, 비용의 대부분은 **모델 추론(GPU)** 에서 발생합니다.

- **GPU 라이선스** — vGPU(가상 GPU)를 쓰면 NVIDIA AI Enterprise(NVAIE) 라이선스가 필요합니다(호스트와 게스트 드라이버 모두). GPU 패스스루(DirectPath) 모드는 NVAIE가 불필요하나 vMotion 등 기능 제약이 따릅니다. 정확한 라이선스 과금 단위는 NVIDIA, Broadcom 라이선싱 자료로 확인하시기 바랍니다.
- **CPU 추론 대안** — 작은 모델, 저부하 작업은 llama.cpp CPU 추론으로 GPU 비용을 줄이는 선택지가 있습니다([10 10.2절](10-models-serving.md)). 성능 트레이드오프를 평가로 확인하십시오.
- **토큰과 단계 비용** — 에이전트는 도구 호출과 재시도로 단계가 늘어 단일 호출보다 토큰을 많이 씁니다. 종료 조건([13 13.4절](13-evaluation-guardrails.md))과 세션 요약([03 3.4절](03-design-patterns.md))으로 토큰 폭증을 통제하십시오.
- **TCO 위임** — GPU, 노드, 스토리지 비용의 정밀 산정과 자원 활용도 개선은 [⑥ TCO와 비용 모델](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/07-tco-cost-model.md)에 위임합니다.

## 14.6 운영 점검 리듬

에이전트 워크로드에 맞춘 가벼운 점검 리듬을 제안합니다(플랫폼 전반 리듬은 ①).

- **일상** — TTFT, 종단 지연, 오류율, GPU 사용률 기준선 이탈 감시, 에이전트 추적 표본 점검.
- **주기** — 평가 묶음 회귀([13](13-evaluation-guardrails.md)) 재실행, MCP 도구와 자격증명 유효성 점검, 토큰과 비용 추세 검토.
- **변경 시** — 모델, 지시문, 도구 변경 후 평가와 관측 기준선 갱신, 업그레이드는 다운타임 창 계획(14.3절).

## 14.7 백업과 복구

에이전트 서비스는 stateless가 아닙니다 — 여러 stateful 자산이 흩어져 있어, 무엇을 백업하는지부터 정리해야 합니다.

| 자산 | 저장 위치 | 백업과 복구 |
|------|-----------|-----------|
| 지식베이스 벡터와 데이터 | pgvector(외부 PostgreSQL) | PostgreSQL 백업([②](https://github.com/JaeHoYun/vcf-private-ai/tree/main/02-vectordb)) |
| 모델 아티팩트 | Model Gallery(Harbor) | 레지스트리 백업 또는 Artifact Mirroring Tool로 재미러([10 10.4절](10-models-serving.md)) |
| 에이전트와 도구 구성 | Agent Builder 구성 코드 | 형상관리(Git)에 보관과 재현([08 8.8절](08-agent-builder.md)) |
| MCP 서버 등록과 승인 | Tool Gallery 등록 정보 | 등록 절차를 문서화해 재등록 가능하게([09 9.4절](09-mcp-tools.md)) |
| 세션 상태 | 배포 단위 확인 필요 | 영속성과 복구 가능 여부는 공식 문서로 확인([01 1.4절](01-foundations.md)) |

- **복구 우선순위** — 구성(Git)과 모델(재미러)은 재현이 쉽고, **지식베이스 데이터는 원본 재인덱싱 비용이 크므로** 백업 가치가 가장 높습니다. PAIS 3.0부터 지식베이스와 인덱스를 복제(clone)할 수 있으므로, 에이전트의 지시문이나 임베딩 모델을 바꾸는 변경은 복제본에 연결한 스테이징 에이전트에서 먼저 검증하고 승격하는 흐름이 가능합니다.
- **DR 위임** — 멀티사이트 재해복구, RTO/RPO, 백업 주기 등 플랫폼 DR 정책은 [① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md)의 10.3절 백업과 복구에 위임합니다. 이 가이드의 몫은 **무엇이 stateful한지 식별**해 DR 범위에서 빠뜨리지 않게 하는 것입니다.

## 14.8 스케일, 알람, SLO, 온콜

14.2절이 무엇을 관측하는지였다면, 여기서는 그 위에 임계, 목표, 대응을 더합니다.

- **스케일** — 모델 엔드포인트는 복제본으로 가용성과 처리량을 늘리되 네임스페이스당 상한이 있습니다(14.4절). 에이전트는 도구 호출 루프와 동시 세션 급증으로 부하가 갑자기 치솟으므로, 복제본을 수동으로 늘릴지 부하 기반 자동 확장이 되는지는 공식 문서로 확인하십시오. 토큰 폭증 통제는 종료 조건과 세션 요약으로 합니다(14.5절).
- **알람** — 14.2절 기준선 위에 임계를 정합니다 — TTFT, 종단 지연 P95(95 백분위), 오류율, GPU 포화, 복제본 가용성. 1차로는 VCF Operations 알람으로 설정하고, 외부 온콜 도구 연동은 앱, 외부 계층입니다.
- **목표 수준(SLO)** — 가용성, TTFT, 오류율 같은 지표에 목표값을 정해 둡니다. 기준선을 실측한 뒤 현실적인 값으로 잡고, 이탈이 잦으면 용량([⑥ 용량 계획과 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/06-capacity-planning.md))이나 설계를 재검토합니다.
- **온콜과 에스컬레이션** — 1차 대응은 알려진 이슈와 트러블슈팅(14.4절)으로, 해소되지 않으면 플랫폼 운영([① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md) 10.4절)과 보안([⑤](https://github.com/JaeHoYun/vcf-private-ai/tree/main/05-security))으로 에스컬레이션합니다. 플랫폼이 약속하는 응답 시간과 통지 기간은 14.11절의 SLA 항목으로 온보딩 때 받아 둡니다.

## 14.9 배치 워크로드 운영

[03 3.7절](03-design-patterns.md)의 배치 파이프라인은 설계였고, 여기서는 그것을 운영에 올릴 때의 규율입니다. PAIS Model Runtime은 온라인 OpenAI 호환 엔드포인트만 공식 제공하므로, 배치도 같은 종류의 엔드포인트를 호출합니다. 실행 경로의 선택지(같은 엔드포인트 공유, 배치 전용 엔드포인트, PAIS 밖의 자가 오프라인 배치)와 플랫폼 쪽 우선순위 수단은 [③ 07 7.9절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/03-serving-api/docs/07-observability-ops.md)이 정본이고, 앱 팀이 운영에서 지킬 것은 다음입니다.

- **실행 단위** — 배치 드라이버는 VKS의 Job 또는 CronJob으로 돌리고, 처리 완료한 문서 ID를 체크포인트로 남겨 재실행 시 이어서 돌립니다. 실패한 문서는 격리 큐로 보내 전체를 멈추지 않습니다. 문서 단위 멱등 쓰기([07 7.4절](07-integration-write-design.md))가 전제입니다.
- **온라인 서비스 보호** — 배치 전용 엔드포인트가 없고 대화형 서비스와 엔드포인트를 나눠 쓴다면, 드라이버의 동시성을 낮게 고정하고 야간 윈도우에 몰며, 대화형 서비스의 첫 토큰 지연 P95가 기준선을 넘으면 드라이버가 스스로 동시성을 줄이는 백프레셔를 둡니다. 배치가 온라인을 잡아먹는 것은 가장 흔한 사고이고, 이를 막는 가장 확실한 수단은 배치 전용 엔드포인트나 네임스페이스로 GPU를 분리하는 것입니다([⑥ 06 용량 계획](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/06-capacity-planning.md)).
- **관측** — 시간당 처리 문서 수, 건당 입력과 출력 토큰, 실패율, 큐 길이와 예상 완료 시각을 지표로 두고, 야간 윈도우 안에 끝나지 않으면 알람합니다. 배치의 토큰 사용량은 온라인과 분리해 집계해야 쇼백이 왜곡되지 않습니다([05 5.4절](05-platform-consumption.md)).
- **품질** — 사람이 결과를 하나씩 보지 않으므로, 샘플 검수 비율(예: 1%)과 스키마 검증 실패율의 알람 임계를 파이프라인에 넣습니다. 골든셋 회귀([13 13.7절](13-evaluation-guardrails.md))는 배치 프롬프트에도 같은 규칙으로 적용합니다.
- **비용** — 배치는 야간 유휴 GPU를 채울 때 토큰당 비용이 가장 낮습니다. 온라인 피크 시간에 돌리는 배치는 같은 작업을 몇 배 비싸게 하는 셈이며, 단가 산식은 [⑥ 07 7.7절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/07-tco-cost-model.md)에 있습니다.

## 14.10 모델 폐기 고지 정책

플랫폼 팀이 모델 엔드포인트를 내리거나 리비전을 바꾸는 일은 소비하는 서비스에는 API 변경과 같습니다. 폐기의 트리거는 여럿입니다. 엔진 업그레이드로 지원에서 빠지는 아키텍처, 새 리비전으로의 교체, 라이선스 변경([10 10.8절](10-models-serving.md)), 보안 이슈, 공유 모델 provider의 결정. 어느 경우든 소비 앱이 준비할 시간을 정책으로 보장해야 합니다.

| 정책 항목 | 정할 것 | 기본값의 예 |
|-----------|---------|-------------|
| 고지 기간 | 프로덕션 소비 서비스가 있는 모델을 내리기 전 최소 고지 기간 | 프로덕션 90일, 파일럿 30일. 보안 이슈는 예외로 즉시 고지와 단축 |
| 병행 유지 기간 | 새 리비전 배포 뒤 구 리비전을 함께 서빙하는 기간 | 고지 기간과 같게. 소비 앱이 회귀를 돌리고 옮길 시간 |
| 마이그레이션 창 | 소비 앱이 옮겨야 하는 기한과 미이행 시 조치 | 창 종료 뒤 구 엔드포인트 차단, 예외는 심사 |
| 고지 채널 | 어디에 어떻게 알리는가 | 서비스 레지스트리의 소비 목록으로 대상 식별, 카탈로그 공지와 담당자 통지 |
| 영향 파악 | 어느 서비스가 그 모델을 쓰는지 | 릴리스 매니페스트([13 13.9절](13-evaluation-guardrails.md))의 모델 필드로 역추적 |
| 임베딩 모델 | 임베딩 교체는 전면 재인덱싱을 수반 | 고지 기간을 더 길게, 재인덱싱 비용은 플랫폼과 앱이 사전 합의([④ 07 7.6절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/04-rag/docs/07-production-operations.md)) |

공유 모델(PAIS 3.0부터)은 provider가 이 정책의 소유자이고, consumer는 매니페스트로 자기 영향을 파악합니다(14.1절). 버전 전환의 기술 절차(섀도와 카나리, 회귀, 롤백 경로)는 [③ 07 7.5절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/03-serving-api/docs/07-observability-ops.md)과 [① 06 6.7절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/06-production.md)에 있으며, 이 절은 그 절차에 "언제 알리고 얼마나 기다리나"를 더한 것입니다.

## 14.11 플랫폼 SLA와 에스컬레이션

서비스의 목표 수준(14.8절)은 플랫폼이 약속하는 수준 위에서만 정할 수 있습니다. 온보딩([05 5.1절](05-platform-consumption.md)) 때 다음 항목을 문서로 받아 두고, 서비스 SLO는 그 안에서 잡습니다.

| SLA 항목 | 앱 팀이 확인할 것 | 관련 절 |
|----------|-------------------|---------|
| 모델 엔드포인트 가용성 | 월 가용성 목표, 복제본 수, 단일 zone 제약 | 14.1절 |
| 지연 목표 | TTFT와 종단 지연의 P95 목표와 측정 조건(동시성 기준) | [⑥ A2.3](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/appendix/A2-inputs-and-defaults.md) |
| 쿼터 증설 리드타임 | GPU와 복제본 증설 요청이 반영되기까지의 시간 | [05 5.1절](05-platform-consumption.md) |
| 업그레이드 사전 통지 | 다운타임을 수반하는 업그레이드의 통지 기간과 창 | 14.3절 |
| 모델 폐기 고지 | 14.10절의 고지 기간과 병행 유지 기간 | 14.10절 |
| 장애 통지 | 플랫폼 장애 시 통지 채널과 시간, 상태 페이지 | 14.8절 |
| 지원 시간과 온콜 | 플랫폼 팀의 대응 시간대와 심각도별 응답 목표 | 아래 에스컬레이션 |
| 지식베이스와 토큰 발급 | 발급 요청의 리드타임 | [05 5.1절](05-platform-consumption.md) |
| 원격 모델 | 원격 클라우드 모델은 외부 제공자의 SLA에 종속되며 플랫폼이 보증하지 않음 | [10 10.1절](10-models-serving.md) |

에스컬레이션은 세 단계로 둡니다. 1차는 서비스 온콜이 알려진 이슈(14.4절)와 서비스 자체의 킬스위치와 롤백으로 대응하고, 2차는 플랫폼 운영([① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md) 10.4절)이 엔드포인트와 클러스터를 보며, 3차는 보안([⑤ 07 7.3절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/07-audit-compliance.md))과 벤더 지원입니다. 각 단계의 연락처와 심각도 정의를 온보딩 문서에 적어 두고, 사고가 보안 사고로 판정되면 1차에서 곧바로 3차로 올립니다.

## 14.12 서비스 퇴역

쓰지 않는 서비스를 그대로 두면 소유자 없는 에이전트와 서비스 계정, 갱신되지 않는 지식베이스, 보존 기간이 지난 대화 데이터가 남습니다([⑤ 08 8.1절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/08-agent-governance.md)의 이탈 에이전트). 퇴역은 다음 순서로 진행하며, 각 단계의 완료를 레지스트리에 기록합니다.

1. **고지** — 사용자와 이해관계자에게 퇴역 일정과 대체 경로를 알립니다. 대외 서비스라면 고지 의무의 적용 범위를 법무와 확인합니다.
2. **트래픽 차단** — BFF에서 요청을 막고, 1계층 게이트웨이의 키와 PAIS API 토큰을 폐기합니다.
3. **에이전트 비활성화와 신원 회수** — 에이전트를 비활성화하고, 서비스 계정과 MCP 서버 인증 토큰을 폐기하며, Tool Gallery의 도구 승인을 해제합니다. 사내 MCP 서버가 이 서비스 전용이었다면 서버도 내립니다([09 9.8절](09-mcp-tools.md)).
4. **데이터 처리** — 지식베이스와 인덱스를 삭제하거나 다른 서비스로 이관하고, 보호 문서의 복호화 사본을 파기하며([06 6.6절](06-data-onboarding.md)), 대화 데이터는 보존 정책대로 삭제를 전파합니다([11 11.7절](11-app-integration-ux.md), [⑤ 05 5.5절, 5.10절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/05-data-governance.md)). 삭제는 원본, 청크, 임베딩, 캐시, 로그까지입니다.
5. **모델 엔드포인트 정리** — 전용 엔드포인트는 내리고 GPU를 반납하며, 공유 모델은 provider의 소비 목록에서 이 서비스를 뺍니다.
6. **관측과 알람 정리** — 대시보드, 알람, 온콜 라우팅에서 서비스를 제거해 유령 알람을 막습니다.
7. **기록 보존** — 감사 로그, 게이트 기록, 릴리스 매니페스트, 출시 심사 패키지는 보존 기간 동안 남깁니다([⑤ 07 7.1.3절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/07-audit-compliance.md)). 레지스트리의 상태를 퇴역으로 바꾸고 소유자와 퇴역일을 적습니다.
8. **쿼터와 비용 반납** — 네임스페이스 쿼터를 줄이거나 반납하고 쇼백 집계에서 서비스를 종료 처리합니다.

퇴역 절차를 미리 정해 두면 파일럿을 끝내는 것도 쉬워집니다. 파일럿의 종료가 곧 이 절차의 축소판이며, 종료하지 못한 파일럿이 쌓이는 것이 섀도 AI(조직이 존재를 모르는 채 쓰이는 AI)의 흔한 출처입니다. 이미 쌓인 섀도 AI를 찾는 신호는 [⑤ 07 7.2.3절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/07-audit-compliance.md)에, 찾은 뒤 등록하고 등급을 판정해 처분하는 순서는 [AX 방법론 07 7.6절](https://github.com/JaeHoYun/enterprise-ax-methodology/blob/main/docs/07-organization-and-control.md)에 있습니다.

서비스 수명주기의 기술 설명은 여기까지입니다. 이 역량을 어디에 써야 성과가 나는지의 유스케이스 선별과 위험 등급 판정은 기획 편 [02 어디에 쓰나](02-use-cases.md)에 있고, 용어와 참조 링크는 [A1 부록](../appendix/A1-reference.md)에, 결정을 적어 두는 워크시트는 [A2 워크시트](../appendix/A2-worksheets.md)에 정리했습니다.

---
[← 이전: 13 평가와 출시 게이트](13-evaluation-guardrails.md) | [목차](../README.md) | [다음: A1 부록 →](../appendix/A1-reference.md)
