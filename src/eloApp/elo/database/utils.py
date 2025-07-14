import unicodedata
import re

def normalizar_string(s):
    """Normaliza uma string: minúsculas, sem acentos, sem espaços extras e com underscores."""
    if not isinstance(s, str):
        return ""
    nfkd_form = unicodedata.normalize('NFKD', s)
    sem_acentos = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    sem_espacos_extra = re.sub(r'\s+', ' ', sem_acentos).strip()
    com_underscore = sem_espacos_extra.replace(' ', '_')
    final = re.sub(r'[^a-zA-Z0-9_]', '', com_underscore)
    return final.lower()