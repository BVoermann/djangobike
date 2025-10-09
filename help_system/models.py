from django.db import models
from django.contrib.auth.models import User
from bikeshop.models import GameSession


DIFFICULTY_LEVELS = [
    ('beginner', 'Anfänger'),
    ('intermediate', 'Fortgeschritten'),
    ('advanced', 'Experte'),
]


class HelpCategory(models.Model):
    """Categories for organizing help content"""
    
    CATEGORY_TYPES = [
        ('basics', 'Grundlagen'),
        ('procurement', 'Einkauf'),
        ('production', 'Produktion'),
        ('sales', 'Verkauf'),
        ('finance', 'Finanzen'),
        ('warehouse', 'Lager'),
        ('strategy', 'Strategie'),
        ('reports', 'Berichte'),
        ('advanced', 'Erweitert'),
    ]
    
    name = models.CharField(max_length=100)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-question-circle')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class TutorialVideo(models.Model):
    """Tutorial videos for different features"""
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='videos')
    
    # Video details
    video_url = models.URLField(help_text="YouTube, Vimeo, or direct video URL")
    video_embed_code = models.TextField(blank=True, help_text="HTML embed code for video")
    thumbnail_url = models.URLField(blank=True)
    duration_minutes = models.IntegerField(help_text="Duration in minutes")
    
    # Metadata
    difficulty_level = models.CharField(max_length=20, choices=DIFFICULTY_LEVELS, default='beginner')
    prerequisites = models.TextField(blank=True, help_text="What users should know before watching")
    learning_objectives = models.TextField(help_text="What users will learn")
    
    # Organization
    order = models.IntegerField(default=0)
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.category.name})"


class InteractiveGuide(models.Model):
    """Interactive popup guides that walk users through features"""
    
    GUIDE_TYPES = [
        ('walkthrough', 'Feature Walkthrough'),
        ('onboarding', 'Initial Onboarding'),
        ('feature_intro', 'New Feature Introduction'),
        ('troubleshooting', 'Problem Solving'),
    ]
    
    TRIGGER_CONDITIONS = [
        ('manual', 'Manual Activation'),
        ('first_visit', 'First Visit to Page'),
        ('session_start', 'New Session'),
        ('feature_access', 'First Feature Access'),
        ('error_state', 'Error Occurred'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='guides')
    
    # Guide configuration
    guide_type = models.CharField(max_length=20, choices=GUIDE_TYPES)
    target_url_pattern = models.CharField(
        max_length=200, 
        help_text="URL pattern where this guide should be available (e.g., '/procurement/*')"
    )
    trigger_condition = models.CharField(max_length=20, choices=TRIGGER_CONDITIONS, default='manual')
    
    # Guide steps (JSON format)
    steps = models.JSONField(default=list, help_text="List of guide steps with targets and content")
    # Format: [{"target": "#element-id", "title": "Step Title", "content": "Step content", "placement": "top"}]
    
    # Conditions
    prerequisites = models.TextField(blank=True)
    user_level_required = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_LEVELS, 
        default='beginner'
    )
    
    # Settings
    is_skippable = models.BooleanField(default=True)
    show_progress = models.BooleanField(default=True)
    auto_advance = models.BooleanField(default=False)
    completion_required = models.BooleanField(default=False)
    
    # Organization
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    start_count = models.IntegerField(default=0)
    completion_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.guide_type}"
    
    @property
    def completion_rate(self):
        if self.start_count > 0:
            return (self.completion_count / self.start_count) * 100
        return 0


class TooltipHelp(models.Model):
    """Question mark tooltips for interface elements"""
    
    TOOLTIP_TYPES = [
        ('info', 'Information'),
        ('tip', 'Pro Tip'),
        ('warning', 'Warning'),
        ('definition', 'Definition'),
    ]
    
    # Target element
    element_selector = models.CharField(
        max_length=200, 
        help_text="CSS selector for the target element (e.g., '#balance-display', '.btn-primary')"
    )
    page_url_pattern = models.CharField(
        max_length=200,
        help_text="URL pattern where this tooltip should appear"
    )
    
    # Content
    title = models.CharField(max_length=100)
    content = models.TextField()
    tooltip_type = models.CharField(max_length=20, choices=TOOLTIP_TYPES, default='info')
    
    # Appearance
    position = models.CharField(
        max_length=20,
        choices=[('top', 'Top'), ('bottom', 'Bottom'), ('left', 'Left'), ('right', 'Right')],
        default='top'
    )
    icon = models.CharField(max_length=50, default='fas fa-question-circle')
    
    # Behavior
    show_on_hover = models.BooleanField(default=True)
    show_on_click = models.BooleanField(default=False)
    auto_hide_delay = models.IntegerField(default=0, help_text="Auto-hide after X seconds (0 = no auto-hide)")
    
    # Organization
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='tooltips')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    view_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.element_selector}"


class ContextualHelp(models.Model):
    """Context-sensitive help based on user actions"""
    
    CONTEXT_TYPES = [
        ('page_load', 'Page Loaded'),
        ('action_taken', 'Action Performed'),
        ('error_occurred', 'Error State'),
        ('milestone_reached', 'Milestone Achieved'),
        ('time_spent', 'Time on Page'),
        ('struggle_detected', 'User Struggling'),
    ]
    
    # Context detection
    context_type = models.CharField(max_length=20, choices=CONTEXT_TYPES)
    trigger_conditions = models.JSONField(
        default=dict,
        help_text="Conditions that trigger this help (e.g., {'page': '/procurement/', 'first_time': true})"
    )
    
    # Content
    title = models.CharField(max_length=200)
    content = models.TextField()
    help_format = models.CharField(
        max_length=20,
        choices=[
            ('popup', 'Popup Modal'),
            ('sidebar', 'Sidebar Panel'),
            ('banner', 'Top Banner'),
            ('tooltip', 'Tooltip'),
            ('guide', 'Interactive Guide'),
        ],
        default='popup'
    )
    
    # Related content
    category = models.ForeignKey(HelpCategory, on_delete=models.CASCADE, related_name='contextual_help')
    related_video = models.ForeignKey(TutorialVideo, on_delete=models.SET_NULL, null=True, blank=True)
    related_guide = models.ForeignKey(InteractiveGuide, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Targeting
    user_experience_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )
    session_month_range = models.CharField(
        max_length=50,
        blank=True,
        help_text="e.g., '1-3' for first 3 months"
    )
    
    # Behavior
    max_displays_per_user = models.IntegerField(default=3)
    cooldown_hours = models.IntegerField(default=24, help_text="Hours before showing again")
    priority = models.IntegerField(default=5, help_text="1=highest, 10=lowest")
    
    # Organization
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    trigger_count = models.IntegerField(default=0)
    interaction_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['priority', 'order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.context_type}"


class UserHelpProgress(models.Model):
    """Track user progress through help content"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='help_progress')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, null=True, blank=True)
    
    # Video progress
    videos_watched = models.ManyToManyField(TutorialVideo, blank=True, related_name='watched_by')
    
    # Guide progress
    guides_completed = models.ManyToManyField(InteractiveGuide, blank=True, related_name='completed_by')
    guides_started = models.ManyToManyField(
        InteractiveGuide, 
        through='GuideProgress', 
        related_name='started_by'
    )
    
    # General progress
    onboarding_completed = models.BooleanField(default=False)
    help_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )
    
    # Preferences
    show_tooltips = models.BooleanField(default=True)
    show_contextual_help = models.BooleanField(default=True)
    auto_play_guides = models.BooleanField(default=False)
    
    # Statistics
    total_help_interactions = models.IntegerField(default=0)
    last_help_accessed = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        pass
    
    def __str__(self):
        return f"{self.user.username} - Help Progress"


class GuideProgress(models.Model):
    """Detailed progress tracking for interactive guides"""
    
    user_progress = models.ForeignKey(UserHelpProgress, on_delete=models.CASCADE)
    guide = models.ForeignKey(InteractiveGuide, on_delete=models.CASCADE)
    
    # Progress tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    current_step = models.IntegerField(default=0)
    total_steps = models.IntegerField(default=0)
    
    # Interaction data
    steps_completed = models.JSONField(default=list)
    time_spent_seconds = models.IntegerField(default=0)
    was_skipped = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user_progress.user.username} - {self.guide.title}"
    
    @property
    def completion_percentage(self):
        if self.total_steps > 0:
            return (len(self.steps_completed) / self.total_steps) * 100
        return 0


class HelpFeedback(models.Model):
    """User feedback on help content"""
    
    CONTENT_TYPES = [
        ('video', 'Tutorial Video'),
        ('guide', 'Interactive Guide'),
        ('tooltip', 'Tooltip'),
        ('contextual', 'Contextual Help'),
    ]
    
    RATING_CHOICES = [
        (1, '⭐ Nicht hilfreich'),
        (2, '⭐⭐ Wenig hilfreich'),
        (3, '⭐⭐⭐ Okay'),
        (4, '⭐⭐⭐⭐ Hilfreich'),
        (5, '⭐⭐⭐⭐⭐ Sehr hilfreich'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_feedback')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.IntegerField(help_text="ID of the help content")
    
    # Feedback
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True)
    
    # Suggestions
    suggested_improvements = models.TextField(blank=True)
    would_recommend = models.BooleanField(default=True)
    
    # Context
    user_experience_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )
    session_context = models.CharField(max_length=200, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.content_type} - {self.rating}⭐"


class HelpAnalytics(models.Model):
    """Analytics for help system usage"""
    
    EVENT_TYPES = [
        ('video_started', 'Video Started'),
        ('video_completed', 'Video Completed'),
        ('guide_started', 'Guide Started'),
        ('guide_completed', 'Guide Completed'),
        ('guide_skipped', 'Guide Skipped'),
        ('tooltip_viewed', 'Tooltip Viewed'),
        ('help_searched', 'Help Searched'),
        ('contextual_help_shown', 'Contextual Help Shown'),
        ('contextual_help_dismissed', 'Contextual Help Dismissed'),
    ]
    
    CONTENT_TYPES = [
        ('video', 'Tutorial Video'),
        ('guide', 'Interactive Guide'),
        ('tooltip', 'Tooltip'),
        ('contextual', 'Contextual Help'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='help_analytics')
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, null=True, blank=True)
    
    # Event data
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.IntegerField()
    
    # Context
    page_url = models.CharField(max_length=300)
    session_month = models.IntegerField(null=True, blank=True)
    user_experience_level = models.CharField(
        max_length=20,
        choices=DIFFICULTY_LEVELS,
        default='beginner'
    )
    
    # Interaction data
    interaction_data = models.JSONField(
        default=dict,
        help_text="Additional data about the interaction"
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.event_type} - {self.timestamp}"
    
    class Meta:
        ordering = ['-timestamp']