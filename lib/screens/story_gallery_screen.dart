import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../providers/story_provider.dart';
import '../theme.dart';

class StoryGalleryScreen extends ConsumerWidget {
  const StoryGalleryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storiesAsync = ref.watch(allStoriesProvider);
    final activeStoryId = ref.watch(activeStoryIdProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Story Gallery', style: TextStyle(fontWeight: FontWeight.bold)),
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
                  Icon(Icons.history_edu, size: 64, color: Colors.white.withOpacity(0.2)),
                  const SizedBox(height: 16),
                  const Text(
                    'No stories found in Firestore.',
                    style: TextStyle(color: Colors.white54),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Upload a run from the Director Studio first.',
                    style: TextStyle(color: Colors.white38, fontSize: 12),
                  ),
                ],
              ),
            );
          }

          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: stories.length,
            itemBuilder: (context, index) {
              final story = stories[index];
              final isActive = story.id == activeStoryId;

              return Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: InkWell(
                  onTap: () {
                    ref.read(activeStoryIdProvider.notifier).setStoryId(story.id);
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Switched to: ${story.title}'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                  borderRadius: BorderRadius.circular(16),
                  child: Container(
                    decoration: BoxDecoration(
                      color: isActive ? AppTheme.accentNeon.withOpacity(0.1) : Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(16),
                      border: Border.all(
                        color: isActive ? AppTheme.accentNeon : Colors.white12,
                        width: isActive ? 2 : 1,
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (story.headlineImageUrl != null)
                          ClipRRect(
                            borderRadius: const BorderRadius.vertical(top: Radius.circular(15)),
                            child: Image.network(
                              story.headlineImageUrl!,
                              height: 140,
                              fit: BoxFit.cover,
                              errorBuilder: (context, error, stackTrace) =>
                                  const SizedBox(height: 140, child: Center(child: Icon(Icons.broken_image, color: Colors.white24))),
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
                            color: isActive ? AppTheme.accentNeon : Colors.white10,
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            isActive ? Icons.auto_awesome : Icons.menu_book,
                            color: isActive ? Colors.black : Colors.white54,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                story.title,
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                  color: isActive ? AppTheme.accentNeon : Colors.white,
                                ),
                              ),
                              if (story.tags.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 6,
                                  runSpacing: 6,
                                  children: story.tags.map((tag) => Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: AppTheme.accentNeon.withOpacity(0.15),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      '#$tag',
                                      style: const TextStyle(
                                        fontSize: 10,
                                        color: AppTheme.accentNeon,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  )).toList(),
                                ),
                              ],
                              if (story.setup.isNotEmpty) ...[
                                const SizedBox(height: 8),
                                Text(
                                  story.setup,
                                  maxLines: isActive ? null : 3,
                                  overflow: isActive ? TextOverflow.visible : TextOverflow.ellipsis,
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
                              const SizedBox(height: 2),
                              Text(
                                'ID: ${story.id}',
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: Colors.white24,
                                  fontFamily: 'monospace',
                                ),
                              ),
                            ],
                          ),
                        ),
                        if (isActive)
                          const Icon(Icons.check_circle, color: AppTheme.accentNeon)
                        else
                          const Icon(Icons.chevron_right, color: Colors.white24),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (err, stack) => Center(
          child: Text('Error: $err', style: const TextStyle(color: Colors.redAccent)),
        ),
      ),
    );
  }
}
