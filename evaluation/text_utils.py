import re


TOKEN_RE = re.compile(r"[0-9]+|[A-Za-zČŠŽĆĐčšžćđ]+")

STOPWORDS = {
    "ali", "brez", "da", "do", "ga", "gre", "ima", "in", "iz", "je", "jih",
    "jo", "kaj", "kako", "kakšen", "kakšna", "kakšne", "kdaj", "ker", "ki",
    "ko", "kolikšna", "koliko", "lahko", "me", "med", "mi", "mora", "moram",
    "na", "nad", "ne", "ni", "o", "ob", "od", "po", "pod", "pri", "se",
    "so", "s", "sta", "te", "ter", "to", "v", "vprašanje", "za", "z", "že",
    "kontekst", "zanesljivo", "odgovoriti", "pove", "danega", "korpusa",
}


def stem_token(token):
    token = token.lower()
    for suffix in (
        "skega", "skem", "skih", "ostjo", "anje", "enega", "ega", "imi",
        "ami", "ijo", "ost", "ih", "im", "em", "om", "a", "e", "i", "o", "u",
    ):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            return token[: -len(suffix)]
    return token


def content_terms(text):
    terms = []
    for token in TOKEN_RE.findall(text.lower()):
        if token in STOPWORDS:
            continue
        if len(token) <= 2 and not token.isdigit():
            continue
        terms.append(stem_token(token))
    return terms


def split_sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [part.strip() for part in parts if part.strip()]


# Words that appear only in Slovenian (not Serbian/Croatian/Bosnian)
_SL_MARKERS = {
    # discourse markers
    "oziroma", "namreč", "temveč", "vendarle", "torej", "čeprav", "sicer",
    # employment law terms (various inflections)
    "delodajalec", "delodajalca", "delodajalcu", "delodajalcem", "delodajalcev",
    "delavec", "delavca", "delavcu", "delavcem", "delavcev",
    "delavci", "delavce",
    "odpovedni", "odpovednega", "odpovednem", "odpovedi", "odpoved",
    "zaposlen", "zaposlena", "zaposlenim", "zaposlenih",
    "člen", "določba", "določbe", "določbo", "določil", "določa",
    "plača", "plačo", "plači", "plačila", "plačilo",
    "zakon", "zakona", "zakonom", "zakonu",
    "dopust", "dopusta", "dopustu", "dopustom",
    "delovnih", "delovni", "delovnem", "delovnega",
    "pravico", "pravici", "pravica", "pravic",
    "pogodba", "pogodbi", "pogodbo", "pogodbe",
    "odpravnina", "odpravnine", "odpravnino",
    "nadomestilo", "nadomestila",
    "odpovedal", "odpovedala",
    # Slovenian labor law abbreviations
    "ZDR", "ZZZPB", "ZMinP",
}

# Words that appear only in Serbian/Croatian/Bosnian (strong markers)
_SCR_MARKERS = {
    "što", "koji", "koja", "koje", "kojim", "kojima", "kojeg", "kojoj",
    "zbog", "radnik", "radnika", "radniku", "radnici", "radnicima",
    "poslodavac", "poslodavca", "poslodavcu",
    "ugovoru", "ugovorom", "ugovora",
    "prema", "između", "njihov", "njihova", "njihove",
    "ovaj", "ovim", "ovome", "ovoga",
    "nije", "nisu", "nismo", "niste",
    "zaposlenog", "zaposlenom",
}


def slovenian_score(text: str) -> float:
    """Return a score 0.0–5.0: 5=clearly Slovenian, 0=clearly Serbo-Croatian, 3=neutral/English."""
    if not text or len(text.split()) < 5:
        return 3.0

    words = set(re.findall(r"[A-Za-zČŠŽĆĐčšžćđ]+", text.lower()))

    sl_hits = len(words & _SL_MARKERS)
    scr_hits = len(words & _SCR_MARKERS)

    if scr_hits == 0 and sl_hits == 0:
        return 3.0  # neutral / English response

    total = sl_hits + scr_hits
    sl_ratio = sl_hits / total

    if scr_hits >= 2:
        return max(0.0, 2.0 - scr_hits * 0.5)

    if sl_hits >= 2 and scr_hits == 0:
        return min(5.0, 3.0 + sl_hits * 0.5)

    return round(sl_ratio * 5.0, 1)
