# A1 — 부록

[← 목차로](../README.md)

이 부록은 본문에 쓰인 약어와 기술 용어를 풀어 둔 용어집과 참조 링크를 담습니다. 본문에서 모르는 용어를 만나면 여기에서 찾으십시오.

## A1.1 용어집

### A1.1.1 에이전트와 도구

- **에이전트(Agent)** — 사용자 요청에 대해 검색, 도구 호출, 종료를 스스로 판단하며 여러 단계를 잇는 워크로드. 어떤 단계를 밟을지가 입력마다 달라진다는 점이 단일 호출과 RAG와 다르다.
- **Agent Builder** — 모델 엔드포인트, 지시문, 지식베이스, 도구, 세션을 묶어 에이전트를 구성하고 챗 컴플리션 엔드포인트로 노출하는 PAIS 모듈.
- **MCP(Model Context Protocol)** — 모델, 에이전트가 외부 도구, 데이터에 접근하는 개방 프로토콜. PAIS는 호출, 호스팅, 등록 세 방향으로 지원한다.
- **Tool Gallery** — MCP 서버를 조직 차원에서 중앙 등록하고 관리하는 PAIS 기능. PAIS 2.1에서 도입.
- **SSE(Server-Sent Events)** — 서버가 클라이언트로 이벤트를 흘려보내는 전송 방식. MCP 연결은 Streamable HTTP 또는 SSE를 요구한다.
- **휴먼인더루프(Human-in-the-loop)** — 되돌리기 어려운 행동 전에 사람의 확인을 두는 통제. PAIS 내장 기능은 확인되지 않아 애플리케이션 계층에서 설계한다.
- **가드레일(Guardrail)** — 에이전트의 입출력과 행동을 제한하는 안전 통제. PAIS 맥락에서는 리소스 쿼터와 거버넌스 의미로 주로 쓰이며, 콘텐츠 가드레일은 애플리케이션 계층 설계가 필요하다.
- **골든셋(Golden set)** — 대표 입력과 기대 동작을 묶은 평가용 데이터셋. 회귀와 A/B 비교의 기준이 된다.
- **LLM 채점(LLM-as-judge)** — 별도 모델에 채점 기준을 주어 자유 서술 답의 품질을 점수화하는 평가 방법. 편향이 있어 사람 표본 검수로 보정한다.
- **자율성 수준(L0–L5)** — 에이전트에 판단과 실행을 얼마나 맡겼는가의 여섯 단계. L0 자율성 없음, L1 행동마다 승인, L2 계획 단위 승인, L3 경계 안 자율, L4 고자율, L5 완전 자율. 첫 배치는 L1 이하([02 2.10절](../docs/02-use-cases.md)).
- **위험 등급** — 유스케이스가 다루는 일과 데이터의 민감도를 낮음, 중간, 높음으로 판정한 값. 고영향 AI 해당 여부, 금융 위험 등급, 개인정보와 기밀, 대외 노출과 쓰기 권한의 네 질문으로 정한다([02 2.9절](../docs/02-use-cases.md)).
- **비인간 신원(NHI, Non-Human Identity)** — 에이전트, 서비스, 도구 서버처럼 사람이 아닌 행위자에 부여하는 고유 신원. 사람이나 다른 에이전트와 자격증명을 공유하지 않는 것이 원칙([⑤ 08 8.2절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/08-agent-governance.md)).
- **도구 오염(Tool poisoning)** — MCP 도구의 설명문에 숨긴 지시로 에이전트를 조종하는 공격. 승인 뒤 설명이 바뀌는 rug pull, 다른 서버의 도구를 가로채는 shadowing을 포함한다. 승인 시점의 설명 해시를 고정해 막는다([09 9.7절](../docs/09-mcp-tools.md)).
- **킬스위치(Kill switch)** — 서비스 단위로 에이전트 비활성화, 토큰 폐기, 도구 승인 해제, 네트워크 차단을 한 번에 일으키는 조치. 사고 대응의 첫 조치([07 7.3절](../docs/07-integration-write-design.md)).
- **섀도 AI(Shadow AI)** — IT와 거버넌스가 존재를 모르는 채 임직원과 부서가 업무에 쓰는 AI 도구와 서비스. 이 가이드의 관점에서는 종료하지 못한 파일럿과 미등록 에이전트가 주된 출처이며, 금지가 아니라 레지스트리 등록과 등급 판정으로 양성화한다([14 14.12절](../docs/14-operations.md), [⑤ 07 7.2.3절](https://github.com/JaeHoYun/vcf-private-ai/blob/main/05-security/docs/07-audit-compliance.md)).
- **ASI01–ASI10** — OWASP Top 10 for Agentic Applications 2026의 에이전트 위협 코드. 목표 탈취, 도구 오남용, 신원과 권한 남용, 에이전트 공급망, 예기치 않은 코드 실행, 메모리와 컨텍스트 오염, 안전하지 않은 에이전트 간 통신, 연쇄 실패, 사람과 에이전트 간 신뢰 악용, 이탈 에이전트([12 12.4절](../docs/12-service-security.md)).

### A1.1.2 모델과 서빙

- **Model Runtime** — completion, embedding 모델을 추론 엔진으로 실행해 OpenAI 호환 엔드포인트로 노출하는 PAIS 모듈.
- **Model Gallery** — 모델 아티팩트의 중앙 저장소. Harbor(OCI 레지스트리) 기반.
- **Harbor** — OCI 호환 컨테이너 레지스트리. Model Gallery의 저장소 구현.
- **vLLM, llama.cpp, Infinity** — Model Runtime의 추론 엔진. PAIS 3.0 기준 vLLM 0.20.0(생성과 임베딩, CUDA 13.0 기본), llama.cpp b9309(CPU 추론), Infinity 0.0.76(임베딩 전용). 2.1은 vLLM 0.11.2, llama.cpp b7739. 버전 정본은 [README 기반 버전표](../README.md#기반-버전-source-of-truth).
- **chat completion / OpenAI 호환 API** — `/chat/completions`, `/completions`, `/embeddings` 등 OpenAI 규약을 따르는 추론 API. 에이전트는 챗 컴플리션 엔드포인트로 노출된다.
- **Artifact Mirroring Tool** — 에어갭 환경에 모델과 아티팩트를 미러링해 반입하는 PAIS 도구(PAIS 2.1에서 도입). pais CLI 플러그인의 `vcf pais amt pull/push` 명령으로 수행한다(VCF CLI 명령 레퍼런스에는 누락, Disconnected Environment 배포 문서에 명시).
- **NIM(NVIDIA Inference Microservices)** — NVIDIA가 제공하는 컨테이너형 추론 모델. Model Gallery로 반입해 관리할 수 있다.
- **공유 모델(provider / consumer)** — PAIS 3.0부터 한 인스턴스(provider)가 서빙하는 completion 또는 embedding 엔드포인트를 다른 인스턴스와 네임스페이스(consumer)가 자기 엔드포인트처럼 참조하는 방식. 지식베이스, 에이전트, 도구는 consumer 쪽에 남는다. 인스턴스 간 접근에는 provider가 발급한 API 토큰이 필요하다.
- **원격 클라우드 모델** — PAIS 3.0부터 Google Gemini 네이티브 API, Gemini Enterprise Agent Platform(구 Vertex AI), OpenAI 호환 서비스의 모델을 `InferenceGatewayRoute` 리소스로 연결해 같은 엔드포인트 형태로 쓰는 방식. 프롬프트가 사외로 나가므로 반출 정책이 전제된다.
- **API 토큰** — PAIS 3.0부터 VCF Automation 계정(`vcfa-<org>-...`) 또는 PAIS 로컬 계정(`pais-<인증공급자>-...`)이 직접 발급하는 장기 토큰. 공유 모델 접근, VCF Consumption CLI 실행, PAIS API 인증에 쓰며 `Authorization: Bearer` 헤더로 보낸다. 외부 OIDC 토큰은 인스턴스 간 접근에 쓸 수 없다.

### A1.1.3 데이터와 검색

- **Data Indexing and Retrieval** — 데이터소스를 인덱싱해 지식베이스로 묶고 검색을 제공하는 PAIS 모듈.
- **지식베이스(Knowledge Base)** — 에이전트가 검색하는 인덱싱된 문서 집합.
- **pgvector** — 벡터 임베딩 저장과 검색을 지원하는 PostgreSQL 확장. PAIS 지식베이스의 벡터 저장에 쓰인다.
- **임베딩(Embedding)** — 텍스트를 벡터로 변환한 표현. 인덱싱과 질의에 같은 임베딩 모델을 써야 검색이 일관된다.
- **Top-K** — 검색에서 가져올 상위 문서 수. 유사도 컷오프와 함께 검색 정밀도와 잡음을 조절한다.
- **RAG(검색 증강 생성)** — 답하기 전 지식베이스를 검색해 컨텍스트로 넣는 고정 흐름. 상세는 시리즈 ④.
- **환각(Hallucination)** — 검색과 도구 근거 없이 그럴듯하게 지어낸 답.
- **파생 사본** — 원문 문서에서 만들어지는 청크, 임베딩, 캐시, 로그, 추적 데이터. 보호 문서를 인입할 때 원문의 등급을 그대로 상속시켜 통제하는 대상([06 6.1절](../docs/06-data-onboarding.md)).
- **복호화 전처리 존** — 보호 문서를 서버 측에서 복호화해 청킹과 임베딩까지 마치는 격리 구역. 평문은 이 존 밖으로 나가지 않는다([06 6.4절](../docs/06-data-onboarding.md)).
- **검색단 권한 필터** — 사용자의 권한(부서, 그룹, 등급)을 검색 단계의 필터로 걸어 권한 밖 문서가 프롬프트에 들어가지 않게 하는 통제. 관리형 지식베이스는 지식베이스 단위 분리로, 커스텀 검색은 청크 ACL로 구현([04 4.5절](../docs/04-identity-propagation.md)).
- **토큰 팽창 계수** — 같은 내용을 한국어로 썼을 때 영어보다 토큰이 늘어나는 비율. 토크나이저마다 달라 자사 문서로 실측하며, 컨텍스트 예산과 사이징과 비용의 입력이 된다([10 10.7절](../docs/10-models-serving.md)).

### A1.1.4 실행과 운영

- **VKS(vSphere Kubernetes Service)** — Supervisor의 vSphere Namespace에 프로비저닝되는 쿠버네티스 클러스터. 모델 엔드포인트와 에이전트 실행 기반.
- **VKr(vSphere Kubernetes release)** — VKS 클러스터에 쓰는, VMware가 서명하고 지원하는 쿠버네티스 배포 릴리스. 버전은 쿠버네티스 마이너 버전을 따른다(예: VKr 1.33 = 쿠버네티스 1.33 기반).
- **Supervisor / vSphere Namespace** — VKS, PAIS가 동작하는 vSphere 상의 쿠버네티스 제어와 격리 단위.
- **DLVM(Deep Learning VM)** — 프로토타이핑과 노트북용 딥러닝 VM 이미지. 프로덕션은 VKS를 쓴다.
- **GPU Operator** — VKS에서 GPU 드라이버와 자원을 관리하는 쿠버네티스 오퍼레이터. PAIS 3.0 기준 25.10.1이 기본이고 26.3.1을 선택할 수 있다(2.1은 25.10.1 단일).
- **Observability** — 추론, GPU, 에이전트 상호작용을 추적, 관측하는 PAIS 모듈. 2.1에서 확장.
- **OpenTelemetry / LLM trace** — 표준 관측 프레임워크와 그 위의 LLM 추적. 사용자, 모델, 에이전트, 지식베이스 상호작용을 따라간다.
- **TTFT(Time to First Token)** — 첫 토큰까지 걸린 시간. 체감 응답성 지표.
- **종단 지연(End-to-end latency)** — 요청부터 최종 응답까지 걸린 전체 시간.
- **SLO(Service Level Objective)** — 서비스가 지켜야 할 목표 수준(가용성, 지연, 오류율 등). 관측 기준선 위에 정해 이탈을 감시한다.
- **NVAIE(NVIDIA AI Enterprise)** — NVIDIA의 엔터프라이즈 AI 소프트웨어 라이선스. vGPU 사용 시 필요하며 패스스루 모드에서는 불필요하다.

### A1.1.5 신원, 통합, 출시

- **BFF(Backend For Frontend)** — 클라이언트와 오케스트레이션 사이에서 사용자 인증, 세션, 요청 정형, 입력 가드를 맡는 프런트엔드 전용 백엔드. 4-Tier 골격의 두 번째 층([11 11.1절](../docs/11-app-integration-ux.md)).
- **토큰 교환(OAuth 2.0 Token Exchange, RFC 8693)** — 사용자 토큰과 서비스 자격증명을 인가 서버에 제시해 대상 시스템용 audience와 scope를 가진 새 토큰을 받는 표준. 위임(delegation)은 `act` 클레임에 행위자를 남기고, 가장(impersonation)은 사용자와 구별되지 않는다([04 4.3절](../docs/04-identity-propagation.md)).
- **AI 게이트웨이(1계층)** — 앱과 ML API Gateway 사이에 두는 선택 계층. 키와 팀 예산, 레이트리밋, 모델 별칭 라우팅, 캐시를 맡는다. 0계층은 경계(로드밸런서와 WAF), 2계층은 PAIS 내장 ML API Gateway([05 5.2절](../docs/05-platform-consumption.md)).
- **쇼백(showback)과 차지백(chargeback)** — 팀별 자원과 토큰 사용량을 보여 주는 것(쇼백)과 실제로 비용을 부과하는 것(차지백). 쇼백을 먼저 하고 미터링이 검증된 뒤 차지백으로 간다([05 5.4절](../docs/05-platform-consumption.md)).
- **멱등 키(Idempotency key)** — 같은 쓰기 요청이 재시도돼도 한 번만 반영되게 하는 요청 식별자. 생성 주체, 저장 위치, 유효 기간을 정해 쓴다([07 7.4절](../docs/07-integration-write-design.md)).
- **보상(compensation)** — 다단계 쓰기의 일부가 실패했을 때 이미 반영된 단계를 되돌리는 절차. 트랜잭션 경계를 넘는 연동에서 롤백을 대신한다([07 7.4절](../docs/07-integration-write-design.md)).
- **릴리스 매니페스트** — 한 릴리스를 이루는 모델 리비전, 엔진 버전, 프롬프트 해시, 도구 설명 해시, 지식베이스와 임베딩, 가드레일 정책, 평가셋 버전을 한 장에 적은 기록. CI가 생성한다([13 13.9절](../docs/13-evaluation-guardrails.md)).
- **출시 심사 패키지** — 위험 등급, 신원 계약, 데이터 소스 승인, 쓰기 분류, 매니페스트, 평가와 레드팀 결과, 고지와 운영 준비, 법무 확인을 묶어 심사 주체에게 제출하는 묶음([13 13.10절](../docs/13-evaluation-guardrails.md)).
- **게이트(PoC, 파일럿, 프로덕션)** — 서비스가 통과하는 세 단계. PoC는 합성이나 공개 데이터로 소수가 써 보는 단계, 파일럿은 실제 데이터를 한정된 사용자가 읽기 전용으로 쓰는 단계, 프로덕션은 그 제한을 푸는 단계. 단계마다 필수 통제가 늘어난다([12 12.7절](../docs/12-service-security.md)).

## A1.2 참조 링크

작성 시점 1차 출처입니다. 기능, 버전, 동작은 릴리스마다 바뀌므로 적용 전 최신 공식 문서로 재확인하시기 바랍니다.

- [Private AI Services 릴리스 노트 — 3.0, 2.1.2, 2.1 (Broadcom TechDocs, 9.1 문서 경로)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/private-ai-release-notes/vmware-private-ai-services-release-notes.html)
- [Private AI Services 릴리스 노트 — 2.1, 2.0.x (Broadcom TechDocs, 9.0 문서 경로)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-release-notes/vmware-private-ai-services-release-notes.html)
- [Private AI Services 상세 디자인 (VCF 9.1 디자인 라이브러리)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-9-0-and-later/9-1/design/design-library/private-ai-platform-detailed-design/private-ai-services.html)
- [What is Private AI Services (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-foundation-9-x/what-is-private-ai-services.html)
- [에이전트 생성 — Create an Agent for a Generative AI Application (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-foundation-9-x/what-is-private-ai-services/deploy-an-agent-for-a-rag-application.html)
- [VCF CLI v9 — pais 명령 레퍼런스 (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/vcf/vcf-consumption/latest/consumer-interfaces-in-vcf/installing-and-using-vcf-cli-v9/command-reference2/pais2.html)
- [Streamline, Simplify and Protect all your AI workloads with VCF 9.1 (blogs.vmware.com)](https://blogs.vmware.com/cloud-foundation/2026/05/05/streamline-simplify-and-protect-all-your-ai-workloads-with-vcf-9-1/)
- [Model Gallery — JupyterLab Notebooks (blogs.vmware.com)](https://blogs.vmware.com/cloud-foundation/2026/02/26/model-gallery-how-to-use-jupyterlab-notebooks-to-simplify-model-deployment-and-management/)
- [Private AI Services API 레퍼런스 (developer.broadcom.com)](https://developer.broadcom.com/xapis/vmware-private-ai-service-api/latest/)
- [Share a Model with Other Private AI Services Instances (Broadcom TechDocs, 3.0)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/what-is-private-ai-services/share-a-model-with-other-private-ai-services-instances.html)
- [Connect to a Remote Model Running in the Cloud (Broadcom TechDocs, 3.0)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/what-is-private-ai-services/connect-to-a-remote-model-running-in-the-cloud.html)
- [Generate API Tokens for VCF Automation or Local Private AI Services Accounts (Broadcom TechDocs, 3.0)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-1/what-is-private-ai-services/generate-api-tokens-for-local-accounts.html)
- [Connect an MCP Server to Private AI Services (Broadcom TechDocs)](https://techdocs.broadcom.com/us/en/vmware-cis/private-ai/foundation-with-nvidia/9-0/private-ai-foundation-9-x/what-is-private-ai-services/adding-mcp-servers-for-real-time-data-access-and-specialized-ai-capabilities/connect-to-an-mcp-server.html)

**표준, 프레임워크, 규제** — 설계와 검증 편이 근거로 삼은 공개 문서입니다. 국내 규제의 시행 일정은 [AX 방법론 부록 A2](https://github.com/JaeHoYun/enterprise-ax-methodology/blob/main/appendix/A2-kr-regulatory-timeline.md)가 단일 출처입니다.

- [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/), [OWASP GenAI LLM Top 10 2026](https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/)
- [OWASP, A Practical Guide for Securely Using Third-Party MCP Servers 1.0](https://genai.owasp.org/resource/cheatsheet-a-practical-guide-for-securely-using-third-party-mcp-servers-1-0/)
- [MCP 사양 2026-07-28 변경 사항](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [RFC 8693 OAuth 2.0 Token Exchange](https://datatracker.ietf.org/doc/html/rfc8693)
- [CSA, Levels of Autonomy for Agentic AI (2026-01-28)](https://cloudsecurityalliance.org/blog/2026/01/28/levels-of-autonomy)
- [CISA 외 공동, Careful Adoption of Agentic AI Services (2026-05-01)](https://www.cisa.gov/resources-tools/resources/careful-adoption-agentic-ai-services)
- [금융위원회, 금융분야 인공지능 가이드라인 통합 개정 (2026-06-18)](https://fsc.go.kr/no010101/87142)
- [개인정보보호위원회, 생성형 인공지능 개발, 활용을 위한 개인정보 처리 안내서 (2025-08-06)](https://www.pipc.go.kr/np/cop/bbs/selectBoardArticle.do?bbsId=BS074&mCode=C020010000&nttId=11410)

**실습과 구성 사례(공개 자료)** — 본문에서 인용한 따라 하기용 자료입니다.

- [Building your GenAI Agents on VCF with Private AI Services — 전체 파이프라인 데모 (blogs.vmware.com, 2025-08)](https://blogs.vmware.com/cloud-foundation/2025/08/26/vmware-private-ai-services-demo/)
- [How to Connect your VMware Private AI Services Agents to OpenWeb UI (blogs.vmware.com, 2025-08)](https://blogs.vmware.com/cloud-foundation/2025/08/15/how-to-connect-your-vmware-private-ai-services-agents-to-openweb-ui/)
- [Activate VCF Private AI Services (blogs.vmware.com, 2026-01)](https://blogs.vmware.com/cloud-foundation/2026/01/15/activate-vcf-private-ai-services/)
- [Deploying PAIS: Navigating Supervisor Networking Stack (blogs.vmware.com, 2026-06)](https://blogs.vmware.com/cloud-foundation/2026/06/11/deploying-vmware-cloud-foundation-private-ai-services-navigating-supervisor-networking-stack/)
- [Keycloak OIDC+PKCE 구성 (williamlam.com, 2026-08)](https://williamlam.com/2026/08/configuring-oidc-with-pkce-in-keycloak-for-vcf-private-ai-services.html) | [Authentik IdP 구성 (williamlam.com, 2025-09)](https://williamlam.com/2025/09/ms-a2-vcf-9-0-lab-configuring-authentik-identity-provider-vmware-for-private-ai-services-pais.html)
- [mcp-langgraph-vllm — LangGraph + 커스텀 MCP 서버 + vLLM 데모 (GitHub)](https://github.com/davgordo/mcp-langgraph-vllm)

시리즈 형제 가이드는 [시리즈 허브](https://github.com/JaeHoYun/vcf-private-ai)에서 모두 볼 수 있습니다.

---
[← 이전: 14 운영과 Day-2](../docs/14-operations.md) | [목차](../README.md) | [다음: A2 워크시트 →](A2-worksheets.md)
