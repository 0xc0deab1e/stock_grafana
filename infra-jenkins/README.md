# Jenkins Infrastructure

## 서비스 설명
- Jenkins CI/CD 서버를 위한 docker-compose 구성입니다.

## 사용법
1. Jenkins 컨테이너 실행:
   ```bash
   docker-compose -f infra-jenkins/docker-compose.jenkins.yml up -d
   ```
2. 웹 브라우저에서 [http://localhost:8080](http://localhost:8080) 접속

## 볼륨
- `jenkins_home`: Jenkins 데이터가 저장되는 볼륨

## 포트
- 8080: Jenkins 웹 UI
- 50000: JNLP agent

## 환경 변수
- JAVA_OPTS: Jenkins 초기 설정 마법사 비활성화
