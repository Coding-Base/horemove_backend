from apps.blog.models import PostCategory
from apps.donations.models import DonationProject
from apps.ministry.models import Doctrine, HomepageSection, Leader, MinistryProfile
from apps.publications.models import PublicationCategory
from apps.sermons.models import SermonCategory, Speaker
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Seeds initial ministry data, doctrinal statements, leaders, and donation projects for HOREMOW."

    def handle(self, *args, **options):
        self.stdout.write("Seeding HOREMOW ministry data...")

        with transaction.atomic():
            # 1. Ministry Profile
            profile, created = MinistryProfile.objects.update_or_create(
                id="00000000-0000-0000-0000-000000000001",
                defaults={
                    "name": "Holiness Revival Movement Worldwide",
                    "acronym": "HOREMOW",
                    "motto": "Holiness without which no man shall see the Lord (Hebrews 12:14)",
                    "vision_statement": (
                        "To prepare the bride of Christ in holiness and righteousness across all "
                        "nations for the glorious second coming of our Lord Jesus Christ."
                    ),
                    "mission_statement": (
                        "Preaching and teaching the uncompromised Word of God, restoring true holiness, "
                        "restitution, and biblical truth to churches, families, and souls worldwide."
                    ),
                    "history": (
                        "Holiness Revival Movement Worldwide (HOREMOW) was birthed out of a divine mandate "
                        "given to Pastor Paul Rika to awaken the body of Christ to true biblical holiness and "
                        "preparation for eternity."
                    ),
                    "headquarters_address": "HOREMOW International Camp Ground, Abuja, Nigeria",
                    "primary_phone": "+234 803 000 0000",
                    "primary_email": "info@horemow.org",
                    "social_links": {
                        "youtube": "https://youtube.com/@horemow",
                        "telegram": "https://t.me/horemow",
                        "facebook": "https://facebook.com/horemow",
                    },
                },
            )
            self.stdout.write(self.style.SUCCESS("[OK] Ministry Profile established"))

            # 2. Leaders
            leaders_data = [
                {
                    "name": "Pastor Paul Rika",
                    "title": "International Director & Founder",
                    "biography": (
                        "Pastor Paul Rika is the International Director and Founder of Holiness Revival Movement Worldwide. "
                        "Anointed with an apostolic mantle for global holiness revival, he travels worldwide preaching repentance, "
                        "restitution, and preparation for the Rapture of the saints."
                    ),
                    "order": 1,
                    "portrait_url": "https://res.cloudinary.com/placeholder/image/upload/pastor-paul-rika.jpg",
                },
                {
                    "name": "Evangelist Linda Paul Rika",
                    "title": "Global Coordinator & Evangelist",
                    "biography": (
                        "Evangelist Linda Paul Rika faithfully partners in the global outreach of HOREMOW, ministering "
                        "to women, youth, and families worldwide, pointing believers toward practical righteous living."
                    ),
                    "order": 2,
                    "portrait_url": "https://res.cloudinary.com/placeholder/image/upload/evangelist-linda-rika.jpg",
                },
            ]
            for item in leaders_data:
                Leader.objects.update_or_create(name=item["name"], defaults=item)
            self.stdout.write(self.style.SUCCESS("[OK] Ministry Leaders seeded"))

            # 3. Doctrines
            doctrines_data = [
                {
                    "title": "Repentance and New Birth",
                    "biblical_reference": "John 3:3-5, Acts 3:19, 2 Corinthians 5:17",
                    "summary": "Genuine conviction of sin leading to godly sorrow, confession, forsaking of sin, and receiving Jesus Christ as personal Lord and Saviour.",
                    "order": 1,
                },
                {
                    "title": "Restitution",
                    "biblical_reference": "Luke 19:8, Matthew 5:23-24, Acts 24:16",
                    "summary": "Righting the wrongs of the past where humanly possible, restoring stolen property, and clearing a guilty conscience before God and man.",
                    "order": 2,
                },
                {
                    "title": "Entire Sanctification & Inward Holiness",
                    "biblical_reference": "1 Thessalonians 4:3, 7; Hebrews 12:14; 1 Peter 1:15-16",
                    "summary": "The instantaneous work of grace in the believer subsequent to salvation, cleansing the heart from inbred sin and imparting divine purity of love and thought.",
                    "order": 3,
                },
                {
                    "title": "Water Baptism & The Lord's Supper",
                    "biblical_reference": "Matthew 28:19, Romans 6:3-4, 1 Corinthians 11:23-26",
                    "summary": "Water baptism by single immersion in the name of the Father, Son, and Holy Ghost as an outward declaration of inward faith.",
                    "order": 4,
                },
                {
                    "title": "The Second Coming of Christ & The Rapture",
                    "biblical_reference": "1 Thessalonians 4:16-17, 1 Corinthians 15:51-52, Titus 2:13",
                    "summary": "The imminent, personal return of our Lord Jesus Christ to catch away His holy bride before the Great Tribulation.",
                    "order": 5,
                },
            ]
            for doc in doctrines_data:
                Doctrine.objects.update_or_create(title=doc["title"], defaults=doc)
            self.stdout.write(self.style.SUCCESS("[OK] Doctrinal statements seeded"))

            # 4. Donation Projects
            projects_data = [
                {
                    "name": "General Ministry Offering",
                    "slug": "general-offering",
                    "description": "Support the ongoing day-to-day work, operations, and crusades of Holiness Revival Movement Worldwide.",
                    "currency": "NGN",
                    "order": 1,
                },
                {
                    "name": "Global Literature & Bible Translation",
                    "slug": "bible-literature-translation",
                    "description": "Financing the translation and free distribution of holiness books, Bibles, and tracts into indigenous languages across the continents.",
                    "currency": "NGN",
                    "order": 2,
                },
                {
                    "name": "Radio & TV Global Broadcast Outreach",
                    "slug": "broadcast-evangelism",
                    "description": "Funding satellite broadcast, online livestreaming, and radio frequencies to bring message of holiness to unreached regions.",
                    "currency": "NGN",
                    "order": 3,
                },
            ]
            for proj in projects_data:
                DonationProject.objects.update_or_create(slug=proj["slug"], defaults=proj)
            self.stdout.write(self.style.SUCCESS("[OK] Donation projects seeded"))

            # 5. Core Categories
            SermonCategory.objects.get_or_create(name="Holiness & Righteousness", slug="holiness-righteousness")
            SermonCategory.objects.get_or_create(name="Eternity & Rapture", slug="eternity-rapture")
            SermonCategory.objects.get_or_create(name="Christian Home & Marriage", slug="christian-home")
            SermonCategory.objects.get_or_create(name="Faith & Deliverance", slug="faith-deliverance")

            Speaker.objects.get_or_create(name="Pastor Paul Rika", title="International Director")

            PublicationCategory.objects.get_or_create(name="Books by Pastor Paul Rika", slug="pastor-paul-rika-books")
            PublicationCategory.objects.get_or_create(name="Christian Living & Discipleship", slug="christian-living")

            PostCategory.objects.get_or_create(name="Revival News", slug="revival-news")
            PostCategory.objects.get_or_create(name="Testimonies", slug="testimonies")
            PostCategory.objects.get_or_create(name="Bible Studies", slug="bible-studies")

            # 6. Homepage Sections
            HomepageSection.objects.update_or_create(
                section_key="hero",
                defaults={
                    "title": "Welcome to Holiness Revival Movement Worldwide",
                    "subtitle": "Spreading the message of righteousness and true holiness across the nations",
                    "is_active": True,
                    "order": 1,
                    "content_payload": {
                        "cta_text": "Explore Sermons",
                        "cta_link": "/sermons",
                        "secondary_cta_text": "Our Beliefs",
                        "secondary_cta_link": "/doctrine",
                    },
                },
            )

        self.stdout.write(self.style.SUCCESS("All HOREMOW seed data successfully initialized!"))
