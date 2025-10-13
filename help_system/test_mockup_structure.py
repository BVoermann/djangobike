"""
Tests to verify that the mock simulation structure matches the actual simulation templates.

This ensures that interactive guides show users accurate representations of the actual interface.
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from bikeshop.models import GameSession
from bs4 import BeautifulSoup
import re

User = get_user_model()


class MockupStructureTest(TestCase):
    """Test that mock simulation templates match actual simulation templates."""

    def setUp(self):
        """Set up test user and session."""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

        # Create a test game session
        self.session = GameSession.objects.create(
            user=self.user,
            name='Test Session',
            current_month=1,
            current_year=2024,
            balance=50000.00
        )

    def get_structural_elements(self, html_content):
        """
        Extract key structural elements from HTML for comparison.
        Returns a dict of structural features.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        structure = {
            'headers': [],
            'card_titles': [],
            'stats_cards': 0,
            'table_headers': [],
            'buttons': [],
            'icons': [],
        }

        # Extract headers (h1-h6)
        for i in range(1, 7):
            headers = soup.find_all(f'h{i}')
            for header in headers:
                text = header.get_text(strip=True)
                if text:
                    structure['headers'].append(text)

        # Extract card titles
        card_headers = soup.find_all(class_=re.compile(r'card-header|card-title'))
        for card in card_headers:
            text = card.get_text(strip=True)
            if text:
                structure['card_titles'].append(text)

        # Count statistics cards (cards with gradient backgrounds in stats row)
        # Look for the row with g-4 class that contains stats cards
        stats_row = soup.find('div', class_=re.compile(r'row.*g-4'))
        if stats_row:
            gradient_cards = stats_row.find_all('div', style=re.compile(r'gradient'))
            structure['stats_cards'] = len([c for c in gradient_cards if 'card' in c.get('class', [])])
        else:
            structure['stats_cards'] = 0

        # Extract table headers
        table_headers = soup.find_all('th')
        for th in table_headers:
            text = th.get_text(strip=True)
            if text and text not in ['', ' ']:
                structure['table_headers'].append(text)

        # Extract button texts
        buttons = soup.find_all('button')
        for btn in buttons:
            text = btn.get_text(strip=True)
            if text:
                structure['buttons'].append(text)

        # Extract common icons
        icons = soup.find_all('i', class_=re.compile(r'fa-'))
        for icon in icons:
            classes = icon.get('class', [])
            icon_class = ' '.join([c for c in classes if c.startswith('fa-')])
            if icon_class:
                structure['icons'].append(icon_class)

        return structure

    def test_procurement_mockup_has_correct_structure(self):
        """Test that procurement mockup has the same structural elements as actual procurement page."""
        # Get the mock simulation page
        mock_response = self.client.get('/help/mock-simulation/')
        self.assertEqual(mock_response.status_code, 200)

        mock_html = mock_response.content.decode('utf-8')

        # Extract the procurement mock content from JavaScript
        # Look for the procurement section in mockContent
        procurement_match = re.search(
            r'procurement:\s*`(.*?)`\s*,\s*production:',
            mock_html,
            re.DOTALL
        )

        self.assertIsNotNone(procurement_match, "Could not find procurement mockup content")
        mock_procurement_html = procurement_match.group(1)

        # Get mock structure
        mock_structure = self.get_structural_elements(mock_procurement_html)

        # Verify key structural elements are present in mockup

        # 1. Main header should be "Einkauf"
        self.assertIn('Einkauf', mock_structure['headers'],
                     "Mockup should have 'Einkauf' header")

        # 2. Should have 4 statistics cards
        self.assertEqual(mock_structure['stats_cards'], 4,
                        "Mockup should have 4 statistics cards (Budget, Suppliers, Components, Total)")

        # 3. Should have key section headers
        expected_sections = ['Lieferant auswählen', 'Bestellübersicht']
        for section in expected_sections:
            self.assertTrue(
                any(section in header for header in mock_structure['headers']),
                f"Mockup should have '{section}' section"
            )

        # 4. Table should have correct headers
        expected_table_headers = ['Komponente', 'Preis', 'Menge', 'Gesamt']
        for header in expected_table_headers:
            self.assertIn(header, mock_structure['table_headers'],
                         f"Mockup table should have '{header}' column")

        # 5. Should have "Bestellung aufgeben" button
        self.assertTrue(
            any('Bestellung aufgeben' in btn for btn in mock_structure['buttons']),
            "Mockup should have 'Bestellung aufgeben' button"
        )

        # 6. Should have key icons
        expected_icons = [
            'fa-shopping-cart',  # Main header
            'fa-wallet',         # Budget card
            'fa-truck',          # Suppliers card
            'fa-boxes',          # Components card
            'fa-calculator',     # Total card
            'fa-industry',       # Supplier info
        ]

        for icon in expected_icons:
            self.assertIn(icon, mock_structure['icons'],
                         f"Mockup should include {icon} icon")

    def test_procurement_mockup_has_supplier_badges(self):
        """Test that mockup shows supplier quality badges like actual page."""
        mock_response = self.client.get('/help/mock-simulation/')
        mock_html = mock_response.content.decode('utf-8')

        # Extract procurement mockup
        procurement_match = re.search(
            r'procurement:\s*`(.*?)`\s*,\s*production:',
            mock_html,
            re.DOTALL
        )
        mock_procurement_html = procurement_match.group(1)

        # Check for supplier badges
        self.assertIn('Premium Qualität', mock_procurement_html,
                     "Mockup should show supplier quality badge")
        self.assertIn('Zahlungsziel', mock_procurement_html,
                     "Mockup should show payment terms badge")
        self.assertIn('Tage', mock_procurement_html,
                     "Mockup should show delivery time")

    def test_procurement_mockup_uses_same_css_classes(self):
        """Test that mockup uses the same CSS classes as actual procurement page."""
        mock_response = self.client.get('/help/mock-simulation/')
        mock_html = mock_response.content.decode('utf-8')

        # Extract procurement mockup
        procurement_match = re.search(
            r'procurement:\s*`(.*?)`\s*,\s*production:',
            mock_html,
            re.DOTALL
        )
        mock_procurement_html = procurement_match.group(1)

        # Check for key CSS classes used in actual procurement page
        expected_classes = [
            'display-4',           # Header styling
            'fw-bold',             # Font weight
            'card border-0',       # Card styling
            'table table-hover',   # Table styling
            'btn btn-primary',     # Button styling
            'supplier-badges',     # Supplier info
        ]

        for css_class in expected_classes:
            self.assertIn(css_class, mock_procurement_html,
                         f"Mockup should use '{css_class}' class for consistency")

    def test_procurement_mockup_layout_matches_actual(self):
        """Test that mockup has the same layout structure as actual page."""
        mock_response = self.client.get('/help/mock-simulation/')
        mock_html = mock_response.content.decode('utf-8')

        # Extract procurement mockup
        procurement_match = re.search(
            r'procurement:\s*`(.*?)`\s*,\s*production:',
            mock_html,
            re.DOTALL
        )
        mock_procurement_html = procurement_match.group(1)
        soup = BeautifulSoup(mock_procurement_html, 'html.parser')

        # Check layout structure
        # 1. Should have header section
        header_section = soup.find('div', class_='text-center')
        self.assertIsNotNone(header_section, "Should have centered header section")

        # 2. Should have dropdown section
        dropdown_section = soup.find('div', class_='dropdown-row')
        self.assertIsNotNone(dropdown_section, "Should have dropdown section")

        # 3. Should have 4-column statistics row
        stats_row = soup.find('div', class_='row g-4')
        if stats_row:
            stat_cols = stats_row.find_all('div', class_=re.compile(r'col-lg-3'))
            self.assertEqual(len(stat_cols), 4, "Should have 4 statistics columns")

        # 4. Should have supplier details card
        supplier_card = soup.find('div', class_='card-header')
        self.assertIsNotNone(supplier_card, "Should have supplier details card")

        # 5. Should have order summary section
        # Look for heading with "Bestellübersicht" text
        order_summary = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        order_summary_found = any('Bestellübersicht' in heading.get_text() for heading in order_summary)
        self.assertTrue(order_summary_found, "Should have order summary section")


class MockupContentTest(TestCase):
    """Test that mockup content is realistic and helpful for learning."""

    def test_procurement_mockup_has_realistic_data(self):
        """Test that mockup uses realistic example data."""
        client = Client()
        response = client.get('/help/mock-simulation/')
        html = response.content.decode('utf-8')

        # Extract procurement mockup
        procurement_match = re.search(
            r'procurement:\s*`(.*?)`\s*,\s*production:',
            html,
            re.DOTALL
        )
        mock_html = procurement_match.group(1)

        # Check for realistic component names (German)
        realistic_components = ['Rahmen', 'Laufradsatz', 'Schaltung']
        for component in realistic_components:
            self.assertIn(component, mock_html,
                         f"Mockup should include realistic component: {component}")

        # Check for realistic prices (in Euros)
        self.assertRegex(mock_html, r'\d+[.,]\d{2}€',
                        "Mockup should show prices in Euro format")

        # Check for realistic supplier name
        self.assertIn('GmbH', mock_html,
                     "Mockup should use realistic German company name")
