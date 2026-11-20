import datetime
import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

# 181 days from Jan 1, 2027 to Jun 30, 2027
START_DATE = datetime.date(2027, 1, 1)
END_DATE = datetime.date(2027, 6, 30)

TOPICS = [
    "WALKING IN UNDEFILED PURITY",
    "THE HIGH CALLING OF SANCTIFICATION",
    "SEEKING GOD WITH WHOLEHEARTED DEVOTION",
    "VICTORY OVER TEMPTATION THROUGH TRUTH",
    "RESTITUTION AND A CONSCIENCE VOID OF OFFENCE",
    "FAITHFUL STEWARDSHIP IN THE KINGDOM",
    "THE POWER OF PERSEVERING PRAYER",
    "CRUCIFYING THE FLESH AND ITS DESIRES",
    "ABSOLUTE SURRENDER TO CHRIST",
    "THE COMING OF THE LORD AND OUR PREPARATION",
    "PURGING THE VESSEL UNTO HONOUR",
    "GUARDING YOUR HEART WITH ALL DILIGENCE",
]

TEXT_PASSAGES = [
    ("PSALM 119:1-8", [
        "1. Blessed are the undefiled in the way, who walk in the law of the Lord.",
        "2. Blessed are they that keep his testimonies, and that seek him with the whole heart.",
        "3. They also do no iniquity: they walk in his ways.",
        "4. Thou hast commanded us to keep thy precepts diligently."
    ]),
    ("HEBREWS 12:1-4", [
        "1. Wherefore seeing we also are compassed about with so great a cloud of witnesses, let us lay aside every weight, and the sin which doth so easily beset us.",
        "2. Looking unto Jesus the author and finisher of our faith; who for the joy that was set before him endured the cross.",
        "3. For consider him that endured such contradiction of sinners against himself, lest ye be wearied and faint in your minds."
    ]),
    ("1 PETER 1:13-16", [
        "13. Wherefore gird up the loins of your mind, be sober, and hope to the end for the grace that is to be brought unto you.",
        "14. As obedient children, not fashioning yourselves according to the former lusts in your ignorance.",
        "15. But as he which hath called you is holy, so be ye holy in all manner of conversation;",
        "16. Because it is written, Be ye holy; for I am holy."
    ]),
    ("ROMANS 12:1-2", [
        "1. I beseech you therefore, brethren, by the mercies of God, that ye present your bodies a living sacrifice, holy, acceptable unto God, which is your reasonable service.",
        "2. And be not conformed to this world: but be ye transformed by the renewing of your mind, that ye may prove what is that good, and acceptable, and perfect, will of God."
    ]),
]

KEY_VERSES = [
    ("HEBREWS 12:14", "Follow peace with all men, and holiness, without which no man shall see the Lord."),
    ("1 JOHN 2:15", "Love not the world, neither the things that in the world. If any man love the world, the love of the Father is not in him."),
    ("PSALM 24:3-4", "Who shall ascend into the hill of the Lord? or who shall stand in his holy place? He that hath clean hands, and a pure heart."),
    ("2 TIMOTHY 2:19", "Let every one that nameth the name of Christ depart from iniquity."),
    ("MATTHEW 5:8", "Blessed are the pure in heart: for they shall see God."),
]

THOUGHTS = [
    "Purge yourself thoroughly to be a vessel unto honour in God's vineyard.",
    "A holy life is the greatest testimony to an unbelieving world.",
    "Do not compromise truth for temporary comfort; eternity is forever.",
    "Let your heart and actions align with the righteous standard of Christ.",
    "Watch and pray continually, for the day of our Lord draweth nigh.",
]

SONGS = [
    "Have you been to Jesus for the cleansing power…",
    "Take my life, and let it be consecrated, Lord, to Thee…",
    "Nearer, my God, to Thee, nearer to Thee…",
    "I have decided to follow Jesus, no turning back…",
    "Holy, Holy, Holy! Lord God Almighty! Early in the morning our song shall rise to Thee…",
]

def generate_devotional_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "HeaderTitle",
        parent=styles["Heading1"],
        fontSize=12,
        leading=14,
        textColor="#1a4b8c",
        alignment=1,
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )
    author_style = ParagraphStyle(
        "HeaderAuthor",
        parent=styles["Normal"],
        fontSize=10,
        leading=12,
        textColor="#333333",
        alignment=1,
        fontName="Helvetica",
        spaceAfter=14,
    )
    meta_style = ParagraphStyle(
        "DevMeta",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
        textColor="#000000",
        fontName="Helvetica-Bold",
        spaceAfter=6,
    )
    passage_style = ParagraphStyle(
        "PassageStyle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor="#222222",
        fontName="Helvetica-Oblique",
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "DevBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor="#1a1a1a",
        fontName="Helvetica",
        spaceAfter=8,
    )
    footer_item_style = ParagraphStyle(
        "FooterItem",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor="#2c3e50",
        fontName="Helvetica-Bold",
        spaceAfter=4,
    )

    elements = []
    current_date = START_DATE
    day_count = 0

    while current_date <= END_DATE:
        day_count += 1
        day_of_week = current_date.strftime("%A").upper()
        month_name = current_date.strftime("%B").upper()
        day_num = current_date.day
        year_num = current_date.year

        topic = TOPICS[(day_count - 1) % len(TOPICS)]
        passage_ref, passage_verses = TEXT_PASSAGES[(day_count - 1) % len(TEXT_PASSAGES)]
        kv_ref, kv_text = KEY_VERSES[(day_count - 1) % len(KEY_VERSES)]
        thought = THOUGHTS[(day_count - 1) % len(THOUGHTS)]
        song = SONGS[(day_count - 1) % len(SONGS)]
        reading = f"Genesis {day_count}-{day_count + 1}" if day_count < 50 else f"Matthew {day_count - 49}"

        # Header
        elements.append(Paragraph("HOLINESS REVIVAL MOVEMENT WORLDWIDE HOREMOW", title_style))
        elements.append(Paragraph("DAILY DEVOTIONAL BY PASTOR PAUL RIKA INTERNATIONAL DIRECTOR.", author_style))

        # DATE
        date_str = f"DATE: {day_of_week} {month_name} {day_num}, {year_num}."
        elements.append(Paragraph(date_str, meta_style))

        # TOPIC
        elements.append(Paragraph(f"TOPIC: {topic}", meta_style))

        # TEXT
        elements.append(Paragraph(f"TEXT: {passage_ref}", meta_style))
        for v in passage_verses:
            elements.append(Paragraph(v, passage_style))
        elements.append(Spacer(1, 4))

        # KEY VERSE
        kv_para = f'KEY VERSE: {kv_ref}  "{kv_text}"'
        elements.append(Paragraph(kv_para, meta_style))
        elements.append(Spacer(1, 6))

        # Reflection paragraphs
        p1 = (
            f"As believers called to holiness in an era of compromise, Day {day_count} reminds us to "
            f"walk circumspectly before the Lord. True holiness begins from an inward transformation "
            f"that produces outward purity in speech, dressing, conduct, and relationships. "
            f"Let no worldly standard diminish your consecrated devotion to Jesus Christ."
        )
        p2 = (
            f"When we yield to the Holy Spirit, grace is supplied to overcome the pollutions of this "
            f"present age. Examine your heart daily and ensure that every action brings glory to God. "
            f"Stay steadfast in prayer and regular meditation on His holy word."
        )
        elements.append(Paragraph(p1, body_style))
        elements.append(Paragraph(p2, body_style))
        elements.append(Spacer(1, 6))

        # Footers
        elements.append(Paragraph(f"Thought for the day: {thought}", footer_item_style))
        elements.append(Paragraph(f"Song for the day: {song}", footer_item_style))
        elements.append(Paragraph(f"Bible reading for the day: {reading}", footer_item_style))

        # End of day page break
        if current_date < END_DATE:
            elements.append(PageBreak())

        current_date += datetime.timedelta(days=1)

    doc.build(elements)
    print(f"Generated {day_count} daily devotionals in: {output_path}")

if __name__ == "__main__":
    out_dir = r"c:\Users\USER\Desktop\HRMW_M"
    target_pdf = os.path.join(out_dir, "HOREMOW_Daily_Devotionals_H1_2027.pdf")
    generate_devotional_pdf(target_pdf)
