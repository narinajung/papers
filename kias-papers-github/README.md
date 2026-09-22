# KIAS 통계물리 최근 논문 — GitHub Pages 판

다섯 분(천현명·이재성·권의준·샤쿨·최재성)의 Google Scholar 논문을 매일 아침 자동으로 받아
한 페이지(index.html)로 만들고, GitHub Pages로 어디서든 열어 보는 저장소입니다.
토픽 분석 탭, "새 논문" 표시(처음 확인한 지 30일 이내), 미분류 태그가 들어 있습니다.

## 올리는 순서 (한 번만)
1. GitHub에서 새 저장소를 만듭니다 (예: `kias-papers`). Pages는 Public 저장소에서 무료입니다.
2. 이 폴더의 파일을 전부 올립니다. 웹에서는 "Add file → Upload files"에 폴더째 끌어다 놓으면 됩니다
   (숨김 폴더 `.github/workflows/update.yml`도 꼭 포함).
3. Settings → Pages → Build and deployment → Source: **Deploy from a branch**, Branch: **main / (root)** → Save.
4. Settings → Actions → General → Workflow permissions: **Read and write permissions** → Save.
5. Actions 탭 → "논문 목록 갱신" → **Run workflow** 로 한 번 돌려 봅니다.

몇 분 뒤 `https://<계정>.github.io/kias-papers/` 에서 열립니다.
휴대폰에서는 이 주소를 홈 화면에 추가하면 앱처럼 씁니다.

## 이후에는
- 매일 06:00(KST)에 자동으로 갱신됩니다. 손으로 돌리려면 Actions → Run workflow.
- 새 논문이 "미분류"로 쌓이면 `topics.json`을 Claude에게 보내 주제를 채운 뒤 올리면 됩니다.
- 사람을 바꾸려면 `kias_papers.py` 맨 위 `PEOPLE`만 고칩니다.
- 분석 글을 고치려면 `template.html`의 `<section class="ana">` 부분입니다.

## 파일
| 파일 | 역할 |
|---|---|
| `.github/workflows/update.yml` | 매일 실행 → index.html, data.json 커밋 |
| `kias_papers.py` | Scholar 받기 + 페이지 만들기 |
| `template.html` | 페이지 디자인과 토픽 분석 글 |
| `topics.json` | 논문 제목 → 주제 코드 |
| `data.json` | 마지막 스냅샷과 각 논문을 처음 본 날짜 (자동 갱신) |
| `index.html` | 결과 페이지 (자동 갱신) |

## 주의
Google Scholar는 자동 접근을 막는 편이라 GitHub의 서버에서 가끔 차단(캡차)될 수 있습니다.
그날은 지난 스냅샷을 그대로 써서 페이지를 만들고 다음 날 다시 시도하므로 페이지가 깨지지는 않습니다.
Actions 로그에 "받기 실패"가 며칠째 계속 뜨면 알려 주세요.
