# 09 — MCP 도구 통합

[← 목차로](../README.md)

에이전트의 능력은 붙인 도구로 정해집니다. PAIS는 Model Context Protocol(MCP)로 외부 시스템을 도구로 연결합니다. 이 문서는 PAIS가 MCP를 어떤 방향으로 다루는지, Tool Gallery로 어떻게 관리하는지, 원격 서버를 어떻게 등록하고 승인하는지, 그리고 전송, 인증, 보안 경계를 다룹니다.

> 본 문서의 수치와 동작은 VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0 기준입니다(작성 2026-06, 9.1.1과 3.0 GA 반영 2026-09). 2.1 환경에서는 "PAIS 3.0부터"로 표기한 대목만 건너뛰면 됩니다. 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

---

## 9.1 PAIS가 MCP를 다루는 세 방향

MCP는 모델과 에이전트가 외부 도구와 데이터에 접근하는 개방 프로토콜입니다. PAIS는 MCP를 세 방향으로 지원합니다.

- **호출(consumer)** — 에이전트가 하나 이상의 MCP 서버가 제공하는 도구로 능력을 확장합니다. 에이전트는 도구를 부를지, 어떤 인자를 넣을지를 스스로 정합니다.
- **호스팅(producer)** — Data Indexing and Retrieval 모듈이 **MCP 서버를 구현**해, 각 지식베이스에 대한 검색 도구를 MCP 도구로 내보냅니다. 즉 지식베이스 검색이 에이전트가 쓰는 MCP 도구로 노출됩니다(9.3절).
- **등록과 승인(register)** — Agent Builder의 MCP 서버 관리에서 원격 서버를 추가하고, 관리자가 도구의 능력과 파라미터를 검토해 **명시적으로 승인한** 도구만 에이전트에 노출합니다(9.4절).

이 세 방향과 중앙 관리(Tool Gallery)는 PAIS 2.1에서 처음 정식 도입됐습니다.

## 9.2 Tool Gallery

**Tool Gallery**는 MCP 서버를 중앙에서 등록하고 관리하는 2.1 신규 기능입니다. 개별 에이전트마다 도구를 흩어 두는 대신, 조직 차원에서 어떤 MCP 서버와 도구가 쓰이는지 한 곳에서 관리하고 거버넌스를 적용하는 지점입니다. 도구 표면을 통제하는 운영과 보안 관점의 핵심 구성요소입니다([⑤](https://github.com/JaeHoYun/vcf-private-ai/tree/main/05-security) 위임).

## 9.3 지식베이스 검색은 MCP 도구다

PAIS에서 지식베이스 검색은 별도 배선 없이 MCP 도구로 노출됩니다 — Data Indexing and Retrieval이 지식베이스마다 검색 도구 집합을 MCP로 내보내기 때문입니다. 그래서 에이전트는 "지금 검색이 필요한가, 무엇으로 검색할까"를 스스로 판단해 이 도구를 호출합니다.

설계상 함의: **단순 Q&A는 RAG(④)로 충분**하지만, 검색을 다른 도구 호출과 섞어 동적으로 판단해야 한다면 검색을 도구로 가진 에이전트가 자연스럽습니다([01 1.1절](01-foundations.md)).

## 9.4 원격 MCP 서버 등록과 승인

외부 시스템을 도구로 붙이는 절차입니다.

1. **서버 추가** — Agent Builder의 MCP 서버 관리에서 원격 MCP 서버 주소를 등록합니다.
2. **도구 검토** — 서버가 제공하는 도구의 능력과 입력 파라미터를 확인합니다.
3. **명시적 승인** — 검토 후 승인한 도구만 에이전트에서 사용할 수 있습니다. 승인은 보안 경계이자, 모델에 노출할 도구 표면을 좁히는 설계 수단입니다([03 3.3절](03-design-patterns.md)).

승인 워크플로우는 **관리자가 도구 등록을 통제**하는 것이며, 런타임 응답에 사람이 개입하는 휴먼인더루프와는 다릅니다(후자는 PAIS 내장 기능으로 확인되지 않으며 애플리케이션 계층 설계입니다 — [13](13-evaluation-guardrails.md)).

## 9.5 연결 요건 — 전송과 인증

원격 MCP 서버를 연결하려면 다음을 충족해야 합니다([근거: Connect an MCP Server to Private AI Services](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-foundation-9-x/what-is-private-ai-services/adding-mcp-servers-for-real-time-data-access-and-specialized-ai-capabilities/connect-to-an-mcp-server.html)).

- **접근** — HTTP 또는 HTTPS로 도달 가능해야 합니다.
- **전송 방식** — Streamable HTTP 또는 Server-Sent Events(SSE)를 지원해야 합니다. SSE는 `http(s)://<서버 FQDN 또는 IP>/sse` 형식의 URL로 등록합니다. 다만 MCP 사양 2026-07-28 개정판은 HTTP+SSE 전송을 폐기 예고(Deprecated) 상태로 분류했고(2025-03-26 개정판부터 비권장), 사양의 폐기 정책상 최소 12개월의 유예 뒤 제거될 수 있습니다. 신규 MCP 서버는 Streamable HTTP로 만들고, 기존 SSE 서버는 전환 계획을 세우십시오. 같은 개정판은 OAuth 동적 클라이언트 등록(RFC 7591)도 폐기 예고하고 Client ID Metadata Documents로 대체하므로, 정적 토큰 대신 OAuth로 MCP 서버를 보호하려는 조직은 이 방향을 기준으로 삼습니다([MCP 2026-07-28 변경 사항](https://modelcontextprotocol.io/specification/2026-07-28/changelog)).
- **인증(선택)** — 정적 인증 토큰을 헤더로 전달할 수 있습니다(예: `Authorization: Apikey <토큰>`).
- **TLS 신뢰** — HTTPS를 쓰면 발급자 인증서를 CA 신뢰 번들에 임포트해 신뢰를 확립합니다.

운영 환경에서는 평문 HTTP 대신 HTTPS와 토큰 인증을 기본으로 두고, 자격증명은 비밀로 관리하십시오([⑤](https://github.com/JaeHoYun/vcf-private-ai/tree/main/05-security)).

## 9.6 사내와 외부 시스템 연결

MCP의 가치는 커스텀 커넥터를 일일이 만들지 않고도 다양한 시스템을 도구로 붙일 수 있다는 점입니다. 연결 대상의 범주와 예:

| 범주 | 예시 시스템 |
|------|-------------|
| 관계형 데이터베이스 | PostgreSQL, Oracle, Microsoft SQL Server |
| ITSM, 서비스 관리 | ServiceNow |
| 개발과 협업 | GitHub, Slack |

각 시스템이 MCP 서버를 제공하거나(공식과 커뮤니티) 사내에서 MCP 서버로 감싸면, 에이전트가 이를 도구로 호출해 실시간 데이터를 읽거나 작업을 수행할 수 있습니다. PAIS의 네이티브 데이터소스 커넥터(지식베이스용 4종)와는 다른 경로임에 유의하십시오 — 지식베이스는 인덱싱과 검색용, MCP는 실시간 도구 호출용입니다(데이터 경로 구분은 [②](https://github.com/JaeHoYun/vcf-private-ai/tree/main/02-vectordb), [④](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag)).

## 9.7 보안 경계

도구는 에이전트의 능력인 동시에 외부 시스템에 대한 공격 표면입니다. 다음을 원칙으로 둡니다.

- **승인된 도구만** — Tool Gallery, 승인 워크플로우로 노출 도구를 통제합니다.
- **권한 최소화** — 도구가 쓰는 자격증명과 범위를 필요한 최소로 둡니다(읽기 전용으로 충분하면 쓰기 권한을 주지 마십시오).
- **전송과 인증 강화** — HTTPS, 토큰, CA 신뢰를 기본으로 둡니다.
- **되돌리기 어려운 행동 보호** — 쓰기, 전송, 결제처럼 영향이 큰 도구는 애플리케이션 계층 확인 게이트로 감쌉니다([07 7.3절](07-integration-write-design.md), 검증은 [13 13.6절](13-evaluation-guardrails.md)).
- **도구 설명 해시 고정** — 도구의 이름, 설명, 입력 스키마는 모델이 읽는 지시입니다. 승인 뒤 서버 측에서 설명이 바뀌면 승인의 전제가 사라지므로(도구 오염과 rug pull), 승인 시점의 해시를 기록하고 서버가 다른 값을 내놓으면 자동으로 승인을 무효화하고 재검토합니다. PAIS의 승인 절차는 등록 시점의 검토이지 이후 변경을 감시하지 않으므로 이 감시는 앱 팀이나 플랫폼 팀이 붙입니다.
- **제3자 MCP 서버는 체크리스트로** — 외부에서 가져온 서버는 출처, 버전 고정, 매니페스트 전수 검토, 이그레스, 재승인 조건까지 [A2.3](../appendix/A2-worksheets.md)을 통과한 뒤 등록합니다. 항목의 근거와 MCP 사양의 인가 요구는 [⑤ 08 8.5절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/08-agent-governance.md)에 있습니다.

격리, 접근 통제, 감사 등 통제 상세는 ⑤에 위임하며, 에이전트를 행위자로 보는 위협과 통제의 정본은 [⑤ 08 에이전트 보안 거버넌스](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/08-agent-governance.md), 이 서비스에 대입하는 점검표는 [12](12-service-security.md)입니다.

## 9.8 사내 MCP 서버 호스팅과 운영

PAIS는 MCP 서버를 **등록, 승인, 소비**하지만, 사내 시스템을 감싸는 **MCP 서버 자체는 사용자 자산**입니다(9.6절). 공식과 커뮤니티 MCP 서버가 없는 사내 시스템은 직접 MCP 서버를 만들어 호스팅해야 하며, 그 수명주기는 앱과 플랫폼 계층의 책임입니다([00 0.3절](00-orientation.md)).

**서버 구현**

- **전송** — PAIS가 연결하려면 Streamable HTTP 또는 SSE를 지원해야 합니다(9.5절).
- **도구 정의** — 도구 이름, 설명, 파라미터를 모델이 헷갈리지 않게 명확히 작성합니다([03 3.3절](03-design-patterns.md)). 비슷한 도구가 많으면 모델이 잘못 고릅니다.
- **테스트** — 등록 전 로컬에서 도구 호출과 스키마를 검증합니다. 읽기 전용 도구부터 노출하고 쓰기 도구는 신중히 더합니다.

**서버 호스팅과 운영**

- **배치 위치** — 사내 MCP 서버는 VKS 클러스터의 워크로드로 올리거나 별도 VM, 컨테이너로 운영합니다. PAIS가 호스팅해 주지 않습니다.
- **고가용성** — PAIS와 같은 가용성 기대를 받는다면 서버도 복제본과 로드밸런서를 갖춰야 합니다. 도구를 부르는 에이전트가 늘면 서버가 단일 장애점이 됩니다.
- **스케일** — 에이전트의 도구 호출은 루프와 다단계로 늘어날 수 있으므로([14](14-operations.md) 비용과 스케일), 서버가 동시 호출을 감당하는지 부하를 가늠합니다.
- **인증과 토큰** — 9.5절의 정적 토큰을 쓰면 로테이션은 운영자 책임입니다. 자격증명은 외부 시크릿 관리로 보관과 교체합니다([⑤ ID, 인증, 접근통제](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/03-identity-access.md)).
- **관측** — 서버 자체의 로그와 지표(호출 수, 오류, 지연)를 수집해 에이전트 추적([14 14.2절](14-operations.md))과 상관 지을 수 있게 합니다.

플랫폼 인프라 운영 전반은 [① Day-2 운영](https://github.com/JaeHoYun/vcf-private-ai/blob/main/01-infra/docs/10-operations.md)에 위임합니다.

## 9.9 도구 호출 이그레스와 네트워크 경로

에이전트는 일반 추론 서빙과 달리 **바깥으로 능동적으로 나가는** 워크로드입니다. 네트워크 경로를 두 방향으로 나눠 봅니다.

- **인바운드(inbound, 들어오는 트래픽)** — 앱이 에이전트와 모델 엔드포인트를 호출하는 트래픽. 엔드포인트는 ML API Gateway 뒤에 노출됩니다([10 10.1절](10-models-serving.md)).
- **이그레스(egress, 나가는 트래픽)** — 에이전트가 도구(원격 MCP 서버와 사내 시스템)를 호출하며 밖으로 나가는 트래픽. 에이전트 워크로드 특유의 경로이자 보안 통제의 핵심입니다.

**이그레스 통제**

- 에이전트가 닿을 수 있는 대상을 **승인된 MCP 서버와 시스템으로 한정**합니다. 도구 승인(9.4절)이 논리적 통제라면, 네트워크 정책은 물리적 통제입니다.
- NSX 분산 방화벽과 이그레스 정책으로 VKS 워크로드의 외부 접근 범위를 좁힙니다(정책 설계 상세는 [⑤ 네트워크, 테넌트, GPU 격리](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/02-network-tenant-isolation.md), [①](https://github.com/JaeHoYun/vcf-private-ai/tree/main/01-infra) 위임).
- **에어갭** — 외부 이그레스가 차단된 환경에서는 사내 MCP 서버와 미러만 도구로 쓸 수 있습니다(Artifact Mirroring Tool 연계 [10 10.4절](10-models-serving.md)).

다음 문서에서는 에이전트가 쓰는 **모델을 어떻게 서빙과 관리**하는지를 다룹니다.

---
[← 이전: 08 Agent Builder로 구축](08-agent-builder.md) | [목차](../README.md) | [다음: 10 모델과 서빙 →](10-models-serving.md)
