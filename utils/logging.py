"""
로깅 유틸리티
애플리케이션에서 사용하는 로거를 설정합니다.
"""

import os
import logging
import datetime
from config import Config


def setup_logging():
    """로깅 시스템을 초기화합니다."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(
        log_dir, f"govdraft_{datetime.datetime.now().strftime('%Y%m%d')}.log"
    )

    # 로그 핸들러 설정
    logger = logging.getLogger("GovDraft")
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # 기존 핸들러 모두 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    try:
        # 로그 파일 초기화
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")  # 빈 파일로 초기화

        # 파일 핸들러 추가
        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # 콘솔 핸들러 추가
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)  # 콘솔에는 ERROR 이상만 출력
        console_formatter = logging.Formatter("%(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 로거가 상위 로거로 메시지를 전달하지 않도록 설정
        logger.propagate = False

        # 로그 시스템 초기화 메시지 기록
        logger.info("로깅 시스템이 초기화되었습니다.")

    except Exception as e:
        print(f"로그 설정 중 오류 발생: {str(e)}")
        # 기본 로깅으로 대체
        logging.basicConfig(
            level=getattr(logging, Config.LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    return logger


# 싱글톤 패턴으로 로거 생성
logger = setup_logging()
