"""저장소 Markdown 문서에 수록하는 다이어그램을 라이트, 다크 SVG 2종으로 생성한다.

실행: python3 assets/build_diagrams.py
문서는 <picture> 요소로 GitHub 테마에 맞는 파일(-light.svg, -dark.svg)을 표시한다.
문구나 배치를 고칠 때는 SVG를 직접 수정하지 않고 이 스크립트를 수정한 뒤 다시 실행한다.
작도 도구(Diagram 클래스와 색상)는 시리즈 저장소 vcf-private-ai의 assets/build_diagrams.py와 같은 기준을 사용한다.
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.dirname(os.path.abspath(__file__))

# GitHub Primer 색상 기준
THEMES = {
    "light": dict(
        bg="#ffffff", text="#1f2328", muted="#59636e", arrow="#59636e", frame="#afb8c1",
        neutral_fill="#f6f8fa", neutral_stroke="#d0d7de", neutral_accent="#59636e",
        blue_fill="#ddf4ff", blue_stroke="#54aeff", blue_accent="#0969da",
        purple_fill="#fbefff", purple_stroke="#c297ff", purple_accent="#8250df",
        green_fill="#dafbe1", green_stroke="#4ac26b", green_accent="#1a7f37",
        orange_fill="#fff1e5", orange_stroke="#fb8f44", orange_accent="#bc4c00",
        red_fill="#ffebe9", red_stroke="#ff8182", red_accent="#cf222e",
    ),
    "dark": dict(
        bg="#0d1117", text="#f0f6fc", muted="#9198a1", arrow="#9198a1", frame="#484f58",
        neutral_fill="#151b23", neutral_stroke="#3d444d", neutral_accent="#9198a1",
        blue_fill="#11284a", blue_stroke="#1f6feb", blue_accent="#4493f8",
        purple_fill="#231c35", purple_stroke="#8957e5", purple_accent="#ab7df8",
        green_fill="#122a1c", green_stroke="#2f9e4f", green_accent="#3fb950",
        orange_fill="#2d1c0f", orange_stroke="#bd561d", orange_accent="#f0883e",
        red_fill="#25171c", red_stroke="#da3633", red_accent="#f85149",
    ),
}
FONT = ("-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Apple SD Gothic Neo', 'Malgun Gothic', "
        "'Noto Sans KR', 'Noto Sans CJK KR', Helvetica, Arial, sans-serif")

# 줄 스타일: 글자 크기, 굵기, 색상 토큰, 줄 높이
STY = {
    "big": (18, 700, "text", 24),
    "title": (15, 700, "text", 21),
    "sub": (13, 400, "muted", 18),
    "body": (13, 400, "text", 18),
}


def text_width(s, size):
    """배지 폭 계산용 근사치."""
    return sum(size * (1.0 if ord(c) > 0x2E80 else 0.6) for c in s)


class Diagram:
    def __init__(self, w, h, title, desc, t):
        self.w, self.h, self.t = w, h, t
        self.title, self.desc = title, desc
        self.o = []

    def c(self, key):
        return self.t.get(key, key)

    def text(self, x, y, s, size=13, weight=400, color="text", anchor="start", halo=False):
        attrs = f' font-size="{size}"'
        if weight != 400:
            attrs += f' font-weight="{weight}"'
        if anchor != "start":
            attrs += f' text-anchor="{anchor}"'
        attrs += f' fill="{self.c(color)}"'
        if halo:
            attrs += f' stroke="{self.t["bg"]}" stroke-width="4" stroke-linejoin="round" paint-order="stroke"'
        self.o.append(f'<text x="{x:g}" y="{y:g}"{attrs}>{escape(s)}</text>')

    def badge(self, x, y, s, kind, anchor="start"):
        """(x, y)는 배지 왼쪽 위. anchor가 middle이면 x가 중심."""
        bw = text_width(s, 12) + 14
        if anchor == "middle":
            x -= bw / 2
        self.o.append(f'<rect x="{x:g}" y="{y:g}" width="{bw:g}" height="20" rx="10" fill="{self.c(kind + "_accent")}"/>')
        self.text(x + bw / 2, y + 14.5, s, 12, 700, self.t["bg"], "middle")
        return bw

    def lines(self, x, y, w, h, lines, align="middle", badge=None, kind="neutral"):
        """lines: [(문자열, 스타일)]. badge가 있으면 가운데 정렬은 첫 줄 위에, 왼쪽 정렬은 첫 줄 앞에 표시."""
        total = sum(STY[st][3] for _, st in lines)
        if badge and align == "middle":
            total += 26
        cy = y + (h - total) / 2
        if badge and align == "middle":
            self.badge(x + w / 2, cy, badge, kind, "middle")
            cy += 26
        for i, (s, st) in enumerate(lines):
            size, wt, col, lh = STY[st]
            base = cy + lh * 0.74
            if align == "middle":
                self.text(x + w / 2, base, s, size, wt, col, "middle")
            else:
                tx = x + 14
                if badge and i == 0:
                    tx += self.badge(tx, base - 15, badge, kind) + 8
                self.text(tx, base, s, size, wt, col)
            cy += lh

    def box(self, x, y, w, h, lines, kind="neutral", dashed=False, align="middle", badge=None, fill=True):
        da = ' stroke-dasharray="6 4"' if dashed else ""
        f = self.c(kind + "_fill") if fill else "none"
        self.o.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="8" fill="{f}" '
                      f'stroke="{self.c(kind + "_stroke")}" stroke-width="1.5"{da}/>')
        self.lines(x, y, w, h, lines, align, badge, kind)

    def cyl(self, x, y, w, h, lines, kind="green"):
        ry = 8
        f, s = self.c(kind + "_fill"), self.c(kind + "_stroke")
        self.o.append(f'<path d="M{x:g},{y + ry:g} A{w / 2:g},{ry} 0 0 1 {x + w:g},{y + ry:g} V{y + h - ry:g} '
                      f'A{w / 2:g},{ry} 0 0 1 {x:g},{y + h - ry:g} Z" fill="{f}" stroke="{s}" stroke-width="1.5"/>')
        self.o.append(f'<path d="M{x:g},{y + ry:g} A{w / 2:g},{ry} 0 0 0 {x + w:g},{y + ry:g}" '
                      f'fill="none" stroke="{s}" stroke-width="1.5"/>')
        self.lines(x, y + 2 * ry, w, h - 2 * ry, lines)

    def frame(self, x, y, w, h, title=None, dashed=False, kind=None, note=None, tx=None):
        """kind가 있으면 해당 색상의 테두리, note는 제목 줄 오른쪽 끝에 표시. tx는 제목 시작 x(화살표 회피용)."""
        da = ' stroke-dasharray="6 4"' if dashed else ""
        stroke = self.c(kind + "_stroke") if kind else self.t["frame"]
        sw = 2 if kind else 1.5
        self.o.append(f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="10" fill="none" '
                      f'stroke="{stroke}" stroke-width="{sw}"{da}/>')
        if title:
            self.text(tx if tx is not None else x + 14, y + 22, title, 13, 700, (kind + "_accent") if kind else "muted")
        if note:
            self.text(x + w - 14, y + 22, note, 13, 700, (kind + "_accent") if kind else "muted", "end")

    def arrow(self, pts, dashed=False, both=False, head=True):
        d = "M" + " L".join(f"{x:g},{y:g}" for x, y in pts)
        attrs = ' stroke-dasharray="5 4"' if dashed else ""
        if head:
            attrs += ' marker-end="url(#ah)"'
        if both:
            attrs += ' marker-start="url(#ah)"'
        self.o.append(f'<path d="{d}" fill="none" stroke="{self.t["arrow"]}" stroke-width="1.5"{attrs}/>')

    def label(self, x, y, lines, anchor="start", step=None):
        """화살표 설명. step이 있으면 번호 원을 앞에 표시(왼쪽 정렬 전용)."""
        if isinstance(lines, str):
            lines = [lines]
        if step is not None:
            self.o.append(f'<circle cx="{x + 9:g}" cy="{y - 4.5:g}" r="9" fill="{self.t["blue_accent"]}" '
                          f'stroke="{self.t["bg"]}" stroke-width="2"/>')
            self.text(x + 9, y, str(step), 11, 700, self.t["bg"], "middle")
            x += 22
        for i, s in enumerate(lines):
            self.text(x, y + i * 17, s, 12, 400, "muted", anchor, halo=True)

    def legend(self, x, y, items):
        """items: [(kind, 설명)]. kind가 dashed면 점선 사각형, line-dashed면 점선 화살표."""
        for kind, s in items:
            if kind == "title":
                self.text(x, y, s, 13, 700, "muted")
                x += text_width(s, 13) + 24
                continue
            if kind == "dashed":
                self.o.append(f'<rect x="{x:g}" y="{y - 12:g}" width="18" height="14" rx="3" fill="none" '
                              f'stroke="{self.t["frame"]}" stroke-width="1.5" stroke-dasharray="4 3"/>')
            elif kind == "line-dashed":
                self.arrow([(x, y - 5), (x + 18, y - 5)], dashed=True)
            else:
                self.o.append(f'<rect x="{x:g}" y="{y - 12:g}" width="18" height="14" rx="3" '
                              f'fill="{self.c(kind + "_fill")}" stroke="{self.c(kind + "_stroke")}" stroke-width="1.5"/>')
            self.text(x + 26, y, s, 12, 400, "muted")
            x += 26 + text_width(s, 12) + 24

    def render(self):
        head = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
            f'viewBox="0 0 {self.w} {self.h}" font-family="{FONT}" role="img" aria-labelledby="t d">',
            f'<title id="t">{escape(self.title)}</title>',
            f'<desc id="d">{escape(self.desc)}</desc>',
            '<defs><marker id="ah" viewBox="0 0 10 10" refX="10" refY="5" markerUnits="userSpaceOnUse" '
            f'markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" '
            f'fill="{self.t["arrow"]}"/></marker></defs>',
        ]
        return "\n".join(head + self.o + ["</svg>"]) + "\n"


# 06: 데이터 소스 온보딩의 여섯 개 존
def data_onboarding_zones(t):
    d = Diagram(1160, 992, "데이터 소스 온보딩의 여섯 개 존",
                "존 1 분산 소스 저장소의 문서를 존 2 수집 커넥터가 암호문 상태로 가져오고, "
                "존 3 복호화 전처리(격리 구역)가 문서보안 서버와 키 서버에 전용 서비스 계정으로 요청해 복호화한 뒤 "
                "정규화, 형식 변환, OCR, PII 마스킹, 청킹, 접근 주체 평탄화를 거쳐 S3 호환 스테이징에 저장한다. "
                "평문은 존 3 밖으로 나가지 않고, 등급과 허용 그룹이 붙은 청크만 존 4 인덱스 저장소로 전송된다. "
                "존 4는 PAIS Data Indexing and Retrieval 또는 커스텀 pgvector이며 등급별 DSM PostgreSQL 인스턴스에 저장한다. "
                "존 5의 앱과 BFF는 사용자 그룹 클레임으로 사전 필터해 검색하고 출력 통제를 거쳐 답을 제시한다. "
                "존 6은 복호화 로그, 검색 로그, LLM 추적을 중앙 수집하고, 문서보안 서버의 정책 변경 이벤트를 받아 "
                "해당 청크를 즉시 비활성화한다.", t)
    L, R = 24, 1112          # 프레임 왼쪽, 오른쪽 끝
    xi, xe = L + 16, R - 16  # 프레임 안쪽 시작, 끝

    # 존 1. 분산 소스 저장소
    d.frame(L, 24, R - L, 112, "존 1. 분산 소스 저장소 (기존 시스템)")
    bw = (xe - xi - 2 * 36) / 3
    sx = [xi + i * (bw + 36) for i in range(3)]
    d.box(sx[0], 60, bw, 60, [("문서관리시스템, 협업 포털", "title"), ("우선 대상", "sub")])
    d.box(sx[1], 60, bw, 60, [("파일 서버, NAS", "title"), ("우선 대상", "sub")])
    d.box(sx[2], 60, bw, 60, [("그룹웨어 첨부, 개인 PC", "title"), ("중앙 저장소로 모은 뒤 대상", "sub")], dashed=True)

    # 존 2. 수집
    d.frame(L, 176, 536, 104, "존 2. 수집 (존 3과 같은 네임스페이스)")
    d.box(xi, 212, 504, 52, [("크롤러와 커넥터", "title"), ("변경 감지 커서, 중복 제거, 버전 관리", "sub")])
    d.arrow([(300, 120), (300, 212)])
    d.arrow([(500, 120), (500, 212)])
    d.label(290, 160, "보호 문서는 암호문 상태로 수집", "end")

    # 문서보안 서버, 키 서버
    d.box(600, 192, 400, 72, [("문서보안 서버, 키 서버", "title"), ("기존 시스템. 전용 서비스 계정과", "sub"),
                              ("허용 프로세스를 별도 정책으로 등록", "sub")])

    # 존 3. 복호화 전처리 (격리)
    zy = 328
    d.frame(L, zy, R - L, 156, "존 3. 복호화 전처리 (격리 VKS 클러스터나 네임스페이스, NSX 분산 방화벽)",
            kind="purple", note="평문은 이 존 밖으로 나가지 않음", tx=258)
    cw, gap, by, bh = 184, (xe - xi - 5 * 184) / 4, zy + 44, 92
    cx = [xi + i * (cw + gap) for i in range(5)]
    d.box(cx[0], by, cw, bh, [("복호화 워커", "title"), ("서비스 신원으로", "sub"), ("문서 단위 권한 확인", "sub")], "purple")
    d.box(cx[1], by, cw, bh, [("정규화", "title"), ("형식 변환, OCR", "sub")], "purple")
    d.box(cx[2], by, cw, bh, [("PII 마스킹, 청킹", "title"), ("개인정보를 가린 뒤", "sub"), ("청크로 분할", "sub")], "purple")
    d.box(cx[3], by, cw, bh, [("접근 주체 평탄화", "title"), ("정책을 허용 그룹 목록으로", "sub"),
                              ("비어 있으면 제한 처리", "sub")], "purple")
    d.cyl(cx[4], by - 4, cw, bh + 8, [("스테이징", "title"), ("S3 호환", "sub")], "purple")
    my = by + bh / 2
    for i in range(4):
        d.arrow([(cx[i] + cw, my), (cx[i + 1], my)])
    d.label(cx[0] + cw + gap / 2, my - 8, "평문", "middle")
    # 수집에서 복호화로, 문서보안 서버와 복호화 워커
    d.arrow([(100, 264), (100, by)])
    d.label(108, 296, "암호문")
    d.arrow([(620, 264), (620, 304), (196, 304), (196, by)], both=True)
    d.label(408, 297, "복호화와 키 요청", "middle")

    # 존 4. 인덱스 저장 (등급별 분리)
    ry = 528
    z4x = 600
    d.frame(z4x, ry, R - z4x, 248, "존 4. 인덱스 저장 (등급별 분리)", kind="green")
    iw = (xe - (z4x + 16) - 40) / 2
    ax, bx = z4x + 16, z4x + 16 + iw + 40
    d.box(ax, ry + 40, iw, 104, [("PAIS Data Indexing", "title"), ("and Retrieval", "title"),
                                 ("관리형 지식베이스", "sub"), ("지식베이스와 인스턴스가 경계", "sub")], "green")
    d.box(bx, ry + 40, iw, 104, [("커스텀 pgvector", "title"), ("청크 메타데이터로", "sub"),
                                 ("문서 단위 접근 주체 필터", "sub")], "green")
    d.text(ax + iw + 20, ry + 97, "또는", 13, 700, "muted", "middle")
    d.cyl(ax, ry + 162, xe - ax, 70, [("DSM PostgreSQL, pgvector", "title"),
                                      ("등급별 인스턴스 분리, vSAN 암호화 스토리지", "sub")])
    sxc = cx[4] + cw / 2
    d.arrow([(sxc, by + bh + 4), (sxc, ry)])
    d.label(sxc - 10, 510, "등급과 허용 그룹이 붙은 청크", "end")

    # 사용자와 존 5. 쿼리와 출력
    d.box(L, ry + 40, 116, 192, [("사용자", "title"), ("질문하고", "sub"), ("답을 열람", "sub")])
    z5x, z5w = 176, 324
    d.frame(z5x, ry, z5w, 248, "존 5. 쿼리와 출력", kind="blue")
    qx, qw = z5x + 16, z5w - 32
    d.box(qx, ry + 40, qw, 88, [("앱과 BFF", "title"), ("사용자 그룹 클레임으로 사전 필터", "sub"),
                                ("기본 거부, 필요 시 문서보안 재검증", "sub")], "blue")
    d.box(qx, ry + 160, qw, 72, [("출력 통제", "title"), ("등급 표시, 복사와 공유 차단,", "sub"),
                                 ("개인정보 마스킹, 유출 방지", "sub")], "blue")
    d.arrow([(qx + qw / 2, ry + 128), (qx + qw / 2, ry + 160)])
    d.arrow([(L + 116, ry + 72), (qx, ry + 72)])
    d.label(158, ry + 64, "질문", "middle")
    d.arrow([(qx, ry + 208), (L + 116, ry + 208)])
    d.label(158, ry + 200, "답", "middle")
    d.arrow([(qx + qw, ry + 84), (z4x, ry + 84)], both=True)
    d.label((qx + qw + z4x) / 2, ry + 76, "사전 필터 검색", "middle")

    # 존 6. 감사와 수명주기
    ey = 820
    d.frame(L, ey, R - L, 124, "존 6. 감사와 수명주기")
    lx, lw = 136, 576
    d.box(lx, ey + 36, lw, 72, [("중앙 로그 수집", "title"), ("복호화 로그, 검색 로그, LLM 추적을 문서 ID로 연결", "sub"),
                                ("로그 저장소도 원문 등급 자산으로 관리", "sub")])
    fx = 760
    d.box(fx, ey + 36, xe - fx, 72, [("수명주기 관리", "title"), ("권한 회수, 등급 상향, 문서 폐기 이벤트 수신", "sub"),
                                     ("청크 즉시 비활성화, 세션 히스토리 무효화", "sub")])
    lmy = ey + 72
    # 감사 로그 수집
    d.arrow([(L, my), (12, my), (12, lmy), (lx, lmy)], dashed=True)
    d.label(36, lmy - 8, "복호화 로그")
    d.arrow([(qx + qw / 2, ry + 232), (qx + qw / 2, ey + 36)], dashed=True)
    d.label(qx + qw / 2 + 10, 804, "LLM 추적")
    d.arrow([(660, ry + 248), (660, ey + 36)], dashed=True)
    d.label(670, 804, "검색 로그")
    # 정책 변경 이벤트와 청크 비활성화
    d.arrow([(1000, 228), (1140, 228), (1140, lmy), (xe, lmy)], dashed=True)
    d.label(1070, 220, "정책 변경 이벤트", "middle")
    d.arrow([(928, ey + 36), (928, ry + 248)], dashed=True)
    d.label(938, 804, "청크 즉시 비활성화")

    d.legend(L, 976, [("purple", "평문이 존재하는 격리 구역"), ("green", "등급별로 분리한 인덱스"),
                      ("blue", "앱 계층"), ("dashed", "중앙화 뒤에 대상"),
                      ("line-dashed", "감사 로그와 정책 변경 이벤트")])
    return d


# 04: 신원이 표현되는 네 경계와 자체 앱 경로
def identity_propagation_boundaries(t):
    d = Diagram(1160, 416, "신원이 표현되는 네 경계와 자체 앱 경로",
                "사용자 요청은 네 경계를 거친다. ① 사용자에서 BFF까지는 조직 IdP가 발급한 사용자 토큰(OIDC)으로 "
                "사용자, 그룹, 테넌트가 전달된다. ② BFF에서 PAIS 에이전트와 모델까지는 서비스 토큰으로 호출하므로 "
                "사용자 신원이 유실되고 PAIS는 호출한 앱만 확인한다. ③ PAIS에서 MCP 도구 서버까지는 정적 도구 토큰이라 "
                "도구 서버는 PAIS가 호출했다는 것만 확인하고, ④ PAIS에서 지식베이스까지는 인스턴스와 네임스페이스 권한으로 "
                "에이전트에 연결된 지식베이스 전체에 접근한다. 따라서 관리형 에이전트 경로의 도구와 지식베이스는 "
                "에이전트의 모든 사용자에게 안전한 범위로 한정한다. 자체 앱 경로에서는 BFF가 토큰 교환으로 받은 "
                "사용자 범위 토큰으로 사내 시스템과 커스텀 검색을 직접 호출한다.", t)

    by, bh = 100, 76
    ay = by + bh / 2

    # 관리형 에이전트 경로: 사용자 신원이 전달되지 않는 구간
    fx, fy, fw, fh = 548, 40, 588, 352
    d.o.append(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" rx="10" fill="{t["red_fill"]}" opacity="0.55"/>')
    d.frame(fx, fy, fw, fh, "관리형 에이전트 경로 (패턴 A)", kind="red",
            note="② 이후 사용자 신원이 전달되지 않음")

    # 첫 줄: 사용자, BFF, PAIS, MCP 도구 서버
    d.box(24, by, 110, bh, [("사용자", "title"), ("조직 IdP 로그인", "sub")])
    d.box(230, by, 180, bh, [("BFF", "title"), ("사용자, 그룹, 테넌트 확인", "sub")], "blue")
    px, pw = 580, 212
    d.box(px, by, pw, bh, [("PAIS 에이전트, 모델", "title"), ("호출한 앱만 확인", "sub")], "orange")
    mx, mw = 916, 200
    d.box(mx, by, mw, bh, [("MCP 도구 서버", "title"), ("PAIS 호출 여부만 확인", "sub")])

    # ① 사용자 토큰
    d.arrow([(134, ay), (230, ay)])
    d.label(140, ay - 12, "사용자 토큰", step=1)
    d.label(162, ay + 20, "OIDC")
    # ② 서비스 토큰과 유실 지점
    d.arrow([(410, ay), (px, ay)])
    d.label(418, ay - 12, "서비스 토큰", step=2)
    d.badge(479, ay + 8, "사용자 신원 유실", "red", "middle")
    # ③ 정적 도구 토큰
    d.arrow([(px + pw, ay), (mx, ay)])
    d.label(px + pw + 6, ay - 12, "정적 도구 토큰", step=3)
    d.label(px + pw + 28, ay + 20, "도구 서버에 등록")

    # ④ 인스턴스 권한으로 지식베이스 검색
    ky = 280
    d.cyl(px, ky, pw, 84, [("지식베이스 검색", "title"), ("에이전트에 연결된 전체", "sub")], "green")
    kx = px + pw / 2
    d.arrow([(kx, by + bh), (kx, ky)])
    d.label(kx + 10, 226, ["인스턴스와", "네임스페이스 권한"], step=4)

    # 설계 결론
    d.box(828, ky, 288, 84, [("설계 결론", "title"), ("도구와 지식베이스는 에이전트의", "sub"),
                             ("모든 사용자에게 안전한 범위로 한정", "sub")], "red", fill=False, dashed=True)

    # 자체 앱 경로
    d.frame(24, 250, 480, 142, "자체 앱 경로 (패턴 B)", kind="blue", tx=166)
    b1x, b2x, bw2, sy = 40, 280, 208, 296
    d.box(b1x, sy, bw2, 80, [("사내 시스템", "title"), ("사용자 권한으로 실행", "sub")])
    d.box(b2x, sy, bw2, 80, [("커스텀 검색", "title"), ("pgvector, 그룹 클레임 필터", "sub")], "green")
    tx_, jy = 320, 226
    c1, c2 = b1x + bw2 / 2, b2x + bw2 / 2
    d.arrow([(tx_, by + bh), (tx_, jy), (c1, jy), (c1, sy)])
    d.arrow([(tx_, jy), (c2, jy), (c2, sy)])
    d.label(tx_ + 10, 200, "사용자 범위 토큰")
    d.label(tx_ + 10, 217, "토큰 교환(RFC 8693)")
    return d


DIAGRAMS = {
    "data-onboarding-zones": data_onboarding_zones,
    "identity-propagation-boundaries": identity_propagation_boundaries,
}

if __name__ == "__main__":
    for name, build in DIAGRAMS.items():
        for theme, t in THEMES.items():
            with open(os.path.join(OUT, f"{name}-{theme}.svg"), "w", encoding="utf-8") as f:
                f.write(build(t).render())
