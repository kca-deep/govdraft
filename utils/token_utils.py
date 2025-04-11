"""
토큰 계산 유틸리티
텍스트 토큰 수 계산 및 비용 산정 관련 기능을 제공합니다.
"""

from functools import lru_cache
import tiktoken
from config import Config
from utils.logging import logger


@lru_cache(maxsize=16)
def get_model_prices():
    """모델별 가격 정보를 반환합니다. 캐싱을 적용하여 성능 최적화."""
    return {
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-4o": {"input": 5.0, "output": 15.0},
    }


def calculate_token_cost(
    input_text: str, output_text: str, model: str = "gpt-4o-mini"
) -> dict:
    """
    입출력 텍스트의 토큰 수와 비용을 계산합니다.

    Args:
        input_text: 입력 텍스트
        output_text: 출력 텍스트
        model: 사용된 모델 이름

    Returns:
        토큰 수와 비용 정보가 담긴 사전
    """
    try:
        # 토큰 인코더 초기화
        encoding = tiktoken.encoding_for_model(model)

        # 토큰 수 계산
        input_tokens = len(encoding.encode(input_text))
        output_tokens = len(encoding.encode(output_text))
        total_tokens = input_tokens + output_tokens

        # 모델별 가격 정보 가져오기
        model_prices = get_model_prices()

        if model not in model_prices:
            logger.warning(
                f"알 수 없는 모델: {model}, 기본 모델(gpt-4o-mini) 가격을 사용합니다."
            )
            model = "gpt-4o-mini"

        # 비용 계산 (USD)
        input_cost_usd = (input_tokens / 1000) * model_prices[model]["input"]
        output_cost_usd = (output_tokens / 1000) * model_prices[model]["output"]
        total_cost_usd = input_cost_usd + output_cost_usd

        # 환율 적용
        total_cost_krw = total_cost_usd * Config.EXCHANGE_RATE

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(total_cost_usd, 6),
            "cost_krw": round(total_cost_krw, 2),
            "model": model,
        }
    except Exception as e:
        logger.error(f"토큰 비용 계산 중 오류: {str(e)}")
        return {
            "error": f"토큰 비용 계산 중 오류: {str(e)}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0,
            "cost_krw": 0,
            "model": model,
        }
