# Korean OpenMW 넥서스 자동 배포

대상: https://www.nexusmods.com/morrowind/mods/60496

## 버전 규칙

태그 `openmw-0.51.0-kr4`에서 엔진 버전 `0.51.0`과 한글판 차수 `4`를 읽어
넥서스 버전을 `0.51.0-KR4`로 만듭니다. 버전 접두사나 차수를 워크플로에 고정하지 않습니다.
기존 넥서스의 `0.51-kr4`는 `0.51.0-KR4`와 같은 버전으로 인식하며 중복 업로드하지 않습니다.

다음 배포는 다음과 같이 준비합니다.

1. 엔진/한글판에 맞는 새 태그를 만듭니다. 예: `openmw-0.51.0-kr5`.
2. 대응하는 Full ZIP과 SHA256을 GitHub 릴리즈에 첨부합니다.
3. 테스트 후 draft와 prerelease 상태를 모두 해제하고 정식 릴리즈를 발행합니다.
4. Actions의 `Publish Korean OpenMW to Nexus Mods` 결과를 확인합니다.

지원하는 파일명은 두 가지입니다.

- compact 배포판: `Morrowind-Korean-OpenMW-0.51.0-KR5-Full.zip`
- upstream port 번들: `Morrowind-Korean-OpenMW-openmw-0.51.0-kr5-Full.zip`

체크섬 파일은 선택된 ZIP 이름 뒤에 `.sha256`을 붙입니다.
두 종류의 ZIP이 한 릴리즈에 동시에 있으면 임의 선택하지 않고 실패합니다.
일반 OpenMW 엔진 태그, 다른 플랫폼 자산, draft/prerelease는 자동 배포하지 않습니다.

## 연결 설정과 테스트

Repository secret `NEXUSMODS_API_KEY`에 모드 소유자의 Personal API Key를 등록합니다.
메인 파일 하나인 현재 구성에서는 업로드 API File ID를 자동 조회합니다.
활성 파일이 여러 개가 되면 Repository variable `NEXUSMODS_FILE_ID`에
Manage Files/Advanced의 업로드용 File ID를 지정합니다. 모드에 속하는지도 확인합니다.

Actions → `Publish Korean OpenMW to Nexus Mods` → Run workflow:

- `tag`: 검사/배포할 정식 한글판 태그. 비우면 최신 정식 릴리즈를 사용합니다.
- `dry_run=true`: GitHub 파일명, SHA256, ZIP만 검사합니다. 업로드하지 않습니다.
- `dry_run=false`: 인증과 중복 버전 확인 후 새 버전인 경우 업로드합니다.

기존 `Korean Windows upstream port` 빌드의 성공도 연결합니다.
그 실행 중 갱신된 최신 정식 릴리즈 파일만 대상으로 합니다.
이 빌드가 만드는 draft prerelease는 검토 후 사람이 정식으로 발행해야 합니다.
빌드나 게임 회귀 검증 절차는 기존 `KOREAN_WINDOWS_RELEASE.md`를 따릅니다.

업로드 전에는 SHA256과 ZIP 무결성을 확인합니다.
중복 버전은 생략하며, 같은 태그의 파일 교체를 다시 배포하려면 새 한글판 차수를 사용하세요.
이전 버전은 자동 보관하지 않습니다. 설치형 도구이므로 새 버전의 모드 매니저 다운로드는 끕니다.
파일 설명에는 GitHub 릴리즈 링크를 넣고 모드의 표시 버전을 새 파일 버전과 맞춥니다.
변경 내역 본문이나 기존 GitHub 빌드/패키징은 수정하지 않습니다.
