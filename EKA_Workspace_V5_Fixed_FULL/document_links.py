"""Validate Drive references without downloading or requesting remote content."""
import re
from urllib.parse import urlsplit,parse_qs,urlencode


def google_drive_reference(value):
    value=value.strip()
    if not value or len(value)>2048 or any(char.isspace() or ord(char)<32 for char in value):
        raise ValueError('Masukkan tautan Google Drive yang valid (maksimal 2048 karakter)')
    try:parts=urlsplit(value);port=parts.port
    except ValueError:raise ValueError('Tautan Google Drive tidak valid')
    host=(parts.hostname or '').lower()
    if parts.scheme!='https' or host not in ('drive.google.com','docs.google.com') or parts.username or parts.password or port not in (None,443):
        raise ValueError('Gunakan tautan HTTPS dari drive.google.com atau docs.google.com')
    query=parse_qs(parts.query)
    identifier=None
    if host=='drive.google.com':
        match=re.fullmatch(r'/file/d/([A-Za-z0-9_-]+)(?:/view|/preview|/edit)?/?',parts.path)
        folder=re.fullmatch(r'/drive/(?:u/\d+/)?folders/([A-Za-z0-9_-]+)/?',parts.path)
        if match:identifier=match.group(1);path='/file/d/'+identifier+'/view'
        elif folder:identifier=folder.group(1);path='/drive/folders/'+identifier
        elif parts.path in ('/open','/uc'):
            identifier=query.get('id',[''])[0];path='/file/d/'+identifier+'/view'
    else:
        match=re.fullmatch(r'/(document|spreadsheets|presentation|forms|drawings)/d/([A-Za-z0-9_-]+)(?:/[^\s]*)?',parts.path)
        if match:identifier=match.group(2);path='/'+match.group(1)+'/d/'+identifier+'/edit'
    if not identifier or not re.fullmatch(r'[A-Za-z0-9_-]{8,200}',identifier):
        raise ValueError('Gunakan tautan berbagi file, folder Drive, atau dokumen Google yang lengkap')
    resource=query.get('resourcekey',[''])[0]
    if resource and not re.fullmatch(r'[A-Za-z0-9_-]{1,200}',resource):raise ValueError('Resource key Google Drive tidak valid')
    url='https://'+host+path+('?' + urlencode({'resourcekey':resource}) if resource else '')
    return {'url':url,'identifier':identifier,'kind':'folder' if host=='drive.google.com' and '/folders/' in path else 'file'}
