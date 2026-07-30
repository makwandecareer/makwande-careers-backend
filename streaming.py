from fastapi.responses import StreamingResponse

def stream_pdf(generator):
    return StreamingResponse(
        generator,
        media_type="application/pdf"
    )
