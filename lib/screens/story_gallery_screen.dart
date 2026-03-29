import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../models/story_summary.dart';
import '../providers/story_provider.dart';
import '../theme.dart';

Color _storyColor(String hex) {
  final clean = hex.replaceAll('#', '').trim();
  final parsed = int.tryParse(clean, radix: 16);
  if (parsed == null || clean.length != 6) return AppTheme.accentNeon;
  return Color(0xFF000000 | parsed);
}

int _completionPercent(StorySummary story) {
  final start = story.storyStartAt ?? story.createdAt;
  final duration = story.storyDurationMinutes <= 0
      ? 1
      : story.storyDurationMinutes;
  final elapsed = DateTime.now().difference(start).inMinutes;
  if (elapsed <= 0) return 0;
  if (elapsed >= duration) return 100;
  return ((elapsed / duration) * 100).clamp(0, 100).round();
}

String _countdownLabel(DateTime target) {
  final diff = target.difference(DateTime.now());
  if (diff.inSeconds <= 0) return 'Starting now';
  if (diff.inDays > 0) return 'Starts in ${diff.inDays}d';
  if (diff.inHours > 0) return 'Starts in ${diff.inHours}h';
  return 'Starts in ${diff.inMinutes}m';
}

class StoryGalleryScreen extends ConsumerWidget {
  const StoryGalleryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storiesAsync = ref.watch(allStoriesProvider);
    final activeStoryId = ref.watch(activeStoryIdProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text(
          'Story Gallery',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: storiesAsync.when(
        data: (stories) {
          if (stories.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.history_edu,
                    size: 64,
                    color: Colors.white.withOpacity(0.2),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    'No stories found in Firestore.',
                    style: TextStyle(color: Colors.white54),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload a run from Director Studio first.',
                    style: TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                ],
              ),
            );
          }

          final liveStories = stories
              .where(
                (s) =>
                    s.storyMode == StoryLifecycleMode.live ||
                    (s.storyMode == StoryLifecycleMode.scheduled &&
                        !s.isUpcoming),
              )
              .toList();
          final upcomingStories = stories
              .where(
                (s) =>
                    s.storyMode == StoryLifecycleMode.scheduled && s.isUpcoming,
              )
              .toList();
          final subscriptionStories = stories
              .where(
                (s) =>
                    s.storyMode == StoryLifecycleMode.subscription &&
                    !s.isOnDemandSubscription,
              )
              .toList();
          final onDemandStories = stories
              .where(
                (s) =>
                    s.storyMode == StoryLifecycleMode.subscription &&
                    s.isOnDemandSubscription,
              )
              .toList();

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              _sectionHeader('Live'),
              ...liveStories.map(
                (story) => _StoryCard(
                  story: story,
                  isActive: story.id == activeStoryId,
                  accent: _storyColor(story.themeColorHex),
                  subtitle: 'Completion: ${_completionPercent(story)}%',
                  modeChip: 'LIVE',
                  onTap: () async {
                    await ref
                        .read(activeStoryIdProvider.notifier)
                        .setStoryId(story.id);
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Switched to: ${story.title}'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),
              _sectionHeader('Upcoming'),
              ...upcomingStories.map(
                (story) => _StoryCard(
                  story: story,
                  isActive: story.id == activeStoryId,
                  accent: _storyColor(story.themeColorHex),
                  subtitle: story.storyStartAt == null
                      ? 'Scheduled'
                      : _countdownLabel(story.storyStartAt!),
                  modeChip: 'UPCOMING',
                  onTap: () async {
                    await ref
                        .read(activeStoryIdProvider.notifier)
                        .setStoryId(story.id);
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(
                          'Selected upcoming story: ${story.title}',
                        ),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ),
              const SizedBox(height: 12),
              _sectionHeader('Subscription'),
              ...subscriptionStories.map(
                (story) => _StoryCard(
                  story: story,
                  isActive: story.id == activeStoryId,
                  accent: _storyColor(story.themeColorHex),
                  subtitle: 'Starts when you follow this story',
                  modeChip: 'SUBSCRIPTION',
                  onTap: () async {
                    await ensureSubscriptionStartForStory(story.id);
                    await ref
                        .read(activeStoryIdProvider.notifier)
                        .setStoryId(story.id);
                    if (!context.mounted) return;
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Subscribed: ${story.title}'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ),
              if (onDemandStories.isNotEmpty) ...[
                const SizedBox(height: 12),
                _sectionHeader('On-Demand'),
                ...onDemandStories.map(
                  (story) => _StoryCard(
                    story: story,
                    isActive: story.id == activeStoryId,
                    accent: _storyColor(story.themeColorHex),
                    subtitle: 'Paced bursts while you are active in the app',
                    modeChip: 'ON-DEMAND',
                    onTap: () async {
                      await ensureSubscriptionStartForStory(story.id);
                      await ref
                          .read(activeStoryIdProvider.notifier)
                          .setStoryId(story.id);
                      if (!context.mounted) return;
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('On-demand active: ${story.title}'),
                          duration: const Duration(seconds: 2),
                        ),
                      );
                    },
                  ),
                ),
              ],
            ],
          );
        },
        loading: () => const Center(
          child: CircularProgressIndicator(color: AppTheme.accentNeon),
        ),
        error: (err, stack) => Center(
          child: Text(
            'Error: $err',
            style: const TextStyle(color: Colors.redAccent),
          ),
        ),
      ),
    );
  }

  Widget _sectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title.toUpperCase(),
        style: const TextStyle(
          color: AppTheme.textDim,
          fontWeight: FontWeight.w700,
          fontSize: 12,
          letterSpacing: 1.4,
        ),
      ),
    );
  }
}

class _StoryCard extends StatelessWidget {
  final StorySummary story;
  final bool isActive;
  final Color accent;
  final String subtitle;
  final String modeChip;
  final Future<void> Function() onTap;

  const _StoryCard({
    required this.story,
    required this.isActive,
    required this.accent,
    required this.subtitle,
    required this.modeChip,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () {
          onTap();
        },
        borderRadius: BorderRadius.circular(16),
        child: Container(
          decoration: BoxDecoration(
            color: isActive
                ? accent.withOpacity(0.12)
                : Colors.white.withOpacity(0.05),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(
              color: isActive ? accent : Colors.white12,
              width: isActive ? 2 : 1,
            ),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (story.headlineImageUrl != null)
                ClipRRect(
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(15),
                  ),
                  child: Image.network(
                    story.headlineImageUrl!,
                    height: 140,
                    fit: BoxFit.cover,
                    errorBuilder: (context, error, stackTrace) =>
                        const SizedBox(
                          height: 140,
                          child: Center(
                            child: Icon(
                              Icons.broken_image,
                              color: Colors.white24,
                            ),
                          ),
                        ),
                  ),
                ),
              Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    Container(
                      width: 48,
                      height: 48,
                      decoration: BoxDecoration(
                        color: accent.withOpacity(isActive ? 0.9 : 0.2),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        isActive ? Icons.auto_awesome : Icons.menu_book,
                        color: isActive ? Colors.black : accent,
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Expanded(
                                child: Text(
                                  story.title,
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.bold,
                                    color: isActive ? accent : Colors.white,
                                  ),
                                ),
                              ),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 8,
                                  vertical: 2,
                                ),
                                decoration: BoxDecoration(
                                  color: accent.withOpacity(0.18),
                                  borderRadius: BorderRadius.circular(999),
                                  border: Border.all(
                                    color: accent.withOpacity(0.35),
                                  ),
                                ),
                                child: Text(
                                  modeChip,
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.w700,
                                    letterSpacing: 0.8,
                                    color: accent,
                                  ),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Text(
                            subtitle,
                            style: TextStyle(fontSize: 12, color: accent),
                          ),
                          if (story.setup.isNotEmpty) ...[
                            const SizedBox(height: 8),
                            Text(
                              story.setup,
                              maxLines: isActive ? null : 2,
                              overflow: isActive
                                  ? TextOverflow.visible
                                  : TextOverflow.ellipsis,
                              style: const TextStyle(
                                fontSize: 12,
                                color: Colors.white70,
                                height: 1.4,
                              ),
                            ),
                          ],
                          const SizedBox(height: 8),
                          Text(
                            '${DateFormat('MMM d, yyyy').format(story.createdAt)} at ${DateFormat('jm').format(story.createdAt)}',
                            style: const TextStyle(
                              fontSize: 12,
                              color: Colors.white38,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 6),
                    Icon(
                      isActive ? Icons.check_circle : Icons.chevron_right,
                      color: isActive ? accent : Colors.white24,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
