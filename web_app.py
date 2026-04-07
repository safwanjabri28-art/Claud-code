#!/usr/bin/env python3
"""
Islam AI Tool — Web Interface
A Flask-based web app for the Islamic knowledge assistant.
"""

from flask import Flask, render_template, request, jsonify

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

import random

app = Flask(__name__)


def match_topic(user_input: str) -> list[str]:
    lower = user_input.lower()
    matched = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            matched.append(topic)
    return matched


def build_response(topics: list[str], user_input: str) -> dict:
    """Build a structured response from matched topics."""
    sections = []

    if "pillars" in topics or "shahada" in topics:
        sections.append({
            "title": "The Five Pillars of Islam",
            "type": "pillars",
            "items": PILLARS_OF_ISLAM,
        })

    if "faith" in topics:
        sections.append({
            "title": "The Six Pillars of Faith (Iman)",
            "type": "faith",
            "items": PILLARS_OF_FAITH,
        })

    if "prayer" in topics:
        sections.append({
            "title": "The Five Daily Prayers",
            "type": "prayers",
            "items": DAILY_PRAYERS,
        })

    if "quran" in topics:
        lower = user_input.lower()
        matched_verses = [
            v for v in QURAN_VERSES
            if any(kw in lower for kw in [v["topic"], v["surah"].lower()])
        ]
        if not matched_verses:
            matched_verses = random.sample(QURAN_VERSES, min(3, len(QURAN_VERSES)))
        sections.append({
            "title": "Quran Verses",
            "type": "quran",
            "items": matched_verses,
        })

    if "hadith" in topics:
        lower = user_input.lower()
        matched_hadith = [
            h for h in HADITH_COLLECTION if h["topic"] in lower
        ]
        if not matched_hadith:
            matched_hadith = random.sample(HADITH_COLLECTION, min(3, len(HADITH_COLLECTION)))
        sections.append({
            "title": "Hadith (Sayings of the Prophet \ufdfa)",
            "type": "hadith",
            "items": matched_hadith,
        })

    if "dua" in topics:
        sections.append({
            "title": "Common Duas (Supplications)",
            "type": "duas",
            "items": COMMON_DUAS,
        })

    if "prophets" in topics:
        sections.append({
            "title": "The 25 Prophets Mentioned in the Quran",
            "type": "prophets",
            "items": PROPHETS,
        })

    if "months" in topics:
        sections.append({
            "title": "The Islamic (Hijri) Calendar Months",
            "type": "months",
            "items": ISLAMIC_MONTHS,
        })

    theme_topics = {"patience", "mercy", "knowledge", "gratitude", "trust", "kindness", "parents", "equality"}
    theme_matches = theme_topics & set(topics)
    if theme_matches and "quran" not in topics and "hadith" not in topics:
        for theme in theme_matches:
            verses = [v for v in QURAN_VERSES if v["topic"] == theme]
            hadiths = [h for h in HADITH_COLLECTION if h["topic"] == theme]
            items = []
            if verses:
                items.append({"type": "quran", "data": verses})
            if hadiths:
                items.append({"type": "hadith", "data": hadiths})
            if items:
                sections.append({
                    "title": f"On {theme.title()}",
                    "type": "theme",
                    "items": items,
                })

    if "fasting" in topics:
        sections.append({
            "title": "Fasting & Ramadan",
            "type": "pillars",
            "items": [PILLARS_OF_ISLAM[3]],
        })

    if "charity" in topics:
        sections.append({
            "title": "Zakat (Charity)",
            "type": "pillars",
            "items": [PILLARS_OF_ISLAM[2]],
        })

    if "hajj" in topics:
        sections.append({
            "title": "Hajj (Pilgrimage)",
            "type": "pillars",
            "items": [PILLARS_OF_ISLAM[4]],
        })

    return {"sections": sections}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    user_input = data.get("question", "").strip()

    if not user_input:
        return jsonify({"sections": []})

    topics = match_topic(user_input)

    if topics:
        response = build_response(topics, user_input)
    else:
        verse = random.choice(QURAN_VERSES)
        hadith = random.choice(HADITH_COLLECTION)
        response = {
            "sections": [
                {
                    "title": "Here is some beneficial knowledge",
                    "type": "quran",
                    "items": [verse],
                },
                {
                    "title": "A Hadith for You",
                    "type": "hadith",
                    "items": [hadith],
                },
            ],
            "fallback": True,
        }

    return jsonify(response)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
