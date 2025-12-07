# GraphFlow Encoding Plugin

Data encoding, hashing, and compression utilities for GraphFlow.

## Installation

```bash
pip install -e packages/graph-plugins-encoding
```

## Steps Provided

### Base64 Encoding

| Step | Description |
|------|-------------|
| `encoding.Base64EncodeStep` | Encode data to Base64 |
| `encoding.Base64DecodeStep` | Decode Base64 data |
| `encoding.Base64URLEncodeStep` | Encode to URL-safe Base64 |
| `encoding.Base64URLDecodeStep` | Decode URL-safe Base64 |

### Hex Encoding

| Step | Description |
|------|-------------|
| `encoding.HexEncodeStep` | Encode data to hexadecimal |
| `encoding.HexDecodeStep` | Decode hexadecimal data |

### Hashing

| Step | Description |
|------|-------------|
| `encoding.MD5HashStep` | Compute MD5 hash |
| `encoding.SHA1HashStep` | Compute SHA1 hash |
| `encoding.SHA256HashStep` | Compute SHA256 hash |
| `encoding.SHA512HashStep` | Compute SHA512 hash |

### Compression

| Step | Description |
|------|-------------|
| `encoding.GzipCompressStep` | Compress data with gzip |
| `encoding.GzipDecompressStep` | Decompress gzip data |

## Examples

### Base64 Encoding

```json
{
  "id": "encode_1",
  "type": "encoding.Base64EncodeStep",
  "config": {
    "input": "{memory.raw_data}"
  },
  "outputs": {
    "output": "{memory.encoded_data}"
  }
}
```

### SHA256 Hashing

```json
{
  "id": "hash_1",
  "type": "encoding.SHA256HashStep",
  "config": {
    "input": "{memory.data_to_hash}",
    "encoding": "utf-8"
  },
  "outputs": {
    "output": "{memory.hash_result}"
  }
}
```

### Gzip Compression

```json
{
  "id": "compress_1",
  "type": "encoding.GzipCompressStep",
  "config": {
    "input": "{memory.large_text}",
    "compression_level": 9,
    "output_format": "base64"
  },
  "outputs": {
    "output": "{memory.compressed_data}"
  }
}
```

### Gzip Decompression

```json
{
  "id": "decompress_1",
  "type": "encoding.GzipDecompressStep",
  "config": {
    "input": "{memory.compressed_data}",
    "input_format": "base64",
    "encoding": "utf-8"
  },
  "outputs": {
    "output": "{memory.decompressed_text}"
  }
}
```

## Configuration Options

### Base64 Steps
- `input` - Input data using `{memory.variable}` syntax
- `encoding` - Text encoding (default: utf-8)
- `url_safe` - Use URL-safe alphabet (Base64URL steps)

### Hash Steps
- `input` - Input data using `{memory.variable}` syntax
- `encoding` - Text encoding for string input (default: utf-8)

### Gzip Steps
- `input` - Input data using `{memory.variable}` syntax
- `compression_level` - 0-9, where 9 is maximum compression (default: 9)
- `output_format` / `input_format` - "base64" or "bytes" (default: base64)
- `encoding` - Text encoding for string conversion (default: utf-8)

## License

MIT
