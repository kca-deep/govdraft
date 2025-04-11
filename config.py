"""
설정 관리 모듈
환경 변수와 애플리케이션 설정을 관리합니다.
"""

import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

# 환경 변수 로드
load_dotenv()

# 공통 SQLAlchemy 객체 초기화
db = SQLAlchemy()


class Config:
    """애플리케이션 설정 클래스"""

    API_BASE_URL = os.getenv("API_BASE_URL", "http://apis.data.go.kr/1741000/publicDoc")
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
    RETRY_DELAY = int(os.getenv("RETRY_DELAY", "2"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    EXCHANGE_RATE = float(os.getenv("EXCHANGE_RATE", "1450"))
    PUBLIC_DATA_API_KEY = os.getenv("PUBLIC_DATA_API_KEY")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # 데이터베이스 설정
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///govdraft.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")

    # 문서 유형별 엔드포인트와 필수 파라미터 정의
    DOC_TYPE_CONFIG = {
        "press": {"endpoint": "getDocPress", "required_params": ["title", "manager"]},
        "speech": {"endpoint": "getDocSpeech", "required_params": ["title"]},
        "publication": {"endpoint": "getDocPublication", "required_params": ["title"]},
        "report": {"endpoint": "getDocReport", "required_params": ["title"]},
        "plan": {"endpoint": "getDocPlan", "required_params": ["title"]},
        "all": {"endpoint": "getDocAll", "required_params": ["title"]},
    }
