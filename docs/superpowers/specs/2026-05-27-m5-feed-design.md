---
title: M5 Feed — AI 뉴스 자동 수집 & Changelog 설계
date: 2026-05-27
status: approved
milestone: M5
---

# M5 Feed — AI 뉴스 자동 수집 & Changelog 설계

## 배경 & 목표

M4(칸반)를 건너뛰고 M5를 먼저 진행한다. 기존 계획의 M5 Feed는 Web Clipper 수동 스크랩만 명시했으나, 이번 구현에서는 다음을 추가한다.

- **자동 헤드라인 수집**: 주요 뉴스 사이트 및 AI 공식 블로그의 헤드라인을 백그라운드에서 주기적으로 수집
- **Changelog 추적**: Claude Code / OpenAI Codex / Google Gemini Code의 릴리즈 노트를 Metering 화면에 통합

---

## 설계 원칙 준수

- **Vault가 진실**: 수집된 항목은 `vault/feed/` 에 마크다운 파일로 저장. 상태(읽음/무시/ingest됨)도 frontmatter로 관리
- **LLM은 ingest 단계에만**: 수집 자체에는 LLM 호출 없음. 비용 0
- **기존 패턴 재사용**: `metering/scanner.py` → `feed/collector.py` 패턴 복제

---

## 아키텍처 & 데이터 흐름

```
[백그라운드 수집 루프]  ← main.py lifespan에서 _collect_loop 태스크 시작
  └─ feed/collector.py
       ├─ RSSCollector      → 뉴스/블로그 소스
       └─ (ScraperCollector → RSS 없는 소스, 필요 시)

  수집 결과 → vault/feed/YYYY-MM-DD-<url-hash[:8]>.md
              frontmatter: { title, url, source, category, status: unread, fetched_at }

[FastAPI 엔드포인트]
  GET  /feed/items          → feed/ 파일 스캔 & frontmatter 파싱
  POST /feed/refresh        → 수집 루프 즉시 트리거 (수동 새로고침)
  POST /feed/status         → { slug, status } 로 frontmatter 갱신
  POST /feed/ingest         → { slugs: string[] } 수신, 각 항목을 순서대로 /agent/ingest에 전달 (항목당 1 SSE 스트림, 순차 처리)

[React Feed 화면]  frontend/src/screens/Feed.tsx
  - 카드 목록 (소스 태그, 날짜, status 표시)
  - 상단 미처리 카운트 + App.tsx 탭 뱃지
  - 필터: 전체 / 뉴스 / AI 공식 / Changelog
  - 체크박스 → "선택 ingest" → LogStream으로 진행 표시
  - 개별 dismiss (숨김, 필터로 복원 가능)

[Metering 화면 확장]
  - 기존 카드 하단에 "Changelog" 섹션 추가
  - /metering/dashboard 응답에 changelogs 필드 추가
  - GitHub Releases RSS 파싱, 최신 3건 표시
```

---

## 수집 소스 목록

| 소스 | 카테고리 | 수집 방식 | URL |
|------|----------|-----------|-----|
| GeekNews (news.hada.io) | 뉴스 | RSS | `https://news.hada.io/rss` |
| AI Times (aitimes.com) | 뉴스 | RSS | `https://www.aitimes.com/rss/allArticle.xml` |
| Anthropic Blog | AI 공식 | RSS | `https://www.anthropic.com/news/rss.xml` |
| OpenAI Blog | AI 공식 | RSS | `https://openai.com/news/rss.xml` |
| Google DeepMind Blog | AI 공식 | RSS | `https://deepmind.google/blog/rss.xml` |
| Claude Code Changelog | Changelog (Metering 전용) | GitHub Releases RSS | `https://github.com/anthropics/claude-code/releases.atom` |
| OpenAI Codex Changelog | Changelog (Metering 전용) | GitHub Releases RSS | `https://github.com/openai/codex/releases.atom` |
| Gemini Code Changelog | Changelog (Metering 전용) | 확인 후 결정 (docs scraping 가능) | TBD |

> 뉴스/블로그 수집 주기: 기본 1시간 (`FEED_COLLECT_INTERVAL` 환경변수로 조정).
> Changelog(Metering용)는 Feed 루프와 별도로 `CHANGELOG_COLLECT_INTERVAL` (기본 6시간) 주기로 수집. Feed 파일로 저장되지 않고 메모리 캐시 후 `/metering/dashboard` 응답에 포함.

---

## 백엔드 파일 구조

```
backend/
└── feed/
    ├── __init__.py
    ├── collector.py   # BaseCollector ABC, RSSCollector 구현, collect_all()
    ├── sources.py     # SOURCES 리스트 (label, url, category, type)
    └── store.py       # FeedStore: feed/ 파일 read/write, frontmatter 파싱·갱신
```

### 핵심 타입

```python
@dataclass
class FeedItem:
    title: str
    url: str
    source: str          # sources.py label
    category: str        # news | ai-official | changelog
    fetched_at: str      # ISO 8601
    status: str = "unread"  # unread | ingested | dismissed
    summary: str = ""    # RSS description (LLM 요약 아님)
```

### 중복 방지

파일명: `YYYY-MM-DD-<sha256(url)[:8]>.md`
- 동일 URL 재수집 시 파일이 이미 존재하면 스킵
- status가 변경된 파일은 덮어쓰지 않음

### main.py 통합

```python
# 기존 _scan_loop 패턴과 동일하게 lifespan에 추가
async def _collect_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(collect_all_feeds)
        except Exception:
            pass
        await asyncio.sleep(_FEED_COLLECT_INTERVAL)
```

---

## 프론트엔드 파일 구조

```
frontend/src/
├── screens/
│   └── Feed.tsx          # 신규
├── components/
│   └── FeedCard.tsx      # 신규 (카드 단위 컴포넌트)
└── api.ts                # getFeedItems, refreshFeed, setFeedStatus, ingestFeedItems 추가
```

### Feed.tsx 레이아웃

```
┌─ Feed ──────────────────────────────────────────────────────────────┐
│  [↻ Refresh]  미처리 N건  [select all unread]  [N selected → Ingest]│
├──────────────────────────────────────────────────────────────────────┤
│  [ALL ×]  [NEWS]  [AI OFFICIAL]  [CHANGELOG]   ← 토글 칩            │
├──────────────────────────────────────────────────────────────────────┤
│▌ □ [GN] GeekNews   LLM 추론 최적화 기법 비교           2h ago        │
│        news.hada.io                                    [dismiss ×]  │
│▌ □ [AN] Anthropic  Claude 4.x released                 1d ago       │
│  □ [CC] Changelog  Claude Code v1.9.0                  2d ago       │
└──────────────────────────────────────────────────────────────────────┘
```

**UI 디자인 규칙 (기존 디자인 시스템 준수):**

- **카드 status 표시**: 좌측 3px 컬러 보더 (nav active 패턴 재사용)
  - `unread`: `t.cyan` + `inset 8px 0 16px -8px cyan55`
  - `ingested`: `#00ff9044` (antigravity green 재사용)
  - `dismissed`: `t.border` (기본 숨김, 필터 복원 시 표시)
- **소스 태그 색상**: news → `t.warn`, ai-official → `t.cyan`, changelog → `t.violet`
- **필터 칩**: `t.mono 9.5px uppercase`, 선택 시 `rgba(122,240,255,0.12)` + `borderGlow`, 미선택 시 `t.bgDeep` + `t.border`
- **체크박스**: native 대신 커스텀 스퀘어 (`1px solid t.border`, 선택 시 cyan fill)
- **동적 액션 바**: 0개 선택 시 ingest 버튼 숨김, N개 선택 시 `NebButton primary`로 등장
- **탭 뱃지**: feedCount > 0일 때 `t.warn` 색으로 전환 (`AppShell`에 `feedCount` prop 추가)
- ingest 시작 후 기존 `LogStream` 컴포넌트를 화면 하단에 마운트

---

## Metering 화면 확장

`/metering/dashboard` 응답에 `changelogs` 필드 추가:

```json
{
  "changelogs": [
    { "tool": "Claude Code", "version": "v1.8.0", "title": "improved tool use", "date": "2026-05-20", "url": "..." },
    { "tool": "OpenAI Codex", "version": "v0.2.1", "title": "streaming fix", "date": "2026-05-18", "url": "..." },
    { "tool": "Gemini Code", "version": null, "title": "수집 불가", "date": null, "url": null }
  ]
}
```

**Changelog 섹션 UI (기존 COLORS 토큰 재사용):**

```
┌─ NebPanel ───────────────────────────────────────────────────┐
│  CHANGELOG TRACKER                                           │  ← mono uppercase
│  ─────────────────────────────────────────────────────────   │
│  ● Claude Code   [v1.8.0]  improved tool use    2026-05-20  │  ← cyan dot
│  ● OpenAI Codex  [v0.2.1]  streaming fix        2026-05-18  │  ← violet dot
│  ○ Gemini Code   [—]       수집 불가             —           │  ← faint (offline)
└──────────────────────────────────────────────────────────────┘
```

- `Metering.tsx` 하단에 `NebPanel`로 Changelog 섹션 추가
- 도구별 색상: `COLORS` 상수 그대로 재사용 (claude_code: cyan, codex: violet, antigravity: green)
- 버전 배지: 기존 `StatusBadge` 스타일 (small bordered pill, mono 8.5px)
- 최신 3건 표시, 클릭 시 `window.open(url, '_blank')`

---

## 에러 처리

- 개별 소스 수집 실패 시 로그만 기록하고 다른 소스는 계속 수집 (소스 격리)
- RSS 파싱 실패 시 해당 소스 스킵, 다음 수집 주기에 재시도
- vault 쓰기 실패 시 예외를 캐치하고 로그 기록

---

## 완료 기준

1. 앱 시작 시 자동으로 헤드라인이 `vault/feed/`에 마크다운 파일로 생성된다
2. Feed 화면에서 미처리 항목이 카드로 표시되고 탭에 카운트 뱃지가 보인다
3. 항목을 선택해 "ingest" 하면 기존 ingest 파이프라인을 타고 wiki 페이지가 생성된다
4. "새로고침" 버튼으로 즉시 수집이 트리거된다
5. dismiss된 항목은 기본 뷰에서 숨겨진다
6. Metering 화면에 Claude Code / Codex / Gemini Code 최신 changelog 3건이 표시된다

---

## 미결 사항

- **Gemini Code changelog URL**: 공식 changelog 페이지 또는 GitHub repo 확인 필요. 없으면 Google AI Studio release notes 대체
- **aitimes.com RSS 유효성**: 실제 RSS URL 검증 필요 (접속 후 확인)
- **수집 주기 기본값**: 1시간으로 설정했으나 실제 운영 후 조정 가능
