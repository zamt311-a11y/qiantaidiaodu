from __future__ import annotations

from typing import Iterable


_ENCODING_ALIASES = {
    "auto": "",
    "utf8": "utf-8",
    "utf-8": "utf-8",
    "utf-8-sig": "utf-8-sig",
    "utf-8-bom": "utf-8-sig",
    "utf8bom": "utf-8-sig",
    "gb18030": "gb18030",
    "gbk": "gbk",
    "gb2312": "gb2312",
    "utf-16": "utf-16",
    "utf16": "utf-16",
    "utf-16le": "utf-16le",
    "utf16le": "utf-16le",
    "utf-16be": "utf-16be",
    "utf16be": "utf-16be",
}


def _candidate_encodings(encoding: str | None) -> Iterable[str]:
    enc = (encoding or "").strip().lower()
    if not enc or enc == "auto":
        return [
            "utf-8-sig",
            "utf-8",
            "gb18030",
            "gbk",
            "gb2312",
            "utf-16",
            "utf-16le",
            "utf-16be",
        ]
    mapped = _ENCODING_ALIASES.get(enc, enc)
    return [mapped]


def decode_csv_bytes(data: bytes, encoding: str | None = None) -> tuple[str, str]:
    last_err: Exception | None = None
    for enc in _candidate_encodings(encoding):
        try:
            return data.decode(enc), enc
        except UnicodeDecodeError as e:
            last_err = e
            continue
    if last_err is not None:
        raise last_err
    return data.decode("utf-8"), "utf-8"
