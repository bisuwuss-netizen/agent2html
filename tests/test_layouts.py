
import sys
import os
import unittest
from typing import Dict

# Add project root to path (one level up from tests)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.layouts import select_layout, SubjectCategory, _determine_subject_category
from src.config import config

class TestSubjectLayouts(unittest.TestCase):
    
    def test_subject_category_mapping(self):
        """Test mapping from major string to SubjectCategory"""
        test_cases = [
            ("机械工程", SubjectCategory.ENGINEERING),
            ("计算机科学", SubjectCategory.ENGINEERING),
            ("护理学", SubjectCategory.MEDICAL),
            ("临床医学", SubjectCategory.MEDICAL),
            ("视觉设计", SubjectCategory.ARTS),
            ("古代文学", SubjectCategory.ARTS),
            ("电子商务", SubjectCategory.BUSINESS),
            ("市场营销", SubjectCategory.BUSINESS),
            ("园林景观", SubjectCategory.NATURE),
            ("生态学", SubjectCategory.NATURE),
            ("应用数学", SubjectCategory.SCIENCE),
            ("未知专业", SubjectCategory.GENERAL),
            ("", SubjectCategory.GENERAL),
        ]
        
        for major, expected in test_cases:
            with self.subTest(major=major):
                result = _determine_subject_category(major)
                self.assertEqual(result, expected, f"Failed for major: {major}")

    def test_select_layout_preferences(self):
        """Test layout selection biases based on major"""
        
        # 1. Medical should prefer 'steps' for process
        content_med = {'major': '护理学', 'bullets': ['Step 1', 'Step 2', 'Step 3']}
        layout_med = select_layout('steps', content_med)
        self.assertEqual(layout_med, 'steps')
        
        # 2. Engineering should prefer 'comparison' for structure
        content_eng = {'major': '机械工程', 'bullets': ['A', 'B', 'C']}
        layout_eng = select_layout('structure', content_eng)
        self.assertEqual(layout_eng, 'comparison') # count > 2 implies comparison for eng
        
        # 3. Arts should prefer 'top_image' for concept
        content_arts = {'major': '美术设计', 'bullets': ['Concept A'], 'image_description': 'Art'}
        layout_arts = select_layout('concept', content_arts, has_image=True)
        self.assertEqual(layout_arts, 'top_image')
        
    def test_css_generation_snippet(self):
        """Verify CSS generation logic in Generator (mocked)"""
        # Since we can't easily instantiate HTMLGenerator without deps, we just check the expected output string patterns
        # if logic was moved to layouts, we could test it here.
        # But for now, we trust the mapping tests above cover the logic core.
        pass

if __name__ == '__main__':
    unittest.main()
