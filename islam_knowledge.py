"""
Islamic Knowledge Base
Contains structured data about core Islamic teachings, Quran verses,
Hadith, pillars, prayers, and more.
"""

PILLARS_OF_ISLAM = [
    {
        "name": "Shahada (Declaration of Faith)",
        "arabic": "الشهادة",
        "description": (
            "The declaration that there is no god but Allah and that "
            "Muhammad (peace be upon him) is His messenger. "
            "It is the foundation of the Islamic faith."
        ),
        "details": (
            "La ilaha illallah, Muhammadur Rasulullah — "
            "There is no deity worthy of worship except Allah, "
            "and Muhammad is the Messenger of Allah."
        ),
    },
    {
        "name": "Salah (Prayer)",
        "arabic": "الصلاة",
        "description": (
            "Muslims are required to perform five daily prayers "
            "facing the Kaaba in Mecca."
        ),
        "details": (
            "The five prayers are: Fajr (dawn), Dhuhr (midday), "
            "Asr (afternoon), Maghrib (sunset), and Isha (night)."
        ),
    },
    {
        "name": "Zakat (Charity)",
        "arabic": "الزكاة",
        "description": (
            "An obligatory form of charity, typically 2.5% of one's "
            "accumulated wealth annually, given to those in need."
        ),
        "details": (
            "Zakat purifies wealth and helps bridge the gap between "
            "the rich and the poor. It is one of the most important "
            "acts of worship in Islam."
        ),
    },
    {
        "name": "Sawm (Fasting during Ramadan)",
        "arabic": "الصوم",
        "description": (
            "Fasting from dawn to sunset during the holy month of "
            "Ramadan, abstaining from food, drink, and other "
            "physical needs."
        ),
        "details": (
            "Fasting teaches self-discipline, self-control, sacrifice, "
            "and empathy for those who are less fortunate. "
            "It is also a time for spiritual reflection and increased devotion."
        ),
    },
    {
        "name": "Hajj (Pilgrimage to Mecca)",
        "arabic": "الحج",
        "description": (
            "A pilgrimage to the holy city of Mecca that every "
            "able-bodied Muslim who can afford it must perform "
            "at least once in their lifetime."
        ),
        "details": (
            "Hajj takes place during the Islamic month of Dhul Hijjah. "
            "It involves rituals including Tawaf (circling the Kaaba), "
            "Sa'i (walking between Safa and Marwah), and standing at Arafat."
        ),
    },
]

PILLARS_OF_FAITH = [
    {
        "name": "Belief in Allah",
        "description": "Belief in the oneness of God (Tawhid), the most fundamental concept in Islam.",
    },
    {
        "name": "Belief in Angels",
        "description": "Belief in the angels created by Allah, including Jibreel (Gabriel), Mikael, and others.",
    },
    {
        "name": "Belief in Holy Books",
        "description": (
            "Belief in the revealed books: the Quran, Torah (Tawrat), "
            "Psalms (Zabur), Gospel (Injil), and the Scrolls of Ibrahim."
        ),
    },
    {
        "name": "Belief in Prophets",
        "description": (
            "Belief in all prophets sent by Allah, from Adam to Muhammad "
            "(peace be upon them all), including Ibrahim, Musa, Isa, and others."
        ),
    },
    {
        "name": "Belief in the Day of Judgment",
        "description": "Belief that all people will be resurrected and held accountable for their deeds.",
    },
    {
        "name": "Belief in Divine Decree (Qadar)",
        "description": "Belief that everything that happens is by the will and knowledge of Allah.",
    },
]

QURAN_VERSES = [
    {
        "surah": "Al-Fatiha",
        "number": "1:1-7",
        "topic": "opening",
        "text": (
            "In the name of Allah, the Most Gracious, the Most Merciful. "
            "All praise is due to Allah, Lord of all the worlds. "
            "The Most Gracious, the Most Merciful. Master of the Day of Judgment. "
            "You alone we worship, and You alone we ask for help. "
            "Guide us on the Straight Path, the path of those who have received "
            "Your grace; not the path of those who have brought down wrath upon "
            "themselves, nor of those who have gone astray."
        ),
    },
    {
        "surah": "Al-Baqarah",
        "number": "2:255",
        "topic": "ayatul kursi",
        "text": (
            "Allah! There is no deity except Him, the Ever-Living, the Sustainer "
            "of existence. Neither drowsiness overtakes Him nor sleep. To Him "
            "belongs whatever is in the heavens and whatever is on the earth. "
            "Who is it that can intercede with Him except by His permission? "
            "He knows what is before them and what will be after them, and they "
            "encompass not a thing of His knowledge except for what He wills. "
            "His Kursi extends over the heavens and the earth, and their "
            "preservation tires Him not. And He is the Most High, the Most Great."
        ),
    },
    {
        "surah": "Al-Ikhlas",
        "number": "112:1-4",
        "topic": "tawhid",
        "text": (
            "Say: He is Allah, the One. Allah, the Eternal Refuge. "
            "He neither begets nor is born. Nor is there to Him any equivalent."
        ),
    },
    {
        "surah": "Al-Baqarah",
        "number": "2:286",
        "topic": "mercy",
        "text": (
            "Allah does not burden a soul beyond that it can bear. "
            "It will have the consequence of what good it has gained, "
            "and it will bear the consequence of what evil it has earned."
        ),
    },
    {
        "surah": "Al-Imran",
        "number": "3:139",
        "topic": "patience",
        "text": "Do not lose heart, nor fall into despair, for you will triumph if you are believers.",
    },
    {
        "surah": "Ar-Rahman",
        "number": "55:13",
        "topic": "gratitude",
        "text": "So which of the favors of your Lord would you deny?",
    },
    {
        "surah": "Al-Baqarah",
        "number": "2:152",
        "topic": "remembrance",
        "text": "So remember Me; I will remember you. And be grateful to Me and do not deny Me.",
    },
    {
        "surah": "At-Tawbah",
        "number": "9:51",
        "topic": "trust",
        "text": (
            "Say: Nothing will happen to us except what Allah has decreed for us; "
            "He is our protector. And upon Allah let the believers rely."
        ),
    },
    {
        "surah": "Al-Ankabut",
        "number": "29:69",
        "topic": "guidance",
        "text": (
            "And those who strive for Us — We will surely guide them to Our ways. "
            "And indeed, Allah is with the doers of good."
        ),
    },
    {
        "surah": "Ash-Sharh",
        "number": "94:5-6",
        "topic": "hardship",
        "text": "Indeed, with hardship comes ease. Indeed, with hardship comes ease.",
    },
    {
        "surah": "Al-Hujurat",
        "number": "49:13",
        "topic": "equality",
        "text": (
            "O mankind, indeed We have created you from male and female and made "
            "you peoples and tribes that you may know one another. Indeed, the "
            "most noble of you in the sight of Allah is the most righteous of you."
        ),
    },
    {
        "surah": "Al-Baqarah",
        "number": "2:185",
        "topic": "ramadan",
        "text": (
            "The month of Ramadan in which was revealed the Quran, a guidance "
            "for the people and clear proofs of guidance and criterion."
        ),
    },
]

HADITH_COLLECTION = [
    {
        "narrator": "Bukhari & Muslim",
        "topic": "actions",
        "text": (
            "The Prophet (peace be upon him) said: 'Actions are judged by "
            "intentions, and every person will get what they intended.'"
        ),
    },
    {
        "narrator": "Muslim",
        "topic": "kindness",
        "text": (
            "The Prophet (peace be upon him) said: 'None of you truly believes "
            "until he loves for his brother what he loves for himself.'"
        ),
    },
    {
        "narrator": "Bukhari",
        "topic": "character",
        "text": (
            "The Prophet (peace be upon him) said: 'The best among you are those "
            "who have the best character and manners.'"
        ),
    },
    {
        "narrator": "Tirmidhi",
        "topic": "knowledge",
        "text": (
            "The Prophet (peace be upon him) said: 'Seeking knowledge is an "
            "obligation upon every Muslim.'"
        ),
    },
    {
        "narrator": "Muslim",
        "topic": "mercy",
        "text": (
            "The Prophet (peace be upon him) said: 'The merciful are shown "
            "mercy by the Most Merciful. Be merciful to those on earth, "
            "and the One in the heavens will be merciful to you.'"
        ),
    },
    {
        "narrator": "Bukhari",
        "topic": "patience",
        "text": (
            "The Prophet (peace be upon him) said: 'No fatigue, nor disease, "
            "nor sorrow, nor sadness, nor hurt, nor distress befalls a Muslim, "
            "even if it were the prick of a thorn, but that Allah expiates "
            "some of his sins for that.'"
        ),
    },
    {
        "narrator": "Bukhari & Muslim",
        "topic": "speech",
        "text": (
            "The Prophet (peace be upon him) said: 'Whoever believes in Allah "
            "and the Last Day should speak good or remain silent.'"
        ),
    },
    {
        "narrator": "Muslim",
        "topic": "gratitude",
        "text": (
            "The Prophet (peace be upon him) said: 'Look at those below you "
            "and do not look at those above you, for it is the best way not "
            "to belittle the blessings of Allah.'"
        ),
    },
    {
        "narrator": "Tirmidhi",
        "topic": "trust",
        "text": (
            "The Prophet (peace be upon him) said: 'If you put your trust "
            "completely in Allah, He will arrange for your sustenance in the "
            "same way as He provides for the birds. They go out in the morning "
            "with empty stomachs and return filled in the evening.'"
        ),
    },
    {
        "narrator": "Bukhari",
        "topic": "parents",
        "text": (
            "The Prophet (peace be upon him) was asked: 'Which deed is most "
            "beloved to Allah?' He said: 'Prayer at its proper time.' He was "
            "asked: 'Then what?' He said: 'Being dutiful to parents.'"
        ),
    },
]

DAILY_PRAYERS = [
    {
        "name": "Fajr",
        "arabic": "الفجر",
        "time": "Dawn (before sunrise)",
        "rakaat": "2 Sunnah + 2 Fard",
        "description": "The pre-dawn prayer, performed before the sun rises.",
    },
    {
        "name": "Dhuhr",
        "arabic": "الظهر",
        "time": "After midday",
        "rakaat": "4 Sunnah + 4 Fard + 2 Sunnah",
        "description": "The midday prayer, performed after the sun passes its zenith.",
    },
    {
        "name": "Asr",
        "arabic": "العصر",
        "time": "Afternoon",
        "rakaat": "4 Fard",
        "description": "The afternoon prayer, performed in the late afternoon.",
    },
    {
        "name": "Maghrib",
        "arabic": "المغرب",
        "time": "Just after sunset",
        "rakaat": "3 Fard + 2 Sunnah",
        "description": "The evening prayer, performed just after the sun sets.",
    },
    {
        "name": "Isha",
        "arabic": "العشاء",
        "time": "Night",
        "rakaat": "4 Fard + 2 Sunnah + 3 Witr",
        "description": "The night prayer, performed after twilight disappears.",
    },
]

PROPHETS = [
    "Adam", "Idris (Enoch)", "Nuh (Noah)", "Hud", "Salih",
    "Ibrahim (Abraham)", "Lut (Lot)", "Ismail (Ishmael)", "Ishaq (Isaac)",
    "Yaqub (Jacob)", "Yusuf (Joseph)", "Shuayb", "Ayyub (Job)",
    "Musa (Moses)", "Harun (Aaron)", "Dhul-Kifl (Ezekiel)",
    "Dawud (David)", "Sulayman (Solomon)", "Ilyas (Elijah)",
    "Al-Yasa (Elisha)", "Yunus (Jonah)", "Zakariya (Zechariah)",
    "Yahya (John the Baptist)", "Isa (Jesus)", "Muhammad (peace be upon him)",
]

ISLAMIC_MONTHS = [
    "Muharram", "Safar", "Rabi al-Awwal", "Rabi al-Thani",
    "Jumada al-Ula", "Jumada al-Thani", "Rajab", "Sha'ban",
    "Ramadan", "Shawwal", "Dhul Qa'dah", "Dhul Hijjah",
]

COMMON_DUAS = [
    {
        "occasion": "Before eating",
        "arabic": "بسم الله",
        "transliteration": "Bismillah",
        "meaning": "In the name of Allah.",
    },
    {
        "occasion": "After eating",
        "arabic": "الحمد لله الذي أطعمنا وسقانا وجعلنا مسلمين",
        "transliteration": "Alhamdulillahil-ladhi at'amana wa saqana wa ja'alana muslimeen",
        "meaning": "All praise is due to Allah who fed us, gave us drink, and made us Muslims.",
    },
    {
        "occasion": "Before sleeping",
        "arabic": "باسمك اللهم أموت وأحيا",
        "transliteration": "Bismika Allahumma amutu wa ahya",
        "meaning": "In Your name, O Allah, I die and I live.",
    },
    {
        "occasion": "Upon waking up",
        "arabic": "الحمد لله الذي أحيانا بعد ما أماتنا وإليه النشور",
        "transliteration": "Alhamdulillahil-ladhi ahyana ba'da ma amatana wa ilayhin-nushur",
        "meaning": "All praise is due to Allah, who gave us life after death, and to Him is the return.",
    },
    {
        "occasion": "Entering the mosque",
        "arabic": "اللهم افتح لي أبواب رحمتك",
        "transliteration": "Allahumma-ftah li abwaba rahmatik",
        "meaning": "O Allah, open the doors of Your mercy for me.",
    },
    {
        "occasion": "For guidance",
        "arabic": "اللهم اهدني وسددني",
        "transliteration": "Allahumma-hdini wa saddidni",
        "meaning": "O Allah, guide me and keep me on the right path.",
    },
    {
        "occasion": "For forgiveness",
        "arabic": "أستغفر الله العظيم وأتوب إليه",
        "transliteration": "Astaghfirullaha al-'Azeem wa atubu ilayh",
        "meaning": "I seek forgiveness from Allah the Almighty, and I repent to Him.",
    },
    {
        "occasion": "For patience",
        "arabic": "ربنا أفرغ علينا صبرا وثبت أقدامنا",
        "transliteration": "Rabbana afrigh 'alayna sabran wa thabbit aqdamana",
        "meaning": "Our Lord, pour upon us patience and plant firmly our feet.",
    },
]

TOPIC_KEYWORDS = {
    "pillars": ["pillar", "pillars", "five pillars", "arkan", "rukn"],
    "faith": ["faith", "iman", "belief", "believe", "aqeedah"],
    "prayer": ["prayer", "salah", "salat", "namaz", "pray", "prayers"],
    "quran": ["quran", "verse", "ayah", "surah", "ayat", "recite"],
    "hadith": ["hadith", "sunnah", "prophet said", "narrated", "hadeeth"],
    "fasting": ["fasting", "fast", "sawm", "ramadan", "siyam"],
    "charity": ["charity", "zakat", "sadaqah", "giving", "donate"],
    "hajj": ["hajj", "pilgrimage", "mecca", "kaaba", "umrah"],
    "dua": ["dua", "supplication", "prayer for", "pray for", "duas"],
    "prophets": ["prophet", "prophets", "messenger", "nabi", "rasul"],
    "months": ["month", "months", "islamic calendar", "hijri"],
    "shahada": ["shahada", "declaration", "testimony", "kalima"],
    "patience": ["patience", "sabr", "hardship", "difficulty", "trial"],
    "mercy": ["mercy", "merciful", "rahma", "compassion", "forgiveness"],
    "knowledge": ["knowledge", "learn", "study", "ilm", "education"],
    "gratitude": ["gratitude", "thankful", "grateful", "shukr", "alhamdulillah"],
    "trust": ["trust", "tawakkul", "reliance", "rely on allah"],
    "kindness": ["kindness", "kind", "good character", "akhlaq", "manners"],
    "parents": ["parents", "mother", "father", "family", "honor parents"],
    "equality": ["equality", "equal", "racism", "tribe", "nation"],
}
