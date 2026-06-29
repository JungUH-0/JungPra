// ===================== data.js =====================
// 음악 데이터 전역 관리
// 이 파일은 모든 페이지에서 가장 먼저 로드됨 (musicData를 전역으로 사용)
//
// 각 속성 설명:
// id        : 음악 고유 번호 → detail.html?id=1 형태로 사용
// title     : 음악/플레이리스트 이름
// artist    : 아티스트명
// genre     : 장르 태그 (test.html에서 선택하는 값과 일치해야 함)
// place     : 장소 태그 (test.html에서 선택하는 값과 일치해야 함)
// mood      : 기분 태그 (test.html에서 선택하는 값과 일치해야 함)
// tags      : 화면에 표시할 해시태그 배열
// desc      : 상세 페이지에 표시할 설명
// thumb     : 썸네일 색상 클래스명 결정용 키
// youtubeUrl: 유튜브 링크 → detail.html에서 새 탭으로 열림
//
// genre 가능값: lofi | pop | jazz | indie | rnb | hiphop | classical | electronic
// place 가능값: cafe | home | drive | gym | study | outdoor
// mood  가능값: focus | excited | healing | romantic | sad | motivated

const musicData = [
  {
    id: 1,
    title: "밤 카페에서 공부할 때",
    artist: "ChilledCow Collective",
    genre: "lofi",   // 장르: 로파이
    place: "cafe",   // 장소: 카페
    mood: "focus",   // 기분: 집중
    tags: ["#로파이", "#카페", "#집중"],
    desc: "잔잔한 비트와 빗소리가 섞인 로파이 플레이리스트. 카페에서 집중이 필요할 때 최고의 선택.",
    thumb: "lofi",
    youtubeUrl: "https://www.youtube.com/watch?v=bkxN8exTygU"
  },
  {
    id: 2,
    title: "드라이브할 때 창문 열고",
    artist: "Highway Vibes",
    genre: "pop",
    place: "drive",
    mood: "excited",
    tags: ["#팝", "#드라이브", "#신남"],
    desc: "신나는 팝 비트로 드라이브 무드를 완성. 창문 열고 바람 맞으며 듣기 딱 좋은 플레이리스트.",
    thumb: "drive",
    youtubeUrl: "https://www.youtube.com/watch?v=DRdAgeHuL_g"
  },
  {
    id: 3,
    title: "비 오는 날 집에서",
    artist: "Rainy Mood Jazz",
    genre: "jazz",
    place: "home",
    mood: "healing",
    tags: ["#재즈", "#집", "#힐링"],
    desc: "빗소리와 함께하는 감성 재즈. 집에서 따뜻한 차 한 잔과 함께 듣기 완벽한 선택.",
    thumb: "jazz",
    youtubeUrl: "https://www.youtube.com/watch?v=E-RFxrJ5AOY"
  },
  {
    id: 4,
    title: "아침 러닝, 에너지 충전",
    artist: "Morning Run Crew",
    genre: "electronic",
    place: "outdoor",
    mood: "motivated",
    tags: ["#일렉트로닉", "#야외", "#의욕"],
    desc: "달리는 발걸음에 맞는 BPM. 아침 러닝의 에너지를 극대화해주는 일렉트로닉 트랙.",
    thumb: "electronic",
    youtubeUrl: "https://www.youtube.com/watch?v=Oz7MAt-5iKY"
  },
  {
    id: 5,
    title: "헬스장 풀파워 세트",
    artist: "GymBeast Playlist",
    genre: "hiphop",
    place: "gym",
    mood: "excited",
    tags: ["#힙합", "#헬스장", "#신남"],
    desc: "강렬한 베이스와 랩으로 운동 한계를 뛰어넘게 해주는 힙합 믹스테이프.",
    thumb: "hiphop",
    youtubeUrl: "https://www.youtube.com/watch?v=GQRp5E2gFSQ"
  },
  {
    id: 6,
    title: "새벽 감성, 혼자인 밤",
    artist: "Midnight Indie",
    genre: "indie",
    place: "home",
    mood: "sad",
    tags: ["#인디", "#집", "#우울"],
    desc: "쓸쓸한 새벽, 혼자 있는 밤에 어울리는 인디 음악. 감정을 천천히 달래줘요.",
    thumb: "indie",
    youtubeUrl: "https://www.youtube.com/watch?v=LJDweY2uDfU"
  },
  {
    id: 7,
    title: "카페에서 기분좋은 오후",
    artist: "Café Romance",
    genre: "rnb",
    place: "cafe",
    mood: "romantic",
    tags: ["#R&B", "#카페", "#감성"],
    desc: "부드러운 R&B 멜로디로 카페에서의 감성적인 순간을 더 특별하게 만들어줘요.",
    thumb: "rnb",
    youtubeUrl: "https://www.youtube.com/watch?v=-Gc76-sPJKk"
  },
  {
    id: 8,
    title: "도서관 집중 타임",
    artist: "Study Session",
    genre: "classical",
    place: "study",
    mood: "focus",
    tags: ["#클래식", "#공부방", "#집중"],
    desc: "가사 없는 클래식 피아노곡들로 구성된 공부 집중 플레이리스트. 뇌가 맑아지는 느낌.",
    thumb: "classical",
    youtubeUrl: "https://www.youtube.com/watch?v=mDX8QrcDI_o"
  },
  {
    id: 9,
    title: "공원 산책, 봄바람",
    artist: "Outdoor Indie",
    genre: "indie",
    place: "outdoor",
    mood: "healing",
    tags: ["#인디", "#야외", "#힐링"],
    desc: "가볍고 따뜻한 인디 팝. 봄날 공원 산책에 딱 맞는 감성 트랙 모음.",
    thumb: "indie",
    youtubeUrl: "https://www.youtube.com/watch?v=g0W21e-Rr-4"
  },
  {
    id: 10,
    title: "집에서 혼자 춤추기",
    artist: "Home Dance Party",
    genre: "pop",
    place: "home",
    mood: "excited",
    tags: ["#팝", "#집", "#신남"],
    desc: "집에서 혼자 신나게 춤추고 싶을 때! 텐션 올려주는 팝 댄스 플레이리스트.",
    thumb: "drive",
    youtubeUrl: "https://www.youtube.com/watch?v=lfbwZdaEHm8"
  },
  {
    id: 11,
    title: "새벽 드라이브, 감성 모드",
    artist: "Midnight Drive",
    genre: "rnb",
    place: "drive",
    mood: "romantic",
    tags: ["#R&B", "#드라이브", "#감성"],
    desc: "도시의 야경을 배경으로 감성적인 R&B와 함께하는 새벽 드라이브.",
    thumb: "rnb",
    youtubeUrl: "https://www.youtube.com/watch?v=V9_aaIIxRRo"
  },
  {
    id: 12,
    title: "로파이로 힐링하는 오후",
    artist: "Afternoon Lofi",
    genre: "lofi",
    place: "home",
    mood: "healing",
    tags: ["#로파이", "#집", "#힐링"],
    desc: "아무것도 하기 싫은 나른한 오후, 소파에 누워 듣기 좋은 로파이 힐링 믹스.",
    thumb: "lofi",
    youtubeUrl: "https://www.youtube.com/watch?v=5qap5aO4i9A"
  }
];