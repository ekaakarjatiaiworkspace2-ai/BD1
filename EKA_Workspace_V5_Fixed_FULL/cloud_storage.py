"""Private storage for yearly company documents. Local testing or S3-compatible private bucket."""
import os
from pathlib import Path
from urllib.parse import quote
from fastapi import HTTPException
from fastapi.responses import FileResponse,StreamingResponse

def storage_mode():
    return "s3" if os.getenv("S3_BUCKET") else "local"

class FileStore:
    def __init__(self,root:Path):
        self.root=root
        self.root.mkdir(parents=True,exist_ok=True)
        self.mode=storage_mode()
        if self.mode=="s3":
            import boto3
            from botocore.config import Config
            self.bucket=os.environ["S3_BUCKET"]
            self.client=boto3.client("s3",
                endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
                region_name=os.getenv("S3_REGION","auto"),
                aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
                config=Config(signature_version="s3v4",retries={"max_attempts":3,"mode":"standard"}))
    def put(self,stream,key):
        stream.seek(0)
        if self.mode=="s3":
            self.client.upload_fileobj(stream,self.bucket,key,ExtraArgs={"ContentType":"application/octet-stream"})
        else:
            dest=self.root/key;dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("wb") as fp:
                while data:=stream.read(1024*1024):fp.write(data)
    def delete(self,key):
        if self.mode=="s3":self.client.delete_object(Bucket=self.bucket,Key=key)
        else:(self.root/key).unlink(missing_ok=True)
    def response(self,key,filename):
        # Content-Disposition forces download: no execution of uploaded HTML or other untrusted files.
        clean=filename.replace("\r","").replace("\n","").replace("\\","_").replace('"','_')
        if self.mode=="s3":
            from starlette.responses import StreamingResponse
            try:r=self.client.get_object(Bucket=self.bucket,Key=key)
            except Exception:raise HTTPException(404,"Berkas tidak ditemukan di penyimpanan")
            def iterate():
                try:
                    for b in r["Body"].iter_chunks(chunk_size=1024*1024):
                        if b:yield b
                finally:r["Body"].close()
            return StreamingResponse(iterate(),media_type="application/octet-stream",
                headers={"Content-Disposition":f"attachment; filename*=UTF-8''{quote(clean)}","Cache-Control":"no-store",
                "X-Content-Type-Options":"nosniff"})
        dest=self.root/key
        if not dest.is_file():raise HTTPException(404,"Berkas tidak ditemukan di penyimpanan")
        return FileResponse(dest,filename=clean,media_type="application/octet-stream",headers={"Cache-Control":"no-store","X-Content-Type-Options":"nosniff"})
