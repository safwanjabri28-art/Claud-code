#!/usr/bin/env python3
"""
Islam AI Tool — An interactive Islamic knowledge assistant.

Provides answers about the Quran, Hadith, pillars of Islam,
daily prayers, duas, prophets, and more.
"""

import random
import textwrap

from islam_knowledge import (
    COMMON_DUAS,
    DAILY_PRAYERS,
    HADITH_COLLECTION,
    ISLAMIC_MONTHS,
    PILLARS_OF_FAITH,
    PILLARS_OF_ISLAM,
    PROPHETS,
    QURAN_VERSES,
    TOPIC_KEYWORDS,
)

SEPARATOR = "─" * 60


def match_topic(user_input: str) -> list[str]:
    """Return a list of matched topic keys based on keywords in user input."""
    lower = user_input.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            matched.append(topic)
    return matched


def format_pillar(pillar: dict) -> str:
    return (
        f"  ■ {pillar['name']}"
        + (f"  ({pillar['arabic']})" if "arabic" in pillar else "")
        + f"\n    {pillar['description']}"
        + (f"\n    ➤ {pillar['details']}" if "details" in pillar else "")
    )


def format_prayer(prayer: dict) -> str:
    return (
        f"  ■ {prayer['name']}  ({prayer['arabic']})\n"
        f"    Time : {prayer['time']}\n"
        f"    Rakaat: {prayer['rakaat']}\n"
        f"    {prayer['description']}"
    )


def format_verse(verse: dict) -> str:
    return (
        f"  📖 Surah {verse['surah']} [{verse['number']}]\n"
        f"    \"{verse['text']}\""
    )


def format_hadith(h: dict) -> str:
    return f"  📜 ({h['narrator']})\n    \"{h['text']}\""


def format_dua(dua: dict) -> str:
    return (
        f"  ■ {dua['occasion']}\n"
        f"    Arabic : {dua['arabic']}\n"
        f"    Translit: {dua['transliteration']}\n"
        f"    Meaning : {dua['meaning']}"
    )


def build_response(topics: list[str], user_input: str) -> str:
    """Build a response string from matched topics."""
    sections: list[str] = []

    if "pillars" in topics or "shahada" in topics:
        header = "The Five Pillars of Islam"
        body = "\n\n".join(format_pillar(p) for p in PILLARS_OF_ISLAM)
        sections.append(f"{header}\n{body}")

    if "faith" in topics:
        header = "The Six Pillars of Faith (Iman)"
        body = "\n\n".join(format_pillar(p) for p in PILLARS_OF_FAITH)
        sections.append(f"{header}\n{body}")

    if "prayer" in topics:
        header = "The Five Daily Prayers"
        body = "\n\n".join(format_prayer(p) for p in DAILY_PRAYERS)
        sections.append(f"{header}\n{body}")

    if "quran" in topics:
        lower = user_input.lower()
        matched_verses = [
            v for v in QURAN_VERSES
            if any(kw in lower for kw in [v["topic"], v["surah"].lower()])
        ]
        if not matched_verses:
            matched_verses = random.sample(QURAN_VERSES, min(3, len(QURAN_VERSES)))
        header = "Quran Verses"
        body = "\n\n".join(format_verse(v) for v in matched_verses)
        sections.append(f"{header}\n{body}")

    if "hadith" in topics:
        lower = user_input.lower()
        matched_hadith = [
            h for h in HADITH_COLLECTION
            if h["topic"] in lower
        ]
        if not matched_hadith:
            matched_hadith = random.sample(HADITH_COLLECTION, min(3, len(HADITH_COLLECTION)))
        header = "Hadith (Sayings of the Prophet ﷺ)"
        body = "\n\n".join(format_hadith(h) for h in matched_hadith)
        sections.append(f"{header}\n{body}")

    if "dua" in topics:
        header = "Common Duas (Supplications)"
        body = "\n\n".join(format_dua(d) for d in COMMON_DUAS)
        sections.append(f"{header}\n{body}")

    if "prophets" in topics:
        header = "The 25 Prophets Mentioned in the Quran"
        body = ", ".join(PROPHETS)
        sections.append(f"{header}\n  {body}")

    if "months" in topics:
        header = "The Islamic (Hijri) Calendar Months"
        body = "\n".join(f"  {i+1}. {m}" for i, m in enumerate(ISLAMIC_MONTHS))
        sections.append(f"{header}\n{body}")

    # Topic-specific Quran + Hadith for themes like patience, mercy, etc.
    theme_topics = {"patience", "mercy", "knowledge", "gratitude", "trust", "kindness", "parents", "equality"}
    theme_matches = theme_topics & set(topics)
    if theme_matches and "quran" not in topics and "hadith" not in topics:
        for theme in theme_matches:
            verses = [v for v in QURAN_VERSES if v["topic"] == theme]
            hadiths = [h for h in HADITH_COLLECTION if h["topic"] == theme]
            parts = []
            if verses:
                parts.append("From the Quran:\n" + "\n".join(format_verse(v) for v in verses))
            if hadiths:
                parts.append("From the Hadith:\n" + "\n".join(format_hadith(h) for h in hadiths))
            if parts:
                sections.append(f"On {theme.title()}\n" + "\n\n".join(parts))

    if "fasting" in topics or "ramadan" in topics:
        fasting_pillar = PILLARS_OF_ISLAM[3]
        ramadan_verse = next((v for v in QURAN_VERSES if v["topic"] == "ramadan"), None)
        parts = [format_pillar(fasting_pillar)]
        if ramadan_verse:
            parts.append(format_verse(ramadan_verse))
        sections.append("Fasting & Ramadan\n" + "\n\n".join(parts))

    if "charity" in topics:
        zakat_pillar = PILLARS_OF_ISLAM[2]
        sections.append("Zakat (Charity)\n" + format_pillar(zakat_pillar))

    if "hajj" in topics:
        hajj_pillar = PILLARS_OF_ISLAM[4]
        sections.append("Hajj (Pilgrimage)\n" + format_pillar(hajj_pillar))

    return ("\n\n" + SEPARATOR + "\n\n").join(sections)


def get_greeting() -> str:
    return textwrap.dedent("""\
    ╔══════════════════════════════════════════════════════════╗
    ║            ﷽  — Islam AI Knowledge Tool                ║
    ║         Bismillahir Rahmanir Raheem                     ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Ask me about:                                          ║
    ║   • Five Pillars of Islam    • Quran Verses             ║
    ║   • Six Pillars of Faith     • Hadith                   ║
    ║   • Daily Prayers (Salah)    • Duas (Supplications)     ║
    ║   • Prophets in the Quran    • Islamic Calendar          ║
    ║   • Fasting & Ramadan        • Zakat (Charity)          ║
    ║   • Hajj (Pilgrimage)        • And more...              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Type 'help' for topics  |  Type 'quit' to exit        ║
    ╚══════════════════════════════════════════════════════════╝
    """)


def get_help() -> str:
    return textwrap.dedent("""\
    Available topics you can ask about:

      pillars     — The Five Pillars of Islam
      faith       — The Six Pillars of Faith (Iman)
      prayer      — The Five Daily Prayers
      quran       — Quran verses (try: "quran patience", "quran mercy")
      hadith      — Hadith / sayings of the Prophet (ﷺ)
      dua         — Common duas and supplications
      prophets    — Prophets mentioned in the Quran
      months      — Islamic Hijri calendar months
      ramadan     — Fasting and Ramadan
      charity     — Zakat and Sadaqah
      hajj        — Pilgrimage to Mecca
      patience    — Verses and hadith about patience
      mercy       — Verses and hadith about mercy
      knowledge   — Verses and hadith about seeking knowledge
      gratitude   — Verses and hadith about gratitude

    You can also ask natural questions like:
      "What are the five pillars?"
      "Tell me about prayer times"
      "Show me a hadith about kindness"
      "What does the Quran say about patience?"
    """)


def get_fallback() -> str:
    verse = random.choice(QURAN_VERSES)
    hadith = random.choice(HADITH_COLLECTION)
    return (
        "I'm not sure about that specific topic yet, but here is some "
        "beneficial knowledge:\n\n"
        + format_verse(verse)
        + "\n\n"
        + format_hadith(hadith)
        + "\n\n  Type 'help' to see all available topics."
    )


def main():
    print(get_greeting())

    while True:
        try:
            user_input = input("\n🕌 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nAssalamu Alaikum! May Allah bless you. Goodbye!")
            break

        if not user_input:
            continue

        lower = user_input.lower()

        if lower in ("quit", "exit", "bye", "q"):
            print("\nAssalamu Alaikum! May Allah bless you. Goodbye!")
            break

        if lower in ("help", "h", "?"):
            print(get_help())
            continue

        topics = match_topic(user_input)

        if topics:
            response = build_response(topics, user_input)
        else:
            response = get_fallback()

        print(f"\n{SEPARATOR}")
        print(response)
        print(SEPARATOR)


if __name__ == "__main__":
    main()
