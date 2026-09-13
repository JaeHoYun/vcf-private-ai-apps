# 10 — 모델과 서빙

[← 목차로](../README.md)

에이전트는 Model Runtime이 서빙하는 모델 위에서 동작합니다. 이 문서는 모델을 어떻게 서빙하고(엔진과 엔드포인트), 어디에 보관하며(Model Gallery), 에어갭 환경에 어떻게 반입하고(Artifact Mirroring Tool), CLI로 어떻게 다루는지를 다룹니다. 서빙 자체의 깊은 설계는 ③에 위임하고, 여기서는 **에이전트 관점에서 알아야 할 만큼**을 정리합니다.

> 본 문서의 수치와 동작은 VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0 기준입니다(작성 2026-06, 9.1.1과 3.0 GA 반영 2026-09). 2.1 환경에서는 "PAIS 3.0부터"로 표기한 대목만 건너뛰면 됩니다. 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

---

## 10.1 Model Runtime — 서빙 계층

Model Runtime은 completion(생성)과 embedding(임베딩) 모델을 추론 엔진으로 실행해 **OpenAI 호환 API**(`/chat/completions`, `/completions`, `/embeddings`)로 노출합니다. 엔드포인트는 ML API Gateway 뒤에 위치하며, 기본 경로는 `https://<PAIS FQDN>/api/v1/compatibility/openai/v1/...`입니다([근거: Private AI Services API](https://developer.broadcom.com/xapis/vmware-private-ai-service-api/latest/), 호출 예시는 [08 8.8절, 8.10절](08-agent-builder.md)).

- **에이전트와의 관계** — 에이전트는 이 completion 엔드포인트를 가져다 세션, 검색, 도구 호출을 더해 씁니다([08 8.2절](08-agent-builder.md)). 모델 엔드포인트는 stateless이고, 에이전트가 그 위 stateful 계층입니다([01 1.4절](01-foundations.md)).
- **임베딩** — 지식베이스 인덱싱과 질의에 쓰는 임베딩도 Model Runtime이 서빙합니다(상세는 [④](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag)).
- **고가용성** — 모델 엔드포인트는 서로 다른 워커 노드에 복제본을 두는 구성(권장 복제본 2 이상)으로 가용성을 확보합니다. 단, 네임스페이스당 모델 엔드포인트 복제본 수에는 상한이 있습니다([14 14.4절](14-operations.md) 알려진 이슈).
- **모델이 도는 자리 세 가지(PAIS 3.0부터)** — 에이전트가 고르는 completion 엔드포인트는 이제 세 종류 중 하나입니다. 이 네임스페이스의 GPU에서 도는 **로컬 모델**, 다른 PAIS 인스턴스나 네임스페이스(provider)가 서빙하는 **공유 모델**, Google Gemini나 OpenAI 호환 서비스에 연결된 **원격 클라우드 모델**입니다. Agent Builder 드롭다운에서는 셋이 같은 엔드포인트로 보이지만, 공유 모델은 provider 쪽 레플리카와 쿼터가 응답 지연을 정하고, 원격 모델은 프롬프트가 사외로 나가므로 지식베이스 검색 결과를 컨텍스트로 넣는 에이전트라면 어떤 데이터가 외부로 가는지 먼저 정해야 합니다([⑤ 데이터 거버넌스](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/05-data-governance.md)). 연결 구조는 [③ 02 2.5.1절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/03-serving-api/docs/02-serving-api-architecture.md)에 있습니다.

## 10.2 서빙 엔진

PAIS 3.0 Model Runtime이 지원하는 추론 엔진과 버전입니다([근거: PAIS 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html)).

| 엔진 | 3.0 | 2.1 | 용도 |
|------|-----|-----|------|
| vLLM | 0.20.0 | 0.11.2 | 생성 + 임베딩. 0.20.0은 CUDA 13.0이 기본이라 GPU 드라이버 580 이상이 필요 |
| llama.cpp | b9309 | b7739 | 생성 + 임베딩 (**CPU 추론**) |
| Infinity | 0.0.76 | 0.0.76 | 임베딩 전용 |

- **llama.cpp = 2.1 신규** — GPU 없이 CPU에서 추론하는 경로가 2.1에서 추가됐습니다. 작은 모델, 저부하 보조 작업이나 GPU가 부족한 환경에서 선택지가 됩니다(성능과 비용 트레이드오프는 [14](14-operations.md), [⑥ TCO와 비용 모델](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/07-tco-cost-model.md)). CPU 추론에서 MCP 도구를 함께 쓸 때 reasoning 모델이 타임아웃되던 문제는 2.1.2에서 수정됐습니다.
- **버전 주의** — 3.0으로 올라갈 때 vLLM이 0.11.2에서 0.20.0으로 크게 올라가므로, 모델 엔드포인트의 VRAM 요구량과 양자화 포맷 지원을 다시 확인하십시오.
- **엔진 버전 오버라이드** — 모델 엔드포인트 정의(YAML)의 `engineImage`로 엔진 이미지를 지정할 수 있습니다.
- **버전 정본** — 엔진 버전의 단일 기준은 [README 기반 버전표](../README.md#기반-버전-source-of-truth)입니다. 본문과 용어집의 버전 표기는 그 요약이며, 갱신은 README 표를 기준으로 맞춥니다.

## 10.3 Model Gallery — 모델 저장소

**Model Gallery**는 모델 아티팩트의 중앙 저장소로, **Harbor**(OCI 호환 컨테이너 레지스트리)를 기반으로 Supervisor 서비스로 배포됩니다([근거: Private AI Services 상세 디자인](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/design/design-library/private-ai-platform-detailed-design/private-ai-services.html)). 모델을 프로젝트와 리포지토리 단위로 보관하며, 리포지토리별로 쓰기 권한을 관리합니다. (CLI, 일부 인자에서는 내부적으로 `model-store`라는 용어도 함께 쓰입니다.)

모델 반입 경로:

- **NVIDIA NIM** — JupyterLab 노트북으로 NIM 모델을 Harbor로 내려받아 관리형 자산으로 만듭니다.
- **자체 모델** — `vcf pais models push`로 임의 모델 리비전을 저장소에 올립니다(10.5절).
- **Hugging Face 등 공개 모델** — 사설 레지스트리에 보관해 반입할 수 있습니다. 구체 절차는 공식 문서로 확인하시기 바랍니다.

> **경계 — 파인튜닝은 PAIS 밖** — Model Gallery는 모델을 **보관하고 반입**하지, 학습하지 않습니다. LoRA, 전체 파인튜닝 같은 도메인 적응 학습은 PAIS 범위 밖이며, 외부 학습 환경(DLVM, 전용 학습 파이프라인)에서 수행한 뒤 산출 모델을 `vcf pais models push`로 Gallery에 반입합니다(10.5절). 학습용 GPU, 노드 사이징은 [⑥ GPU 사이징](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/docs/02-gpu-sizing.md), [①](https://github.com/JaeHoYun/vcf-private-ai/tree/main/01-infra)에 위임합니다.

## 10.4 에어갭 반입 — Artifact Mirroring Tool

PAIS는 **Artifact Mirroring Tool** 로 에어갭(외부망 차단) 환경에 모델과 아티팩트를 반입하는 경로를 제공합니다(PAIS 2.1에서 도입). 인터넷에 연결된 준비 환경에서 컨테이너 이미지, Helm 차트, 모델 파일을 미러링한 뒤, 격리망으로 옮겨 설치하고 운영합니다. [PAIS 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-release-notes/vmware-private-ai-services-release-notes.html)는 NVIDIA GPU 모델 엔드포인트와 **에이전트를 포함한** 전체 Private AI 기능을 에어갭에서 운영할 수 있다고 명시합니다.

> **CLI 주의** — Artifact Mirroring Tool은 pais CLI 플러그인의 **`vcf pais amt pull` / `vcf pais amt push`** 명령으로 수행합니다(`vcf plugin install pais`로 설치). 단 이 `vcf pais amt` 명령은 **VCF CLI 명령 레퍼런스 페이지에는 누락**되어 있고(거기에는 `vcf pais models`만 표기, 10.5절), PAIF **Disconnected Environment 배포 문서**에만 명시돼 있으니 해당 문서를 1차 근거로 삼으십시오. 에어갭 절차는 릴리스마다 달라질 수 있으니 적용 직전 공식 문서와 KB로 재확인하십시오. ([근거: Upload the Private AI Services Components to a Disconnected Environment](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-foundation-9-x/deploying-private-ai-foundation-with-nvidia/installing-and-configuring-private-ai-services/upload-the-private-ai-services-components-to-a-disconnected-environment.html))

## 10.5 CLI — `vcf pais models`

작성 시점 공식 CLI 레퍼런스에서 PAIS 관련 명령은 **`vcf pais models` 그룹 하나**이며, 하위 명령은 다음 여섯입니다.

| 명령 | 용도 |
|------|------|
| `vcf pais models list` | 모델 목록 |
| `vcf pais models list-revisions` | 모델 리비전 목록 |
| `vcf pais models pull` | 모델 내려받기 |
| `vcf pais models push` | 모델 올리기 |
| `vcf pais models delete` | 모델 삭제 |
| `vcf pais models delete-revision` | 리비전 삭제 |

예: `vcf pais models pull --modelStore <레지스트리>/<리포지토리> --modelName <모델> --tag <태그>`

위 표는 **VCF CLI 명령 레퍼런스 페이지** 기준입니다. 에어갭 반입용 `vcf pais amt`(pull/push)는 이 레퍼런스에 빠져 있으나 실재하는 명령입니다 — 근거와 주의는 10.4절에 정리했습니다. `vcf pais agents` 같은 하위 명령은 없으며, 에이전트, MCP, 지식베이스 구성은 주로 UI(Agent Builder, VCF Automation)와 REST API로 다룹니다.

CLI의 형태에 대해 한 가지 정리해 둡니다. 단독 실행 파일 형태의 `pais` CLI는 DLVM 9.1 이미지에서 제거됐고, 지금 쓰는 것은 VCF Consumption CLI의 `pais` 플러그인입니다. DLVM 9.1.1 이미지에는 VCF CLI 9.1.0과 확장된 플러그인, helm, kubectl vSphere 플러그인이 함께 들어 있습니다. PAIS 3.0부터는 이 CLI로 PAIS 관리 클러스터의 kubeconfig를 받는 절차와 지원 번들 수집이 간단해졌습니다. VCF Automation 네임스페이스에서 CLI 명령을 실행하려면 3.0부터 API 토큰이 필요합니다([08 8.9절](08-agent-builder.md)).

## 10.6 에이전트 관점의 모델 선택

에이전트가 쓸 모델을 고를 때의 기준을 한데 정리합니다([08 8.2절](08-agent-builder.md)와 연결).

- **도구 호출 지원** — 도구를 적극적으로 쓰는 에이전트라면 네이티브 도구 호출 지원 모델을 우선합니다. 미지원 모델로도 구성은 가능하나 별도 설정이 필요합니다([03 3.4절](03-design-patterns.md)).
- **컨텍스트 길이** — 긴 대화 이력, 검색 결과, 도구 응답을 담을 만큼 충분해야 합니다.
- **비용과 지연** — 큰 모델은 TTFT, 토큰 비용이 큽니다. 보조 작업은 작은 모델(또는 CPU 추론)으로 분리하는 멀티 모델 구성을 고려하십시오.
- **임베딩 모델** — 지식베이스를 쓰면 별도 임베딩 모델이 필요합니다. 인덱싱과 질의에 같은 임베딩 모델을 써야 검색이 일관됩니다([④](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag)).
- **공유 모델을 먼저 찾는다(PAIS 3.0부터)** — 조직에 중앙 provider 인스턴스가 있다면, 사내 표준 LLM과 임베딩 모델은 자기 네임스페이스에 새로 띄우지 말고 공유 모델을 참조하는 편이 GPU와 운영 부담을 줄입니다. 전용 파인튜닝 모델이나 규제로 분리해야 하는 데이터를 다루는 에이전트만 로컬 모델을 씁니다. 원격 클라우드 모델은 반출 정책이 허용하는 유스케이스에 한정합니다.
- **한국어와 라이선스는 별도 절에서** — 한국어 서비스라면 10.7절의 선정 기준을, 어떤 모델이든 사내 서비스에 올리기 전에는 10.8절의 라이선스 심사를 거칩니다.

## 10.7 한국어 모델과 임베딩 선정 기준

한국어 서비스는 모델 선택의 기준이 두 군데서 달라집니다. 같은 내용이라도 토큰 수가 늘어나 비용과 컨텍스트 예산이 달라지고, 영어 벤치마크 점수가 한국어 품질을 보장하지 않습니다. 이 절은 특정 모델을 추천하지 않습니다. 후보는 분기마다 바뀌므로, 후보를 거르는 기준과 실측 절차만 고정합니다.

**토큰 팽창 계수** — 한국어는 토크나이저에 따라 한 글자가 한 토큰이 되기도 하고 세 글자가 한 토큰이 되기도 합니다([③ 00 서빙 입문](https://github.com/JaeHoYun/vcf-private-ai/blob/main/03-serving-api/docs/00-serving-primer.md)). 같은 문서를 영어로 쓴 것보다 토큰이 많이 나오는 정도를 이 가이드는 **토큰 팽창 계수**라고 부릅니다. 계수는 모델마다 다르므로 후보 모델의 토크나이저로 자사 대표 문서 100건을 직접 세어 구합니다. 이 값은 세 곳의 입력이 됩니다. 컨텍스트 예산(검색 청크를 몇 개 넣을 수 있는가, [03 3.8절](03-design-patterns.md)), 사이징(KV 캐시와 동시성, [⑥ A2.2](https://github.com/JaeHoYun/vcf-private-ai/blob/main/06-sizing-cost/appendix/A2-inputs-and-defaults.md)), 토큰 예산과 쇼백([05 5.4절](05-platform-consumption.md))입니다. 계수가 큰 모델은 같은 GPU에서 처리량이 그만큼 줄어드니, 벤치마크 점수가 조금 높아도 총비용에서 뒤집힐 수 있습니다.

**생성 모델의 선정 기준**

| 기준 | 무엇을 보나 | 어떻게 확인하나 |
|------|-------------|-----------------|
| 한국어 능력 | 한국어 사전학습 비중, 한국어 공개 벤치마크 점수 | KMMLU, KoBEST, HAE-RAE Bench 같은 공개 벤치마크로 1차 스크리닝[^kmmlu][^kobest] |
| 자사 태스크 적합성 | 실제 질문과 문서에서의 답 품질, 존댓말과 문체 일관성, 형식 준수(JSON, 표) | 골든셋으로 실측([13 13.7절](13-evaluation-guardrails.md)). 공개 벤치마크는 후보를 거르는 용도이고 최종 판단은 자사 골든셋 |
| 토큰 팽창 계수 | 위 절차로 구한 값 | 후보 간 상대 비교, 비용 산식에 반영 |
| 도구 호출 | 네이티브 도구 호출 지원과 한국어 지시문에서의 인자 정확도 | 도구 선택 정확도 측정([13 13.3절](13-evaluation-guardrails.md)) |
| 서빙 적합성 | vLLM 0.20.0 또는 llama.cpp에서 지원하는 아키텍처와 양자화 포맷, VRAM 요구량 | 10.2절의 엔진 지원 범위, 스테이징 엔드포인트에서 실측 |
| 라이선스 | 상업 이용 조건과 파생 조건 | 10.8절 체크리스트 |
| 한국어 특화 모델 대 다국어 모델 | 한국어 특화 모델은 토큰 효율과 문체에서 유리할 수 있으나, 도구 호출과 긴 컨텍스트와 엔진 지원에서 뒤질 수 있음 | 두 부류에서 최소 하나씩 후보를 두고 같은 골든셋으로 비교 |

**임베딩과 리랭커의 선정 기준** — 지식베이스의 검색 품질은 생성 모델보다 임베딩이 먼저 정합니다.

| 기준 | 무엇을 보나 | 비고 |
|------|-------------|------|
| 한국어 검색 품질 | 다국어 임베딩 벤치마크의 한국어 태스크 점수, 자사 문서로 만든 검색 골든셋(질문과 정답 청크)의 적중률 | MTEB 계열 벤치마크로 스크리닝[^mteb], 최종은 자사 검색 골든셋 |
| 최대 입력 길이 | 512 토큰급과 8K 토큰급의 차이. 한국어는 토큰 팽창으로 청크가 잘릴 수 있음 | 청크 크기([④ 02](https://github.com/JaeHoYun/vcf-private-ai/blob/main/04-rag/docs/02-ingestion-indexing.md))와 함께 정함 |
| 차원 | 벡터 차원이 클수록 저장과 검색 비용 증가 | pgvector 인덱스 크기와 질의 지연에 반영([②](https://github.com/JaeHoYun/vcf-private-ai/tree/main/02-vectordb)) |
| 리랭커 | 1차 검색 결과를 재정렬하는 교차 인코더의 한국어 지원 여부 | 있으면 검색 정밀도가 크게 오르나 지연이 추가됨 |
| 엔진 호환 | Infinity 또는 vLLM 임베딩 서빙 지원 | 10.2절 |
| 교체 비용 | 임베딩 모델을 바꾸면 전면 재인덱싱 | 처음 고를 때 신중히, 교체 계획은 [④ 07 7.6절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/04-rag/docs/07-production-operations.md)과 [14 14.7절](14-operations.md) |

인덱싱과 질의에 같은 임베딩 모델을 써야 한다는 원칙(10.6절)은 한국어에서도 같고, 공유 모델 provider가 임베딩 모델을 바꾸면 모든 consumer의 지식베이스가 영향을 받으므로 14.10절의 폐기 고지 정책이 임베딩에도 적용됩니다.

**골든셋에 한국어 벤치마크를 접목하는 법** — 공개 벤치마크 문항을 그대로 골든셋에 넣지 않습니다. 벤치마크는 후보 스크리닝용이고, 골든셋은 자사 문서와 실제 질문으로 만듭니다. 다만 벤치마크의 문항 형식(객관식 지식, 추론, 독해)은 골든셋의 항목 유형을 설계할 때 참고가 되고, 한국어 인젝션과 탈옥 문장을 골든셋에 넣어 가드 모델의 한국어 탐지율을 확인하는 것은 [12 12.3절](12-service-security.md)의 요구입니다. 한국어 문서 파이프라인(한국어 OCR, 문장 분리와 청킹, 형식 분포에 따른 변환)은 [06 6.8절](06-data-onboarding.md)과 [④ 02 2.3.2절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/04-rag/docs/02-ingestion-indexing.md)에 있습니다.

## 10.8 모델 라이선스 심사 체크리스트

가중치가 공개돼 있다는 것과 사내 서비스에 써도 된다는 것은 다른 문제입니다. 공개 모델의 라이선스는 크게 넷으로 나뉩니다. 허용적 오픈소스 라이선스(Apache 2.0, MIT 계열), 제공자가 만든 커뮤니티 또는 맞춤 라이선스(사용 정책 수용, 이용자 수 임계, 파생 모델 명명 의무 같은 조건이 붙음), 연구와 비상업 한정 라이선스, 그리고 상용 약관(NVIDIA NIM처럼 별도 엔터프라이즈 라이선스가 필요한 경우)입니다. 학습 데이터셋의 라이선스는 모델 라이선스와 별개이고, 파인튜닝 산출물은 원 모델의 조건을 승계합니다.

이 절은 법률 해석이 아닙니다. 체크리스트의 답은 법무와 지식재산 담당이 확정하고([⑦ 09 9.2.1절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/07-design/docs/09-roles-raci.md)), 그 결과가 Model Gallery 반입 게이트의 "라이선스 검토 통과" 칸이 됩니다([⑤ 04 4.2절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/04-airgap-supply-chain.md)).

| # | 항목 | 확인 질문 | 기록할 것 |
|---|------|-----------|-----------|
| 1 | 라이선스 유형과 원문 | 어떤 라이선스이며 원문 전체를 확보했는가. 모델 카드의 요약이 아니라 원문 | 라이선스 이름, 버전, 원문 사본과 확보일 |
| 2 | 상업 이용 | 사내 업무용 사용이 허용되는가. 대외 서비스 제공은 별도 조건인가 | 허용 범위 |
| 3 | 이용자 수와 매출 임계 | 조직 규모나 이용자 수에 따라 별도 허가가 필요한 조항이 있는가 | 해당 여부와 근거 조항 |
| 4 | 파생과 재배포 | 파인튜닝 산출물과 양자화본을 만들어도 되는가, 사내 배포는 재배포에 해당하는가, 파생 모델 이름에 원 모델명을 넣어야 하는가 | 파생 조건, 명명 의무 |
| 5 | 귀속 표기와 고지 | 라이선스 사본 첨부, 출처 표기, 이용 정책 고지 의무가 있는가 | 표기 위치(문서, 화면, 배포물) |
| 6 | 사용 제한 | 금지 용도, 지역과 수출 통제, 특정 산업 제한이 있는가 | 해당 여부, 유스케이스와 대조 |
| 7 | 보증과 면책 | 제공자의 보증 범위와 이용자의 면책 의무 | 위험 수용 여부 |
| 8 | 데이터셋과 생성물 | 학습 데이터셋의 라이선스가 별도인가, 생성물의 권리 귀속과 제3자 권리 침해 시 책임은 어떻게 되는가 | 데이터셋 카드, 생성물 정책 |
| 9 | 부속 모델 | 임베딩, 리랭커, 가드 모델, 토크나이저도 같은 심사를 거쳤는가 | 모델별 결과 |
| 10 | 엔진과 런타임 | 서빙 엔진의 오픈소스 라이선스 의무, NIM과 NVIDIA AI Enterprise 약관의 적용 범위 | 엔진별 결과([14 14.5절](14-operations.md)) |

**보존과 감시** — 심사 결과, 라이선스 원문 사본, 모델 카드와 데이터셋 카드를 거버넌스 기록으로 보존하고 릴리스 매니페스트([13 13.9절](13-evaluation-guardrails.md))에서 참조합니다. 제공자가 라이선스를 바꾸거나 모델 카드를 갱신하면 재심사 대상이므로, 반입 시점의 사본을 남기고 갱신을 주기적으로 확인합니다. 공유 모델은 provider가 심사하고 consumer는 결과를 참조하되, 자기 유스케이스가 사용 제한(6번)에 걸리는지는 consumer가 확인합니다.

다음 문서에서는 만든 에이전트를 운영에 올리기 전 **평가하고 가드레일을 설계**하는 방법을 다룹니다.

[^kmmlu]: Son 외, [KMMLU: Measuring Massive Multitask Language Understanding in Korean](https://arxiv.org/abs/2402.11548) (2024). 한국어 지식 평가 벤치마크.
[^kobest]: Kim 외, [KoBEST: Korean Balanced Evaluation of Significant Tasks](https://arxiv.org/abs/2204.04541) (2022). 한국어 이해 과제 묶음. HAE-RAE Bench는 Son 외, [arXiv 2309.02706](https://arxiv.org/abs/2309.02706) (2023).
[^mteb]: Muennighoff 외, [MTEB: Massive Text Embedding Benchmark](https://arxiv.org/abs/2210.07316) (2022). 다국어 태스크와 리더보드는 [MTEB 리더보드](https://huggingface.co/spaces/mteb/leaderboard)에서 한국어 태스크를 골라 봅니다.

---
[← 이전: 09 MCP 도구 통합](09-mcp-tools.md) | [목차](../README.md) | [다음: 11 앱 통합과 신뢰 UX →](11-app-integration-ux.md)
