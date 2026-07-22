# Rokey Cobot Project 2

![Rokey Cobot setup](resource/img/img1.jpg)

협동로봇과 비전 AI를 활용한 자동 분리수거 시스템입니다. RealSense RGB-D 카메라로 물체를 인식하고, YOLO 기반 객체 검출 결과를 로봇 좌표계로 변환해 Doosan 협동로봇이 물체를 집어 분류 위치로 옮깁니다. 웹/Firebase 연동을 통해 작업 시작, 비상정지, 쓰레기통 상태, 작업 완료 상태를 확인할 수 있도록 구성했습니다.

## 프로젝트 개요

- 카메라 영상에서 분리수거 대상 객체를 검출합니다.
- 객체의 위치와 자세를 계산해 로봇이 집을 수 있는 좌표로 변환합니다.
- 평면 각도뿐 아니라 Z축 기울기까지 고려해 그립 자세를 보정합니다.
- 물체 내부의 물 유무와 수위 상태를 비전으로 확인합니다.
- 음성 명령으로 작업 일시정지, 재개, 대상 선택이 가능하도록 구성했습니다.
- Firebase 기반 웹 인터페이스와 연동해 로봇 상태와 작업 흐름을 관리합니다.

## 시스템 아키텍처

![System architecture](resource/img/system_architectur.png)

## 플로우 차트

| 웹 플로우 | 로봇 플로우 | 예외 처리 플로우 |
| --- | --- | --- |
| <img src="resource/img/web_flowchart.png" alt="Web flowchart" width="300"> | <img src="resource/img/robot_flowchart.png" alt="Robot flowchart" width="300"> | <img src="resource/img/exception_flowchart.png" alt="Exception flowchart" width="300"> |

## 시연 영상

[최종 시연 영상 보기](<resource/img/최종 영상.mp4>)

## 주요 기능

### 음성 기능

음성 명령을 통해 로봇 작업을 일시정지하거나 재개하고, 특정 분류 대상을 선택할 수 있습니다.

### Z Tilting 그립

객체의 평면 회전 각도와 Z축 기울기 각도를 함께 계산해, 물체 자세에 맞춘 그립을 수행합니다.

![Z tilting grip](resource/img/z_tilting.gif)

### 물 감지 기능

물체 내부의 물 유무를 판단하고, 수위 상태를 단계별로 추정합니다.

| 물 O | 물 X |
| --- | --- |
| <img src="resource/img/물O.gif" alt="Water detected" width="420"> | <img src="resource/img/물X.gif" alt="Water not detected" width="420"> |

| 0% | 25% | 50% | 75% |
| --- | --- | --- | --- |
| <img src="resource/img/water0.png" alt="Water level 0%" width="210"> | <img src="resource/img/water25.png" alt="Water level 25%" width="210"> | <img src="resource/img/water50.png" alt="Water level 50%" width="210"> | <img src="resource/img/water75.png" alt="Water level 75%" width="210"> |

## 기술 구성

- **Robot**: Doosan M0609 협동로봇, OnRobot RG 그리퍼
- **Vision**: Intel RealSense RGB-D Camera, OpenCV, YOLO
- **Robot Middleware**: ROS 2, Doosan Robotics ROS 2 패키지
- **Backend / Control**: Python, Firebase Firestore
- **Auxiliary Features**: STT 음성 명령, 비상정지, 쓰레기통 포화 상태 확인

## 저장소 구조

```text
.
├── cobot2/       # 로봇 제어, 객체 검출, 좌표 변환, Firebase 연동 로직
├── resource/     # 보정 데이터, 클래스 정보, 이미지/영상 자료
├── test/         # ROS 2 패키지 테스트
├── package.xml   # ROS 2 패키지 메타데이터
└── setup.py      # Python 패키지 설정
```

## 참고

이 프로젝트는 실제 협동로봇, 그리퍼, RGB-D 카메라, Firebase 환경에서 제작되었습니다.
