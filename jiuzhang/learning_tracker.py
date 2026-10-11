"""Learning Tracker for JiuZhang Mathematics Platform.

Tracks user progress, achievements, and learning analytics.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import hashlib


class LearningTracker:
    """Track user learning progress and achievements."""
    
    def __init__(self, user_id: str = "default", storage_path: str = None):
        self.user_id = user_id
        self.storage_path = Path(storage_path or "~/.jiuzhang/tracker").expanduser()
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.progress_file = self.storage_path / f"progress_{user_id}.json"
        self.achievements_file = self.storage_path / f"achievements_{user_id}.json"
        
        self.progress = self._load_progress()
        self.achievements = self._load_achievements()
    
    def _load_progress(self) -> Dict:
        """Load user progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "started_lessons": [],
            "completed_lessons": [],
            "total_time_spent": 0,
            "last_activity": None,
            "streak_days": 0,
            "courses_completed": [],
            "topics_mastered": []
        }
    
    def _save_progress(self):
        """Save user progress to file."""
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, ensure_ascii=False, indent=2)
    
    def _load_achievements(self) -> Dict:
        """Load user achievements from file."""
        if self.achievements_file.exists():
            try:
                with open(self.achievements_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {
            "completed_lessons": 0,
            "streak_days": 0,
            "courses_finished": 0,
            "badges": []
        }
    
    def _save_achievements(self):
        """Save user achievements to file."""
        with open(self.achievements_file, 'w', encoding='utf-8') as f:
            json.dump(self.achievements, f, ensure_ascii=False, indent=2)
    
    def start_lesson(self, lesson_id: str, category: str, level: str):
        """Record when user starts a lesson."""
        lesson_key = f"{category}.{level}.{lesson_id}"
        
        if lesson_key not in self.progress["started_lessons"]:
            self.progress["started_lessons"].append(lesson_key)
            self.progress["last_activity"] = datetime.now().isoformat()
            self._save_progress()
    
    def complete_lesson(self, lesson_id: str, category: str, level: str, time_taken: float = 0):
        """Record when user completes a lesson."""
        lesson_key = f"{category}.{level}.{lesson_id}"
        
        if lesson_key not in self.progress["completed_lessons"]:
            self.progress["completed_lessons"].append(lesson_key)
            self.progress["total_time_spent"] += time_taken
            self.progress["last_activity"] = datetime.now().isoformat()
            
            # Update streak if this is consecutive day
            today = datetime.now().date().isoformat()
            if self.progress.get("last_completion_date") != today:
                if self.progress.get("last_completion_date") == (datetime.now().date().isoformat() if datetime.now().date().day == datetime.now().date().day - 1 else None):
                    self.progress["streak_days"] += 1
                else:
                    self.progress["streak_days"] = 1
                self.progress["last_completion_date"] = today
            
            # Check for achievements
            self.achievements["completed_lessons"] += 1
            self._check_achievements()
            
            self._save_progress()
            self._save_achievements()
    
    def complete_course(self, course_name: str):
        """Record when user completes a course."""
        if course_name not in self.progress["courses_completed"]:
            self.progress["courses_completed"].append(course_name)
            self.achievements["courses_finished"] += 1
            self._check_achievements()
            self._save_progress()
            self._save_achievements()
    
    def master_topic(self, topic_id: str):
        """Record when user masters a topic."""
        if topic_id not in self.progress["topics_mastered"]:
            self.progress["topics_mastered"].append(topic_id)
            self._save_progress()
    
    def _check_achievements(self):
        """Check and award achievements based on progress."""
        new_badges = []
        
        # Milestone badges
        if self.achievements["completed_lessons"] >= 10:
            new_badges.append("ten_lessons")
        if self.achievements["completed_lessons"] >= 50:
            new_badges.append("fifty_lessons")
        if self.achievements["completed_lessons"] >= 100:
            new_badges.append("hundred_lessons")
        
        if self.achievements["courses_finished"] >= 5:
            new_badges.append("course_completions_5")
        if self.achievements["courses_finished"] >= 10:
            new_badges.append("course_completions_10")
        
        if self.progress["streak_days"] >= 7:
            new_badges.append("week_streak")
        if self.progress["streak_days"] >= 30:
            new_badges.append("month_streak")
        
        # Add new badges
        for badge in new_badges:
            if badge not in self.achievements["badges"]:
                self.achievements["badges"].append(badge)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of user progress."""
        return {
            "completed_lessons": len(self.progress["completed_lessons"]),
            "started_lessons": len(self.progress["started_lessons"]),
            "total_courses_completed": len(self.progress["courses_completed"]),
            "topics_mastered": len(self.progress["topics_mastered"]),
            "total_time_spent_hours": round(self.progress["total_time_spent"] / 3600, 2),
            "current_streak_days": self.progress["streak_days"],
            "last_activity": self.progress.get("last_activity"),
            "completion_rate": round(
                len(self.progress["completed_lessons"]) / max(len(self.progress["started_lessons"]), 1) * 100, 2
            ) if self.progress["started_lessons"] else 0
        }
    
    def get_achievements(self) -> Dict[str, Any]:
        """Get user achievements."""
        return self.achievements
    
    def get_study_recommendations(self) -> List[Dict[str, str]]:
        """Provide personalized study recommendations."""
        recommendations = []
        
        # Recommend unfinished lessons in recently studied categories
        recent_categories = set()
        for lesson in self.progress["started_lessons"][-10:]:  # Last 10 lessons
            if '.' in lesson:
                category = lesson.split('.')[0]
                recent_categories.add(category)
        
        # Suggest next lessons in the same category
        for category in recent_categories:
            recommendations.append({
                "type": "continue_category",
                "category": category,
                "message": f"Continue studying {category} concepts"
            })
        
        # Suggest lessons based on gaps in prerequisites
        recommendations.append({
            "type": "prerequisite_gap",
            "message": "Review foundational concepts to strengthen understanding"
        })
        
        # Suggest challenging topics based on mastery level
        if len(self.progress["topics_mastered"]) > 10:
            recommendations.append({
                "type": "advance_level",
                "message": "Consider advancing to more challenging topics"
            })
        else:
            recommendations.append({
                "type": "foundational",
                "message": "Focus on mastering fundamental concepts first"
            })
        
        return recommendations