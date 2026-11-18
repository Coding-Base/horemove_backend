from datetime import date

import pytest
from apps.blog.models import Comment, Post, PostCategory
from apps.sermons.models import Sermon, SermonCategory, Speaker
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_draft_sermon_is_hidden_from_public():
    category = SermonCategory.objects.create(name="Holiness", slug="holiness")
    speaker = Speaker.objects.create(name="Pastor Paul Rika")

    # Create draft sermon
    Sermon.objects.create(
        title="Draft Sermon on Repentance",
        slug="draft-sermon",
        category=category,
        speaker=speaker,
        date_preached=date.today(),
        status="DRAFT",
    )
    # Create published sermon
    Sermon.objects.create(
        title="Published Sermon on Holiness",
        slug="published-sermon",
        category=category,
        speaker=speaker,
        date_preached=date.today(),
        status="PUBLISHED",
        published_at=timezone.now(),
    )

    client = APIClient()
    # Anonymous public access
    response = client.get("/api/v1/sermons/")
    assert response.status_code == 200
    results = response.json()["results"]
    slugs = [item["slug"] for item in results]
    assert "published-sermon" in slugs
    assert "draft-sermon" not in slugs


@pytest.mark.django_db
def test_comment_submission_and_xss_sanitization():
    cat = PostCategory.objects.create(name="Teachings", slug="teachings")
    post = Post.objects.create(
        title="Understanding True Righteousness",
        slug="true-righteousness",
        category=cat,
        excerpt="An excerpt",
        body_markdown="Full body",
        status="PUBLISHED",
        published_at=timezone.now(),
    )

    client = APIClient()
    # Submit comment containing malicious script tags
    malicious_payload = {
        "author_name": "Test Visitor",
        "author_email": "visitor@example.com",
        "content": "Praise God! <script>alert('xss attack');</script><b>Amen!</b>",
    }
    response = client.post(
        f"/api/v1/posts/{post.slug}/comments/",
        malicious_payload,
        format="json",
    )
    assert response.status_code == 201

    comment = Comment.objects.get(author_email="visitor@example.com")
    assert comment.status == "PENDING"
    # Verify malicious script tag was stripped
    assert "<script>" not in comment.content
    assert "alert(" not in comment.content
    assert "<b>Amen!</b>" in comment.content

    # Verify unapproved comment is not returned in public post view
    public_post_res = client.get(f"/api/v1/posts/{post.slug}/")
    assert len(public_post_res.json()["comments"]) == 0

    # Once approved by moderator, it appears
    comment.status = "APPROVED"
    comment.save()
    public_post_res2 = client.get(f"/api/v1/posts/{post.slug}/")
    assert len(public_post_res2.json()["comments"]) == 1


@pytest.mark.django_db
def test_contact_honeypot_drops_spam():
    client = APIClient()
    spam_data = {
        "name": "Bot Spammer",
        "email": "bot@spam.com",
        "subject": "SEO Services",
        "message": "Buy cheap backlinks",
        "hp_website": "http://spam-link.ru",  # Honeypot filled
    }
    response = client.post("/api/v1/contact/submit/", spam_data, format="json")
    assert response.status_code == 200
    # Honeypot spam is not persisted in the database
    from apps.contact.models import ContactSubmission

    assert ContactSubmission.objects.filter(email="bot@spam.com").count() == 0
