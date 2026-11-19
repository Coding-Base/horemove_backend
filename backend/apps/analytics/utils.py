import re

KNOWN_BOT_PATTERNS = [
    r"bot",
    r"crawler",
    r"spider",
    r"slurp",
    r"googlebot",
    r"bingbot",
    r"yandex",
    r"baiduspider",
    r"duckduckbot",
    r"facebookexternalhit",
    r"twitterbot",
    r"linkedinbot",
    r"whatsapp",
    r"telegrambot",
    r"uptime",
    r"pingdom",
    r"ahrefsbot",
    r"semrushbot",
    r"dotbot",
    r"rogue",
    r"python-requests",
    r"postmanruntime",
    r"curl",
    r"wget",
    r"headlesschrome",
]

BOT_REGEX = re.compile("|".join(KNOWN_BOT_PATTERNS), re.IGNORECASE)

COUNTRY_NAMES = {
    "NG": "Nigeria",
    "US": "United States",
    "GB": "United Kingdom",
    "GH": "Ghana",
    "KE": "Kenya",
    "ZA": "South Africa",
    "CA": "Canada",
    "DE": "Germany",
    "FR": "France",
    "AU": "Australia",
    "IN": "India",
    "CM": "Cameroon",
    "LR": "Liberia",
    "SL": "Sierra Leone",
    "UG": "Uganda",
    "RW": "Rwanda",
    "TZ": "Tanzania",
    "ZW": "Zimbabwe",
    "ZM": "Zambia",
    "CI": "Côte d'Ivoire",
    "BJ": "Benin",
    "TG": "Togo",
    "IT": "Italy",
    "ES": "Spain",
    "NL": "Netherlands",
    "BR": "Brazil",
    "PH": "Philippines",
    "AE": "United Arab Emirates",
}

PAGE_TITLE_MAP = {
    "/": "Homepage & Video Emblem",
    "/about": "About HOREMOW",
    "/sermons": "Audio & Video Sermons",
    "/devotional": "Daily Devotional",
    "/directory": "Overseers & Leadership Directory",
    "/give": "Donations & Giving Portal",
    "/events": "Global Conferences & Crusades",
    "/bookstore": "Holiness Bookstore",
    "/gallery": "Conference & Crusades Gallery",
    "/blog": "HOREMOW Journal",
    "/broadcasts": "Broadcasts & TV Stream",
    "/locations": "Fellowship Locations",
    "/contact": "Contact Headquarters",
}


def is_bot_user_agent(user_agent: str) -> bool:
    if not user_agent:
        return False
    return bool(BOT_REGEX.search(user_agent))


def detect_device_type(user_agent: str) -> str:
    if not user_agent:
        return "desktop"
    ua = user_agent.lower()
    if any(k in ua for k in ["ipad", "tablet", "playbook", "silk", "kindle"]):
        return "tablet"
    if "android" in ua and "mobile" not in ua:
        return "tablet"
    if any(k in ua for k in ["mobile", "iphone", "ipod", "android", "blackberry", "opera mini", "windows phone"]):
        return "mobile"
    return "desktop"


def get_client_ip(request) -> str:
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "")


def resolve_country(request) -> tuple[str, str]:
    """
    Resolves country code and country name from reverse proxy headers
    (such as Cloudflare CF-IPCountry or Render headers).
    Defaults to Nigeria ("NG") for localhost / development.
    """
    cf_country = request.META.get("HTTP_CF_IPCOUNTRY", "").upper()
    if cf_country and len(cf_country) == 2 and cf_country != "XX":
        name = COUNTRY_NAMES.get(cf_country, cf_country)
        return cf_country, name

    x_country = request.META.get("HTTP_X_COUNTRY_CODE", "").upper()
    if x_country and len(x_country) == 2 and x_country != "XX":
        name = COUNTRY_NAMES.get(x_country, x_country)
        return x_country, name

    # Check for localhost / private IP in development
    ip = get_client_ip(request)
    if ip in ["127.0.0.1", "localhost", "::1"] or ip.startswith("192.168.") or ip.startswith("10."):
        return "NG", "Nigeria"

    return "XX", "Global / Unassigned"
