import re
import unicodedata

CATEGORY_KEYWORDS = {
    "cafe": ("cafe", "coffee", "espresso", "καφε", "καφετερ"),
    "restaurant": (
        "restaurant",
        "dinner",
        "lunch",
        "meal",
        "food",
        "taverna",
        "εστιατορ",
        "φαγητ",
        "γευμα",
        "ταβερν",
    ),
    "bakery": ("bakery", "bread", "pastry", "αρτοποι", "φουρν", "ψωμι"),
    "supermarket": ("supermarket", "grocery", "groceries", "σουπερ μαρκετ"),
    "pharmacy": ("pharmacy", "medicine", "drugstore", "φαρμακ", "φαρμακα"),
    "clothes": ("clothes", "clothing", "fashion", "ρουχα", "ενδυ"),
    "books": ("bookshop", "bookstore", "books", "βιβλιοπωλ", "βιβλια"),
    "convenience": ("convenience store", "mini market", "παντοπωλ", "μινι μαρκετ"),
    "hairdresser": (
        "hairdresser",
        "hair salon",
        "haircut",
        "barber",
        "κομμωτ",
        "κουρειο",
        "κουρεμα",
    ),
    "hotel": ("hotel", "accommodation", "stay", "ξενοδοχ", "διαμον"),
}


def normalize_search_text(value):
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    return re.sub(r"[^\w]+", " ", without_accents).strip()


def infer_categories(question):
    normalized = normalize_search_text(question)
    return [
        category
        for category, keywords in CATEGORY_KEYWORDS.items()
        if any(normalize_search_text(keyword) in normalized for keyword in keywords)
    ]
