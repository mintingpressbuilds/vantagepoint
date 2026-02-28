import os
from pruv import xy_wrap, CloudClient, XYChain

PRUV_API_KEY = os.getenv("PRUV_API_KEY")  # None in local dev — fine


def get_wrapper(chain_name="vantagepoint"):
    return xy_wrap(
        chain_name=chain_name, auto_redact=True,
        **({"api_key": PRUV_API_KEY} if PRUV_API_KEY else {})
    )


def extract_receipt_info(wrapped_result):
    return {
        "chain_id": wrapped_result.chain.id,
        "chain_root": wrapped_result.chain.root,
        "chain_length": wrapped_result.chain.length,
        "chain_verified": wrapped_result.verified,
        "receipt": wrapped_result.receipt,
    }
