# 08 — Agent Builder로 구축

[← 목차로](../README.md)

이 문서는 PAIS Agent Builder로 에이전트 하나를 처음부터 구성하는 절차를 다룹니다. 모델 엔드포인트 선택부터 지시문, 지식베이스, 도구, 세션 구성, Playground 테스트, REST API 소비까지 순서대로 따라갑니다. 화면 라벨과 세부 단계는 릴리스에 따라 다를 수 있으므로 공식 문서와 함께 보시기 바랍니다.

> 본 문서의 수치와 동작은 VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0 기준입니다(작성 2026-06, 9.1.1과 3.0 GA 반영 2026-09). 2.1 환경에서는 "PAIS 3.0부터"로 표기한 대목만 건너뛰면 됩니다. 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

---

## 8.1 구성 흐름 개요

Agent Builder에서는 코드부터 작성하지 않습니다. **UI 위저드로 구성 → Playground로 테스트 → REST API로 소비**가 기본 흐름이며, 구성 결과를 코드로 내보내 형상관리할 수 있습니다.

1. 새 에이전트 생성(Create Agent) — 이름과 설명 입력
2. completion 모델 엔드포인트 선택
3. 지시문(Instructions) 작성 — 선택
4. 지식베이스 연결 — 선택
5. 도구(MCP) 연결 — 선택
6. 세션과 검색 파라미터 조정
7. Playground에서 대화로 검증
8. 챗 컴플리션 엔드포인트를 REST API로 호출

구성요소는 [01 1.3절](01-foundations.md)에서 소개한 표와 같습니다. 아래에서 항목별로 채웁니다.

## 8.2 모델 엔드포인트 선택

에이전트는 **Model Runtime에서 서빙 중인 completion 모델 엔드포인트** 하나를 사용합니다. Agent Builder에서 드롭다운으로 선택하며, 목록에 없다면 먼저 모델을 서빙해야 합니다([10](10-models-serving.md)).

선택 기준(도구 호출 지원, 컨텍스트 길이, 비용, 지연, 임베딩 모델)은 [10 10.6절 에이전트 관점의 모델 선택](10-models-serving.md)에 모아 두었습니다. 구성 단계에서는 특히 **도구 호출 지원**을 먼저 확인하십시오 — 도구를 적극적으로 쓰는 에이전트를 네이티브 도구 호출(tool calling) 미지원 모델로 구성하면 별도 설정이 필요합니다([03 3.4절](03-design-patterns.md)).

## 8.3 지시문(Instructions) 작성

지시문은 에이전트의 시스템 프롬프트이자 행동 정책입니다(선택 항목). 다음을 명확히 적습니다.

- **역할과 범위** — 무엇을 하는 에이전트인지, 무엇은 하지 않는지.
- **도구와 검색 사용 지침** — 언제 지식베이스를 검색하고 언제 도구를 부를지에 대한 안내.
- **응답 형식, 언어, 톤** — 출력 형식과 어조.
- **거절과 한계** — 권한 밖 요청이나 근거 부족 시 어떻게 답할지.

지시문은 짧고 구체적일수록 모델이 일관되게 따릅니다. 길고 모순된 지시문은 도구 오선택과 환각을 늘립니다. 효과는 Playground와 평가([13](13-evaluation-guardrails.md))로 확인하며 수정과 보완합니다.

## 8.4 지식베이스 연결

검색이 필요하면 Data Indexing and Retrieval에서 만든 지식베이스를 연결합니다. 지식베이스 구성, 청크, 임베딩의 상세는 ④에 위임하고, 여기서는 **에이전트가 검색을 어떻게 쓰는지**만 다룹니다.

- **검색은 도구다** — 연결된 지식베이스 검색은 에이전트가 호출 여부와 검색어를 스스로 정하는 도구로 동작합니다.
- **검색 파라미터** — Top-K(가져올 문서 수), 유사도 컷오프(0–1), 인용 표시를 조정합니다. 잡음이 많으면 컷오프를 높이고, 누락이 잦으면 Top-K를 키우거나 컷오프를 낮춥니다.
- **인용** — 답변에 출처 표시를 켜면 환각을 줄이고 검증을 돕습니다.

> 지식베이스의 벡터 저장은 pgvector 확장을 갖춘 외부 PostgreSQL을 사용합니다. 임베딩 모델은 Model Runtime이 서빙하며, 인덱싱과 질의에 **같은 임베딩 모델**이 쓰입니다(상세와 구성은 [②](https://github.com/JaeHoYun/vcf-private-ai/tree/main/02-vectordb), [④](https://github.com/JaeHoYun/vcf-private-ai/tree/main/04-rag)). 특정 기본 임베딩 모델명은 공식 문서로 확인하시기 바랍니다.

## 8.5 도구(MCP) 연결

에이전트에 외부 시스템 도구를 붙이려면 MCP 서버의 도구를 연결합니다. 등록, 승인, 전송, 인증의 상세는 [09 MCP 도구 통합](09-mcp-tools.md)에서 다룹니다. 여기서는 다음만 기억하면 됩니다.

- 도구는 **관리자가 승인한 것만** 에이전트에 노출됩니다.
- 도구는 최소한으로 명확하게 — 비슷한 도구가 많으면 모델이 잘못 고릅니다([03 3.3절](03-design-patterns.md)).

## 8.6 세션과 검색 파라미터

[03 3.4절](03-design-patterns.md)에서 설계한 값을 여기서 적용합니다 — 대화 이력 길이, 유지 시간(TTL), 요약 전략, 그리고 위의 검색 파라미터. 기본값에서 시작해 실제 대화와 평가로 조정하는 편이 안전합니다.

## 8.7 Playground로 테스트

Agent Builder는 **Playground**(대화형 테스트 화면)를 제공합니다. 배포 전에 다음을 확인하십시오.

- 의도한 질문에서 **지식베이스를 검색하는가**, 검색어가 적절한가.
- 도구가 필요한 상황에서 **올바른 도구를 부르는가**, 파라미터가 맞는가.
- 근거 없이 단정하지 않는가, 권한 밖 요청을 적절히 거절하는가.
- 지시문 변경이 행동을 의도대로 바꾸는가.

Playground는 1차 검증 수단이며, 반복 가능한 품질 측정은 CI/CD 자동 테스트로 보완합니다([13](13-evaluation-guardrails.md)).

## 8.8 REST API 소비와 구성 코드 내보내기

완성된 에이전트는 **챗 컴플리션 엔드포인트**로 노출됩니다. 애플리케이션은 이 엔드포인트를 OpenAI 호환 방식으로 호출해 에이전트를 소비합니다 — 모델 엔드포인트를 직접 부르는 것과 달리, 에이전트 엔드포인트는 검색, 도구, 세션을 그 위에 더해 줍니다.

공식 API 문서 기준 경로와 호출 형식입니다([근거: Private AI Services API](https://developer.broadcom.com/xapis/vmware-private-ai-service-api/latest/)). 모델을 직접 부르는 경로와 에이전트 전용 경로가 나뉘며, 둘 다 OpenAI 규약을 따릅니다. 요청과 응답 본문의 전체 스키마는 위 API 문서를 기준으로 하십시오.

```bash
# 모델 엔드포인트 직접 호출 (stateless)
curl 'https://<PAIS FQDN>/api/v1/compatibility/openai/v1/chat/completions' \
    --header 'Content-Type: application/json' \
    --header "Authorization: Bearer $TOKEN" \
    --data '{"model": "<모델명>", "messages": [{"role": "user", "content": "..."}]}'

# 에이전트 호출 — 검색, 도구, 세션이 더해진 엔드포인트
curl 'https://<PAIS FQDN>/api/v1/compatibility/openai/v1/agents/<agent-id>/chat/completions' \
    --header 'Content-Type: application/json' \
    --header "Authorization: Bearer $TOKEN" \
    --data '{"messages": [{"role": "user", "content": "..."}]}'
```

> **PAIS 3.0에서 바뀐 것** — 에이전트 API의 `completion_role` 필드가 제거되고 응답 role은 항상 `assistant`입니다. 메시지 배열 없이 프롬프트 문자열을 보내는 non-chat completions 형태는 OpenAI 호환 API와 Agent Builder API 양쪽에서 deprecated이므로 위 `chat/completions` 경로만 쓰십시오. boolean 필드는 엄격히 검증되어 `"stream": "true"` 같은 문자열 값은 거부됩니다. ([근거: PAIS 3.0 릴리스 노트](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html))

- **구성 코드 내보내기** — Agent Builder는 구성 코드(View Configuration Code) 보기를 제공합니다. 이를 형상관리에 두면 에이전트 정의를 코드로 추적하고 재현할 수 있습니다.
- **자동화** — 구성을 코드로 다루면 CI/CD에서 에이전트를 배포하고 테스트하는 파이프라인을 구성할 수 있습니다([13](13-evaluation-guardrails.md)).

## 8.9 신원의 두 층위 — 서비스 인증과 최종 사용자

에이전트 엔드포인트를 앱에서 소비할 때(8.8절), 신원은 두 층위로 나뉩니다. **서비스 인증(앱 → PAIS)** 은 앱이 엔드포인트를 호출할 때 쓰는 서비스 신원(OIDC 액세스 토큰, 3.0부터는 인스턴스 간 연결과 자동화용 API 토큰)이고, **최종 사용자 신원**은 그 뒤에 있는 사람입니다. 엔드포인트는 호출하는 서비스만 알 뿐 사용자가 누구인지 모르므로, 사용자 로그인과 사용자별 접근 권한과 테넌트 격리는 앱이 책임집니다.

이 구분에서 따라 나오는 설계 원칙(사용자 신원은 앱이 입구에서 강제한다, 도구와 지식베이스는 사용자 권한을 넘지 않게 한다, 사용자 집단이 다르면 에이전트와 네임스페이스를 나눈다)과, 신원이 어느 경계에서 끊기고 앱이 무엇으로 대신하는지의 규약(토큰 교환, 서명된 컨텍스트, 지식베이스 권한 일치, 감사 필드)은 설계 편 [04 사용자 신원과 권한 전파](04-identity-propagation.md)가 정본입니다. 구축 단계에서 기억할 것은 두 가지입니다. 관리형 에이전트에 연결하는 도구와 지식베이스는 그 에이전트의 사용자 전원에게 안전해야 하고, PAIS가 사용자 컨텍스트를 도구와 검색까지 전파하는지는 공식 문서로 확인되기 전까지 전파되지 않는다고 가정합니다.

PAIS 배포에 필요한 OIDC 공급자(Authorization Code + PKCE 흐름)의 실구성 사례는 [04 4.1절](04-identity-propagation.md)에 있습니다.

접근 통제, 감사, 격리의 구현 상세는 ⑤에 위임합니다.

## 8.10 엔드포인트 소비 — 인증, 스트리밍, 견고성

에이전트 엔드포인트를 앱에서 호출할 때(8.8절), 단일 모델 호출보다 견고성이 더 중요합니다 — 에이전트는 도구와 검색으로 단계가 많아 종단 지연이 크고 부분 실패가 잦기 때문입니다.

- **인증** — OpenAI 호환 호출에 서비스 인증 토큰을 `Authorization: Bearer <액세스 토큰>` 헤더로 싣습니다([근거: Private AI Services API](https://developer.broadcom.com/xapis/vmware-private-ai-service-api/latest/)). 토큰 발급, 로테이션은 앱, 플랫폼 책임이며, 최종 사용자 신원과는 별개입니다(8.9절).
- **스트리밍** — 긴 응답은 스트리밍(서버가 토큰을 흘려보냄)으로 받아 체감 지연(TTFT)을 줄입니다. 앱은 부분 응답을 누적하고 파싱하고 중간 도구 호출 이벤트를 처리해야 합니다.
- **타임아웃과 재시도** — 에이전트 호출은 길어질 수 있으니 단일 호출보다 타임아웃을 넉넉히 잡고, 실패 시 지수 백오프로 재시도합니다. 무한 대기, 즉시 연속 재시도는 피합니다.
- **멱등**(idempotent, 같은 요청을 여러 번 보내도 결과가 한 번과 같음) — 도구가 외부 시스템에 쓰기와 전송을 하면 재시도가 같은 작업을 두 번 실행할 수 있습니다. 멱등 키나 중복 검사로 재시도 안전성을 확보합니다.

전용 SDK는 없습니다 — OpenAI 호환이므로 기존 OpenAI 클라이언트(Python, JS 등)의 base URL만 PAIS 엔드포인트로 바꿔 그대로 씁니다([10 10.1절](10-models-serving.md)).

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://<PAIS FQDN>/api/v1/compatibility/openai/v1",
    api_key=access_token,  # PAIS 액세스 토큰(Bearer) — OIDC로 발급(8.9절)
)
response = client.chat.completions.create(
    model="<모델명>",
    messages=[{"role": "user", "content": "..."}],
)
```

에이전트를 부를 때는 base URL 뒤에 에이전트 경로(`agents/<agent-id>`)가 붙습니다(8.8절). 호출 코드 위에 얹는 앱의 골격(4-Tier, BFF, 세션)과 화면 명세(출처 카드, 폴백, 진행 표시, 사람 이관, 고지)는 [11 앱 통합과 신뢰 UX](11-app-integration-ux.md)에서 다룹니다. **채팅 UI를 바로 붙이려면** — Open WebUI를 PAIS 에이전트의 프론트엔드로 연결하는 공식 절차가 공개돼 있습니다. 파이프 함수(Pipe Function)로 에이전트 목록(`/assistants`)을 조회해 모델 드롭다운에 노출하고 `agents/<id>`로 라우팅하며, 클러스터 안에서는 nginx mTLS 프록시를 경유합니다([근거: How to Connect your VMware Private AI Services Agents to OpenWeb UI, blogs.vmware.com 2025-08](https://blogs.vmware.com/cloud-foundation/2025/08/15/how-to-connect-your-vmware-private-ai-services-agents-to-openweb-ui/)).

다음 문서에서는 에이전트의 능력을 넓히는 **MCP 도구 통합**을 자세히 다룹니다.

---
[← 이전: 07 사내 시스템 연동과 쓰기 설계](07-integration-write-design.md) | [목차](../README.md) | [다음: 09 MCP 도구 통합 →](09-mcp-tools.md)
