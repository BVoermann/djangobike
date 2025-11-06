from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from bikeshop.models import GameSession
from .models import (
    HelpCategory, TutorialVideo, InteractiveGuide, TooltipHelp,
    ContextualHelp, UserHelpProgress, GuideProgress, HelpFeedback, HelpAnalytics,
    DIFFICULTY_LEVELS
)
import json
import re


def get_or_create_user_progress(user):
    """Get or create UserHelpProgress"""
    user_progress, created = UserHelpProgress.objects.get_or_create(user=user)
    return user_progress


@login_required
def help_dashboard(request):
    """Main help dashboard showing all available help content"""
    user_progress = get_or_create_user_progress(request.user)
    
    # Get categories with content counts
    categories = HelpCategory.objects.filter(is_active=True).prefetch_related(
        'videos', 'guides', 'tooltips'
    )
    
    # Get featured videos
    featured_videos = TutorialVideo.objects.filter(
        is_featured=True, 
        is_active=True
    )[:6]
    
    # Get recommended content based on user level
    recommended_videos = TutorialVideo.objects.filter(
        difficulty_level=user_progress.help_level,
        is_active=True
    ).exclude(
        id__in=user_progress.videos_watched.values_list('id', flat=True)
    )[:4]
    
    # Get available guides
    available_guides = InteractiveGuide.objects.filter(
        is_active=True
    ).exclude(
        id__in=user_progress.guides_completed.values_list('id', flat=True)
    )[:4]
    
    # Recent activity
    recent_analytics = HelpAnalytics.objects.filter(
        user=request.user
    ).order_by('-timestamp')[:10]
    
    # Progress statistics
    total_videos = TutorialVideo.objects.filter(is_active=True).count()
    watched_videos = user_progress.videos_watched.count()
    total_guides = InteractiveGuide.objects.filter(is_active=True).count()
    completed_guides = user_progress.guides_completed.count()
    
    context = {
        'user_progress': user_progress,
        'categories': categories,
        'featured_videos': featured_videos,
        'recommended_videos': recommended_videos,
        'available_guides': available_guides,
        'recent_analytics': recent_analytics,
        'progress_stats': {
            'videos_progress': (watched_videos / total_videos * 100) if total_videos > 0 else 0,
            'guides_progress': (completed_guides / total_guides * 100) if total_guides > 0 else 0,
            'watched_videos': watched_videos,
            'total_videos': total_videos,
            'completed_guides': completed_guides,
            'total_guides': total_guides,
        }
    }
    
    return render(request, 'help_system/dashboard.html', context)


@login_required
def video_library(request):
    """Library of all tutorial videos"""
    category_filter = request.GET.get('category')
    difficulty_filter = request.GET.get('difficulty')
    search_query = request.GET.get('search', '')
    
    videos = TutorialVideo.objects.filter(is_active=True)
    
    # Apply filters
    if category_filter:
        videos = videos.filter(category__category_type=category_filter)
    if difficulty_filter:
        videos = videos.filter(difficulty_level=difficulty_filter)
    if search_query:
        videos = videos.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query)
        )
    
    videos = videos.select_related('category').order_by('category', 'order')
    
    # Get user progress
    user_progress = get_or_create_user_progress(request.user)
    watched_video_ids = user_progress.videos_watched.values_list('id', flat=True)
    
    # Get categories for filter
    categories = HelpCategory.objects.filter(is_active=True)
    
    context = {
        'videos': videos,
        'categories': categories,
        'watched_video_ids': watched_video_ids,
        'current_category': category_filter,
        'current_difficulty': difficulty_filter,
        'search_query': search_query,
        'difficulty_choices': DIFFICULTY_LEVELS,
    }
    
    return render(request, 'help_system/video_library.html', context)


@login_required
def video_detail(request, video_id):
    """Detailed view of a tutorial video"""
    video = get_object_or_404(TutorialVideo, id=video_id, is_active=True)
    
    # Get or create user progress
    user_progress = get_or_create_user_progress(request.user)
    
    # Check if user has watched this video
    has_watched = user_progress.videos_watched.filter(id=video_id).exists()
    
    # Get related videos
    related_videos = TutorialVideo.objects.filter(
        category=video.category,
        is_active=True
    ).exclude(id=video_id)[:4]
    
    # Get user feedback for this video
    user_feedback = HelpFeedback.objects.filter(
        user=request.user,
        content_type='video',
        content_id=video_id
    ).first()
    
    # Record analytics
    HelpAnalytics.objects.create(
        user=request.user,
        event_type='video_started',
        content_type='video',
        content_id=video_id,
        page_url=request.get_full_path(),
        user_experience_level=user_progress.help_level
    )
    
    # Increment view count
    video.view_count += 1
    video.save(update_fields=['view_count'])
    
    context = {
        'video': video,
        'has_watched': has_watched,
        'related_videos': related_videos,
        'user_feedback': user_feedback,
        'user_progress': user_progress,
    }
    
    return render(request, 'help_system/video_detail.html', context)


@login_required
def interactive_guides(request):
    """View all available interactive guides"""
    category_filter = request.GET.get('category')
    
    guides = InteractiveGuide.objects.filter(is_active=True)
    
    if category_filter:
        guides = guides.filter(category__category_type=category_filter)
    
    guides = guides.select_related('category').order_by('category', 'order')
    
    # Get user progress
    user_progress = get_or_create_user_progress(request.user)
    
    completed_guide_ids = user_progress.guides_completed.values_list('id', flat=True)
    started_guide_ids = user_progress.guides_started.values_list('id', flat=True)
    
    # Get categories for filter
    categories = HelpCategory.objects.filter(is_active=True)
    
    context = {
        'guides': guides,
        'categories': categories,
        'completed_guide_ids': completed_guide_ids,
        'started_guide_ids': started_guide_ids,
        'current_category': category_filter,
    }
    
    return render(request, 'help_system/interactive_guides.html', context)


@login_required
def guide_detail(request, guide_id):
    """Detailed view of an interactive guide"""
    guide = get_object_or_404(InteractiveGuide, id=guide_id, is_active=True)
    
    # Get or create user progress
    user_progress = get_or_create_user_progress(request.user)
    
    # Check user's progress on this guide
    guide_progress = GuideProgress.objects.filter(
        user_progress=user_progress,
        guide=guide
    ).first()
    
    has_completed = user_progress.guides_completed.filter(id=guide_id).exists()
    
    context = {
        'guide': guide,
        'guide_progress': guide_progress,
        'has_completed': has_completed,
        'user_progress': user_progress,
    }
    
    return render(request, 'help_system/guide_detail.html', context)


@login_required
def contextual_help_api(request):
    """API endpoint for context-sensitive help"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    page_url = request.GET.get('page_url', '')
    user_session_id = request.GET.get('session_id')
    
    # Get user progress
    user_progress = get_or_create_user_progress(request.user)
    
    # Don't show contextual help if user has disabled it
    if not user_progress.show_contextual_help:
        return JsonResponse({'help_items': []})
    
    # Get relevant contextual help
    help_items = ContextualHelp.objects.filter(
        is_active=True,
        user_experience_level=user_progress.help_level
    )
    
    # Filter by URL pattern
    matching_help = []
    for help_item in help_items:
        trigger_conditions = help_item.trigger_conditions
        
        # Check URL pattern
        if 'page_pattern' in trigger_conditions:
            pattern = trigger_conditions['page_pattern']
            if re.match(pattern.replace('*', '.*'), page_url):
                matching_help.append(help_item)
        
        # Check if this is first visit
        if help_item.context_type == 'page_load' and 'first_time' in trigger_conditions:
            # Check if user has visited this page before
            previous_visits = HelpAnalytics.objects.filter(
                user=request.user,
                page_url=page_url
            ).count()
            
            if previous_visits == 0 and trigger_conditions['first_time']:
                matching_help.append(help_item)
    
    # Format response
    help_data = []
    for help_item in matching_help:
        # Check cooldown and max displays
        recent_displays = HelpAnalytics.objects.filter(
            user=request.user,
            content_type='contextual',
            content_id=help_item.id,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=help_item.cooldown_hours)
        ).count()
        
        total_displays = HelpAnalytics.objects.filter(
            user=request.user,
            content_type='contextual',
            content_id=help_item.id,
            event_type='contextual_help_shown'
        ).count()
        
        if recent_displays == 0 and total_displays < help_item.max_displays_per_user:
            help_data.append({
                'id': help_item.id,
                'title': help_item.title,
                'content': help_item.content,
                'format': help_item.help_format,
                'priority': help_item.priority,
                'related_video_id': help_item.related_video.id if help_item.related_video else None,
                'related_guide_id': help_item.related_guide.id if help_item.related_guide else None,
            })
    
    # Sort by priority
    help_data.sort(key=lambda x: x['priority'])
    
    return JsonResponse({'help_items': help_data})


@login_required
def tooltip_help_api(request):
    """API endpoint for tooltip help"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    page_url = request.GET.get('page_url', '')
    
    # Get user progress
    user_progress = get_or_create_user_progress(request.user)
    
    # Don't show tooltips if user has disabled them
    if not user_progress.show_tooltips:
        return JsonResponse({'tooltips': []})
    
    # Get relevant tooltips for this page
    tooltips = TooltipHelp.objects.filter(
        is_active=True
    )
    
    # Filter by URL pattern
    matching_tooltips = []
    for tooltip in tooltips:
        pattern = tooltip.page_url_pattern
        if re.match(pattern.replace('*', '.*'), page_url):
            matching_tooltips.append({
                'id': tooltip.id,
                'element_selector': tooltip.element_selector,
                'title': tooltip.title,
                'content': tooltip.content,
                'tooltip_type': tooltip.tooltip_type,
                'position': tooltip.position,
                'icon': tooltip.icon,
                'show_on_hover': tooltip.show_on_hover,
                'show_on_click': tooltip.show_on_click,
                'auto_hide_delay': tooltip.auto_hide_delay,
            })
    
    return JsonResponse({'tooltips': matching_tooltips})


def mock_simulation(request, mock_type='overview'):
    """Mock simulation environment for guided tours"""
    context = {
        'mock_type': mock_type,
    }
    return render(request, 'help_system/mock_simulation.html', context)


def start_guide_api(request, guide_id):
    """API endpoint to start an interactive guide"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Check authentication for AJAX requests
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'Authentication required',
            'message': 'Please log in to access interactive guides'
        }, status=401)
    
    guide = get_object_or_404(InteractiveGuide, id=guide_id, is_active=True)
    
    # Get or create user progress
    user_progress = get_or_create_user_progress(request.user)

    # Handle guide progress - use filter().first() to avoid MultipleObjectsReturned error
    # This can happen if there are duplicate records in the database
    guide_progress = GuideProgress.objects.filter(
        user_progress=user_progress,
        guide=guide
    ).first()

    if guide_progress:
        # Reset existing progress
        guide_progress.current_step = 0
        guide_progress.steps_completed = []
        guide_progress.completed_at = None
        guide_progress.was_skipped = False
        guide_progress.total_steps = len(guide.steps)
        guide_progress.save()
        created = False
    else:
        # Create new guide progress
        guide_progress = GuideProgress.objects.create(
            user_progress=user_progress,
            guide=guide,
            total_steps=len(guide.steps),
            current_step=0
        )
        created = True
    
    # Record analytics
    HelpAnalytics.objects.create(
        user=request.user,
        event_type='guide_started',
        content_type='guide',
        content_id=guide_id,
        page_url=request.META.get('HTTP_REFERER', ''),
        user_experience_level=user_progress.help_level
    )
    
    # Update guide statistics
    guide.start_count += 1
    guide.save(update_fields=['start_count'])
    
    return JsonResponse({
        'success': True,
        'guide': {
            'id': guide.id,
            'title': guide.title,
            'steps': guide.steps,
            'is_skippable': guide.is_skippable,
            'show_progress': guide.show_progress,
            'current_step': guide_progress.current_step,
        }
    })


@login_required
def update_guide_progress_api(request, guide_id):
    """API endpoint to update guide progress"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        step_number = data.get('step_number')
        action = data.get('action')  # 'complete', 'skip', 'finish'
        
        guide = get_object_or_404(InteractiveGuide, id=guide_id, is_active=True)
        user_progress = get_object_or_404(UserHelpProgress, user=request.user)
        guide_progress = get_object_or_404(
            GuideProgress,
            user_progress=user_progress,
            guide=guide
        )
        
        if action == 'complete':
            # Mark step as completed
            if step_number not in guide_progress.steps_completed:
                guide_progress.steps_completed.append(step_number)
            guide_progress.current_step = step_number + 1
            
        elif action == 'skip':
            # Skip the entire guide
            guide_progress.was_skipped = True
            guide_progress.completed_at = timezone.now()
            
            # Record analytics
            HelpAnalytics.objects.create(
                user=request.user,
                event_type='guide_skipped',
                content_type='guide',
                content_id=guide_id,
                page_url=request.META.get('HTTP_REFERER', ''),
                user_experience_level=user_progress.help_level
            )
            
        elif action == 'finish':
            # Complete the guide
            guide_progress.completed_at = timezone.now()
            user_progress.guides_completed.add(guide)
            
            # Record analytics
            HelpAnalytics.objects.create(
                user=request.user,
                event_type='guide_completed',
                content_type='guide',
                content_id=guide_id,
                page_url=request.META.get('HTTP_REFERER', ''),
                user_experience_level=user_progress.help_level
            )
            
            # Update guide statistics
            guide.completion_count += 1
            guide.save(update_fields=['completion_count'])
        
        guide_progress.save()
        
        return JsonResponse({
            'success': True,
            'current_step': guide_progress.current_step,
            'completed': guide_progress.completed_at is not None,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def mark_video_watched_api(request, video_id):
    """API endpoint to mark a video as watched"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    video = get_object_or_404(TutorialVideo, id=video_id, is_active=True)
    user_progress = get_or_create_user_progress(request.user)
    
    # Mark video as watched
    user_progress.videos_watched.add(video)
    user_progress.total_help_interactions += 1
    user_progress.last_help_accessed = timezone.now()
    user_progress.save()
    
    # Record analytics
    HelpAnalytics.objects.create(
        user=request.user,
        event_type='video_completed',
        content_type='video',
        content_id=video_id,
        page_url=request.META.get('HTTP_REFERER', ''),
        user_experience_level=user_progress.help_level
    )
    
    return JsonResponse({'success': True})


@login_required
def submit_feedback_api(request):
    """API endpoint to submit help feedback"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Create or update feedback
        feedback, created = HelpFeedback.objects.update_or_create(
            user=request.user,
            content_type=data.get('content_type'),
            content_id=data.get('content_id'),
            defaults={
                'rating': data.get('rating'),
                'comment': data.get('comment', ''),
                'suggested_improvements': data.get('suggested_improvements', ''),
                'would_recommend': data.get('would_recommend', True),
                'session_context': data.get('session_context', ''),
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Feedback submitted successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def update_help_preferences_api(request):
    """API endpoint to update user help preferences"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        user_progress = get_or_create_user_progress(request.user)
        
        # Update preferences
        if 'show_tooltips' in data:
            user_progress.show_tooltips = data['show_tooltips']
        if 'show_contextual_help' in data:
            user_progress.show_contextual_help = data['show_contextual_help']
        if 'auto_play_guides' in data:
            user_progress.auto_play_guides = data['auto_play_guides']
        if 'help_level' in data:
            user_progress.help_level = data['help_level']
        
        user_progress.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Preferences updated successfully'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def record_help_interaction_api(request):
    """API endpoint to record help interactions for analytics"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        user_progress = get_or_create_user_progress(request.user)
        
        # Record analytics
        HelpAnalytics.objects.create(
            user=request.user,
            event_type=data.get('event_type'),
            content_type=data.get('content_type'),
            content_id=data.get('content_id'),
            page_url=data.get('page_url', ''),
            user_experience_level=user_progress.help_level,
            interaction_data=data.get('interaction_data', {})
        )
        
        # Update tooltip view count if applicable
        if data.get('content_type') == 'tooltip':
            try:
                tooltip = TooltipHelp.objects.get(id=data.get('content_id'))
                tooltip.view_count += 1
                tooltip.save(update_fields=['view_count'])
            except TooltipHelp.DoesNotExist:
                pass
        
        return JsonResponse({'success': True})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def help_search_api(request):
    """API endpoint for searching help content"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search videos
    videos = TutorialVideo.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(tags__icontains=query),
        is_active=True
    )[:5]
    
    # Search guides
    guides = InteractiveGuide.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query),
        is_active=True
    )[:5]
    
    # Format results
    results = []
    
    for video in videos:
        results.append({
            'type': 'video',
            'id': video.id,
            'title': video.title,
            'description': video.description[:150] + '...' if len(video.description) > 150 else video.description,
            'category': video.category.name,
            'difficulty': video.get_difficulty_level_display(),
            'url': reverse('help_system:video_detail', args=[video.id]),
        })
    
    for guide in guides:
        results.append({
            'type': 'guide',
            'id': guide.id,
            'title': guide.title,
            'description': guide.description[:150] + '...' if len(guide.description) > 150 else guide.description,
            'category': guide.category.name,
            'guide_type': guide.get_guide_type_display(),
            'url': reverse('help_system:guide_detail', args=[guide.id]),
        })
    
    # Record search analytics
    user_progress = get_or_create_user_progress(request.user)
    
    HelpAnalytics.objects.create(
        user=request.user,
        event_type='help_searched',
        content_type='video',  # Default, we don't have a search content type
        content_id=0,
        page_url=request.META.get('HTTP_REFERER', ''),
        user_experience_level=user_progress.help_level,
        interaction_data={'search_query': query, 'results_count': len(results)}
    )
    
    return JsonResponse({'results': results})


@login_required
def documentation(request):
    """Comprehensive game documentation with searchable content"""
    return render(request, 'help_system/documentation.html')