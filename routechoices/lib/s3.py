# import os.path    # Used in s3_rename_object
import urllib.parse
from io import BytesIO

import boto3
import botocore
from django.conf import settings
from django.http import HttpResponse
from PIL import Image

from routechoices.lib import cache
from routechoices.lib.duration_constants import (
    DURATION_ONE_MONTH,
)
from routechoices.lib.helpers import (
    get_best_image_mime,
    safe64encodedsha,
    set_content_disposition,
)
from routechoices.lib.streaming_response import StreamingHttpRangeResponse

# def bytes_to_str(b):
#     if isinstance(b, str):
#         return b
#     return b.decode("utf-8")


# def s3_object_size(key, bucket):
#     s3 = get_s3_client()
#     return s3.head_object(Bucket=bucket, Key=key).get("ContentLength", 0)


# def s3_rename_object(bucket, src, dest):
#     src = bytes_to_str(src)
#     dest = bytes_to_str(dest)
#     s3 = get_s3_client()
#     s3.copy_object(Bucket=bucket, CopySource=os.path.join(bucket, src), Key=dest)
#     s3.delete_object(Bucket=bucket, Key=src)


def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        config=botocore.client.Config(signature_version="s3v4"),
    )


def s3_object_url(method, key, bucket):
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        ClientMethod=f"{method.lower()}_object", Params={"Bucket": bucket, "Key": key}
    )


def s3_delete_key(key, bucket):
    s3 = get_s3_client()
    s3.delete_object(
        Bucket=bucket,
        Key=key,
    )


def serve_from_s3(
    bucket,
    request,
    path,
    filename="",
    mime="application/force-download",
    headers=None,
    dl=True,
):
    if request.method not in ("GET", "HEAD"):
        raise NotImplementedError()

    url = s3_object_url(request.method, path, bucket)
    url = url[len(settings.AWS_S3_ENDPOINT_URL) :]

    response = HttpResponse("", headers=headers, content_type=mime)
    response["X-Accel-Redirect"] = urllib.parse.quote(f"/s3{url}".encode())
    response["X-Accel-Buffering"] = "no"
    response["Content-Disposition"] = set_content_disposition(filename, dl=dl)
    return response


def serve_image_from_s3(
    request,
    image_field,
    output_filename,
    mime=None,
    default_mime="image/png",
    img_mode=None,
    headers=None,
):
    if not mime:
        mime = get_best_image_mime(request, default_mime)

    if mime[:6] != "image/":
        raise ValueError("Invalid mime type requested")

    cache_key = f"s3:image:{image_field.name}:{mime}"

    if headers is None:
        headers = {}

    image = None
    if image := cache.get(cache_key):
        headers["X-Cache-Hit"] = 1
    else:
        file_path = image_field.name
        s3_buffer = BytesIO()
        out_buffer = BytesIO()
        s3_client = get_s3_client()
        s3_client.download_fileobj(settings.AWS_S3_BUCKET, file_path, s3_buffer)
        img_data = s3_buffer.getvalue()
        pil_image = Image.open(BytesIO(img_data)).convert("RGBA")
        if (img_mode and pil_image.mode != img_mode) or mime == "image/jpeg":
            pil_image = pil_image.convert("RGB")

        pil_image.save(
            out_buffer,
            mime[6:].upper(),
            optimize=True,
            quality=80,
        )
        image = out_buffer.getvalue()
        cache.set(cache_key, image, DURATION_ONE_MONTH)

    resp = StreamingHttpRangeResponse(
        request,
        image,
        content_type=mime,
        headers=headers,
    )
    resp["ETag"] = f'W/"{safe64encodedsha(image)}"'
    resp["Content-Disposition"] = set_content_disposition(
        f"{output_filename}.{mime[6:]}", dl=False
    )
    return resp
