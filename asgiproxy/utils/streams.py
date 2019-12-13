async def read_stream_in_chunks(stream, chunk_size=524_288):
    while True:
        chunk = await stream.read(chunk_size)
        yield chunk
        if not chunk:
            break
