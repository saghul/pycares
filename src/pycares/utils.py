
def ascii_bytes(data):
    if isinstance(data, str):
        return data.encode('ascii')
    if isinstance(data, bytes):
        return data
    raise TypeError('only str (ascii encoding) and bytes are supported')

def maybe_str(data):
    if isinstance(data, str):
        return data
    if isinstance(data, bytes):
        try:
            return data.decode('ascii')
        except UnicodeDecodeError:
            return data
    raise TypeError('only str (ascii encoding) and bytes are supported')

def parse_name(name):
    if isinstance(name, str):
        return name.encode('idna')
    if isinstance(name, bytes):
        return name
    raise TypeError('only str and bytes are supported')


__all__ = ['ascii_bytes', 'maybe_str', 'parse_name']

