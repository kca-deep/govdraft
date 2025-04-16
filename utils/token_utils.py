"""
토큰 계산 유틸리티
텍스트 토큰 수 계산 및 비용 산정 관련 기능을 제공합니다.
"""

from functools import lru_cache
import tiktoken
from typing import Dict, Union, Optional, overload
from config import Config
from utils.logging import logger


@lru_cache(maxsize=16)
def get_model_prices():
    """모델별 가격 정보를 반환합니다. 캐싱을 적용하여 성능 최적화.
    가격은 1M(백만) 토큰당 USD 기준.
    """
    return {
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},  # 백만 토큰당 가격
        "gpt-4o": {"input": 5.0, "output": 15.0},  # 백만 토큰당 가격
    }


@overload
def calculate_token_cost(
    input_text: str, output_text: str, model: str = "gpt-4o-mini"
) -> Dict[str, Union[int, float, str]]: ...


@overload
def calculate_token_cost(
    input_tokens: int, output_tokens: int, model: str = "gpt-4o-mini"
) -> Dict[str, Union[int, float, str]]: ...


def calculate_token_cost(
    input_text_or_tokens: Union[str, int],
    output_text_or_tokens: Union[str, int],
    model: str = "gpt-4o-mini",
) -> Dict[str, Union[int, float, str]]:
    """
    입출력 텍스트의 토큰 수와 비용을 계산합니다.
    텍스트나 토큰 수를 직접 입력할 수 있습니다.

    Args:
        input_text_or_tokens: 입력 텍스트 또는 토큰 수
        output_text_or_tokens: 출력 텍스트 또는 토큰 수
        model: 사용된 모델 이름

    Returns:
        토큰 수와 비용 정보가 담긴 사전
    """
    try:
        # 입력이 문자열인지 숫자인지 확인
        if isinstance(input_text_or_tokens, str) and isinstance(
            output_text_or_tokens, str
        ):
            # 텍스트로부터 토큰 수 계산
            encoding = tiktoken.encoding_for_model(model)
            input_tokens = len(encoding.encode(input_text_or_tokens))
            output_tokens = len(encoding.encode(output_text_or_tokens))
        elif isinstance(input_text_or_tokens, int) and isinstance(
            output_text_or_tokens, int
        ):
            # 이미 계산된 토큰 수 사용
            input_tokens = input_text_or_tokens
            output_tokens = output_text_or_tokens
        else:
            raise TypeError("입력과 출력은 둘 다 문자열이거나 둘 다 정수여야 합니다.")

        total_tokens = input_tokens + output_tokens

        # 모델별 가격 정보 가져오기
        model_prices = get_model_prices()

        if model not in model_prices:
            logger.warning(
                f"알 수 없는 모델: {model}, 기본 모델(gpt-4o-mini) 가격을 사용합니다."
            )
            model = "gpt-4o-mini"

        # 비용 계산 (USD) - 백만 토큰당 가격으로 계산
        input_cost_usd = (input_tokens / 1_000_000) * model_prices[model]["input"]
        output_cost_usd = (output_tokens / 1_000_000) * model_prices[model]["output"]
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
            "input_tokens": input_tokens if "input_tokens" in locals() else 0,
            "output_tokens": output_tokens if "output_tokens" in locals() else 0,
            "total_tokens": total_tokens if "total_tokens" in locals() else 0,
            "cost_usd": 0,
            "cost_krw": 0,
            "model": model,
        }
