
def ensure_bytes(data):
    if isinstance(data, str):
        return data.encode('ascii')
    if isinstance(data, bytes):
        return data
    raise TypeError('only str (ascii encoding) and bytes are supported')


__all__ = ['ensure_bytes']

