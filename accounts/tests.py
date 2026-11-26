"""Focused account model and authentication tests."""
from io import BytesIO
from tempfile import TemporaryDirectory

from PIL import Image

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import RegisterForm, ProfileForm, UserNameForm
from .models import Profile, ProfileLink, ProfileDocument
from pathlib import Path
from zipfile import ZipFile

from .forms import ProfileDocumentForm

class AccountTests(TestCase):
    """Verify profile signals and registration validation."""

    def test_registration_logs_user_in_with_configured_backend(self):
        """A successful signup creates a session despite multiple backends."""
        response = self.client.post(
            "/accounts/register/",
            {
                "username": "newstudent",
                "first_name": "New",
                "last_name": "Student",
                "email": "newstudent@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )
        self.assertRedirects(response, "/accounts/profile/edit/?welcome=1")
        self.assertTrue(self.client.session.get("_auth_user_id"))
        self.assertTrue(Profile.objects.filter(user__username="newstudent").exists())

    def test_profile_created_for_user(self):
        """New users receive exactly one profile."""
        user = get_user_model().objects.create_user("student", password="StrongPassword123!")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_username_is_rejected_case_insensitively(self):
        """Registration rejects a username case variant."""
        get_user_model().objects.create_user("Student", password="StrongPassword123!")
        form = RegisterForm({"username": "student", "first_name": "A", "last_name": "B", "email": "new@example.com", "password1": "StrongPassword123!", "password2": "StrongPassword123!"})
        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

class AuthenticationTests(TestCase):
    """Verify authentication and account access restrictions."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="student",
            first_name="Test",
            last_name="Student",
            email="student@example.com",
            password="StrongPassword123!",
        )

    def test_login_with_username(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "student",
                "password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )

    def test_login_with_email(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "student@example.com",
                "password": "StrongPassword123!",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )

    def test_invalid_password_is_rejected(self):
        response = self.client.post(
            reverse("accounts:login"),
            {
                "username": "student",
                "password": "WrongPassword",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_duplicate_email_is_rejected(self):
        form = RegisterForm(
            {
                "username": "anotherstudent",
                "first_name": "Another",
                "last_name": "Student",
                "email": "STUDENT@example.com",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_required_registration_fields(self):
        form = RegisterForm({})

        self.assertFalse(form.is_valid())

        for field in (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ):
            with self.subTest(field=field):
                self.assertIn(field, form.errors)

    def test_guest_cannot_edit_profile(self):
        response = self.client.get(
            reverse("accounts:profile_edit")
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(
            reverse("accounts:login"),
            response.url,
        )

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("accounts:logout")
        )

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)

    def test_logout_clears_session(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("accounts:logout")
        )

        self.assertEqual(response.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)


class ProfileManagementTests(TestCase):
    """Verify profile updates and field validation."""

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="profile_student",
            first_name="Test",
            last_name="Student",
            email="profile@example.com",
            password="StrongPassword123!",
        )

    def setUp(self):
        self.client.force_login(self.user)

        self.profile = Profile.objects.get(user=self.user)

        self.profile_data = {
            "first_name": "Updated",
            "last_name": "Student",
            "email": "profile@example.com",
            "phone_number": "+1 519 555 0123",
            "headline": "Software Developer",
            "bio": "Interested in software development.",
            "university": "University of Windsor",
            "program": "Master of Applied Computing",
            "year_of_study": 5,
            "availability_hours": 10,
            "open_to_teams": True,
        }

    def test_profile_edit_page_loads(self):
        response = self.client.get(
            reverse("accounts:profile_edit")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "accounts/profile_form.html",
        )

    def test_profile_information_can_be_updated(self):
        response = self.client.post(
            reverse("accounts:profile_edit"),
            self.profile_data,
        )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()
        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(
            self.profile.headline,
            "Software Developer",
        )
        self.assertEqual(
            self.profile.phone_number,
            "+1 519 555 0123",
        )
        self.assertEqual(self.profile.availability_hours, 10)

    def test_phone_number_is_optional(self):
        data = self.profile_data.copy()
        data["phone_number"] = ""

        form = ProfileForm(data, instance=self.profile)

        self.assertTrue(form.is_valid(), form.errors)

    def test_valid_phone_number_is_accepted(self):
        form = ProfileForm(
            self.profile_data,
            instance=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_phone_numbers_are_rejected(self):
        invalid_numbers = (
            "123abc",
            "123",
            "1234567890123456",
            "phone-number",
        )

        for phone in invalid_numbers:
            with self.subTest(phone=phone):
                data = self.profile_data.copy()
                data["phone_number"] = phone

                form = ProfileForm(
                    data,
                    instance=self.profile,
                )

                self.assertFalse(form.is_valid())
                self.assertIn("phone_number", form.errors)

    def test_required_personal_fields(self):
        for field in ("first_name", "last_name", "email"):
            with self.subTest(field=field):
                data = self.profile_data.copy()
                data[field] = ""

                form = UserNameForm(
                    data,
                    instance=self.user,
                )

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_invalid_email_is_rejected(self):
        data = self.profile_data.copy()
        data["email"] = "invalid-email"

        form = UserNameForm(data, instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_required_academic_fields(self):
        for field in (
            "university",
            "program",
            "year_of_study",
            "availability_hours",
        ):
            with self.subTest(field=field):
                data = self.profile_data.copy()
                data[field] = ""

                form = ProfileForm(
                    data,
                    instance=self.profile,
                )

                self.assertFalse(form.is_valid())
                self.assertIn(field, form.errors)

    def test_negative_availability_is_rejected(self):
        data = self.profile_data.copy()
        data["availability_hours"] = -5

        form = ProfileForm(data, instance=self.profile)

        self.assertFalse(form.is_valid())
        self.assertIn("availability_hours", form.errors)

    def test_excessive_availability_is_rejected(self):
        data = self.profile_data.copy()
        data["availability_hours"] = 169

        form = ProfileForm(data, instance=self.profile)

        self.assertFalse(form.is_valid())
        self.assertIn("availability_hours", form.errors)

    def test_phone_number_is_not_exposed_publicly(self):
        self.profile.phone_number = "+1 519 555 0123"
        self.profile.save()

        self.client.logout()

        response = self.client.get(
            self.profile.get_absolute_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            self.profile.phone_number,
        )

    def test_duplicate_email_on_profile_update_is_rejected(self):
        get_user_model().objects.create_user(
            username="existing_student",
            email="existing@example.com",
            password="StrongPassword123!",
        )

        data = self.profile_data.copy()
        data["email"] = "EXISTING@example.com"

        form = UserNameForm(data, instance=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_user_can_keep_existing_email(self):
        form = UserNameForm(
            self.profile_data,
            instance=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)

class ProfilePhotoTests(TestCase):
    """Verify profile picture uploads and image validation."""

    def setUp(self):
        # Keep uploaded test files separate from actual user files.
        media_directory = TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)

        settings_override = override_settings(
            MEDIA_ROOT=media_directory.name
        )

        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.user = get_user_model().objects.create_user(
            username="photo_student",
            first_name="Photo",
            last_name="Student",
            email="photo@example.com",
            password="StrongPassword123!",
        )

        self.client.force_login(self.user)

        self.profile = Profile.objects.get(user=self.user)

        self.profile_data = {
            "first_name": "Photo",
            "last_name": "Student",
            "email": "photo@example.com",
            "university": "University of Windsor",
            "program": "Master of Applied Computing",
            "year_of_study": 5,
            "availability_hours": 10,
        }

    def create_image(self, size=(200, 200)):
        """Generate a valid PNG image for upload tests."""
        buffer = BytesIO()

        image = Image.new("RGB", size, color="blue")
        image.save(buffer, format="PNG")

        return SimpleUploadedFile(
            "profile.png",
            buffer.getvalue(),
            content_type="image/png",
        )

    def test_valid_profile_picture_is_accepted(self):
        form = ProfileForm(
            self.profile_data,
            {"photo": self.create_image()},
            instance=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_profile_picture_is_rejected(self):
        invalid_file = SimpleUploadedFile(
            "invalid.png",
            b"This is not an image.",
            content_type="image/png",
        )

        form = ProfileForm(
            self.profile_data,
            {"photo": invalid_file},
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)

    def test_oversized_image_dimensions_are_rejected(self):
        form = ProfileForm(
            self.profile_data,
            {"photo": self.create_image((4097, 100))},
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("photo", form.errors)

    def test_profile_picture_can_be_uploaded(self):
        data = self.profile_data.copy()
        data["photo"] = self.create_image()

        response = self.client.post(
            reverse("accounts:profile_edit"),
            data,
        )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()

        self.assertTrue(self.profile.photo)
        self.assertTrue(
            self.profile.photo.storage.exists(
                self.profile.photo.name
            )
        )

    def test_profile_picture_can_be_removed(self):
        self.profile.photo.save(
            "profile.png",
            self.create_image(),
            save=True,
        )

        data = self.profile_data.copy()
        data["photo-clear"] = "on"

        response = self.client.post(
            reverse("accounts:profile_edit"),
            data,
        )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()

        self.assertFalse(self.profile.photo)

class ResumeManagementTests(TestCase):
    """Verify resume uploads, downloads and privacy restrictions."""

    def setUp(self):
        private_directory = TemporaryDirectory()
        self.addCleanup(private_directory.cleanup)

        settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=Path(private_directory.name)
        )

        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.user = get_user_model().objects.create_user(
            username="resume_student",
            first_name="Resume",
            last_name="Student",
            email="resume@example.com",
            password="StrongPassword123!",
        )

        self.other_user = get_user_model().objects.create_user(
            username="another_student",
            password="StrongPassword123!",
        )

        self.profile = Profile.objects.get(user=self.user)

        self.client.force_login(self.user)

        self.profile_data = {
            "first_name": "Resume",
            "last_name": "Student",
            "email": "resume@example.com",
            "university": "University of Windsor",
            "program": "Master of Applied Computing",
            "year_of_study": 5,
            "availability_hours": 10,
        }

    def create_pdf(self):
        """Generate a file with the expected PDF signature."""
        return SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4\nTest resume content\n%%EOF",
            content_type="application/pdf",
        )

    def create_docx(self):
        """Generate a minimal DOCX archive for validation tests."""
        buffer = BytesIO()

        with ZipFile(buffer, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document/>")

        return SimpleUploadedFile(
            "resume.docx",
            buffer.getvalue(),
            content_type=(
                "application/vnd.openxmlformats-officedocument"
                ".wordprocessingml.document"
            ),
        )

    def save_resume(self, is_public=False):
        """Attach a resume to the test profile."""
        self.profile.resume.save(
            "resume.pdf",
            self.create_pdf(),
            save=False,
        )

        self.profile.resume_is_public = is_public
        self.profile.save()

    def test_pdf_resume_is_accepted(self):
        form = ProfileForm(
            self.profile_data,
            {"resume": self.create_pdf()},
            instance=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_docx_resume_is_accepted(self):
        form = ProfileForm(
            self.profile_data,
            {"resume": self.create_docx()},
            instance=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_resume_extension_is_rejected(self):
        upload = SimpleUploadedFile(
            "resume.exe",
            b"Invalid file",
        )

        form = ProfileForm(
            self.profile_data,
            {"resume": upload},
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("resume", form.errors)

    def test_fake_pdf_is_rejected(self):
        upload = SimpleUploadedFile(
            "resume.pdf",
            b"This is not a PDF.",
            content_type="application/pdf",
        )

        form = ProfileForm(
            self.profile_data,
            {"resume": upload},
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("resume", form.errors)

    def test_oversized_resume_is_rejected(self):
        upload = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-" + b"x" * (5 * 1024 * 1024),
            content_type="application/pdf",
        )

        form = ProfileForm(
            self.profile_data,
            {"resume": upload},
            instance=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("resume", form.errors)

    def test_resume_can_be_uploaded(self):
        data = self.profile_data.copy()
        data["resume"] = self.create_pdf()

        response = self.client.post(
            reverse("accounts:profile_edit"),
            data,
        )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()

        self.assertTrue(self.profile.resume)
        self.assertFalse(self.profile.resume_is_public)

        self.assertTrue(
            self.profile.resume.storage.exists(
                self.profile.resume.name
            )
        )

    def test_owner_can_download_private_resume(self):
        self.save_resume()

        response = self.client.get(
            reverse(
                "accounts:resume_download",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)

        self.assertIn(
            "attachment",
            response["Content-Disposition"],
        )

        response.close()

    def test_other_user_cannot_download_private_resume(self):
        self.save_resume()

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "accounts:resume_download",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_download_private_resume(self):
        self.save_resume()

        self.client.logout()

        response = self.client.get(
            reverse(
                "accounts:resume_download",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_public_resume_can_be_downloaded(self):
        self.save_resume(is_public=True)

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "accounts:resume_download",
                args=[self.user.username],
            )
        )

        self.assertEqual(response.status_code, 200)
        response.close()

    def test_resume_can_be_replaced(self):
        self.save_resume()

        old_name = self.profile.resume.name
        storage = self.profile.resume.storage

        data = self.profile_data.copy()
        data["resume"] = self.create_docx()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("accounts:profile_edit"),
                data,
            )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()

        self.assertNotEqual(
            self.profile.resume.name,
            old_name,
        )

        self.assertFalse(storage.exists(old_name))

        self.assertTrue(
            storage.exists(self.profile.resume.name)
        )

    def test_resume_can_be_deleted(self):
        self.save_resume(is_public=True)

        old_name = self.profile.resume.name
        storage = self.profile.resume.storage

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse("accounts:resume_delete")
            )

        self.assertEqual(response.status_code, 302)

        self.profile.refresh_from_db()

        self.assertFalse(self.profile.resume)
        self.assertFalse(self.profile.resume_is_public)
        self.assertFalse(storage.exists(old_name))

    def test_resume_deletion_requires_post(self):
        self.save_resume()

        response = self.client.get(
            reverse("accounts:resume_delete")
        )

        self.assertEqual(response.status_code, 405)

        self.profile.refresh_from_db()
        self.assertTrue(self.profile.resume)

class ProfileDocumentTests(TestCase):
    """Verify supporting document management and access permissions."""

    def setUp(self):
        private_directory = TemporaryDirectory()
        self.addCleanup(private_directory.cleanup)

        settings_override = override_settings(
            PRIVATE_MEDIA_ROOT=Path(private_directory.name)
        )

        settings_override.enable()
        self.addCleanup(settings_override.disable)

        self.user = get_user_model().objects.create_user(
            username="document_owner",
            first_name="Document",
            last_name="Owner",
            email="owner@example.com",
            password="StrongPassword123!",
        )

        self.other_user = get_user_model().objects.create_user(
            username="other_student",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.profile = Profile.objects.get(user=self.user)

        self.client.force_login(self.user)

    def create_pdf(self):
        """Generate a PDF upload for document validation tests."""
        return SimpleUploadedFile(
            "certificate.pdf",
            b"%PDF-1.4\nTest certificate content\n%%EOF",
            content_type="application/pdf",
        )

    def create_document(self, is_public=False):
        """Create a supporting document owned by the test user."""
        return ProfileDocument.objects.create(
            profile=self.profile,
            title="Test Certificate",
            file=self.create_pdf(),
            original_filename="certificate.pdf",
            is_public=is_public,
        )

    def test_valid_document_is_accepted(self):
        form = ProfileDocumentForm(
            {"title": "Certificate"},
            {"file": self.create_pdf()},
            profile=self.profile,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_document_requires_title(self):
        form = ProfileDocumentForm(
            {"title": ""},
            {"file": self.create_pdf()},
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_document_requires_file(self):
        form = ProfileDocumentForm(
            {"title": "Certificate"},
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_invalid_document_extension_is_rejected(self):
        upload = SimpleUploadedFile(
            "document.exe",
            b"Invalid file",
        )

        form = ProfileDocumentForm(
            {"title": "Invalid Document"},
            {"file": upload},
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_fake_pdf_is_rejected(self):
        upload = SimpleUploadedFile(
            "certificate.pdf",
            b"This is not a PDF.",
            content_type="application/pdf",
        )

        form = ProfileDocumentForm(
            {"title": "Invalid Certificate"},
            {"file": upload},
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_oversized_document_is_rejected(self):
        upload = SimpleUploadedFile(
            "certificate.pdf",
            b"%PDF-" + b"x" * (5 * 1024 * 1024),
            content_type="application/pdf",
        )

        form = ProfileDocumentForm(
            {"title": "Large Document"},
            {"file": upload},
            profile=self.profile,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_document_can_be_uploaded(self):
        response = self.client.post(
            reverse("accounts:document_add"),
            {
                "title": "Certificate",
                "file": self.create_pdf(),
            },
        )

        self.assertEqual(response.status_code, 302)

        document = ProfileDocument.objects.get(
            profile=self.profile,
            title="Certificate",
        )

        self.assertFalse(document.is_public)
        self.assertEqual(
            document.original_filename,
            "certificate.pdf",
        )

        self.assertTrue(
            document.file.storage.exists(document.file.name)
        )

    def test_owner_can_download_private_document(self):
        document = self.create_document()

        response = self.client.get(
            reverse(
                "accounts:document_download",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)

        self.assertIn(
            "attachment",
            response["Content-Disposition"],
        )

        response.close()

    def test_other_user_cannot_download_private_document(self):
        document = self.create_document()

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "accounts:document_download",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_guest_cannot_download_private_document(self):
        document = self.create_document()

        self.client.logout()

        response = self.client.get(
            reverse(
                "accounts:document_download",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_public_document_can_be_downloaded(self):
        document = self.create_document(is_public=True)

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "accounts:document_download",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        response.close()

    def test_guest_can_download_public_document(self):
        document = self.create_document(is_public=True)

        self.client.logout()

        response = self.client.get(
            reverse(
                "accounts:document_download",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 200)
        response.close()

    def test_private_document_is_hidden_from_other_users(self):
        document = self.create_document()

        self.client.force_login(self.other_user)

        response = self.client.get(
            self.profile.get_absolute_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, document.title)

    def test_public_document_is_visible_to_other_users(self):
        document = self.create_document(is_public=True)

        self.client.force_login(self.other_user)

        response = self.client.get(
            self.profile.get_absolute_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, document.title)

    def test_owner_can_delete_document(self):
        document = self.create_document()

        document_id = document.pk
        file_name = document.file.name
        storage = document.file.storage

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                reverse(
                    "accounts:document_delete",
                    args=[document_id],
                )
            )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            ProfileDocument.objects.filter(
                pk=document_id
            ).exists()
        )

        self.assertFalse(storage.exists(file_name))

    def test_other_user_cannot_delete_document(self):
        document = self.create_document()

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "accounts:document_delete",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            ProfileDocument.objects.filter(
                pk=document.pk
            ).exists()
        )

    def test_other_user_cannot_change_document_visibility(self):
        document = self.create_document()

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "accounts:document_visibility",
                args=[document.pk],
            ),
            {"is_public": "true"},
        )

        self.assertEqual(response.status_code, 404)

        document.refresh_from_db()
        self.assertFalse(document.is_public)

    def test_document_deletion_requires_post(self):
        document = self.create_document()

        response = self.client.get(
            reverse(
                "accounts:document_delete",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertTrue(
            ProfileDocument.objects.filter(
                pk=document.pk
            ).exists()
        )

    def test_document_visibility_change_requires_post(self):
        document = self.create_document()

        response = self.client.get(
            reverse(
                "accounts:document_visibility",
                args=[document.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

        document.refresh_from_db()
        self.assertFalse(document.is_public)

class ProfileLinkTests(TestCase):
    """Verify profile link management and ownership permissions."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="link_owner",
            password="StrongPassword123!",
        )

        self.other_user = get_user_model().objects.create_user(
            username="other_user",
            password="StrongPassword123!",
        )

        self.profile = Profile.objects.get(user=self.user)
        self.client.force_login(self.user)

    def create_link(self):
        """Create an external link belonging to the test profile."""
        return ProfileLink.objects.create(
            profile=self.profile,
            label="github",
            url="https://github.com/student",
        )

    def test_profile_link_can_be_added(self):
        response = self.client.post(
            reverse("accounts:profile_link_add"),
            {
                "label": "github",
                "url": "https://github.com/student",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            ProfileLink.objects.filter(
                profile=self.profile,
                label="github",
                url="https://github.com/student",
            ).exists()
        )

    def test_invalid_link_is_rejected(self):
        response = self.client.post(
            reverse("accounts:profile_link_add"),
            {
                "label": "github",
                "url": "invalid-url",
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertFalse(
            ProfileLink.objects.filter(
                profile=self.profile
            ).exists()
        )

    def test_owner_can_delete_profile_link(self):
        link = self.create_link()

        response = self.client.post(
            reverse(
                "accounts:profile_link_delete",
                args=[link.pk],
            )
        )

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            ProfileLink.objects.filter(pk=link.pk).exists()
        )

    def test_other_user_cannot_delete_profile_link(self):
        link = self.create_link()
        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "accounts:profile_link_delete",
                args=[link.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            ProfileLink.objects.filter(pk=link.pk).exists()
        )

    def test_link_deletion_requires_post(self):
        link = self.create_link()

        response = self.client.get(
            reverse(
                "accounts:profile_link_delete",
                args=[link.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

        self.assertTrue(
            ProfileLink.objects.filter(pk=link.pk).exists()
        )

    def test_guest_cannot_add_profile_link(self):
        self.client.logout()

        response = self.client.post(
            reverse("accounts:profile_link_add"),
            {
                "label": "github",
                "url": "https://github.com/student",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response.url)

        self.assertFalse(
            ProfileLink.objects.filter(
                profile=self.profile
            ).exists()
        )

    def test_profile_link_is_publicly_visible(self):
        link = self.create_link()
        self.client.logout()

        response = self.client.get(
            self.profile.get_absolute_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, link.url)