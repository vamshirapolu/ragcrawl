"""Tests for project metadata validation."""

import re
from pathlib import Path

import pytest

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # Fallback for older Pythons


@pytest.fixture
def pyproject_data():
    """Load pyproject.toml data."""
    pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        return tomllib.load(f)


@pytest.fixture
def license_file():
    """Load LICENSE file content."""
    license_path = Path(__file__).parent.parent.parent / "LICENSE"
    with open(license_path) as f:
        return f.read()


class TestProjectMetadata:
    """Test project metadata consistency."""

    def test_license_field_is_valid_spdx(self, pyproject_data):
        """Verify license field uses valid SPDX identifier."""
        license_value = pyproject_data["project"]["license"]
        assert license_value == "Apache-2.0", (
            f"License should be 'Apache-2.0' (SPDX ID), got '{license_value}'"
        )

    def test_license_classifier_matches_license_field(self, pyproject_data):
        """Verify license classifier matches the license field."""
        license_field = pyproject_data["project"]["license"]
        classifiers = pyproject_data["project"]["classifiers"]
        
        # Map SPDX IDs to PyPI classifiers
        spdx_to_classifier = {
            "Apache-2.0": "License :: OSI Approved :: Apache Software License",
            "MIT": "License :: OSI Approved :: MIT License",
        }
        
        expected_classifier = spdx_to_classifier.get(license_field)
        assert expected_classifier is not None, f"Unknown SPDX license: {license_field}"
        assert expected_classifier in classifiers, (
            f"Classifier '{expected_classifier}' not found in classifiers"
        )

    def test_license_file_exists_and_contains_apache(self, license_file):
        """Verify LICENSE file exists and contains Apache License text."""
        assert "Apache License" in license_file
        assert "Version 2.0" in license_file
        assert "http://www.apache.org/licenses/" in license_file

    def test_license_file_has_copyright_notice(self, license_file):
        """Verify LICENSE file has copyright notice."""
        # Should contain copyright year and author
        assert re.search(r"Copyright \d{4}", license_file), (
            "LICENSE should contain copyright year"
        )
        assert "Vamshi Rapolu" in license_file, (
            "LICENSE should contain author name"
        )

    def test_python_version_consistency(self, pyproject_data):
        """Verify Python version requirements are consistent."""
        requires_python = pyproject_data["project"]["requires-python"]
        classifiers = pyproject_data["project"]["classifiers"]
        
        # Extract minimum version from requires-python
        match = re.search(r">=(\d+\.\d+)", requires_python)
        assert match, f"Invalid requires-python format: {requires_python}"
        min_version = match.group(1)
        
        # Check that classifiers include the minimum version
        expected_classifier = f"Programming Language :: Python :: {min_version}"
        assert expected_classifier in classifiers, (
            f"Missing classifier for minimum Python version: {expected_classifier}"
        )

    def test_project_urls_are_valid(self, pyproject_data):
        """Verify project URLs are properly configured."""
        urls = pyproject_data["project"]["urls"]
        
        required_urls = ["Homepage", "Repository", "Documentation", "Issues"]
        for url_key in required_urls:
            assert url_key in urls, f"Missing required URL: {url_key}"
            assert urls[url_key].startswith("http"), (
                f"Invalid URL for {url_key}: {urls[url_key]}"
            )

    def test_readme_file_exists(self, pyproject_data):
        """Verify README file specified in pyproject.toml exists."""
        readme = pyproject_data["project"]["readme"]
        readme_path = Path(__file__).parent.parent.parent / readme
        assert readme_path.exists(), f"README file not found: {readme}"

    def test_required_metadata_fields_present(self, pyproject_data):
        """Verify all required metadata fields are present."""
        project = pyproject_data["project"]
        
        required_fields = [
            "name",
            "version",
            "description",
            "readme",
            "license",
            "requires-python",
            "authors",
            "keywords",
            "classifiers",
        ]
        
        for field in required_fields:
            assert field in project, f"Missing required field: {field}"
            assert project[field], f"Field '{field}' is empty"

    def test_authors_have_required_fields(self, pyproject_data):
        """Verify authors have name and email."""
        authors = pyproject_data["project"]["authors"]
        assert len(authors) > 0, "At least one author required"
        
        for author in authors:
            assert "name" in author, "Author missing 'name' field"
            assert "email" in author, "Author missing 'email' field"
            assert "@" in author["email"], f"Invalid email: {author['email']}"

    def test_keywords_are_relevant(self, pyproject_data):
        """Verify keywords are relevant to the project."""
        keywords = pyproject_data["project"]["keywords"]
        
        # Should have at least a few keywords
        assert len(keywords) >= 3, "Should have at least 3 keywords"
        
        # Check for expected keywords
        expected_keywords = ["crawler", "llm", "rag", "markdown"]
        for keyword in expected_keywords:
            assert keyword in keywords, f"Missing expected keyword: {keyword}"

    def test_development_status_classifier(self, pyproject_data):
        """Verify development status classifier is present."""
        classifiers = pyproject_data["project"]["classifiers"]
        
        # Should have a development status
        dev_status_classifiers = [c for c in classifiers if c.startswith("Development Status")]
        assert len(dev_status_classifiers) == 1, (
            "Should have exactly one Development Status classifier"
        )

    def test_typing_classifier_present(self, pyproject_data):
        """Verify typing classifier is present for type-annotated code."""
        classifiers = pyproject_data["project"]["classifiers"]
        assert "Typing :: Typed" in classifiers, (
            "Should include 'Typing :: Typed' classifier for type-annotated code"
        )


class TestCommunityFiles:
    """Test community and documentation files."""

    def test_contributing_file_exists(self):
        """Verify CONTRIBUTING.md exists."""
        contributing_path = Path(__file__).parent.parent.parent / "CONTRIBUTING.md"
        assert contributing_path.exists(), "CONTRIBUTING.md file not found"

    def test_code_of_conduct_exists(self):
        """Verify CODE_OF_CONDUCT.md exists."""
        coc_path = Path(__file__).parent.parent.parent / "CODE_OF_CONDUCT.md"
        assert coc_path.exists(), "CODE_OF_CONDUCT.md file not found"

    def test_support_file_exists(self):
        """Verify SUPPORT.md exists."""
        support_path = Path(__file__).parent.parent.parent / "SUPPORT.md"
        assert support_path.exists(), "SUPPORT.md file not found"

    def test_changelog_exists(self):
        """Verify CHANGELOG.md exists."""
        changelog_path = Path(__file__).parent.parent.parent / "CHANGELOG.md"
        assert changelog_path.exists(), "CHANGELOG.md file not found"

    def test_issue_template_exists(self):
        """Verify issue template exists."""
        template_path = Path(__file__).parent.parent.parent / ".github" / "ISSUE_TEMPLATE.md"
        assert template_path.exists(), "Issue template not found"

    def test_contributing_has_required_sections(self):
        """Verify CONTRIBUTING.md has required sections."""
        contributing_path = Path(__file__).parent.parent.parent / "CONTRIBUTING.md"
        with open(contributing_path) as f:
            content = f.read()
        
        required_sections = [
            "Code of Conduct",
            "How to Contribute",
            "Development Setup",
            "Running Tests",
        ]
        
        for section in required_sections:
            assert section in content, f"CONTRIBUTING.md missing section: {section}"

    def test_changelog_has_version_entries(self):
        """Verify CHANGELOG.md has version entries."""
        changelog_path = Path(__file__).parent.parent.parent / "CHANGELOG.md"
        with open(changelog_path) as f:
            content = f.read()
        
        # Should have version headers like ## [0.0.1]
        assert re.search(r"##\s+\[\d+\.\d+\.\d+\]", content), (
            "CHANGELOG.md should have version entries"
        )

    def test_code_of_conduct_references_contributor_covenant(self):
        """Verify CODE_OF_CONDUCT.md references Contributor Covenant."""
        coc_path = Path(__file__).parent.parent.parent / "CODE_OF_CONDUCT.md"
        with open(coc_path) as f:
            content = f.read()
        
        assert "Contributor Covenant" in content, (
            "CODE_OF_CONDUCT.md should reference Contributor Covenant"
        )
