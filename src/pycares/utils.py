from typing import Union

try:
    import idna as idna2008
except ImportError:
    idna2008 = None


def ascii_bytes(data: Union[str, bytes]) -> bytes:
    if isinstance(data, str):
        return data.encode("ascii")
    if isinstance(data, bytes):
        return data
    raise TypeError("only str (ascii encoding) and bytes are supported")


def maybe_str(data: Union[str, bytes]) -> Union[str, bytes]:
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        try:
            return data.decode("ascii")
        except UnicodeDecodeError:
            return data
    raise TypeError("only str (ascii encoding) and bytes are supported")


def parse_name_idna2008(name: str) -> bytes:
    parts = name.split(".")
    r = []
    for part in parts:
        if part.isascii():
            r.append(part.encode("ascii"))
        elif len(part) > 253:
            raise RuntimeError(
                f"domains can only be less than 253 characters in length not {len(name)}"
            )
        else:
            r.append(idna2008.encode(part))
    return b".".join(r)


def parse_name(name: Union[str, bytes]) -> Union[bytes, str]:
    if isinstance(name, str):
        if name.isascii():
            return name.encode("ascii")
        if idna2008 is not None:
            return parse_name_idna2008(name)
        return name.encode("idna")
    if isinstance(name, bytes):
        return name
    raise TypeError("only str and bytes are supported")


__all__ = ["ascii_bytes", "maybe_str", "parse_name"]
