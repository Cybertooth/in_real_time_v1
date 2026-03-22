import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story_item.dart';
import '../providers/story_provider.dart';
import '../theme.dart';
import '../widgets/shared_widgets.dart';

/// Social media feed — intercepted posts styled per platform.
class SocialPostScreen extends ConsumerWidget {
  const SocialPostScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final postsAsync = ref.watch(socialPostProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('SOCIAL INTERCEPTS')),
      body: postsAsync.when(
        data: (posts) {
          if (posts.isEmpty) {
            return const EmptyState(
              icon: Icons.public_off,
              title: 'NO POSTS',
              subtitle: 'Intercepted social media activity will appear here.',
            );
          }
          return ListView.builder(
            padding: const EdgeInsets.all(16),
            itemCount: posts.length,
            itemBuilder: (_, i) => _PostCard(post: posts[i]),
          );
        },
        loading: () => const Center(child: CircularProgressIndicator(color: AppTheme.accentNeon)),
        error: (e, _) => Center(child: Text('Error: $e')),
      ),
    );
  }
}

class _PostCard extends StatelessWidget {
  final SocialPost post;
  const _PostCard({required this.post});

  IconData _platformIcon(String p) => switch (p.toLowerCase()) {
    'instagram' => Icons.camera_alt,
    'twitter' => Icons.alternate_email,
    'facebook' => Icons.facebook,
    'tiktok' => Icons.music_note,
    _ => Icons.public,
  };

  Color _platformColor(String p) => switch (p.toLowerCase()) {
    'instagram' => const Color(0xFFE1306C),
    'twitter' => const Color(0xFF1DA1F2),
    'facebook' => const Color(0xFF4267B2),
    'tiktok' => const Color(0xFF69C9D0),
    _ => AppTheme.socialPostColor,
  };

  @override
  Widget build(BuildContext context) {
    final pColor = _platformColor(post.platform);
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(16),
      decoration: AppTheme.cardDecoration(accentBorder: pColor),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: platform + timestamp
          Row(
            children: [
              TypeBadge(label: post.platform, color: pColor, icon: _platformIcon(post.platform)),
              const Spacer(),
              TimestampLabel(time: post.unlockTimestamp, showDate: false),
            ],
          ),
          const SizedBox(height: 12),
          // Author row
          Row(
            children: [
              CircleAvatar(
                radius: 18,
                backgroundColor: pColor.withOpacity(0.15),
                child: Text(
                  post.author.isNotEmpty ? post.author[0].toUpperCase() : '?',
                  style: TextStyle(color: pColor, fontWeight: FontWeight.bold, fontSize: 14),
                ),
              ),
              const SizedBox(width: 10),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(post.author, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14)),
                  Text('@${post.handle}', style: Theme.of(context).textTheme.labelSmall),
                ],
              ),
            ],
          ),
          const SizedBox(height: 12),
          // Content
          if (post.imageUrl != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Image.network(post.imageUrl!, fit: BoxFit.cover, width: double.infinity),
              ),
            ),
          Text(post.content, style: Theme.of(context).textTheme.bodyMedium?.copyWith(height: 1.6)),
          const SizedBox(height: 12),
          // Engagement
          Row(
            children: [
              Icon(Icons.favorite_border, size: 16, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text('${post.likes}', style: Theme.of(context).textTheme.bodySmall),
              const SizedBox(width: 20),
              Icon(Icons.chat_bubble_outline, size: 16, color: AppTheme.textMuted),
              const SizedBox(width: 4),
              Text('${post.comments}', style: Theme.of(context).textTheme.bodySmall),
              const Spacer(),
              Icon(Icons.share_outlined, size: 16, color: AppTheme.textMuted),
            ],
          ),
        ],
      ),
    );
  }
}
