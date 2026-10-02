"""
Upload endpoint for question/answer attachments - screenshots, error
logs, short screen recordings, spec documents, etc.

Storage: uploads go to Cloudinary (persistent cloud storage) when
CLOUDINARY_* env vars are set - which they should be in any real
deployment. On Render specifically (and most PaaS free tiers), the
local filesystem is ephemeral: anything written to disk at runtime is
wiped on every restart, redeploy, or free-tier spin-down/spin-up cycle.
Attachments were disappearing because they were being saved there -
the database row survives (it's in Postgres/Neon), but the actual file
on local disk doesn't, leaving a broken link days or even minutes later.

If Cloudinary isn't configured (e.g. you haven't set it up yet, or
you're just running locally and don't want to), this falls back to the
old local-disk behavior so nothing breaks - it just comes with the same
"will eventually disappear in production" caveat as before.
"""

import os
import uuid
import imghdr
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

from app.auth import get_current_user

logger = logging.getLogger("simdaa.uploads")
router = APIRouter(prefix="/uploads", tags=["Uploads"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
DOCUMENT_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS | DOCUMENT_EXTENSIONS | VIDEO_EXTENSIONS

# Different kinds of attachment genuinely need different ceilings - a
# 5 MB cap that's reasonable for a screenshot would reject almost any
# real screen recording before it even got to the size check being the
# point.
MAX_SIZE_BY_EXTENSION = {
    **{ext: 5 * 1024 * 1024 for ext in IMAGE_EXTENSIONS},       # 5 MB
    **{ext: 20 * 1024 * 1024 for ext in DOCUMENT_EXTENSIONS},   # 20 MB
    **{ext: 75 * 1024 * 1024 for ext in VIDEO_EXTENSIONS},      # 75 MB
}

# imghdr identifies these two as "jpeg"/"webp" respectively - map its
# vocabulary onto the extensions we accept, so a real image always
# matches regardless of which of the two spellings the extension used.
_IMGHDR_TO_EXTENSIONS = {
    "png": {".png"},
    "jpeg": {".jpg", ".jpeg"},
    "gif": {".gif"},
    "webp": {".webp"},
}

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
CLOUDINARY_CONFIGURED = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET)

if CLOUDINARY_CONFIGURED:
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True,
    )
else:
    logger.warning(
        "CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET not set - attachments will "
        "be saved to local disk, which Render (and most free-tier hosts) "
        "wipes on every restart/redeploy. Set these to fix attachments "
        "disappearing in production."
    )


def _looks_like_claimed_type(ext: str, head: bytes) -> bool:
    """Checks the file's actual leading bytes against what its
    extension claims to be, instead of trusting the filename alone -
    otherwise anyone can rename any file (e.g. an HTML file with an
    embedded script) to end in ".png" or ".pdf" and have it accepted
    and served back from our own domain. Not every format has a cheap,
    reliable signature to check (notably legacy .doc/.xls/.ppt, and
    plain .txt/.csv, which have no fixed header at all) - those fall
    through to "allowed by extension", same as before this function
    existed. Everything we CAN verify, we do."""

    if ext in IMAGE_EXTENSIONS:
        detected = imghdr.what(None, h=head)
        return detected in _IMGHDR_TO_EXTENSIONS and ext in _IMGHDR_TO_EXTENSIONS[detected]

    if ext == ".pdf":
        return head.startswith(b"%PDF-")

    if ext in {".docx", ".xlsx", ".pptx"}:
        # These are all just ZIP archives internally.
        return head.startswith(b"PK\x03\x04")

    if ext in {".doc", ".xls", ".ppt"}:
        # Legacy binary Office formats all share this OLE header -
        # can't distinguish which one from the header alone, but this
        # at least confirms it's a real Office binary, not something
        # renamed to look like one.
        return head.startswith(b"\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1")

    if ext == ".mp4" or ext == ".mov":
        # MP4/MOV (ISO base media format): a 4-byte size, then "ftyp".
        return len(head) >= 8 and head[4:8] == b"ftyp"

    if ext == ".webm" or ext == ".mkv":
        # Both are Matroska-based (EBML header).
        return head.startswith(b"\x1a\x45\xdf\xa3")

    if ext == ".avi":
        return head.startswith(b"RIFF") and b"AVI " in head[:16]

    return True  # .txt, .csv - no reliable signature to check


def _cloudinary_resource_type(ext: str) -> str:
    if ext in IMAGE_EXTENSIONS:
        return "image"
    if ext in VIDEO_EXTENSIONS:
        return "video"
    return "raw"  # documents - Cloudinary stores these as opaque files


@router.post("/")
async def upload_image(file: UploadFile = File(...), current_user=Depends(get_current_user)):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    contents = await file.read()
    max_size = MAX_SIZE_BY_EXTENSION[ext]
    if len(contents) > max_size:
        raise HTTPException(status_code=400, detail=f"File too large (max {max_size // (1024 * 1024)} MB for this file type)")

    if not _looks_like_claimed_type(ext, contents[:64]):
        raise HTTPException(status_code=400, detail="This file's contents don't match its extension.")

    filename = f"{uuid.uuid4().hex}{ext}"

    if CLOUDINARY_CONFIGURED:
        try:
            result = cloudinary.uploader.upload(
                contents,
                public_id=filename,
                resource_type=_cloudinary_resource_type(ext),
                folder="simdaa-solvo",
            )
            return {"url": result["secure_url"]}
        except Exception as exc:
            logger.error("Cloudinary upload failed, falling back to local disk: %s", exc)
            # Fall through to local-disk save below rather than losing
            # the user's attachment entirely over a transient API issue.

    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(contents)

    return {"url": f"/uploads/{filename}"}
