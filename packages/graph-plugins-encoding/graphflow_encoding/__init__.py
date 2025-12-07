"""GraphFlow Encoding Plugin - Data encoding, hashing, and compression utilities."""

from .base64_steps import (
    Base64EncodeStep,
    Base64DecodeStep,
    Base64URLEncodeStep,
    Base64URLDecodeStep,
)

from .text_encoding import (
    HexEncodeStep,
    HexDecodeStep,
)

from .hashing import (
    MD5HashStep,
    SHA1HashStep,
    SHA256HashStep,
    SHA512HashStep,
)

from .compression import (
    GzipCompressStep,
    GzipDecompressStep,
)

__version__ = "1.0.0"


__all__ = [
    # Base64 Steps
    'Base64EncodeStep',
    'Base64DecodeStep',
    'Base64URLEncodeStep',
    'Base64URLDecodeStep',
    # Hex Steps
    'HexEncodeStep',
    'HexDecodeStep',
    # Hash Steps
    'MD5HashStep',
    'SHA1HashStep',
    'SHA256HashStep',
    'SHA512HashStep',
    # Compression Steps
    'GzipCompressStep',
    'GzipDecompressStep',
]
