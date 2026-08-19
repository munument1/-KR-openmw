OpenMW
======

OpenMW는 Bethesda Softworks의 《The Elder Scrolls III: Morrowind》를 실행할 수 있도록 지원하는 오픈 소스 오픈 월드 RPG 게임 엔진입니다. OpenMW로 Morrowind를 플레이하려면 정품 게임을 보유하고 있어야 합니다.

OpenMW에는 Bethesda의 Construction Set을 대체하는 편집 도구인 OpenMW-CS도 포함되어 있습니다.

* 버전: 0.52.0
* 라이선스: GPLv3 (자세한 내용은 [LICENSE](https://gitlab.com/OpenMW/openmw/-/raw/master/LICENSE) 참조)
* 웹사이트: https://www.openmw.org
* IRC: irc.libera.chat의 #openmw
* Discord: https://discord.gg/bWuqq2e


폰트 라이선스:
* DejaVuLGCSansMono.ttf: 커스텀 라이선스 (자세한 내용은 [files/data/fonts/DejaVuFontLicense.txt](https://gitlab.com/OpenMW/openmw/-/raw/master/files/data/fonts/DejaVuFontLicense.txt) 참조)
* DemonicLetters.ttf: SIL Open Font License (자세한 내용은 [files/data/fonts/DemonicLettersFontLicense.txt](https://gitlab.com/OpenMW/openmw/-/raw/master/files/data/fonts/DemonicLettersFontLicense.txt) 참조)
* MysticCards.ttf: SIL Open Font License (자세한 내용은 [files/data/fonts/MysticCardsFontLicense.txt](https://gitlab.com/OpenMW/openmw/-/raw/master/files/data/fonts/MysticCardsFontLicense.txt) 참조)

현재 상태
---------

Morrowind, Tribunal, Bloodmoon의 메인 퀘스트는 모두 완료할 수 있습니다. 일부 사이드 퀘스트에서 문제가 발생할 수 있지만 드문 편입니다. "1.0" 출시 전에 해결해야 할 문제 목록은 [버그 트래커](https://gitlab.com/OpenMW/openmw/-/issues/?milestone_title=openmw-1.0)에서 확인할 수 있습니다. 아직 "1.0"이 출시되기 전이지만, OpenMW는 향상된 그래픽과 사용자 인터페이스를 비롯한 다양한 새로운 [기능](https://wiki.openmw.org/index.php?title=Features)을 제공합니다.

기존 Morrowind 엔진용으로 제작된 모드는 호환 여부가 제각각일 수 있습니다. OpenMW의 스크립트 컴파일러는 Morrowind보다 더 철저하게 오류를 검사하기 때문에, Morrowind용으로 제작된 모드가 반드시 OpenMW에서도 실행된다고 보장할 수 없습니다. 또한 일부 모드는 원본 엔진의 특이한 동작이나 버그에 의존하기도 합니다.

이러한 호환성 문제는 사례별로 검토하고 있습니다. 경우에 따라 OpenMW에 우회 처리를 추가할 수 있지만, 모드 자체를 수정하는 것만이 해결책인 경우도 있습니다. 작동하거나 작동하지 않는 모드를 알고 있다면 [Mod status](https://wiki.openmw.org/index.php?title=Mod_status) 위키 페이지에 자유롭게 추가해 주세요.

시작하기
-------

* [공식 포럼](https://forum.openmw.org/)
* [설치 안내](https://openmw.readthedocs.io/en/latest/manuals/installation/index.html)
* [소스에서 빌드하기](https://wiki.openmw.org/index.php?title=Development_Environment_Setup)
* [게임 테스트하기](https://wiki.openmw.org/index.php?title=Testing)
* [기여하는 방법](https://wiki.openmw.org/index.php?title=Contribution_Wanted)
* [버그 신고](https://gitlab.com/OpenMW/openmw/issues) - 처음 버그를 신고하기 전에 [가이드라인](https://wiki.openmw.org/index.php?title=Bug_Reporting_Guidelines)을 읽어 주세요!
* [알려진 문제](https://gitlab.com/OpenMW/openmw/issues?label_name%5B%5D=Bug)

데이터 경로
----------

데이터 경로는 OpenMW가 Morrowind 파일을 어디에서 찾아야 하는지 지정합니다. Morrowind와 OpenMW가 올바르게 설치되어 있다면 런처를 실행했을 때 OpenMW가 해당 파일의 위치를 자동으로 찾을 수 있습니다. WINE을 통해 설치한 Morrowind도 정상적인 설치로 간주됩니다.

명령줄 옵션
-----------

    사용법: openmw <옵션>
    사용 가능한 옵션:
      --config arg                          추가 설정 디렉터리
      --replace arg                         현재 소스의 값을 낮은 우선순위 소스의
                                            값 뒤에 추가하지 않고 대신 대체할 설정
      --user-data arg                       사용자 데이터 디렉터리 설정
                                            (저장 파일, 스크린샷 등에 사용)
      --resources arg (=resources)          리소스 디렉터리 설정
      --help                                도움말 표시
      --version                             버전 정보를 표시하고 종료
      --data arg (=data)                    데이터 디렉터리 설정
                                            (뒤에 지정된 디렉터리일수록 우선순위가 높음)
      --data-local arg                      로컬 데이터 디렉터리 설정
                                            (가장 높은 우선순위)
      --fallback-archive arg (=fallback-archive)
                                            대체 BSA 아카이브 설정
                                            (뒤에 지정된 아카이브일수록 우선순위가 높음)
      --start arg                           시작 셀 지정
      --content arg                         콘텐츠 파일:
                                            esm/esp 또는
                                            omwgame/omwaddon/omwscripts
      --groundcover arg                     지면 식생 콘텐츠 파일:
                                            esm/esp 또는
                                            omwgame/omwaddon
      --no-sound [=arg(=1)] (=0)            모든 사운드 비활성화
      --script-all [=arg(=1)] (=0)          시작 시 모든 스크립트 컴파일
                                            (대화 스크립트 제외)
      --script-all-dialogue [=arg(=1)] (=0) 시작 시 모든 대화 스크립트 컴파일
      --script-console [=arg(=1)] (=0)      콘솔 전용 스크립트 기능 활성화
      --script-run arg                      시작 시 실행할 콘솔 명령 목록이
                                            들어 있는 파일 선택
      --script-warn [=arg(=1)] (=1)         스크립트 컴파일 시 경고 처리 방식
                                            0 - 경고 무시
                                            1 - 경고를 표시하지만 스크립트는
                                                정상적으로 컴파일된 것으로 처리
                                            2 - 경고를 오류로 처리
      --load-savegame arg                   게임 시작 시 저장 파일 불러오기
                                            (절대 경로 또는 현재 작업 디렉터리
                                            기준의 상대 경로 지정)
      --skip-menu [=arg(=1)] (=0)           게임 시작 시 메인 메뉴 건너뛰기
      --new-game [=arg(=1)] (=0)            새 게임 시작 시퀀스 실행
                                            (skip-menu=0이면 무시됨)
      --encoding arg (=win1252)             OpenMW 게임 메시지에 사용할 문자 인코딩:

                                            win1250 - 폴란드어, 체코어, 슬로바키아어,
                                            헝가리어, 슬로베니아어, 보스니아어,
                                            크로아티아어, 세르비아어(라틴 문자),
                                            루마니아어, 알바니아어 등의
                                            중부·동부 유럽 언어

                                            win1251 - 러시아어, 불가리아어,
                                            세르비아어(키릴 문자) 등
                                            키릴 문자 계열 언어

                                            win1252 - 서유럽(라틴 문자) 계열.
                                            기본값으로 사용
      --fallback arg                        대체(fallback) 값 설정
      --no-grab [=arg(=1)] (=0)             마우스 커서를 게임 창에 고정하지 않음
      --export-fonts [=arg(=1)] (=0)        Morrowind .fnt 폰트를 현재 디렉터리에
                                            PNG 이미지와 XML 파일로 내보내기
      --activate-dist arg (=-1)             활성화 거리 강제 지정
      --random-seed arg (=<impl defined>)   난수 생성기의 시드 값
