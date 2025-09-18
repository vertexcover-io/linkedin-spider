import re


class PatternDetector:
    def __init__(self) -> None:
        self.location_patterns = [
            r"[A-Z][a-z]+,\s*[A-Z][a-z]+",
            r"[A-Z][a-z]+,\s*[A-Z]{2}",
            r"(?i)\b(remote|on-site|hybrid|work\s+from\s+home|wfh)\b",
            r"(?i)\b(united\s+states|usa|united\s+kingdom|uk|india|canada|australia|germany|france|japan|china|brazil|mexico|netherlands|sweden|norway|denmark|finland|switzerland|austria|singapore|malaysia)\b",
            r"(?i)\b(new\s+york|los\s+angeles|chicago|houston|boston|seattle|denver|atlanta|miami|san\s+francisco|mumbai|delhi|bangalore|hyderabad|chennai|london|paris|berlin|tokyo|sydney|toronto)\b",
        ]

        self.degree_patterns = [
            r"(?i)\b(bachelor|master|phd|doctor|doctorate)\b",
            r"(?i)\b(b\.?\s*(a|sc?|e|tech?|com?|ba|bs|be))\b",
            r"(?i)\b(m\.?\s*(a|sc?|e|tech?|com?|ba|bs|be))\b",
            r"(?i)\b(diploma|certificate|degree)\b",
            r"(?i)\b(engineering|computer\s+science|business|management|arts|science)\b",
        ]

        self.exclude_patterns = [
            r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            r"\b(19|20)\d{2}\b",
            r"\b\d+\s*(months?|mos|years?|yrs?)\b",
            r"(?i)\b(present|current)\b",
            r"(?i)\b(company|corp|inc|ltd|manager|director|engineer|developer)\b",
        ]

    def is_likely_location(self, text: str) -> bool:
        if not text or len(text.strip()) < 2:
            return False

        text = text.strip()

        for pattern in self.exclude_patterns:
            if re.search(pattern, text):
                return False

        for pattern in self.location_patterns:
            if re.search(pattern, text):
                return True

        if len(text) > 100:
            return False

        return False

    def is_likely_degree(self, text: str) -> bool:
        if not text or len(text.strip()) < 3:
            return False

        text = text.strip()

        for pattern in self.exclude_patterns:
            if re.search(pattern, text):
                return False

        for pattern in self.degree_patterns:
            if re.search(pattern, text):
                return True

        return False

    def is_time_duration(self, text: str) -> bool:
        if not text:
            return False

        duration_patterns = [
            r"\b\d+\s*(months?|mos|years?|yrs?)\b",
            r"(?i)\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b",
            r"\b(19|20)\d{2}\b",
            r"(?i)\b(present|current)\b",
        ]

        for pattern in duration_patterns:
            if re.search(pattern, text):
                return True

        return False
