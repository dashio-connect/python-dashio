import json
import base64
import zlib


def decode_cfg(cfg: str) -> dict:
    """Loads a CFG from iotdasboard app

    Parameters
    ----------
    cfg : str
        A base64 zipped json

    Returns
    -------
    dict
        A dictionary representing the cfg.
    """

    ztmp_b = base64.b64decode(f"{cfg}{'=' * (len(cfg) % 4)}") # Deal with missing padding
    try:
        tmp_b = zlib.decompress(ztmp_b)
    except zlib.error:
        tmp_b = zlib.decompress(ztmp_b, wbits= -8) # Deal with missing header
    try:
        cfg_dict = json.loads(tmp_b)
    except json.JSONDecodeError:
        return ""
    return cfg_dict
