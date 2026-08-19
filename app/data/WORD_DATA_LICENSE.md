# 끝말잇기 단어 데이터 출처

`word_chain_words.json`은 기존 프로젝트 단어 목록과 국립국어원
한국어기초사전의 표제어를 합쳐 생성했습니다.

- 출처: 국립국어원 한국어기초사전
- 원본: <https://krdict.korean.go.kr/download/downloadPopup>
- 내려받은 자료: 2026년 8월 19일 JSON 전체 내려받기
- 적용 범위: `word_chain_words.json`에 추가된 한국어기초사전 유래 표제어
- 라이선스: 크리에이티브 커먼즈 저작자표시-동일조건변경허락 2.0 대한민국
  (CC BY-SA 2.0 KR)
- 라이선스 안내: <https://krdict.korean.go.kr/kor/kboardPolicy/copyRightTermsInfo>

게임용 목록은 원본에서 품사가 명사이고 구성 단위가 단어인 항목 가운데,
두 글자 이상의 완성형 한글 표제어만 남기고 중복을 제거한 2차 데이터입니다.
`scripts/build_word_chain_dictionary.py`로 같은 변환을 다시 실행할 수 있습니다.
