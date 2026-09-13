# 00 — 개관

[← 목차로](../README.md)

이 가이드는 VCF 9.1.x Private AI Services(PAIS) 3.0 위에서 기업이 **서비스 하나를 기획부터 운영까지 만들고 책임지는 방법**을 다룹니다. 여기서 서비스란 챗과 Q&A RAG, 문서 처리 배치 파이프라인, 기존 업무 시스템에 심는 코파일럿, 그리고 스스로 검색하고 도구를 호출하는 에이전트를 아우릅니다. 이 문서는 가이드 전체의 지도입니다 — 무엇을 답하는지, 누구를 위한 것인지, 무엇을 다루고 무엇은 다른 편에 위임하는지, 그리고 PAIS의 어떤 구성요소를 어디서 설명하는지를 먼저 정리합니다.

> 본 문서의 수치와 동작은 VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0 기준입니다(작성 2026-06, 9.1.1과 3.0 GA 반영 2026-09). 2.1 환경에서는 "PAIS 3.0부터"로 표기한 대목만 건너뛰면 되고, 2.1 기준 문서 전체는 태그 `baseline-pais-2.1`에 있습니다. 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

---

## 0.1 이 가이드가 답하는 질문

시리즈 ①–⑦은 Private AI 플랫폼을 세우고(인프라, 검색, 서빙, 보안, 사이징) 한 워크로드를 조립(④ RAG)하고 전체 설계(⑦)까지 다룹니다. 그 플랫폼은 인프라팀과 플랫폼팀의 관점에서 쓰였습니다. 아직 답하지 않은 질문이 하나 있습니다.

> **"이 플랫폼 위에서 실제 서비스 하나를, 기획부터 출시와 운영까지 어떻게 만들고 누가 무엇을 책임지나?"**

이 질문은 플랫폼을 만드는 쪽이 아니라 **플랫폼을 소비하는 쪽**의 질문입니다. 서비스를 기획하는 담당자, 설계하는 아키텍트, 만드는 앱 팀, 출시를 심사하는 보안과 법무, 운영하는 팀이 차례로 부딪히는 결정을 이 가이드가 서비스 수명주기 순서로 안내합니다.

서비스는 형태에 따라 네 유형으로 나뉩니다. 유형마다 PAIS의 어떤 모듈을 쓰고 어떤 결정이 무거운지가 다릅니다.

| 서비스 유형 | 모습 | 핵심 PAIS 모듈 | 무거운 결정 |
|-------------|------|----------------|-------------|
| 챗과 Q&A RAG | 사용자가 묻고 지식베이스 근거와 함께 답을 받음 | Model Runtime, Data Indexing and Retrieval | 데이터 소스 온보딩과 권한 필터, 신뢰 UX |
| 문서 처리 배치 | 대량 문서를 요약, 분류, 추출해 시스템에 적재. 사용자 대화 없음 | Model Runtime(임베딩과 완성) | 온라인 서비스와의 GPU 우선순위, 단가 |
| 임베드 코파일럿 | 기존 업무 화면 안에서 초안과 제안을 보여줌 | Model Runtime, 필요 시 Data Indexing | 사용자 신원 전파, 기존 시스템 연동 |
| 에이전트 | 검색할지, 어떤 도구를 부를지, 멈출지를 모델이 판단하며 여러 단계를 이음 | Agent Builder, MCP Servers and Tool Gallery, Observability | 자율성 상한, 쓰기 작업 승인, 도구 거버넌스 |

에이전트는 단일 호출과 다릅니다. 사용자의 한 요청에 대해 에이전트는 (1) 지식베이스를 검색할지 판단하고 (2) 필요하면 사내 시스템 도구를 호출하며 (3) 그 결과로 다음 행동을 정하고 (4) 충분하면 답을 종합합니다. PAIS는 이 흐름을 직접 다루는 모듈 — **Agent Builder, MCP Servers and Tool Gallery, Observability** — 을 2.1에서 정식 제공했습니다. 이 가이드의 구축 편(08–10)이 그 모듈로 에이전트를 구성, 통합, 서빙하는 실무를 다루며, 나머지 세 유형은 같은 수명주기 안에서 에이전트와 나란히 다룹니다.

## 0.2 독자와 선행지식

**대상 독자** — 서비스 수명주기의 단계마다 독자가 다릅니다.

| 단계 | 독자 | 이 가이드에서 |
|------|------|---------------|
| 기획과 선정 | 유스케이스를 고르고 위험 등급을 정하는 사업 담당자와 AI 리더 | 00–02 |
| 설계 | 신원, 데이터 소스, 시스템 연동, 플랫폼 소비를 정하는 아키텍트 | 03–07 |
| 구축 | Agent Builder와 MCP와 모델 엔드포인트로 구현하고 앱에 통합하는 개발팀 | 08–11 |
| 검증과 출시 | 서비스 보안 준비와 평가 게이트를 심사하는 보안, 법무, 품질 담당자 | 12–13 |
| 운영과 종료 | 관측, 업그레이드, 비용, 퇴역을 책임지는 운영팀 | 14 |

**선행지식** — 이 가이드는 플랫폼이 이미 구축돼 있다고 전제합니다. 다음을 먼저 보면 수월합니다.

| 알아둘 것 | 모르면 |
|-----------|--------|
| 인프라, VKS, GPU 워크로드 도메인 | 시리즈 [① 인프라](https://github.com/JaeHoYun/vcf-private-ai/tree/main/01-infra) |
| 모델 서빙과 OpenAI 호환 엔드포인트 | 시리즈 [③ 서빙 API](https://github.com/JaeHoYun/vcf-private-ai/tree/main/03-serving-api) |
| RAG, 지식베이스, 벡터 검색 | 시리즈 [④ RAG](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag) |
| 임베딩, 토큰, 쿠버네티스 같은 기초 어휘 | [Private AI 입문(Primer)](https://github.com/JaeHoYun/vcf-private-ai/tree/main/00-foundations) |
| 에이전트 일반 개념(도구 호출과 계획) | [01 서비스 유형과 PAIS 3.0 지형](01-foundations.md)에서 짚습니다 |

## 0.3 다루는 것과 다루지 않는 것

**다루는 것** — 서비스 수명주기 다섯 부입니다.

- **기획과 선정** — 어떤 일에 써야 성과가 나는지, 파일럿이 어디서 멈추는지, 위험 등급과 자율성 상한을 어떻게 정하는지([02](02-use-cases.md))
- **설계** — 언제 에이전트로 풀지, 단일과 멀티, 도구와 지식 연결, 세션, 배치 파이프라인([03](03-design-patterns.md)), 사용자 신원이 어디까지 따라가는지([04](04-identity-propagation.md)), 앱 팀이 플랫폼에서 무엇을 받고 게이트웨이와 토큰 예산을 어떻게 소비하는지([05](05-platform-consumption.md)), 어떤 문서를 어떤 승인으로 들이고 보호 문서는 어떻게 다루는지([06](06-data-onboarding.md)), 사내 시스템 연동과 쓰기의 승인과 정합성([07](07-integration-write-design.md))
- **구축** — PAIS 3.0 Agent Builder로 에이전트를 구성하는 절차([08](08-agent-builder.md)), MCP로 사내와 외부 시스템 도구를 연결하고 승인하고 관리하는 방법([09](09-mcp-tools.md)), 에이전트가 쓰는 모델을 Model Runtime으로 서빙하고 Model Gallery로 관리하는 방법과 한국어 모델 선정 기준과 라이선스 심사([10](10-models-serving.md)), 앱으로 감싸고 사용자가 답을 믿게 만드는 화면과 고지와 대화 데이터([11](11-app-integration-ux.md))
- **검증과 출시** — 서비스 하나를 출시하기까지 앱 팀이 준비하고 증명할 보안, 곧 가드레일 선택과 배치, 에이전트 위협 점검, 자율성 상한, 레드팀, 게이트별 체크리스트([12](12-service-security.md)), 평가와 가드레일 한계와 휴먼인더루프, 프롬프트 수명주기와 릴리스 매니페스트와 출시 심사 패키지([13](13-evaluation-guardrails.md))
- **운영과 종료** — 배포 토폴로지, 관측, 업그레이드, 비용, 배치 워크로드 운영, 모델 폐기 고지, 플랫폼 SLA, 서비스 퇴역([14](14-operations.md))

**다루지 않는 것 (위임)**

| 주제 | 위임 |
|------|------|
| 인프라 구축과 Day-2 플랫폼 운영 | [① 인프라](https://github.com/JaeHoYun/vcf-private-ai/tree/main/01-infra) |
| 지식베이스와 RAG 파이프라인 상세(청크, 임베딩, 재순위) | [④ RAG](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag) |
| 플랫폼 보안 통제, 격리, 접근, 감사의 카탈로그와 검증 방법 | [⑤ 보안과 거버넌스](https://github.com/JaeHoYun/vcf-private-ai/tree/main/05-security) — 이 가이드는 서비스 하나에 그 통제를 적용하는 순서만 다룹니다 |
| GPU, 노드 사이징, TCO | [⑥ 사이징과 비용](https://github.com/JaeHoYun/vcf-private-ai/tree/main/06-sizing-cost) |
| 플랫폼 전체 설계 결정과 블루프린트 | [⑦ 통합 설계](https://github.com/JaeHoYun/vcf-private-ai/tree/main/07-design) |
| 전사 AI 전환 전략, 운영모델, 규제 일정 | [AX 방법론](https://github.com/JaeHoYun/enterprise-ax-methodology) — 국내 규제 시효 정보의 단일 출처는 그 부록 A2입니다 |

**PAIS가 대신해 주지 않는 것 — 이 가이드가 다루는 이유**

PAIS가 제공하는 모듈과 시리즈가 떠받치는 인프라 위에는, 어떤 플랫폼도 대신 만들어 주지 않는 **서비스 쪽의 책임**이 있습니다. 이전 판에서 "앱과 외부 계층의 책임"으로 경계만 그었던 항목들이며, 이제 이 가이드가 그 책임을 어떻게 이행하는지까지 다룹니다.

| 책임 영역 | 왜 PAIS 밖인가 | 이 가이드에서 |
|-----------|----------------|---------------|
| 최종 사용자 신원과 인가(사용자별 접근 권한과 테넌트 격리) | 에이전트 엔드포인트는 호출하는 서비스만 알 뿐, 최종 사용자가 누구인지 모른다 | [04 사용자 신원과 권한 전파](04-identity-propagation.md)가 정본, [08 8.9절](08-agent-builder.md)의 두 층위 원칙, [⑤ ID, 인증, 접근통제](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/03-identity-access.md) |
| 평가 방법 설계(골든셋, 채점, 회귀, A/B) | PAIS에 이름 붙은 전용 평가 프레임워크는 확인되지 않음 | 앱과 CI 계층에서 설계 [13](13-evaluation-guardrails.md) |
| 콘텐츠 가드레일(입출력 필터, PII, 프롬프트 인젝션) | PAIS 내장 콘텐츠 가드레일은 확인되지 않음 | [12 12.3절](12-service-security.md)의 선택과 배치가 정본, 경계는 [13 13.5절](13-evaluation-guardrails.md), 플랫폼 정책은 [⑤ 앱 계층 가드레일](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/06-app-guardrails.md) |
| 휴먼인더루프(되돌리기 어려운 행동 승인) | PAIS 내장 휴먼인더루프 기능은 확인되지 않음 | [07 7.3절](07-integration-write-design.md)의 승인 게이트와 승인 큐가 정본, [03 3.5절](03-design-patterns.md), [13 13.6절](13-evaluation-guardrails.md) 검증 점검 |
| 사내 MCP 서버 구현과 호스팅 | PAIS는 도구의 등록, 승인, 소비만 담당하며, 서버 자체는 사용자 자산이다 | 앱, 플랫폼 계층에서 구현, 운영 [09](09-mcp-tools.md) |
| 모델 파인튜닝과 도메인 적응 학습 | Model Gallery는 모델 보관과 반입만 담당하며, 학습 파이프라인은 범위 밖이다 | 외부와 DLVM에서 학습 후 Gallery로 반입 [10](10-models-serving.md) |
| 애플리케이션 자체(런타임, UI, 세션 저장, CI/CD, 호출 견고성) | 서비스를 소비하고 노출하는 앱은 PAIS가 아니다 | 자체 구현, 엔드포인트 소비는 [08 8.8절](08-agent-builder.md), 골격과 화면 명세와 대화 데이터는 [11](11-app-integration-ux.md) |
| 외부 시크릿 관리, 관측 백엔드, 온콜 연동 | 기업 표준 보안과 관측 시스템과의 통합 영역 | 외부 시스템 통합 [14](14-operations.md), [⑤ ID, 인증, 접근통제](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/03-identity-access.md) |

이 영역들은 PAIS가 *못* 하는 것이 아니라 *플랫폼의 일이 아닌* 것입니다. 벤더중립 에이전트 설계 이론(추론, 계획, 평가 방법론 일반)은 이 가이드의 범위 밖이며, 필요한 만큼만 [01](01-foundations.md), [03](03-design-patterns.md)에서 다루고 곧바로 PAIS 구현 설명으로 넘어갑니다.

## 0.4 PAIS 6개 모듈 지도

PAIS 3.0은 여섯 모듈로 이뤄집니다(모듈 구성은 2.1과 같고, 3.0은 Model Runtime의 연결 방식과 인증 수단을 넓혔습니다). 서비스 유형에 따라 이 중 여러 모듈을 함께 씁니다.

| 모듈 | 역할 | 이 가이드 |
|------|------|-----------|
| Model Gallery | 모델 아티팩트 저장소(Harbor 기반 OCI 레지스트리) | [10](10-models-serving.md) |
| Model Runtime | 추론과 임베딩 모델 서빙(OpenAI 호환 엔드포인트). 3.0부터 로컬 서빙에 더해 다른 인스턴스의 공유 모델과 원격 클라우드 모델을 같은 엔드포인트 형태로 연결 | [10](10-models-serving.md) |
| Data Indexing and Retrieval | 지식베이스 인덱싱과 검색(pgvector) | [08](08-agent-builder.md) 연결, 데이터 소스 온보딩은 [06](06-data-onboarding.md), 파이프라인 상세는 ④ 위임 |
| MCP Servers and Tool Gallery | 외부 도구를 MCP로 연결과 중앙 관리(2.1 신규) | [09](09-mcp-tools.md) |
| Agent Builder | 모델, 지식, 도구, 세션을 묶어 에이전트 구성 | [08](08-agent-builder.md) |
| Observability | 추론, GPU, 에이전트 상호작용 추적, 관측(2.1 확장) | [14](14-operations.md) |

세 모듈(MCP, Agent Builder, 확장된 Observability)이 2.0과 구분되는 2.1의 에이전트 기능을 이룹니다. 3.0은 새 모듈을 더하지 않고, 에이전트가 쓸 모델을 어디서 가져오는지(공유 모델, 원격 클라우드 모델)와 무엇으로 인증하는지(API 토큰)를 넓혔습니다. 자세한 모듈별 역할과 에이전트 구성요소는 [01](01-foundations.md)에서 풀어 설명합니다.

## 0.5 읽는 순서

- 문서 번호는 서비스 수명주기 순서(기획과 선정 00–02, 설계 03–07, 구축 08–11, 검증과 출시 12–13, 운영과 종료 14)를 따릅니다. 처음부터 끝까지 읽으면 서비스 하나의 흐름이 됩니다.
- **무엇에 적용할지, 도입할 가치가 있는지부터 판단해야 한다면** [02 어디에 쓰나](02-use-cases.md)를 먼저 읽으십시오. 위험 등급과 자율성 상한을 정하는 절도 거기 있습니다. 뒤의 설계와 구축 문서를 몰라도 읽을 수 있습니다.
- **개념부터 잡으려면** 00 → [01](01-foundations.md) → [03](03-design-patterns.md)을 차례로 읽으십시오.
- **손으로 먼저 만들어 보려면** [08 Agent Builder](08-agent-builder.md)로 건너뛰고, 도구 연결이 필요할 때 [09 MCP](09-mcp-tools.md), 모델 선택이 필요할 때 [10 모델과 서빙](10-models-serving.md)으로 돌아오십시오.
- **출시를 심사하거나 준비하는 단계라면** [12 서비스 보안 준비와 가드레일](12-service-security.md) → [13 평가와 출시 게이트](13-evaluation-guardrails.md) → [14 운영과 Day-2](14-operations.md)가 핵심입니다. 플랫폼 전체의 보안 착수 순서는 [⑤ 00 어디서부터 시작하나](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/00-where-to-start.md)가 맡습니다.

## 0.6 앞으로의 지형 — 2026-08 Explore 발표와 9.1.1 GA 이후 (참고)

이 가이드의 본문은 PAIS 3.0(2026-09-03 GA) 기준입니다. 2026년 8월 말 VMware Explore에서 발표된 항목 가운데 일부는 9.1.1 / 3.0 릴리스 노트로 확인되어 본문에 들어갔고, 나머지는 아직 발표 단계입니다. 이 절은 그 경계를 기록하는 자리입니다. **아래 "발표 단계" 항목은 GA 문서와 릴리스 노트로 확인되기 전에는 본문 논지에 반영하지 않습니다.** 본문의 각 절에서는 이 절로 링크만 두고, 확인되는 시점에 해당 본문에 정식 반영합니다.

**9.1.1 / PAIS 3.0에서 GA로 확인되어 본문에 반영한 것**

- **멀티테넌트 모델 공유** — Explore에서 "Model Runtime 강화"로 발표된 것이 PAIS 3.0의 공유 모델 호스팅으로 나왔습니다. [10 10.1절](10-models-serving.md)과 [14 14.1절](14-operations.md)에 반영했습니다.
- **원격 클라우드 모델과 API 토큰** — 발표 자료에는 부각되지 않았지만 3.0 릴리스 노트에 있는 GA 기능입니다. [10](10-models-serving.md), [08 8.9절](08-agent-builder.md), [13 13.5절](13-evaluation-guardrails.md)에 반영했습니다.
- **VCF Operations AI Assistant** — PAIS 모델 엔드포인트를 백엔드로 플랫폼을 진단하는 기능이 9.1.1로 GA됐습니다. 이 가이드 범위 밖이라 [① 10 10.4.4절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md)에 있습니다.

**발표 단계 — 본문 미반영**

- **AI Gateway** — 온프레미스와 클라우드 모델 사이의 프롬프트 라우팅, 사용자 단위 토큰 제한, OpenID Connect 기반 애플리케이션 인가. 공식 블로그와 보도 모두 "향후 릴리스"로 표기합니다. 지금은 호출 빈도 제어를 앱 계층이 맡는다는 [③ 05 5.5절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/03-serving-api/docs/05-auth-and-gateway.md)의 결론이 그대로입니다.
- **Secure Agent Framework** — 에이전트가 생성한 코드를 격리 실행하는 샌드박스와, 도구 접근과 에이전트 간 통신과 출력 검증을 통제하는 Agent Harness. 향후 릴리스입니다. 이 가이드가 앱 계층 책임으로 정리한 통제(0.3절, [13 13.5절](13-evaluation-guardrails.md))의 일부가 플랫폼으로 내려올 수 있는 대목이라 계속 지켜봅니다.
- **Model Autoscaling** — 지연과 세션 임계 기반 자동 스케일. 향후 릴리스이며, 레플리카 수는 여전히 수동 설정입니다([14 14.8절](14-operations.md)).
- **AgentMinder** — 에이전트에 신원과 임무를 부여하고, 도구 호출을 게이트웨이에서 인증과 정책 평가 후 승인된 백엔드로만 보내며, OpenTelemetry로 감사하는 별도 제품. 2026-08-31 GA로 발표됐고([Broadcom 보도자료](https://www.globenewswire.com/news-release/2026/08/31/3353342/19933/en/broadcom-unveils-agentminder-an-enterprise-solution-for-ai-agent-governance-and-runtime-control.html)) VKS 등 Kubernetes에 배포하지만 PAIS 구성요소는 아닙니다. 에이전트가 도구를 부르는 경로에 정책 집행 계층을 둘 때의 위치는 [13 13.5절](13-evaluation-guardrails.md)과 [⑤ 08 8.8절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/08-agent-governance.md)에서 다룹니다.
- **vDefend와 Avi Load Balancer의 에이전틱 보안** — MCP 서버와 LLM과 데이터스토어 자동 탐지, 섀도 AI 탐지, 미승인 MCP 도구 접근 차단, 자격증명과 PII 유출 방지. 보도자료가 전부 미래형으로 기술하며 버전과 시점이 없습니다([Broadcom 보도자료](https://www.globenewswire.com/news-release/2026/08/31/3353355/19933/en/broadcom-delivers-end-to-end-security-identity-and-observability-for-agentic-ai.html)).
- **VMware Private AI Cloud, VMware AI Factory** — 인프라와 에이전트와 데이터와 보안을 아우르는 브랜드와, 베어메탈부터 모델 서빙까지의 자동화 프로그램(AMD Instinct MI350과 ROCm, OEM AI ReadyNode 포함). 라이선스 패키징은 공개되지 않았고 애널리스트는 새 AI 기능 대부분이 별도 애드온일 가능성을 짚습니다.
- **Tanzu Platform의 에이전트 계층** — 기본 차단(deny-by-default) 샌드박스와 크리덴셜 분리 보관을 내세우는 에이전트 개발과 실행 계층. Secure Agent Framework와 같은 방향의 발표입니다.

출처: [Explore 2026: VMware AI Factory and other new AI innovations in VCF (VMware Cloud Foundation Blog, 2026-09-03)](https://blogs.vmware.com/cloud-foundation/2026/09/03/explore-2026-vmware-ai-factory-and-other-new-ai-innovations-in-vcf/) | [Announcing General Availability of VCF 9.1.1 (VMware Cloud Foundation Blog, 2026-09-03)](https://blogs.vmware.com/cloud-foundation/2026/09/03/announcing-general-availability-of-vmware-cloud-foundation-9-1-1/) | [VMware Cloud Foundation 9.1.1 Adds Shared AI Models, but Key Features Remain in Preview (eWeek)](https://www.eweek.com/news/vmware-vcf-shared-ai-models/) | [Broadcom 보도자료 — VMware AI Factory (2026-08-31)](https://www.globenewswire.com/news-release/2026/08/31/3353363/19933/en/broadcom-announces-vmware-ai-factory-enabling-faster-time-to-production-ai-and-greater-control-over-ai-tokenomics.html) | [Broadcom 보도자료 — Tanzu AI-ready Data Foundations](https://www.globenewswire.com/news-release/2026/08/31/3353356/19933/en/broadcom-unveils-ai-ready-data-foundations-in-vmware-tanzu-platform-to-power-secure-enterprise-ai-cloud.html) | [SiliconANGLE](https://siliconangle.com/2026/08/31/broadcoms-private-ai-cloud-spans-infrastructure-agents-data-and-security/) | [Network World](https://www.networkworld.com/article/4215847/private-ai-cloud-agentic-infrastructure-dominate-vmware-explore.html)

---
[목차](../README.md) | [다음: 01 서비스 유형과 PAIS 3.0 지형 →](01-foundations.md)
